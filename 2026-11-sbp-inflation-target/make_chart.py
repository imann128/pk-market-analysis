"""FY27 CPI inflation: actual months, scenario paths to June 2027, and FY27 averages against the SBP projection."""
import argparse

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D

from target_path import (FY27_YOY, BASE, SBP_JULY_PROJECTION, path, repeat_path,
                         required_mom, fy_average_of)

SURFACE = "#fbfaf7"
INK = "#14181f"
INK_2 = "#5b5e66"
INK_3 = "#9a9ca3"
RULE = "#e4e2dc"
KICKER = "#1f5fbf"
BLUE = "#2a78d6"
ORANGE = "#e0602b"
GREY = "#7d8088"
BAND = "#e6f0e9"
BAND_INK = "#2e7d4f"
PROJ = "#b9b8b2"

FONT = "Inter"
FONT_DISPLAY = "Inter Display"
Y_MAX = 14


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--series", default="PAKISTAN MACRO", help="kicker text above the title")
    ap.add_argument("-o", "--out", default="fy27_inflation_paths.png")
    return ap.parse_args()


def spread(values: list[float], min_gap: float) -> list[float]:
    """Nudge label positions apart so neighbours are at least `min_gap` apart, keeping their order."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [values[i] for i in order]
    for i in range(1, len(pos)):
        pos[i] = max(pos[i], pos[i - 1] + min_gap)
    shift = (sum(values[i] for i in order) - sum(pos)) / len(pos)
    pos = [p + shift for p in pos]
    out = [0.0] * len(values)
    for i, p in zip(order, pos):
        out[i] = p
    return out


def main() -> None:
    args = parse_args()
    months = list(FY27_YOY) + list(BASE)
    labels = [f"{m}\n{'2026' if i < 6 else '2027'}" if m in ("Jul", "Jan") else m for i, m in enumerate(months)]
    actual = [v * 100 for v in FY27_YOY.values()]
    x_actual, x_proj = list(range(4)), list(range(3, 12))

    m7 = required_mom(0.07)
    flat, rise, repeat = path(0.0), path(m7), repeat_path()
    scenarios = [
        dict(proj=repeat, name="Repeat last year's\nmonthly pattern", short="repeat last year",
             color=GREY, style=(0, (3, 2.5)), lw=1.6),
        dict(proj=rise, name=f"Prices rise {m7:.2%}\na month", short=f"{m7:.2%} a month",
             color=ORANGE, style="-", lw=2.2),
        dict(proj=flat, name="Prices flat", short="prices flat", color=BLUE, style="-", lw=2.6),
    ]
    for s in scenarios:
        s["avg"] = fy_average_of(s["proj"]) * 100
    flat_avg = scenarios[2]["avg"]
    lo, hi = (v * 100 for v in SBP_JULY_PROJECTION)

    plt.rcParams.update({"font.family": FONT, "font.size": 14})
    fig = plt.figure(figsize=(10, 10), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    ax = fig.add_axes([0.1, 0.14, 0.56, 0.51])
    side = fig.add_axes([0.865, 0.14, 0.125, 0.51])
    for a in (ax, side):
        a.set_facecolor(SURFACE)
        a.set_ylim(0, Y_MAX)

    fig.text(0.075, 0.935, args.series, fontsize=12.5, color=KICKER, fontweight="semibold")
    fig.text(0.075, 0.88, "How low can FY27 inflation average?", fontsize=31, color=INK,
             fontfamily=FONT_DISPLAY, fontweight="semibold")
    fig.text(0.075, 0.845, "Pakistan CPI inflation, year on year, FY27 (Jul 2026 to Jun 2027)",
             fontsize=15, color=INK_2)

    fig.text(0.075, 0.735, f"{flat_avg:.1f}%", fontsize=58, color=BLUE, fontfamily=FONT_DISPLAY,
             fontweight="semibold", va="baseline")
    fig.text(0.3, 0.784, "FY27 average even if prices stop rising\nfrom November 2026 to June 2027", fontsize=15.5,
             color=INK, va="center", linespacing=1.25)
    fig.text(0.3, 0.737, f"Above SBP's July projection of {lo:.1f}-{hi:.1f}%, due for revision in January 2027",
             fontsize=12.5, color=INK_2, va="center")

    handles = [
        Line2D([], [], color=INK, lw=2.4, label="Actual"),
        Line2D([], [], color=BLUE, lw=2.4, label="Prices flat"),
        Line2D([], [], color=ORANGE, lw=2.2, label=f"Prices rise {m7:.2%} a month"),
        Line2D([], [], color=GREY, lw=1.6, ls=(0, (3, 2.5)), label="Repeat last year's monthly pattern"),
        Patch(facecolor=BAND, edgecolor=BAND_INK, linewidth=0.4, label="SBP target 5-7%"),
    ]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.065, 0.693), ncol=5, frameon=False,
               fontsize=10.5, handlelength=1.5, handletextpad=0.45, columnspacing=1.0, labelcolor=INK_2)

    ax.axhspan(5, 7, color=BAND, linewidth=0, zorder=0)
    ax.text(-0.15, 6.55, "SBP target range 5-7%", fontsize=12, color=BAND_INK, va="center", ha="left",
            fontweight="medium")

    end_labels = spread([s["proj"][-1] * 100 for s in scenarios], 1.45)
    for s, ly in zip(scenarios, end_labels):
        y = [actual[-1]] + [v * 100 for v in s["proj"]]
        ax.plot(x_proj, y, color=s["color"], linewidth=s["lw"], linestyle=s["style"],
                zorder=4 if s["color"] == BLUE else 3)
        ax.text(11.35, ly, s["name"], fontsize=11.5, color=INK_2, va="bottom", ha="left", clip_on=False,
                linespacing=1.15)
        ax.text(11.35, ly - 0.05, f"{y[-1]:.1f}%", fontsize=11.5, color=INK, va="top", ha="left",
                fontweight="semibold", clip_on=False)
    ax.text(11.35, 13.6, "June 2027, y/y", fontsize=10.5, color=INK_2, va="center", ha="left", clip_on=False)

    ax.plot(x_actual, actual, color=INK, linewidth=2.6, zorder=5)
    ax.scatter(x_actual, actual, s=36, color=INK, zorder=6)
    for xi, v in zip(x_actual, actual):
        first = xi == x_actual[0]
        ax.text(xi + (0.12 if first else 0), v + (-0.45 if first else 0.4), f"{v:.1f}%",
                ha="left" if first else "center", va="top" if first else "bottom", fontsize=12.5, color=INK,
                fontweight="semibold")
    ax.text(1.5, 13.6, "Actual", ha="center", va="center", fontsize=13, color=INK, fontweight="semibold")
    ax.text(7.5, 13.6, "Scenarios, Nov 2026 to Jun 2027", ha="center", va="center", fontsize=13, color=INK_2)
    ax.axvline(3.5, color=RULE, linewidth=1.2, zorder=1)

    apr = months.index("Apr")
    ax.annotate("April 2026 energy spike\ndrops out of the y/y base", xy=(apr, flat[apr - 4] * 100),
                xytext=(apr, 2.6), fontsize=11.5, color=INK_2, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=INK_3, lw=1, shrinkA=14, shrinkB=2))

    ax.set_xlim(-0.3, 11.15)
    ax.set_xticks(range(12))
    ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.set_yticks(range(0, Y_MAX + 1, 2))
    ax.tick_params(colors=INK_2, length=0, labelsize=12)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.grid(axis="y", color=RULE, linewidth=0.8, zorder=0)

    fig.add_artist(Line2D([0.85, 0.85], [0.14, 0.65], color=RULE, linewidth=1.2))
    fig.text(0.865, 0.637, "FY27 average", fontsize=12, color=INK, fontweight="semibold", va="center")
    side.set_xlim(0, 1)
    side.axis("off")
    side.add_patch(Rectangle((0.06, lo), 0.12, hi - lo, facecolor=PROJ, edgecolor="none", zorder=1))
    side.text(0.27, (lo + hi) / 2, f"SBP July\nprojection\n{lo:.1f}-{hi:.1f}%", fontsize=10.5, color=INK_2,
              va="center", ha="left", linespacing=1.2)
    avg_labels = spread([s["avg"] for s in scenarios], 1.05)
    for s, ly in zip(scenarios, avg_labels):
        side.scatter([0.12], [s["avg"]], s=70, color=s["color"], edgecolor=SURFACE, linewidth=1.5, zorder=3)
        side.text(0.27, ly + 0.02, f"{s['avg']:.1f}%", fontsize=11.5, color=INK, fontweight="semibold",
                  va="bottom", ha="left")
        side.text(0.27, ly - 0.02, s["short"], fontsize=9.5, color=INK_2, va="top", ha="left")

    fig.add_artist(Line2D([0.075, 0.965], [0.072, 0.072], color=RULE, linewidth=1))
    fig.text(0.075, 0.045, "Sources: PBS national CPI; SBP Annual Report FY26, Table 1.2. Lines show year-on-year "
             "inflation; FY27 average is index-weighted.", fontsize=10.5, color=INK_3)
    fig.text(0.075, 0.022, "Code: github.com/imann128/pk-market-analysis", fontsize=10.5, color=INK_3)

    fig.savefig(args.out, facecolor=SURFACE)
    print(f"saved {args.out}")
    for s in scenarios:
        print(f"  {s['short'].replace(chr(10), ' '):<28} Jun 2027 {s['proj'][-1]:.2%}  FY27 average {s['avg']:.2f}%")


if __name__ == "__main__":
    main()
