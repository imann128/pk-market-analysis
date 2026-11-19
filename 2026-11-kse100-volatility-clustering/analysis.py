"""Volatility clustering in KSE-100 daily returns."""
from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd


def load_closes(path: str, keep_today: bool = False, end: str | None = None) -> pd.Series:
    """Daily closes from an Investing.com CSV, oldest first, excluding today's intraday row and rows after `end`."""
    df = pd.read_csv(path, thousands=",", encoding="utf-8-sig")
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    if not keep_today:
        df = df[df["Date"].dt.date != date.today()]
    if end is not None:
        df = df[df["Date"] <= pd.Timestamp(end)]
    df = df.sort_values("Date")
    if df["Date"].duplicated().any():
        raise ValueError("duplicate dates in input")
    return df.set_index("Date")["Price"].astype(float)


def daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change().dropna().rename("daily_return")


def trading_days_per_year(r: pd.Series) -> float:
    return len(r) / ((r.index[-1] - r.index[0]).days / 365.25)


def rolling_vol(r: pd.Series, window: int = 20) -> pd.Series:
    """Annualised rolling standard deviation, using only the trailing window at each date."""
    return (r.rolling(window).std() * np.sqrt(trading_days_per_year(r))).dropna().rename("vol")


def next_day_after_big(r: pd.Series, quantile: float = 0.95) -> dict[str, float]:
    """Absolute next-day return after days above the |r| quantile versus after all other days.

    Missing values mark excluded days; pairs involving them are skipped.
    """
    a = r.abs()
    big = a > a.quantile(quantile)
    nxt = a.shift(-1)
    valid = a.notna() & nxt.notna()
    after_big, after_other = nxt[big & valid], nxt[~big & valid]
    return {
        "n_big": int(len(after_big)),
        "mean_big": float(after_big.mean()),
        "mean_other": float(after_other.mean()),
        "median_big": float(after_big.median()),
        "median_other": float(after_other.median()),
    }


def clustering_summary(r: pd.Series) -> dict[str, float]:
    nd = next_day_after_big(r)
    return {
        "n": int(r.notna().sum()),
        "ac1_r": r.autocorr(1),
        "ac1_abs": r.abs().autocorr(1),
        "ac5_abs": r.abs().autocorr(5),
        "ratio_median": nd["median_big"] / nd["median_other"],
        "ratio_mean": nd["mean_big"] / nd["mean_other"],
    }


def robustness_samples(r: pd.Series, scale_window: int = 250) -> dict[str, pd.Series]:
    """Sub-periods, crisis exclusion, and returns scaled by trailing volatility.

    Crisis days are masked rather than dropped, so days on either side of a
    crisis are not treated as consecutive.
    """
    crisis = (((r.index >= "2020-02-01") & (r.index <= "2020-06-30"))
              | ((r.index >= "2026-02-01") & (r.index <= "2026-05-31")))
    scaled = (r / r.rolling(scale_window).std().shift(1)).dropna()
    return {
        "Full sample": r,
        "2017-2019": r["2017":"2019"],
        "2021-2024": r["2021":"2024"],
        "Excl. Feb-Jun 2020, Feb-May 2026": r.mask(crisis),
        f"Scaled by past {scale_window}-day vol": scaled,
    }


def report(r: pd.Series, window: int) -> None:
    print(f"Daily returns: N = {len(r)} ({r.index[0]:%d %b %Y} to {r.index[-1]:%d %b %Y}), "
          f"{trading_days_per_year(r):.0f} trading days per year")
    gaps = int((r.index.to_series().diff().dt.days > 3).sum())
    print(f"Returns spanning more than 3 calendar days (holidays): {gaps}\n")

    print("Autocorrelation: return vs absolute return")
    for k in (1, 2, 5, 10, 20):
        print(f"  lag {k:>2}: r {r.autocorr(k):+.3f}   |r| {r.abs().autocorr(k):+.3f}")

    nd = next_day_after_big(r)
    print(f"\nNext-day |move| after a top-5% day (n = {nd['n_big']}) vs after other days")
    print(f"  median {nd['median_big']:.2%} vs {nd['median_other']:.2%} -> "
          f"{nd['median_big'] / nd['median_other']:.1f}x")
    print(f"  mean   {nd['mean_big']:.2%} vs {nd['mean_other']:.2%} -> "
          f"{nd['mean_big'] / nd['mean_other']:.1f}x")

    print("\nRobustness")
    print(f"  {'Sample':<36}{'N':>6}{'ac1 r':>9}{'ac1 |r|':>9}{'ac5 |r|':>9}{'median x':>10}{'mean x':>8}")
    for name, x in robustness_samples(r).items():
        c = clustering_summary(x)
        print(f"  {name:<36}{c['n']:>6}{c['ac1_r']:>+9.3f}{c['ac1_abs']:>+9.3f}{c['ac5_abs']:>+9.3f}"
              f"{c['ratio_median']:>10.2f}{c['ratio_mean']:>8.2f}")

    v = rolling_vol(r, window)
    p10, p25, p50, p75, p90 = np.percentile(v, [10, 25, 50, 75, 90])
    print(f"\n{window}-day annualised volatility")
    print(f"  percentiles 10/25/50/75/90: {p10:.1%} / {p25:.1%} / {p50:.1%} / {p75:.1%} / {p90:.1%}")
    print(f"  max    {v.max():.1%} on {v.idxmax():%d %b %Y}")
    print(f"  min    {v.min():.1%} on {v.idxmin():%d %b %Y}")
    print(f"  latest {v.iloc[-1]:.1%} on {v.index[-1]:%d %b %Y}")
    print("\nYearly peaks:")
    for y, g in v.groupby(v.index.year):
        print(f"  {y}: {g.max():.1%} on {g.idxmax():%d %b}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="Investing.com daily historical data CSV")
    ap.add_argument("--window", type=int, default=20, help="rolling window in trading days (default: 20)")
    ap.add_argument("--end", help="last date to include, YYYY-MM-DD (default: all complete rows)")
    ap.add_argument("--keep-today", action="store_true", help="keep a row dated today")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    report(daily_returns(load_closes(args.csv, args.keep_today, args.end)), args.window)
