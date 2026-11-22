"""What the July-October 2026 CPI data allow for FY27 average inflation and for reaching the SBP target range."""
import numpy as np
from scipy.optimize import brentq

SBP_JULY_PROJECTION = (0.055, 0.075)  # SBP Annual Report FY26, Table 1.2, FY27 average CPI; to be revised Jan 2027

FY27_YOY = {"Jul": 0.092, "Aug": 0.111, "Sep": 0.1026, "Oct": 0.0961}  # PBS, national CPI
FY27_MOM = {"Jul": 0.012, "Aug": 0.012, "Sep": 0.013, "Oct": 0.0108}   # SBP Inflation Monitor, Oct 2026; PBS

# MoM of Nov 2025 to Jun 2026: the months leaving the 12-month window (PBS)
BASE = {
    "Nov": 0.0040, "Dec": -0.0045, "Jan": 0.0039, "Feb": 0.0027,
    "Mar": 0.0118, "Apr": 0.0248,
    "May": 294.34 / (285.73 * 1.0248) - 1,  # index levels: Mar 285.73, Apr = Mar x 1.0248, May 294.34
    "Jun": -0.0030,
}


def path(mom: float) -> list[float]:
    """Year-on-year inflation for Nov 2026 to Jun 2027 under a constant monthly rate."""
    yoy, out = FY27_YOY["Oct"], []
    for old in BASE.values():
        yoy = (1 + yoy) * (1 + mom) / (1 + old) - 1
        out.append(yoy)
    return out


def fy26_index() -> list[float]:
    """FY26 monthly index levels (Jul 2025 to Jun 2026) relative to June 2026 = 1."""
    level, fy27 = 1.0, []
    for m in FY27_MOM.values():
        level *= 1 + m
        fy27.append(level)
    jul_sep = [fy27[i] / (1 + y) for i, y in enumerate(list(FY27_YOY.values())[:3])]
    oct_jun = [1.0]
    for m in reversed(list(BASE.values())):
        oct_jun.insert(0, oct_jun[0] / (1 + m))
    return jul_sep + oct_jun


def oct_2025_check() -> tuple[float, float]:
    """October 2025 index computed forwards from FY27 data and backwards from June 2026."""
    level = float(np.prod([1 + m for m in FY27_MOM.values()]))
    return level / (1 + FY27_YOY["Oct"]), fy26_index()[3]


def repeat_path() -> list[float]:
    """Year-on-year inflation for Nov 2026 to Jun 2027 if each month repeats the same month a year earlier."""
    return [FY27_YOY["Oct"]] * len(BASE)


def fy_average_of(projected: list[float]) -> float:
    """FY27 period-average inflation for a projected Nov-Jun YoY path: average FY27 index over average FY26 index."""
    w = fy26_index()
    yoy = list(FY27_YOY.values()) + list(projected)
    return sum(wi * (1 + y) for wi, y in zip(w, yoy)) / sum(w) - 1


def fy_average(mom: float) -> float:
    """FY27 period-average inflation under a constant monthly rate from Nov 2026 to Jun 2027."""
    return fy_average_of(path(mom))


def required_mom(target: float) -> float:
    """Constant monthly rate, Nov 2026 to Jun 2027, that gives `target` year-on-year in June 2027."""
    return brentq(lambda m: path(m)[-1] - target, -0.05, 0.05)


def required_mom_for_average(target: float) -> float:
    """Constant monthly rate, Nov 2026 to Jun 2027, that gives an FY27 period average of `target`."""
    return brentq(lambda m: fy_average(m) - target, -0.05, 0.05)


if __name__ == "__main__":
    fwd, bwd = oct_2025_check()
    print(f"Consistency: Oct 2025 index forwards {fwd:.4f}, backwards {bwd:.4f}")
    w = fy26_index()[:4]
    jul_oct = sum(wi * (1 + y) for wi, y in zip(w, FY27_YOY.values())) / sum(w) - 1
    print(f"Jul-Oct 2026 period average: {jul_oct:.2%} (SBP Inflation Monitor: 10.1%)")
    print(f"May 2026 MoM (derived): {BASE['May']:.2%} (SBP: 0.5%)\n")

    print(f"FY27 average with flat prices from November: {fy_average(0.0):.2%}")
    for avg in (SBP_JULY_PROJECTION[1], 0.07, SBP_JULY_PROJECTION[0], 0.05):
        m = required_mom_for_average(avg)
        print(f"FY27 average of {avg:.1%} needs MoM of {m:+.2%} every month, Nov to Jun "
              f"({(1 + m) ** 8 - 1:+.1%} in total)")

    print()
    for tgt in (0.07, 0.05):
        m = required_mom(tgt)
        print(f"June 2027 YoY = {tgt:.0%} needs MoM of {m:.2%} a month "
              f"({(1 + m) ** 12 - 1:.1%} annualised); FY27 average then {fy_average(m):.2%}")

    print(f"\nRepeat last year's monthly pattern: Jun 2027 {repeat_path()[-1]:.2%}, "
          f"FY27 average {fy_average_of(repeat_path()):.2%}")

    print("\nScenarios (constant MoM, Nov 2026 to Jun 2027)")
    for m in (0.0, required_mom(0.07), 0.005, 0.0108):
        p = path(m)
        print(f"  MoM {m:.2%}: Dec {p[1]:.1%}  Mar {p[4]:.1%}  Apr {p[5]:.1%}  Jun {p[7]:.1%}  "
              f"FY27 avg {fy_average(m):.1%}")
