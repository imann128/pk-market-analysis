"""
Base-effect projection for Pakistan CPI (YoY).

Identity used:
    (1 + YoY_t) = (1 + YoY_{t-1}) * (1 + MoM_t) / (1 + MoM_{t-12})

So next month's YoY depends on only two things:
    1. the new month's MoM (unknown, so we use scenarios)
    2. the MoM from the same month last year (known, this is the "base")

Source: PBS monthly CPI releases (national CPI, base 2015-16).
"""

# Latest known YoY (October 2026, PBS)
YOY_OCT_2026 = 0.0961

# MoM of the months that will leave the 12-month window (PBS)
BASE_MOM = {
    "Nov": 0.0040,   # Nov 2025, reported as 0.4% (rounded)
    "Dec": -0.0045,  # Dec 2025, PBS press release: -0.45%
    "Jan": 0.0039,   # Jan 2026, PBS monthly review: +0.39%
}

# Scenarios for the new months' MoM (assumed constant across Nov-Jan)
SCENARIOS = {
    "Prices flat (0.0%)": 0.0000,
    "Same as base (~0.4%)": 0.0040,
    "Half of Oct pace (0.55%)": 0.0055,
    "Oct pace continues (1.1%)": 0.0108,
}


def project(yoy_start: float, new_mom: float, base: dict) -> list[tuple[str, float]]:
    """Roll the YoY forward one month at a time."""
    path, yoy = [], yoy_start
    for month, old_mom in base.items():
        yoy = (1 + yoy) * (1 + new_mom) / (1 + old_mom) - 1
        path.append((month, yoy))
    return path


def breakeven_mom(yoy_prev: float, yoy_target: float, old_mom: float) -> float:
    """MoM needed in the new month to land exactly on yoy_target."""
    return (1 + yoy_target) * (1 + old_mom) / (1 + yoy_prev) - 1


if __name__ == "__main__":
    print(f"Start: Oct 2026 YoY = {YOY_OCT_2026:.2%}\n")

    for name, mom in SCENARIOS.items():
        path = project(YOY_OCT_2026, mom, BASE_MOM)
        line = "  ".join(f"{m}: {y:.2%}" for m, y in path)
        print(f"{name:<28} {line}")

    # MoM needed in Nov 2026 to keep YoY unchanged at 9.61%
    be = breakeven_mom(YOY_OCT_2026, YOY_OCT_2026, BASE_MOM["Nov"])
    print(f"\nNov MoM needed to hold YoY at 9.61%: {be:.2%}")

    # Cumulative Nov-Jan MoM needed so Jan 2027 YoY <= 9.61%
    base_cum = 1.0
    for m in BASE_MOM.values():
        base_cum *= 1 + m
    print(f"Cumulative base (Nov25-Jan26): {base_cum - 1:.2%}")
    print("=> Jan 2027 YoY stays <= 9.61% only if prices rise less than "
          f"{base_cum - 1:.2%} in total over Nov-Jan.")
