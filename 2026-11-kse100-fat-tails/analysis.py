"""KSE-100 weekly return distribution compared with a fitted normal distribution."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date

import pandas as pd
from scipy import stats


@dataclass
class Summary:
    returns: pd.Series
    n: int
    mean: float
    std: float
    skew: float
    excess_kurtosis: float


def load_closes(path: str, keep_today: bool = False) -> pd.Series:
    """Daily closes from an Investing.com CSV, oldest first, excluding today's intraday row."""
    df = pd.read_csv(path, thousands=",", encoding="utf-8-sig")
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    if not keep_today:
        df = df[df["Date"].dt.date != date.today()]
    df = df.sort_values("Date")
    if df["Date"].duplicated().any():
        raise ValueError("duplicate dates in input")
    return df.set_index("Date")["Price"].astype(float)


def weekly_returns(close: pd.Series) -> pd.Series:
    """Simple returns between the last closes of consecutive Mon-Fri weeks, labelled by Friday."""
    weekly_close = close.resample("W-FRI").last().dropna()
    if weekly_close.index[-1] > close.index[-1]:
        weekly_close = weekly_close.iloc[:-1]
    return weekly_close.pct_change().dropna().rename("weekly_return")


def summarise(r: pd.Series) -> Summary:
    return Summary(
        returns=r,
        n=len(r),
        mean=r.mean(),
        std=r.std(ddof=1),
        skew=float(stats.skew(r, bias=False)),
        excess_kurtosis=float(stats.kurtosis(r, bias=False)),
    )


def bell_curve_tail_prob(s: Summary, threshold: float) -> float:
    """P(|weekly return| > threshold) under a normal with the sample mean and std."""
    return float(stats.norm.sf(threshold, s.mean, s.std) + stats.norm.cdf(-threshold, s.mean, s.std))


def report(s: Summary, week: pd.Timestamp, tail_threshold: float) -> None:
    r = s.returns
    print(f"Weekly returns: N = {s.n} ({r.index[0]:%d %b %Y} to {r.index[-1]:%d %b %Y})")
    print(f"  mean = {s.mean:+.2%}   std = {s.std:.2%}")
    print(f"  skew = {s.skew:+.2f}   excess kurtosis = {s.excess_kurtosis:.2f}\n")

    v = r.loc[week]
    z = (v - s.mean) / s.std
    n_ge = int((r >= v).sum())
    print(f"Week ending {week:%d %b %Y}: {v:+.2%}")
    print(f"  z-score    = {z:+.2f}")
    print(f"  percentile = {(r < v).mean():.1%}")
    if v > 0:
        print(f"  {n_ge} of {s.n} weeks were this good or better (~1 every {s.n / n_ge:.0f} weeks)")
        print(f"  bell curve expects {stats.norm.sf(z) * s.n:.1f} such weeks\n")

    print("Tail counts: actual vs bell curve")
    zs = (r - s.mean) / s.std
    for k in (2, 3, 4):
        actual = int((zs.abs() > k).sum())
        expected = s.n * 2 * stats.norm.sf(k)
        print(f"  |z| > {k} (|move| > {k * s.std:.1%}): actual {actual:>3}, "
              f"bell curve {expected:6.2f} -> {actual / expected:.1f}x")

    p = bell_curve_tail_prob(s, tail_threshold)
    actual = int((r.abs() > tail_threshold).sum())
    print(f"\nMoves beyond ±{tail_threshold:.0%}: actual {actual}, bell curve {p * s.n:.2f} "
          f"(once every ~{1 / (p * 52):.0f} years)")

    print("\nLargest weekly moves:")
    for d, x in r.reindex(r.abs().sort_values(ascending=False).index).head(6).items():
        print(f"  {d:%d %b %Y}: {x:+.2%} (z = {(x - s.mean) / s.std:+.1f})")

    jb = stats.jarque_bera(r)
    print(f"\nJarque-Bera = {jb.statistic:.0f}, p = {jb.pvalue:.1e}")


def resolve_week(r: pd.Series, week: str | None) -> pd.Timestamp:
    if week is None:
        return r.index[-1]
    ts = pd.Timestamp(week)
    if ts not in r.index:
        raise SystemExit(f"{week} is not a week label; expected the week's Friday date")
    return ts


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="Investing.com daily historical data CSV")
    ap.add_argument("--week", help="Friday date of the week (default: latest complete week)")
    ap.add_argument("--tail", type=float, default=0.11, help="tail threshold as a decimal (default: 0.11)")
    ap.add_argument("--keep-today", action="store_true", help="keep a row dated today")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    s = summarise(weekly_returns(load_closes(args.csv, args.keep_today)))
    report(s, resolve_week(s.returns, args.week), args.tail)
