# Annotation Sample Size Decision Record

**Date**: 2026-06-13
**Project**: PROJ-316 - The Impact of Subtle Linguistic Cues on Perceived Authenticity
**Task ID**: T000b
**Phase**: Phase -2 (Power Analysis Decision Gate)

## 1. Power Analysis Inputs (From T000a & T000)

- **Effect Size (f²)**: 0.15 (Medium effect, based on Cohen's conventions for social science behavioral studies).
- **Source**: Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
- **Statistical Power Target**: ≥ 0.80
- **Significance Level (α)**: 0.05
- **Predictors (k)**: 4 (First-person count, Hedge count, Sentiment score, Conversation length)

## 2. Power Analysis Results (From T000)

Based on the inputs above, the power analysis script (`code/power_analysis.py`) calculated the required sample size:

- **Required Sample Size (N)**: 92
- **Achieved Power at N=92**: 0.81

## 3. Budget Constraints

- **Annotation Budget**: 200 turns (Maximum capacity for manual human annotation within project timeline).
- **Cost Estimate**: ~200 rating operations.

## 4. Decision Logic

The decision logic for this gate is defined in `tasks.md`:
> "If T000 output N > budget, halt project and flag for human input. If N <= budget, record N and proceed."

- **Calculated N (92)** ≤ **Budget (200)**? **YES**.

## 5. Final Decision

**The project will proceed to Phase 0 (Data Acquisition & Annotation).**

- **Final Annotation Sample Size (N)**: 92
- **Justification**: The calculated sample size of 92 provides sufficient statistical power (≥ 0.80) to detect a medium effect size (f² = 0.15) in the planned multiple regression analysis. This number is well within the allocated annotation budget of 200, allowing for a buffer of 108 samples for potential data cleaning, edge case exclusions, or power margin.

## 6. Next Steps

1. Proceed to **T001c**: Generate "Gold Standard" subset. (Note: While the power analysis suggests 92, the immediate task T001c specifies a pilot of 50 turns for lexicon validation. The full 92 will be targeted for the final analysis dataset).
2. Execute **T001f**: Acquire raw conversation dataset.
3. Execute **T002**: Implement annotation tool.
4. Execute **T001e**: Generate human hedge labels for the full N=92 set (or as many as can be reliably annotated to meet the N=92 threshold).

---
*This decision is recorded to satisfy Constitution Principle II (Verified Accuracy) and FR-011 (Power Analysis).*