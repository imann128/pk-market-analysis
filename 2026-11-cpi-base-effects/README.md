# Pakistan CPI base effects: did inflation really fall?

Pakistan's headline inflation fell to 9.61% YoY in October 2026 from 10.26% in September. This analysis shows how much of that drop came from the comparison month (October 2025) rather than prices cooling, and projects what the base does to the next three readings.

## The identity

Year-on-year inflation is a rolling 12-month window. Each month one new month enters and the same month from last year leaves:

```
(1 + YoY_t) = (1 + YoY_(t-1)) × (1 + MoM_t) / (1 + MoM_(t-12))
```

- `YoY_t`: this month's year-on-year inflation
- `MoM_t`: this month's month-on-month price change (new month entering)
- `MoM_(t-12)`: the same month last year (old month leaving, the "base")

October check: `1.1026 × 1.0108 / 1.017 - 1 ≈ 9.6%` (PBS: 9.61%).

## Findings

- October's drop was mostly a base effect. October 2025 was a hot month (+1.7% MoM), so removing it lowered YoY even though prices rose 1.1% this October.
- The next base is unfavourable. November 2025 to January 2026 added only 0.34% to prices in total, with December 2025 at -0.45%.
- Even with flat prices, December 2026 YoY rises to about 9.7%. For January 2027 YoY to stay at or below 9.61%, prices must rise less than 0.34% in total over November to January.

| Scenario (MoM each month) | Nov 2026 | Dec 2026 | Jan 2027 |
|---|---|---|---|
| Prices flat (0.0%) | 9.17% | 9.67% | 9.24% |
| Same as base (~0.4%) | 9.61% | 10.55% | 10.56% |
| Half of October's pace (0.55%) | 9.77% | 10.88% | 11.05% |
| October's pace continues (1.1%) | 10.35% | 12.05% | 12.82% |

## Limitations

- This is arithmetic, not a forecast. It separates the effect of the base from the effect of new price changes.
- December often has seasonal food price falls. A repeat of last December would cancel part of the base effect.
- November 2025 MoM is the rounded 0.4% from the PBS release, so outputs carry roughly ±0.05 percentage points of rounding error.

## Data

Pakistan Bureau of Statistics monthly CPI releases (national CPI, base 2015-16): October 2026, November 2025, December 2025 (-0.45% MoM) and January 2026 (+0.39% MoM). The inputs are typed into the script with their sources in comments.

## Run

```bash
python base_effects.py
```
