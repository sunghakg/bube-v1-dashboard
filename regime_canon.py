# ⚠ 자동 벤더링 사본 — 원본은 bube-v1-trader/regime_canon.py (단일 소스).
#   daily_backtest 워크플로가 매 실행 원본으로 덮어씀. 이 파일 직접 수정 금지.
# -*- coding: utf-8 -*-
"""캐논 레짐 감지기 — 단일 소스 (single source of truth).

봇(bube_trader.py)과 백테(backtest/regime_detector.py)가 이 모듈 하나를 import.
규칙이 두 곳에 존재해서 생기는 감지기 이중화(2026-07-09 라이브 -25.9% 검증에서
발견, gap -16.2pp)를 구조적으로 차단한다.

검증 근거: 캐논 16y 백테 Cal 2.55 / MDD -23.5% (Phase 1 등조건 감지기 3종 비교,
2026-07-09, local/strategies/detector_unify_2026_07_09/DECISION_PACKET.md).
★이 파일의 규칙 변경 = 그 검증의 무효 = 재검증 대상.

신호 5종 (모두 t-1 종가로 t일 결정 — look-ahead-safe):
  1. VIX 수준      : ≤18 BULL / >30 BEAR
  2. QQQ 주간 RSI14: ≥60 BULL / <40 BEAR (완결 주만, shift 1일)
  3. SPY vs 200일선: ±2% 밴드
  4. SOXL vs 50일선: ±5% 밴드
  5. SOXL 5일 모멘텀: ±5%

분류 soft (운영 캐논): BEAR ≥2표 → BEAR / BULL ≥3표 → BULL / else NEUTRAL
  (비대칭 = 위험회피: 곰은 2표, 소는 3표 필요)
fast-BEAR: VIX9D(t-1)/VIX(t-1) > 1.05 → 분류·평활과 무관하게 즉시 BEAR.
"""
from __future__ import annotations
from typing import Literal
import pandas as pd

VIX9D_BACKWARDATION_THR = 1.05
RSI_PERIOD = 14

# 각 신호의 (bear_thr, bull_thr, higher_is_bull) — 검증본 고정값
VIX_BEAR_THR, VIX_BULL_THR = 30, 18
RSI_BEAR_THR, RSI_BULL_THR = 40, 60
MA200_BAND = 0.02
MA50_BAND = 0.05
MOM5_BAND = 0.05

SIGNAL_COLS = ["signal_vix", "signal_rsi", "signal_ma200", "signal_trend", "signal_mom"]


def rsi_wilder(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Classic Wilder RSI (EMA alpha=1/period)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def weekly_rsi_daily(qqq_close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """QQQ 주간(W-FRI) Wilder RSI → 일별 ffill → shift(1).

    각 거래일은 '가장 최근 완결된 주'의 RSI를 사용 (look-ahead 없음).
    ⚠ Wilder는 재귀식 — 웜업으로 시리즈 앞에 ≥365일 여분 데이터 필요
    (yangbyungi_backtest.qqq_weekly_rsi의 prepend_days=365와 동일 요건)."""
    weekly = qqq_close.resample("W-FRI").last().dropna()
    rsi_w = rsi_wilder(weekly, period=period)
    return rsi_w.reindex(qqq_close.index, method="ffill").shift(1).ffill()


def _vote(value: float, bear_thr: float, bull_thr: float,
          higher_is_bull: bool = True) -> str:
    if higher_is_bull:
        if value >= bull_thr:
            return "BULL"
        elif value < bear_thr:
            return "BEAR"
        return "NEUTRAL"
    else:
        if value <= bull_thr:
            return "BULL"
        elif value > bear_thr:
            return "BEAR"
        return "NEUTRAL"


def prepare_signal_frame(spy_close: pd.Series, soxl_close: pd.Series,
                         vix_close: pd.Series, qqq_close: pd.Series,
                         vix9d_close: pd.Series | None = None) -> pd.DataFrame:
    """일봉 종가 시리즈들 → t-1 시프트된 시그널 프레임 (index=SPY 거래일).

    연산 순서는 종전 backtest/regime_detector.get_regime_series와 문자 그대로
    동일 (등가성 골든테스트로 고정). vix9d는 dropna 이후 부착 — NaN이어도
    행이 죽지 않고 해당일 fast만 비활성."""
    spy_ma200 = spy_close.rolling(200).mean()
    soxl_ma50 = soxl_close.rolling(50).mean()
    soxl_mom5 = soxl_close.pct_change(5)
    qqq_rsi = weekly_rsi_daily(qqq_close)

    df = pd.DataFrame(index=spy_close.index)
    df["vix"] = vix_close.reindex(df.index).shift(1)
    df["qqq_rsi"] = qqq_rsi.reindex(df.index)   # weekly_rsi_daily 내부에서 이미 shift(1)
    df["spy_close"] = spy_close.shift(1)
    df["spy_ma200"] = spy_ma200.shift(1)
    df["soxl_close"] = soxl_close.shift(1)
    df["soxl_ma50"] = soxl_ma50.shift(1)
    df["soxl_mom5"] = soxl_mom5.shift(1)
    df = df.dropna()

    if vix9d_close is not None:
        df["vix9d"] = vix9d_close.reindex(df.index).shift(1)
    return df


def classify(df: pd.DataFrame,
             mode: Literal["majority", "strict", "soft"] = "soft",
             vix9d_fast_bear: bool = True) -> pd.DataFrame:
    """시그널 프레임 → 투표 → regime 분류 (+ fast-BEAR 즉시 오버라이드).

    signal_*/bull_votes/bear_votes/regime 컬럼을 추가해 반환.
    종전 regime_detector 분류 블록의 verbatim 이식."""
    df = df.copy()
    df["signal_vix"] = df["vix"].apply(
        lambda v: _vote(v, bear_thr=VIX_BEAR_THR, bull_thr=VIX_BULL_THR, higher_is_bull=False)
    )
    df["signal_rsi"] = df["qqq_rsi"].apply(
        lambda v: _vote(v, bear_thr=RSI_BEAR_THR, bull_thr=RSI_BULL_THR, higher_is_bull=True)
    )
    df["signal_ma200"] = df.apply(
        lambda r: "BULL" if r["spy_close"] > r["spy_ma200"] * (1 + MA200_BAND)
                  else ("BEAR" if r["spy_close"] < r["spy_ma200"] * (1 - MA200_BAND) else "NEUTRAL"),
        axis=1
    )
    df["signal_trend"] = df.apply(
        lambda r: "BULL" if r["soxl_close"] > r["soxl_ma50"] * (1 + MA50_BAND)
                  else ("BEAR" if r["soxl_close"] < r["soxl_ma50"] * (1 - MA50_BAND) else "NEUTRAL"),
        axis=1
    )
    df["signal_mom"] = df["soxl_mom5"].apply(
        lambda v: "BULL" if v > MOM5_BAND else ("BEAR" if v < -MOM5_BAND else "NEUTRAL")
    )

    df["bull_votes"] = df[SIGNAL_COLS].apply(lambda r: (r == "BULL").sum(), axis=1)
    df["bear_votes"] = df[SIGNAL_COLS].apply(lambda r: (r == "BEAR").sum(), axis=1)
    df["neutral_votes"] = 5 - df["bull_votes"] - df["bear_votes"]

    if mode == "majority":
        # whichever has more votes; tie → BEAR (risk-off bias)
        def _classify(r):
            if r["bear_votes"] >= r["bull_votes"]:
                return "BEAR" if r["bear_votes"] >= 2 else ("BULL" if r["bull_votes"] >= 2 else "NEUTRAL")
            else:
                return "BULL" if r["bull_votes"] >= 2 else "NEUTRAL"
        df["regime"] = df.apply(_classify, axis=1)
    elif mode == "strict":
        # ≥3 BEAR votes → BEAR, ≥3 BULL votes → BULL, else NEUTRAL
        def _classify(r):
            if r["bear_votes"] >= 3:
                return "BEAR"
            elif r["bull_votes"] >= 3:
                return "BULL"
            return "NEUTRAL"
        df["regime"] = df.apply(_classify, axis=1)
    else:  # soft
        # ≥2 BEAR → BEAR; ≥3 BULL → BULL; else NEUTRAL
        def _classify(r):
            if r["bear_votes"] >= 2:
                return "BEAR"
            elif r["bull_votes"] >= 3:
                return "BULL"
            return "NEUTRAL"
        df["regime"] = df.apply(_classify, axis=1)

    # VIX9D fast-BEAR 오버라이드 — 즉시 (look-ahead-safe: t-1 값, prepare에서 shift 완료)
    if vix9d_fast_bear and "vix9d" in df.columns:
        mask = (df["vix9d"] / df["vix"] > VIX9D_BACKWARDATION_THR) & df["vix9d"].notna()
        df.loc[mask, "regime"] = "BEAR"

    return df
