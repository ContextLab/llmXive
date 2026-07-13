# Research: The Influence of Perceived Agency in AI Interactions on Trust

## Research Question

Does increasing a user's perception of agency in their interactions with an AI assistant—even when illusory—increase trust in the AI's recommendations?

## Background & Literature Review

### Theoretical Framework

The study is grounded in the **illusion of control** literature (Langer, 1975), which posits that individuals perceive greater control over outcomes when they are allowed to make choices, even if those choices have no causal impact. In human-AI interaction, this suggests that providing users with adjustable controls (e.g., sliders to "tune" AI recommendations) may increase perceived agency and, consequently, trust in the AI's output.

Trust in automation is typically measured using validated psychometric scales. The **Trust in Automation Scale** (Lee & See, 2004) is a widely used instrument that assesses trust across multiple dimensions (e.g., reliability, predictability, helpfulness). This study will use the full item set from Lee & See (2004) to ensure comparability with prior research.

### Prior Empirical Evidence

| Study | Key Finding | Relevance |
|-------|-------------|-----------|
| Langer (1975) | Individuals perceive greater control when given choices, even if choices are illusory. | Supports the manipulation of perceived agency via UI controls. |
| Lee & See (2004) | Validated Trust in Automation Scale; trust is multidimensional and context-dependent. | Provides the measurement instrument for the primary outcome. |
| Hoff & Bashir (2015) | Trust in automation is influenced by user expectations, prior experience, and system transparency. | Suggests that perceived agency may be a key factor in trust formation. |
| Dzindolet et al. (2003) | Trust in automated decision aids is higher when users feel they have control over the system. | Directly supports the hypothesis that perceived agency increases trust. |

### Hypotheses

- **H1 (Primary)**: Participants in the High Agency condition will report significantly higher trust scores than those in the Low Agency condition (tested via planned orthogonal contrast in ANOVA).
- **H2**: Participants in the High Agency and Low Agency conditions will report significantly higher trust scores than those in the Control condition (combined vs. control contrast).
- **H3**: The effect of perceived agency on trust will be robust across different participant exclusion thresholds (sensitivity analysis).
- **H4 (Manipulation Check)**: Participants in the High Agency condition will report significantly higher perceived agency scores than those in the Low Agency condition.

## Dataset Strategy

### Data Collection Method

This study employs a **self-collected dataset** via a custom experimental interface. Participants will be recruited via Prolific/MTurk and randomly assigned to one of three conditions:

1. **High Agency**: Users interact with adjustable sliders to "tune" AI recommendations (illusory control; sliders do not alter output).
2. **Low Agency**: Users are presented with a fixed AI recommendation and a single "accept/reject" button.
3. **Control**: Users view a static, non-interactive display of an AI recommendation.

**Stimulus Consistency**: The AI recommendation content (text, values, visual presentation) is **identical** across all three conditions. Only the UI interaction layer (sliders vs. button vs. static) varies. This ensures that trust is measured against the same stimulus, isolating the effect of perceived agency.

### Variables Captured

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `participant_id` | String | Generated | Unique identifier for each session. |
| `condition` | Categorical | Randomized | High Agency, Low Agency, or Control. |
| `adherence_rate` | Float (0-100) | Behavioral | Percentage of AI recommendations followed. |
| `trust_score` | Float (1-5) | Psychometric | Mean score from Lee & See (2004) scale items. |
| `perceived_agency_score` | Float (1-5) | Psychometric | Mean score from Langer-style manipulation check. |
| `illusion_belief` | Boolean | Survey | Debriefing: "Did you believe the sliders changed the recommendation?" |
| `attention_check_pass` | Boolean | Survey | Whether the participant passed the attention check. |
| `completion_time` | Float (seconds) | Behavioral | Time taken to complete the task. |

### Verified Datasets

**N/A**: This study does not rely on external datasets. All data is self-collected via the experiment interface. The dataset variables (Condition ID, Adherence Rate, Trust Score, Perceived Agency Score, Attention Check Status) are fully contained within the survey export, and no external data linkage is required.

### Data Quality Assurance

- **Attention Checks**: Participants who fail attention checks or exhibit straight-lining responses will be flagged for exclusion.
- **Manipulation Check**: `perceived_agency_score` will be analyzed to confirm the High Agency condition successfully increased perceived control.
- **Randomization Check**: Post-hoc tests will verify that conditions are balanced on demographic covariates.
- **Data Hygiene**: Raw data will be checksummed; no in-place modifications; derivations written to new files.

## Statistical Analysis Plan

### Primary Analysis: One-Way ANOVA with Planned Contrasts

The primary hypotheses (H1, H2) will be tested using a **One-Way ANOVA** framework followed by **planned orthogonal contrasts**:

1. **Omnibus Test**: One-Way ANOVA to test for any significant differences in Trust Score across the three conditions.
2. **Planned Contrast 1**: High Agency vs. Low Agency (coefficients: +1, -1, 0).
3. **Planned Contrast 2**: (High Agency + Low Agency) vs. Control (coefficients: +0.5, +0.5, -1).

These contrasts are pre-registered to maximize statistical power and avoid data dredging. The ANOVA framework aligns with the power analysis (f=0.25) and provides a robust omnibus test before pairwise comparisons.

### Secondary Analysis: Pairwise Comparisons with Multiple-Comparison Correction

To explore all pairwise differences (High vs. Low, High vs. Control, Low vs. Control), **Tukey HSD post-hoc tests** will be applied to control the family-wise error rate (FWER). This addresses SC-005 (Type I error control). The Tukey correction is applied to the omnibus F-test and pairwise comparisons.

### Effect Size Calculation

For all significant pairwise comparisons, **Cohen's d** will be calculated to quantify the magnitude of observed effects (SC-004). Cohen's d thresholds: 0.2 (small), 0.5 (medium), 0.8 (large).

### Power Analysis

A **pre-study power calculation** will be conducted using `pwr` (R) or `statsmodels.stats.power` (Python) to determine the required sample size for:

- **Effect size**: f = 0.25 (medium, ANOVA).
- **Power**: ≥ 0.80.
- **Alpha**: 0.05.
- **Design**: One-way ANOVA with 3 groups.

The output will be a pre-study report documenting the required sample size (SC-002).

### Sensitivity Analysis

To assess the robustness of findings (SC-003), a **threshold sensitivity sweep** will be performed:

- **Threshold range**: 0.75 to 0.90 for **attention check pass rate** and **completion time** (NOT adherence rate).
- **Metric**: Variation in primary outcome (trust difference between High and Low Agency).
- **Output**: Plot of p-values and effect sizes across thresholds.

**Rationale for Exclusion Criteria**: Adherence rate is a behavioral outcome and is NOT used as an exclusion criterion to avoid selection bias. Participants who disagree with the AI (low adherence) are retained to preserve the validity of the trust measure.

### Assumptions & Limitations

- **Observational Nature**: While the *condition* is randomized, the *psychological mechanism* (perceived agency) is measured via a manipulation check. Findings will be framed as associational regarding the psychological mechanism, but causal regarding the UI manipulation.
- **Collinearity**: Adherence rate and trust score are conceptually distinct (behavioral vs. psychometric). Adherence is NOT used as a covariate in the primary trust analysis to avoid circularity.
- **Power Limitation**: If the final sample size is smaller than the power analysis target, post-hoc power will be calculated and the limitation explicitly stated.
- **Illusion Validity**: If participants realize the sliders are illusory (detected via `illusion_belief`), a sub-group analysis will be performed to assess the effect size among those who believed the illusion.

## Statistical Rigor Checklist

| Requirement | Method | Status |
|-------------|--------|--------|
| Multiple-comparison correction | Tukey HSD (FWER control) | ✅ Planned |
| Sample-size / power justification | Pre-study power analysis (f=0.25, power≥0.80) | ✅ Planned |
| Causal-inference assumptions | Randomized condition; manipulation check validates construct | ✅ Addressed |
| Measurement validity | Lee & See (2004) scale (validated instrument); Langer-style check | ✅ Addressed |
| Predictor collinearity | Adherence and trust are independent measures; adherence not used as filter | ✅ Addressed |

## Decision/Rationale

### Why Self-Collected Data?

External datasets do not contain the required experimental manipulation (High/Low/Control agency conditions) or the specific trust scale items (Lee & See, 2004). Self-collection ensures:

- **Full variable fit**: All required variables are captured directly.
- **Manipulation fidelity**: Conditions are implemented as specified in the technical design.
- **Reproducibility**: Data collection interface is version-controlled and checksummed.

### Why CPU-Tractable Methods?

The analysis pipeline relies on standard statistical methods (ANOVA, Tukey HSD, Cohen's d) that are computationally lightweight and run efficiently on CPU. No deep learning, large-LLM inference, or GPU-accelerated methods are required. This ensures:

- **Feasibility**: Pipeline completes within 6 hours on GitHub Actions free-tier.
- **Reproducibility**: No CUDA or GPU dependencies; all libraries have CPU wheels.

### Why ANOVA + Contrasts + Tukey?

- **ANOVA**: Provides a robust omnibus test aligned with the power analysis (f=0.25).
- **Planned Contrasts**: Test specific directional hypotheses (H1, H2) with higher power than post-hoc tests.
- **Tukey HSD**: Controls FWER for all pairwise comparisons, ensuring Type I error is managed even when exploring non-hypothesized pairs.
- **Consistency**: This approach avoids the inconsistency of mixing one-tailed t-tests with two-tailed Tukey corrections.

## References

- Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology, 32*(2), 311–328.
- Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors, 46*(1), 50–80.
- Hoff, K. A., & Bashir, M. (2015). Trust in automation: Integrating empirical evidence on factors that influence trust. *Human Factors, 57*(3), 407–434.
- Dzindolet, M. T., Peterson, S. A., Pomranky, R. A., Pierce, L. G., & Beck, H. P. (2003). The role of trust in automation reliance. *International Journal of Human-Computer Studies, 58*(6), 697–718.