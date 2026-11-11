"""Base-effect projection of Pakistan's year-on-year CPI inflation (PBS national CPI, base 2015-16)."""

YOY_OCT_2026 = 0.0961  # PBS, October 2026

# Month-on-month CPI changes leaving the 12-month window (PBS)
BASE_MOM = {
    "Nov": 0.0040,   # Nov 2025, published rounded to 0.4%
    "Dec": -0.0045,  # Dec 2025, PBS press release
    "Jan": 0.0039,   # Jan 2026, PBS monthly review
}

# Month-on-month CPI change assumed for each new month, Nov 2026 to Jan 2027
SCENARIOS = {
    "Prices flat (0.0%)": 0.0000,
    "Same as base (~0.4%)": 0.0040,
    "Half of Oct pace (0.55%)": 0.0055,
    "Oct pace continues (1.1%)": 0.0108,
}


def project(yoy_start: float, new_mom: float, base: dict[str, float]) -> list[tuple[str, float]]:
    """YoY path from (1 + YoY_t) = (1 + YoY_t-1) * (1 + MoM_t) / (1 + MoM_t-12)."""
    path, yoy = [], yoy_start
    for month, old_mom in base.items():
        yoy = (1 + yoy) * (1 + new_mom) / (1 + old_mom) - 1
        path.append((month, yoy))
    return path


def breakeven_mom(yoy_prev: float, yoy_target: float, old_mom: float) -> float:
    """Month-on-month change that produces yoy_target."""
    return (1 + yoy_target) * (1 + old_mom) / (1 + yoy_prev) - 1


if __name__ == "__main__":
    print(f"Start: Oct 2026 YoY = {YOY_OCT_2026:.2%}\n")

    for name, mom in SCENARIOS.items():
        path = project(YOY_OCT_2026, mom, BASE_MOM)
        print(f"{name:<28} " + "  ".join(f"{m}: {y:.2%}" for m, y in path))

    be = breakeven_mom(YOY_OCT_2026, YOY_OCT_2026, BASE_MOM["Nov"])
    print(f"\nNov MoM that holds YoY at {YOY_OCT_2026:.2%}: {be:.2%}")

    base_cum = 1.0
    for m in BASE_MOM.values():
        base_cum *= 1 + m
    print(f"Cumulative base, Nov 2025 to Jan 2026: {base_cum - 1:.2%}")
    print(f"Jan 2027 YoY stays at or below {YOY_OCT_2026:.2%} only if prices rise "
          f"less than {base_cum - 1:.2%} in total over Nov to Jan.")
