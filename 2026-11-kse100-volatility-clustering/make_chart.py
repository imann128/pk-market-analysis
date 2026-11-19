"""Rolling annualised volatility of the KSE-100 with labelled peaks."""
import argparse

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from analysis import daily_returns, load_closes, rolling_vol

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e0"
LINE = "#2a78d6"
FILL = "#2a78d6"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="Investing.com daily historical data CSV")
    ap.add_argument("--window", type=int, default=20, help="rolling window in trading days (default: 20)")
    ap.add_argument("--peaks", nargs="*", default=["2020", "2025", "2026"],
                    help="years whose peak volatility is labelled (default: 2020 2025 2026)")
    ap.add_argument("--end", help="last date to include, YYYY-MM-DD")
    ap.add_argument("--keep-today", action="store_true", help="keep a row dated today")
    ap.add_argument("-o", "--out", default="kse100_volatility.png")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    r = daily_returns(load_closes(args.csv, args.keep_today, args.end))
    v = rolling_vol(r, args.window) * 100
    median = v.median()

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15})
    fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ax.fill_between(v.index, 0, v.values, color=FILL, alpha=0.15, linewidth=0, zorder=1)
    ax.plot(v.index, v.values, color=LINE, linewidth=1.6, zorder=2)
    ax.axhline(median, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
    ax.text(v.index[-1] + pd.Timedelta(days=45), median - 1.5, f"Median\n{median:.0f}%", color=INK_2,
            fontsize=13, ha="left", va="top")

    top = v.max() * 1.18
    for y in args.peaks:
        g = v[v.index.year == int(y)]
        if g.empty:
            continue
        d = g.idxmax()
        ax.annotate(f"{g.max():.0f}%\n{d:%b %Y}", xy=(d, g.max()), xytext=(d, g.max() + top * 0.07),
                    color=INK, fontsize=14, fontweight="bold", ha="center",
                    arrowprops=dict(arrowstyle="-", color=INK_2, lw=1))

    lo = v.idxmin()
    ax.annotate(f"Calmest: {v.min():.0f}%\n{lo:%b %Y}", xy=(lo, v.min()), xytext=(lo, top * 0.56),
                color=INK_2, fontsize=13, ha="center", zorder=5, bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec="none"),
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=1))

    last = v.index[-1]
    ax.scatter([last], [v.iloc[-1]], s=70, color=LINE, edgecolor=SURFACE, linewidth=2, zorder=4)
    ax.text(last + pd.Timedelta(days=45), v.iloc[-1], f"Now\n{v.iloc[-1]:.0f}%", color=INK, fontsize=14,
            fontweight="bold", ha="left", va="center")

    ax.set_ylim(0, top)
    ax.set_xlim(v.index[0], v.index[-1] + pd.Timedelta(days=330))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.set_ylabel("Volatility (annualised)", color=INK_2)
    ax.tick_params(colors=INK_2, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)

    fig.text(0.07, 0.955, "KSE-100: calm and chaos come in streaks", fontsize=22,
             fontweight="bold", color=INK)
    fig.text(0.07, 0.918, f"{args.window}-day rolling volatility, {v.index[0]:%b %Y} to {v.index[-1]:%b %Y}",
             fontsize=15, color=INK_2)
    fig.text(0.07, 0.025, f"Data: Investing.com daily closes. Volatility = standard deviation of daily returns "
             f"over the past {args.window} trading days, annualised.", fontsize=10.5, color=INK_2)
    fig.subplots_adjust(left=0.11, right=0.95, top=0.88, bottom=0.08)
    fig.savefig(args.out, facecolor=SURFACE)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
