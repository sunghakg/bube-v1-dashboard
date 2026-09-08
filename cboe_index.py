# ⚠ 자동 벤더링 사본 — 원본은 bube-v1-trader/backtest/cboe_index.py (단일 소스).
#   daily_backtest 워크플로가 매 실행 원본으로 덮어씀. 이 파일 직접 수정 금지.
"""Cboe 공식 CDN 지수 일봉 로더 (백테 경로 전용).

## 왜 필요한가 (2026-08-31 실측)

yfinance `^VIX9D`가 **2026-07-17 이후 조용히 멈췄다** — 응답은 성공하고 행만
안 온다. 캐논 백테 프레임에서 vix9d가 30 거래일 결측이었고, 아무 경고도 없었다.

무성(無聲)인 이유는 두 겹이다.

1. `regime_canon.prepare_signal_frame`은 vix9d를 **dropna 뒤에** 부착한다.
   → 결측이 행을 지우지 않으므로 PR#67 `_assert_no_gaps` 가드에 안 걸린다.
2. `regime_canon.classify`의 fast-BEAR 마스크는 `df["vix9d"].notna()`로 닫힌다.
   → 값이 없으면 **오버라이드가 그냥 안 걸린다**. 예외도 로그도 없다.

즉 크래시 브레이크(VIX9D/VIX>1.05 즉시 BEAR)가 무경고로 해제된 상태였다.
2026-07-20~08-31 구간은 VIX9D/VIX≈0.83인 평온장이라 **실현 피해는 0일**이지만,
하필 그 장치가 필요한 국면에서만 조용히 없는 구조였다.

## 라이브는 왜 멀쩡했나

봇(`bube_trader._fetch_index_close`)은 2026-07-11 PR#43 사건 뒤 이미
**Cboe CDN 1차 → yfinance 폴백**으로 바꿔 뒀다 (2026-08-31 프리마켓 런 로그:
`VIX9D source: Cboe 공식`). 백테만 단일 벤더로 남아 있었고, 그래서 봇↔백테가
또 갈라져 있었다 — 2026-07-09 라이브 −25.9%를 만든 '감지기 코드 이중화'와
같은 계열의 재발이다. 이 모듈은 백테 쪽을 봇과 같은 산출원으로 맞춘다.

## 소스 교체가 과거 수치를 바꾸는가 — 실측 (2009-04-20~2026-08-31, 4,094행)

  · Cboe vs yfinance 값 불일치: 3,906 중첩일 중 52일 (2018~2019 집중, 최대 1.22)
  · fast-BEAR 비율(>1.05) 판정 뒤집힘: **1일** (2019-01-03)
  · 최종 레짐 라벨 차이: **0일** — 그날은 투표만으로도 이미 BEAR
  · Cboe 내부 결측(첫 유효행 이후): **0일** ↔ yfinance 30일

⇒ 헤드라인 무변, 결측만 메워진다. 값이 어긋난 52일은 Cboe가 산출원(정본)이다.
"""
from __future__ import annotations

import io
import urllib.request

import pandas as pd

CBOE_INDEX_CSV = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{sym}_History.csv"

# 심볼별 전체 히스토리 메모 (프로세스 1회 fetch). 스윕이 get_regime_series를
# 수백 번 부르므로 없으면 CDN을 그만큼 때린다. VIX9D 전 구간이 3,937행이라 가볍다.
_MEMO: dict[str, pd.DataFrame] = {}


def parse_history_ohlc(text: str) -> pd.DataFrame:
    """Cboe daily_prices CSV(DATE,OPEN,HIGH,LOW,CLOSE) → OHLC DataFrame.

    CLOSE가 빈 행은 드랍 — `parse_history_csv`와 같은 판정이며, 그 함수가
    이 결과의 CLOSE 열을 그대로 쓴다(파서는 여기 하나뿐).
    O/H/L은 결측이면 CLOSE로 메운다: Cboe는 1990년대 초 일부 행에 종가만 싣고,
    지수라 그 날의 O=H=L=C로 두는 편이 열을 비우는 것보다 다운스트림에 안전하다."""
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().upper() for c in df.columns]
    idx = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    out = pd.DataFrame(index=idx)
    for col in ("OPEN", "HIGH", "LOW", "CLOSE"):
        out[col.capitalize()] = pd.to_numeric(df.get(col), errors="coerce").values
    out = out[out["Close"].notna()]
    for col in ("Open", "High", "Low"):
        out[col] = out[col].fillna(out["Close"])
    out.index.name = None
    return out


def parse_history_csv(text: str) -> pd.Series:
    """Cboe daily_prices CSV(DATE,OPEN,HIGH,LOW,CLOSE) → Close Series(DatetimeIndex).

    값 없는 행은 드랍 — NaN을 남기지 않아 다운스트림 reindex에서 결측일로
    자연 처리된다. (봇 `bube_trader._parse_cboe_history_csv`와 동일 시맨틱;
    tests/test_vix9d_source.py가 두 구현의 동치를 고정한다.)"""
    return parse_history_ohlc(text)["Close"].rename("Close")


def fetch_ohlc(sym: str, start: str, end: str, *, timeout: int = 20) -> pd.DataFrame:
    """Cboe 공식 CDN 지수 일봉 OHLC. 실패 시 예외 전파 (호출부가 폴백 결정).

    Cboe CSV는 EOD 확정치만 실려 장중 partial bar가 없다.
    연구 경로(`local/strategies`의 `load_ohlc`)가 봇·백테와 같은 산출원을 쓰도록
    OHLC 형태로도 내준다 — Close만 필요한 호출자는 `fetch_close`를 쓴다."""
    if sym not in _MEMO:
        req = urllib.request.Request(CBOE_INDEX_CSV.format(sym=sym),
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            _MEMO[sym] = parse_history_ohlc(r.read().decode())
    df = _MEMO[sym].loc[str(start):str(end)]
    if df.empty:
        raise RuntimeError(f"Cboe {sym} CSV empty after date filter ({start}~{end})")
    return df


def fetch_close(sym: str, start: str, end: str, *, timeout: int = 20) -> pd.Series:
    """Cboe 공식 CDN 지수 일봉 종가. 실패 시 예외 전파 (호출부가 폴백 결정)."""
    return fetch_ohlc(sym, start, end, timeout=timeout)["Close"].rename("Close")
