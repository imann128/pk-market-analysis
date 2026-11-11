"""Histogram of KSE-100 weekly returns against a fitted normal distribution."""
import argparse

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

from analysis import bell_curve_tail_prob, load_closes, resolve_week, summarise, weekly_returns

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e0"
BARS = "#2a78d6"
CURVE = "#eb6834"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="Investing.com daily historical data CSV")
    ap.add_argument("--week", help="Friday date of the week (default: latest complete week)")
    ap.add_argument("--tail", type=float, default=0.11, help="tail threshold as a decimal (default: 0.11)")
    ap.add_argument("--bin-width", type=float, default=1.0, help="bin width in percentage points (default: 1.0)")
    ap.add_argument("--keep-today", action="store_true", help="keep a row dated today")
    ap.add_argument("-o", "--out", default="kse100_weekly_returns.png")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    s = summarise(weekly_returns(load_closes(args.csv, args.keep_today)))
    week = resolve_week(s.returns, args.week)

    r = s.returns * 100
    mu, sd, n = s.mean * 100, s.std * 100, s.n
    bw = args.bin_width
    v = r.loc[week]
    one_in = n / int((s.returns >= s.returns.loc[week]).sum())
    tail_pct = args.tail * 100
    tail_years = round(1 / (bell_curve_tail_prob(s, args.tail) * 52), -1)
    tail_actual = int((r.abs() > tail_pct).sum())
    years = (r.index[-1] - r.index[0]).days / 365.25

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15})
    fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    lo, hi = np.floor(r.min()) - 1, np.ceil(r.max()) + 1
    counts, *_ = ax.hist(r, bins=np.arange(lo, hi + bw, bw), color=BARS, edgecolor=SURFACE,
                         linewidth=2, zorder=2)
    top = counts.max() * 1.12

    x = np.linspace(lo, hi, 600)
    ax.plot(x, stats.norm.pdf(x, mu, sd) * n * bw, color=CURVE, linewidth=2.5, zorder=3)

    ax.axvline(v, color=INK, linewidth=1.5, linestyle=(0, (4, 3)), zorder=4)
    label = f"Week ending {week.day} {week:%b}\n{v:+.1f}%"
    if v > 0:
        label += f"\n~1 in {one_in:.0f} weeks"
    room_right = (hi + 0.5 - v) / (hi - lo + 1)
    on_right = room_right >= 0.25
    ax.text(v + 0.6 if on_right else v - 0.6, top * 0.88, label, color=INK, fontsize=15,
            fontweight="bold", va="center", ha="left" if on_right else "right", zorder=5)

    for d in (r.idxmin(), r.idxmax()):
        ax.annotate(f"{r[d]:+.1f}%\n{d:%b %Y}", xy=(r[d], top * 0.012), xytext=(r[d], top * 0.16),
                    color=INK_2, fontsize=13, ha="center",
                    arrowprops=dict(arrowstyle="-", color=INK_2, lw=1))

    ax.text(0.02, 0.4,
            f"Moves beyond ±{tail_pct:.0f}%:\nbell curve: once in ~{tail_years:.0f} years\n"
            f"actual: {tail_actual} times in {years:.0f} years",
            transform=ax.transAxes, color=INK, fontsize=14, va="center",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=GRID))

    curve_x = mu - sd * 1.1
    curve_y = stats.norm.pdf(curve_x, mu, sd) * n * bw
    ax.annotate("Bell curve\n(what textbooks assume)", xy=(curve_x, curve_y),
                xytext=(0.31, 0.72), textcoords="axes fraction", color=INK, fontsize=13,
                ha="right", va="center", arrowprops=dict(arrowstyle="-", color=CURVE, lw=2))
    ax.text(0.02, 0.58, "■", transform=ax.transAxes, color=BARS, fontsize=16, va="center")
    ax.text(0.05, 0.58, "Actual weeks", transform=ax.transAxes, color=INK, fontsize=13, va="center")

    ax.set_xlim(lo - 0.5, hi + 0.5)
    ax.set_ylim(0, top)
    ax.set_xlabel("Weekly return (%)", color=INK_2)
    ax.set_ylabel("Number of weeks", color=INK_2)
    ax.tick_params(colors=INK_2, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)

    fig.text(0.07, 0.955, f"KSE-100: {years:.0f} years of weekly returns", fontsize=22,
             fontweight="bold", color=INK)
    fig.text(0.07, 0.918, f"{n} weeks, {r.index[0]:%b %Y} to {r.index[-1]:%b %Y}",
             fontsize=15, color=INK_2)
    fig.text(0.07, 0.025, "Data: Investing.com daily closes, weekly = Friday to Friday. "
             "Bell curve fitted with the same mean and standard deviation.",
             fontsize=10.5, color=INK_2)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.88, bottom=0.1)
    fig.savefig(args.out, facecolor=SURFACE)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
