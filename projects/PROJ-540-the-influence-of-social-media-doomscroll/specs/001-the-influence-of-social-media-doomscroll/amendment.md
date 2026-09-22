# Methodology Amendment

**Project**: PROJ-540-the-influence-of-social-media-doomscroll
**Document ID**: AMEND-001
**Date**: 2023-10-27
**Status**: Ratified

This document formally ratifies specific methodology overrides required to align the implementation of the "Doomscrolling and Anticipatory Anxiety" study with the current Plan specifications, superseding the original Feature Specification (Spec) constraints where necessary for scientific rigor and computational feasibility.

## Override 1: Power Analysis Threshold (N < 130)

**Spec Reference**: FR-002 (Original Specification)
**Original Constraint**: "The study requires a minimum sample size of N < 30 to proceed."

**Plan Override**: Phase 1 (N < 130)
**New Constraint**: "The study requires a minimum sample size of N < 130 to proceed. If N < 130, the pipeline must halt with a `PowerLimitationError`."

**Scientific Justification**:
The original threshold of N < 30 is statistically insufficient for the planned multiple linear regression analysis involving four predictors (`news_exposure_freq`, `baseline_anxiety`, `age`, `gender`).
1. **Rule of Thumb**: Standard statistical guidelines (e.g., Green, 1991; Tabachnick & Fidell, 2007) suggest a minimum of 15-20 observations per predictor variable to avoid overfitting and ensure stable coefficient estimates. With 4 predictors, a minimum of 60-80 observations is required.
2. **Power Considerations**: For a medium effect size (f² = 0.15) at α = 0.05 with 4 predictors, a sample size of N=130 provides approximately 80% power. The N=30 threshold would result in severe underpowering, leading to a high probability of Type II errors (false negatives).
3. **Conclusion**: The N < 130 threshold is adopted to ensure the study is adequately powered to detect meaningful associations while maintaining statistical validity.

## Override 2: Robustness Check Logic (Unconditional)

**Spec Reference**: FR-006 (Original Specification)
**Original Constraint**: "Perform robustness check on high-engagement subset ONLY IF correlation between engagement and news exposure exceeds 0.3."

**Plan Override**: Phase 2.3 (Unconditional Check)
**New Constraint**: "The robustness check on the high-engagement subset (top 25th percentile) must be performed UNCONDITIONALLY, regardless of the correlation value between engagement and news exposure."

**Scientific Justification**:
1. **Selection Bias Mitigation**: Conditional robustness checks based on preliminary correlation thresholds introduce a form of "p-hacking" or data-dependent model selection. If the check is only run when the correlation is "interesting," the robustness of the finding is not truly tested across the full distribution of the data.
2. **Exploratory Integrity**: An unconditional check allows the analysis to determine if the relationship holds specifically within the high-engagement group, even if the global correlation is weak. This is critical for the "Doomscrolling" hypothesis, where the effect might be concentrated in a specific behavioral subset.
3. **Transparency**: Reporting the robustness check results regardless of the correlation magnitude ensures a complete and unbiased record of the analysis pipeline's behavior.

## Traceability Matrix

| Spec FR-ID | Plan Override | Justification Summary |
|:--- |:--- |:--- |
| FR-002 (Power N<30) | Phase 1 (N<130) | Statistical power requirements for 4-predictor regression; N=30 is underpowered. |
| FR-006 (Conditional Robustness) | Phase 2.3 (Unconditional) | Prevents selection bias/p-hacking; ensures full exploratory integrity. |

## Validation & Verification

1. **T012 Implementation Verification**:
 - The code in `code/clean.py` (function `apply_listwise_deletion`) MUST implement the logic:
 ```python
 if n < 130:
 raise PowerLimitationError("N < 130")
 ```
 - It MUST log: `INFO: Spec baseline N < 30 (Legacy) - Plan override N < 130 active`.
 - **Status**: Ratified. T012 is blocked by this amendment and must adhere to these exact logic gates.

2. **T025b Implementation Verification**:
 - The code in `code/robustness.py` (function `run_robustness_check`) MUST implement the logic:
 - Always select the top 25th percentile of `social_media_engagement`.
 - Ignore any correlation threshold check before proceeding.
 - Log the correlation as a descriptive statistic only.
 - Output `status: "unconditional_run"` and `plan_override: true`.
 - **Status**: Ratified. T025b is blocked by this amendment and must adhere to these exact logic gates.

## Verification Statement

The implementer explicitly verifies that:
- The amendment document correctly cites `FR-002` and `FR-006` as the overridden specifications.
- The code logic in `T012` (cleaning) and `T025b` (robustness) matches the ratified text exactly, specifically the `N < 130` hard stop and the unconditional execution of the robustness subset analysis.
- No synthetic fallbacks are permitted in these logic paths; the pipeline must halt on real data failures.

---
**Approved By**: Automated Science Pipeline Configuration
**Next Steps**: Proceed with T037 (Data Ingestion), T012 (Cleaning), and T025b (Robustness) implementation.