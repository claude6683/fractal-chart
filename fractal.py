"""현재 차트와 비슷한 과거 구간 3개를 찾아 site/data/*.json 으로 저장.
GitHub Actions가 매일 실행합니다. (PC 실행: python fractal.py)
"""
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

INDEXES = {"NASDAQ": "^IXIC", "SP500": "^GSPC", "KOSPI": "^KS11", "BTC": "BTC-USD"}
BPM = {"BTC": 30}         # 한 달 = 며칠(비트코인은 365일 거래). 기본 21
WINDOWS = [40, 60, 90]   # 비교할 최근 거래일 수
TOP, GAP = 3, 120         # 사례 개수, 사례 간 최소 간격(거래일)
OUT = os.path.join("site", "data")


def load(ticker):
    if os.environ.get("FRACTAL_DEMO"):          # 오프라인 테스트용 가짜 데이터
        rng = np.random.default_rng(1)
        n = 9000
        c = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
        o = c * (1 + rng.normal(0, 0.003, n))
        h = np.maximum(o, c) * (1 + abs(rng.normal(0, 0.004, n)))
        l = np.minimum(o, c) * (1 - abs(rng.normal(0, 0.004, n)))
        idx = pd.bdate_range(end="2026-11-20", periods=n)
        return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c}, index=idx)
    import yfinance as yf
    df = yf.download(ticker, start="1985-01-01", auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    return df[(df > 0).all(axis=1)]


def zs(a):
    return (a - a.mean()) / a.std()


def bars(df, a, b, e):
    """a~b 구간 OHLC를 e일 종가=100 으로 환산. i = e 기준 상대 거래일."""
    base = df["Close"].iloc[e]
    seg = df.iloc[a:b + 1]
    out = []
    for k, (o, h, l, c) in enumerate(seg[["Open", "High", "Low", "Close"]].values):
        out.append({"i": a + k - e,
                    "o": round(o / base * 100, 2), "h": round(h / base * 100, 2),
                    "l": round(l / base * 100, 2), "c": round(c / base * 100, 2)})
    return out


def run(name, ticker):
    df = load(ticker)
    close = df["Close"].values
    bpm = BPM.get(name, 21)
    F = 3 * bpm                # 이후 구간 = 3개월
    L = np.log(close)
    n = len(L)
    for W in WINDOWS:
        cs = n - W
        cur = L[cs:]
        zc = zs(cur)
        cret = cur[-1] - cur[0]
        cands = []
        for s in range(0, cs - W):
            if s + W + F > n:
                break
            w = L[s:s + W]
            corr = float(np.mean(zc * zs(w)))
            cands.append((corr - abs((w[-1] - w[0]) - cret), corr, s))
        cands.sort(reverse=True)
        picks = []
        for sc, corr, s in cands:
            if all(abs(s - q[2]) > GAP for q in picks):
                picks.append((sc, corr, s))
            if len(picks) == TOP:
                break
        matches = []
        for sc, corr, s in picks:
            e = s + W - 1
            fwd = {str(k + 1): round((close[e + d] / close[e] - 1) * 100, 1) for k, d in enumerate((bpm, 2 * bpm, 3 * bpm))}
            matches.append({"from": str(df.index[s].date()), "to": str(df.index[e].date()),
                            "corr": round(corr, 2),
                            "ret": round((close[e] / close[s] - 1) * 100, 1),
                            "fwd": fwd, "bars": bars(df, s, e + F, e)})
        data = {"name": name, "W": W, "F": F,
                "asof": str(df.index[-1].date()),
                "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "current": bars(df, cs, n - 1, n - 1),
                "matches": matches}
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, f"{name}_{W}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print(name, W, "OK", [m["from"] for m in matches])


if __name__ == "__main__":
    for nm, tk in INDEXES.items():
        run(nm, tk)
