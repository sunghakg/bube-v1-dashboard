#!/usr/bin/env python3
"""Global M2 → SOXX 78일 선행 가설 검증 스크립트.

블로그 주장: "Global M2를 약 78일 선행시키면 2025년 이후 SOXX와 거의 똑같이
움직인다. 따라서 지금 M2가 하락 전환이면 7월~3분기 큰 하락이 온다."

이 스크립트는 그 주장을 4가지 통계 검정으로 검증한다:
  [T1] 레벨 상관 lag 스캔  — 상관을 최대화하는 선행일수가 정말 ~78일인가
  [T2] 구간 안정성          — 그 선행일수가 다른 기간에서도 유지되는가 (과적합 체크)
  [T3] 변화율 상관          — 추세를 제거해도(4주 로그수익률) 상관이 남는가
                              (두 우상향 시계열의 레벨 상관은 대부분 허구 상관)
  [T4] 예측력               — M2 변화(78일 전)가 SOXX 이후 4주 수익률의
                              방향/크기를 실제로 맞히는가 (hit-rate + OLS)
  [P]  플라시보             — SOXX와 무관한 랜덤워크 추세로도 레벨 상관 0.9가
                              쉽게 나옴을 보여 시각적 '커플링'의 증거력을 측정

데이터:
  SOXX/환율  yfinance
  US M2      FRED fredgraph.csv (WM2NS, 주간)
  EU M2      ECB Data API (BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E)
  CN/JP M2   기본 생략(공개 API 부재). --m2-csv 로 TradingView Global M2
             인디케이터 내보내기 CSV를 주면 그 시계열을 그대로 사용(최고 정합).

사용:
  python verify_m2_lead.py                  # US+EU 합성 M2로 검증
  python verify_m2_lead.py --m2-csv m2.csv  # TradingView 내보내기 사용
  python verify_m2_lead.py --start 2023-01-01
"""
from __future__ import annotations

import argparse
import io
import sys
import urllib.request

import numpy as np
import pandas as pd

CLAIMED_LEAD_DAYS = 78
LAG_SCAN_DAYS = range(-60, 181, 2)   # 음수 = M2가 오히려 후행하는 경우도 탐색
CHANGE_WINDOW_DAYS = 28              # 변화율 검정용 4주 창


def _http_csv(url: str) -> pd.DataFrame:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return pd.read_csv(io.StringIO(r.read().decode("utf-8")))


def fetch_us_m2(start: str) -> pd.Series:
    df = _http_csv(
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id=WM2NS&cosd={start}"
    )
    df.columns = ["date", "usd_bn"]
    s = pd.Series(
        pd.to_numeric(df["usd_bn"], errors="coerce").values,
        index=pd.to_datetime(df["date"]), name="US",
    ).dropna()
    return s * 1e9  # billions USD → USD


def fetch_eu_m2(start: str) -> pd.Series:
    url = (
        "https://data-api.ecb.europa.eu/service/data/BSI/"
        "M.U2.Y.V.M20.X.1.U2.2300.Z01.E"
        f"?startPeriod={start[:7]}&format=csvdata"
    )
    df = _http_csv(url)
    s = pd.Series(
        pd.to_numeric(df["OBS_VALUE"], errors="coerce").values,
        index=pd.to_datetime(df["TIME_PERIOD"]) + pd.offsets.MonthEnd(0),
        name="EU",
    ).dropna()
    return s * 1e6  # millions EUR → EUR


def fetch_yf(ticker: str, start: str) -> pd.Series:
    import yfinance as yf

    df = yf.download(ticker, start=start, progress=False, auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"yfinance empty for {ticker}")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.rename(ticker)


def build_global_m2(start: str, m2_csv: str | None) -> pd.Series:
    """일간 인덱스로 ffill된 Global M2 (USD) 시계열."""
    if m2_csv:
        raw = pd.read_csv(m2_csv)
        date_col = raw.columns[0]
        val_col = raw.columns[-1]
        s = pd.Series(
            pd.to_numeric(raw[val_col], errors="coerce").values,
            index=pd.to_datetime(raw[date_col]), name="GlobalM2",
        ).dropna().sort_index()
        print(f"[data] TradingView CSV 사용: {m2_csv} ({len(s)} rows)")
        return s

    us = fetch_us_m2(start)
    print(f"[data] US M2(WM2NS): {len(us)}주, 마지막 {us.index[-1].date()}")
    parts = {"US": us}
    try:
        eu_eur = fetch_eu_m2(start)
        eurusd = fetch_yf("EURUSD=X", start)
        eu = (eu_eur.reindex(eurusd.index, method="ffill") * eurusd).dropna()
        parts["EU"] = eu
        print(f"[data] EU M2(ECB)×EURUSD: 마지막 {eu.index[-1].date()}")
    except Exception as e:  # EU 실패해도 US 단독으로 진행
        print(f"[warn] EU M2 수집 실패 → US 단독으로 진행: {e}")

    daily = pd.date_range(us.index.min(), max(p.index.max() for p in parts.values()))
    total = sum(p.reindex(daily, method="ffill") for p in parts.values())
    total = total.dropna().rename("GlobalM2")
    print(f"[data] 합성 Global M2 구성: {'+'.join(parts)} "
          "(CN/JP 제외 — 정확 재현은 --m2-csv 사용)")
    return total


def lag_corr_curve(soxx: pd.Series, m2_daily: pd.Series,
                   lags=LAG_SCAN_DAYS) -> pd.Series:
    """corr( log SOXX_t , log M2_{t-k} ) — k>0이면 M2가 k일 선행."""
    out = {}
    ls = np.log(soxx)
    lm = np.log(m2_daily)
    for k in lags:
        shifted = lm.shift(k, freq="D").reindex(ls.index).dropna()
        common = ls.loc[shifted.index]
        if len(common) > 60:
            out[k] = float(np.corrcoef(common, shifted)[0, 1])
    return pd.Series(out).sort_index()


def change_corr(soxx: pd.Series, m2_daily: pd.Series, lead: int,
                win: int = CHANGE_WINDOW_DAYS) -> tuple[float, int]:
    """추세 제거: 4주 로그변화율끼리의 상관 (lead일 선행 적용)."""
    ds = np.log(soxx).diff(int(win * 5 / 7))          # 거래일 기준 ≈4주
    dm = np.log(m2_daily).diff(win).shift(lead, freq="D")
    df = pd.concat([ds, dm.reindex(ds.index)], axis=1).dropna()
    # 겹침 창으로 인한 자기상관 → 비중복 표본만 사용해 보수적으로 검정
    df_nonovl = df.iloc[::win]
    r = float(df_nonovl.corr().iloc[0, 1])
    return r, len(df_nonovl)


def predictive_test(soxx: pd.Series, m2_daily: pd.Series, lead: int,
                    win: int = CHANGE_WINDOW_DAYS):
    """M2 변화 → SOXX '이후' 4주 수익률: hit-rate와 OLS 기울기.

    가설이 참이면 SOXX_t ≈ M2_{t-lead} 이므로, t 이후 win일간의 SOXX 변화는
    M2의 (t-lead)~(t-lead+win) 변화에 대응한다. 그 창은 t 시점에 이미 관측
    가능하며, 시프트는 (lead - win)일이다.
    """
    m2_chg = np.log(m2_daily).diff(win)
    fwd = np.log(soxx).shift(-int(win * 5 / 7)) - np.log(soxx)
    sig = m2_chg.shift(lead - win, freq="D").reindex(fwd.index)
    df = pd.concat([sig.rename("sig"), fwd.rename("fwd")], axis=1).dropna()
    df = df.iloc[::win]  # 비중복 표본
    if len(df) < 8:
        return None
    hit = float((np.sign(df.sig) == np.sign(df.fwd)).mean())
    x = df.sig.values
    y = df.fwd.values
    beta, alpha = np.polyfit(x, y, 1)
    resid = y - (beta * x + alpha)
    se = resid.std(ddof=2) / (x.std(ddof=1) * np.sqrt(len(x)))
    return {"n": len(df), "hit_rate": hit, "beta": float(beta),
            "t_stat": float(beta / se) if se > 0 else np.nan}


def placebo_level_corr(soxx: pd.Series, n_sims: int = 500,
                       seed: int = 42) -> np.ndarray:
    """SOXX와 무관한 랜덤워크(드리프트 有)와의 최대 레벨 상관 분포."""
    rng = np.random.default_rng(seed)
    ls = np.log(soxx).values
    n = len(ls)
    best = np.empty(n_sims)
    for i in range(n_sims):
        rw = np.cumsum(rng.normal(0.0005, 0.01, n))
        # lag 스캔과 동일하게 '가장 잘 맞는 시프트'를 골라주는 과정을 흉내
        cands = [np.corrcoef(ls[k:], rw[: n - k])[0, 1]
                 for k in range(0, 120, 5)]
        best[i] = np.nanmax(np.abs(cands))
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--claim-window", default="2025-01-01",
                    help="블로그가 커플링을 주장한 구간 시작일")
    ap.add_argument("--m2-csv", default=None,
                    help="TradingView Global M2 인디케이터 내보내기 CSV 경로")
    ap.add_argument("--plot", action="store_true", help="차트 PNG 저장")
    a = ap.parse_args()

    soxx = fetch_yf("SOXX", a.start)
    print(f"[data] SOXX: {len(soxx)}일, 마지막 {soxx.index[-1].date()} "
          f"종가 {soxx.iloc[-1]:.2f}")
    m2 = build_global_m2(a.start, a.m2_csv)

    soxx_claim = soxx[soxx.index >= a.claim_window]
    soxx_prior = soxx[soxx.index < a.claim_window]

    print("\n===== [T1] 레벨 상관 lag 스캔 (주장 구간:", a.claim_window, "~) =====")
    curve = lag_corr_curve(soxx_claim, m2)
    k_star = int(curve.idxmax())
    print(f"  최적 선행일수 k* = {k_star}일  (corr={curve.max():.3f})")
    print(f"  주장된 78일에서의 corr = {curve.get(78, curve.get(k_star)):.3f}")
    verdict_t1 = abs(k_star - CLAIMED_LEAD_DAYS) <= 21
    print(f"  → 78일 주장과 {'대체로 일치' if verdict_t1 else '불일치'} "
          f"(허용오차 ±21일)")

    print("\n===== [T2] 선행일수 안정성 (이전 구간과 비교) =====")
    if len(soxx_prior) > 120:
        curve_prior = lag_corr_curve(soxx_prior, m2)
        k_prior = int(curve_prior.idxmax())
        print(f"  {a.start}~{a.claim_window} 구간 최적 k = {k_prior}일 "
              f"(corr={curve_prior.max():.3f})")
        stable = abs(k_prior - k_star) <= 21
        print(f"  → 선행일수가 {'안정적' if stable else '구간마다 달라짐 → 과적합 신호'}")
    else:
        print("  (이전 구간 데이터 부족 — --start 를 더 과거로)")

    print("\n===== [T3] 변화율(추세 제거) 상관 =====")
    r_lvl = curve.get(78, np.nan)
    r_chg, n_chg = change_corr(soxx_claim, m2, CLAIMED_LEAD_DAYS)
    print(f"  레벨 corr(78d lead)  = {r_lvl:.3f}")
    print(f"  4주 변화율 corr(78d) = {r_chg:.3f}  (비중복 n={n_chg})")
    if not np.isnan(r_chg) and abs(r_chg) < 0.3:
        print("  → 레벨 상관은 높지만 변화율 상관이 약함: "
              "'커플링'의 상당 부분이 공통 상승추세(허구 상관)")

    print("\n===== [T4] 예측력 검정 =====")
    pred = predictive_test(soxx, m2, CLAIMED_LEAD_DAYS)
    if pred:
        print(f"  n={pred['n']}  방향 적중률={pred['hit_rate']:.0%}  "
              f"beta={pred['beta']:.2f}  t={pred['t_stat']:.2f}")
        sig = abs(pred["t_stat"]) > 2 and pred["hit_rate"] > 0.6
        print(f"  → 통계적으로 {'유의한 예측력' if sig else '유의한 예측력 없음'} "
              "(t>2 & hit>60% 기준)")
    else:
        print("  표본 부족")

    print("\n===== [P] 플라시보: 무관한 랜덤워크와의 '최적 시프트' 레벨 상관 =====")
    best = placebo_level_corr(soxx_claim)
    q50, q90 = np.quantile(best, [0.5, 0.9])
    print(f"  무관한 시계열도 시프트를 고르면 |corr| 중앙값 {q50:.2f}, "
          f"상위10% {q90:.2f}")
    pct = float((best >= abs(r_lvl)).mean()) if not np.isnan(r_lvl) else np.nan
    print(f"  관측된 레벨 corr {r_lvl:.2f} 이상이 우연히 나올 확률 ≈ {pct:.0%}")

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 1, figsize=(11, 8))
        ax = axes[0]
        ax.plot(soxx.index, soxx, color="tab:red", lw=1.2, label="SOXX")
        ax2 = ax.twinx()
        m2s = m2.shift(CLAIMED_LEAD_DAYS, freq="D")
        ax2.plot(m2s.index, m2s, color="tab:cyan", lw=1.2,
                 label=f"Global M2 (+{CLAIMED_LEAD_DAYS}d)")
        ax.set_title("SOXX vs Global M2 shifted +78d")
        ax.legend(loc="upper left"); ax2.legend(loc="lower right")
        axes[1].plot(curve.index, curve.values)
        axes[1].axvline(78, color="r", ls="--", label="claimed 78d")
        axes[1].axvline(k_star, color="g", ls=":", label=f"best {k_star}d")
        axes[1].set_xlabel("M2 lead (days)"); axes[1].set_ylabel("level corr")
        axes[1].legend(); axes[1].set_title("Lag scan")
        fig.tight_layout()
        fig.savefig("m2_soxx_lead.png", dpi=120)
        print("\n[plot] m2_soxx_lead.png 저장")

    return 0


if __name__ == "__main__":
    sys.exit(main())
