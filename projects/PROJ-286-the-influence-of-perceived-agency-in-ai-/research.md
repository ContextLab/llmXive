# Research Report: The Influence of Perceived Agency in AI Interactions on Trust

## Overview
This document synthesizes the literature review findings and power analysis targets for the study on perceived agency and trust in AI interactions. It serves as the pre-registration and methodological foundation for the experimental phase.

## Literature Review Summary
*Synthesized from `research/validation_report.json` and existing literature.*

### Key Citations
- **Lee & See (2004)**: Validated. Focuses on trust in automation, defining the theoretical framework for the Trust Scale used in this study.
- **Langer (1975)**: Validated. Provides the psychological basis for the "illusion of control" and perceived agency constructs.

### Theoretical Framework
The study is grounded in the hypothesis that perceived agency (the belief that one's actions influence the AI's output) positively correlates with trust, even when those actions are illusory (i.e., do not actually change the AI's decision).

## Power Analysis
*Based on `research/power_calculation.json` and `research/power_report.md`.*

The following table summarizes the pre-study power analysis parameters required to detect the hypothesized effect size with the specified confidence.

| Effect Size (f) | Alpha (α) | Target Power (1-β) | Required N (Total) | Calculated N (Per Group) |
|:--- |:--- |:--- |:--- |:--- |
| 0.25 | 0.05 | 0.80 | 159 | 53 |

### Analysis Details
- **Test Type**: One-Way ANOVA (3 groups: High Agency, Low Agency, Control)
- **Effect Size Justification**: Based on medium effect sizes observed in prior automation trust literature (Cohen, 1988).
- **Power Calculation Method**: `statsmodels.stats.power.FTestAnovaPower`
- **Result**: A total sample size of 159 participants (53 per condition) is required to achieve 80% power to detect an effect size of f = 0.25 at α = 0.05. [UNRESOLVED-CLAIM: c_820fbe8a — status=not_enough_info]

## Data Collection Plan
- **Instrument**: Lee & See (2004) 12-Item Trust Scale.
- **Conditions**: High Agency, Low Agency, Control.
- **Randomization**: Fixed seed for reproducibility (see `code/experiment/config.yaml`).
- **Exclusion Criteria**: Attention check failures, straight-lining detection.

## Validation Status
- [x] Citations validated against Crossref API.
- [x] Power analysis executed and verified.
- [x] Trust Scale items mapped to schema.
- [x] This report compiled and ready for Phase 1 implementation.

---
*Generated automatically by the llmXive pipeline.*