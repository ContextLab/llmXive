# Research: The Influence of Perceived Agency in AI Interactions on Trust

## Summary

This research phase validates the theoretical foundations and data requirements for the experimental study. It confirms the validity of the Lee & See (2004) Trust in Automation scale, the concept of "illusion of control" (Langer, 1975), and the statistical power requirements for the study.

## Literature Review

### Trust in Automation (Lee & See, 2004)

The primary outcome measure for this study is the "Trust in Automation" scale developed by Lee and See (2004). This scale is widely validated for measuring trust in automated systems and consists of items that assess the user's belief in the system's reliability, competence, and predictability.

*   **Source**: Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
*   **Key Findings**: The study established a multidimensional model of trust, identifying factors such as performance, process, and purpose. The scale items typically use a **7-point Likert format** (1 = "Do not trust at all" to 7 = "Trust completely") to measure agreement with statements like "I trust this system to do what it says it will do."
*   **Relevance**: This scale provides a robust, validated psychometric instrument for measuring the dependent variable (trust) in the context of AI interactions. The exact items will be extracted from the primary source and stored in `docs/trust_scale_items.md` to ensure fidelity.

### Illusion of Control (Langer, 1975)

The independent variable manipulation is grounded in the concept of "illusion of control," first described by Langer (1975).

*   **Source**: Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311–328.
*   **Key Findings**: Langer demonstrated that individuals often perceive a degree of control over outcomes even when the outcome is entirely determined by chance, provided that certain "skill-like" cues (e.g., choice, familiarity, involvement) are present.
*   **Relevance**: This study will leverage this phenomenon by providing users with "illusory" controls (sliders) in the High Agency condition. The hypothesis is that these cues will increase perceived agency and, consequently, trust, even though the underlying AI logic remains unchanged.

### Statistical Power & Methodology

The study design requires a power analysis to determine the necessary sample size.

*   **Alpha Level**: 0.05 (standard significance threshold).
*   **Target Power**: 0.80 (standard for detecting medium effects).
*   **Primary Hypothesis**: A directional contrast between High Agency and Low Agency conditions.
*   **Effect Size**: The primary power calculation targets a **medium effect size (Cohen's d = 0.5)** for the planned contrast (High vs. Low). While an omnibus ANOVA (f=0.25) is a secondary check, the sample size is driven by the specific directional hypothesis.
*   **Correction**: Tukey HSD for multiple comparisons to control family-wise error rate.

## Dataset Strategy

### Data Source

This study generates its own data through a controlled experimental interface. No external dataset download is required for the analysis phase. The data collection interface will export a CSV file containing the following variables:

| Variable | Type | Description | Source |
|----------|------|-------------|--------|
| `participant_id` | String | Unique anonymous identifier | Generated |
| `condition` | Categorical | Experimental condition (High, Low, Control) | Randomized |
| `adherence_rate` | Float | Percentage of AI recommendations followed | Behavioral Measure (Secondary Outcome) |
| `trust_score` | Float | Sum/Average of Lee & See (2004) scale items | Psychometric Measure (Primary Outcome) |
| `attention_check` | Boolean | Pass/Fail status of attention check | Data Quality |
| `perceived_agency_score` | Float | Manipulation check: Perceived agency (1-7 Likert) | Manipulation Check |
| `demographics` | JSON | Optional demographics (age, gender, etc.) | Self-reported |

### Verification Report

*   **Lee & See (2004) Items**: The exact items from the Lee & See (2004) scale will be verified against the primary source and stored in `docs/trust_scale_items.md` prior to implementation. The analysis pipeline will read these items to ensure fidelity.
*   **Variables**: All required variables (Condition, Adherence, Trust, Perceived Agency) are captured directly in the survey export. No external data linkage is needed.
*   **Data Quality**: Attention checks will be included to filter out low-quality responses. The sensitivity analysis will test the robustness of results to different exclusion thresholds.
*   **Adherence**: `adherence_rate` is treated as a secondary outcome/manipulation check. The sample size is powered for the primary outcome (trust). If adherence is analyzed as a co-primary outcome, a separate power justification or multiple-testing correction will be applied.

## Power Calculation

A pre-study power calculation is required to determine the sample size.

*   **Test**: Two-sample t-test (Planned Contrast: High vs. Low).
*   **Effect Size (d)**: 0.5 (Medium).
*   **Alpha**: 0.05.
*   **Power**: 0.80.
*   **Groups**: 3 (High, Low, Control) - *Note: Sample size is calculated for the primary contrast, but total N will be distributed across 3 groups.*

Using `pwr` (R) or `statsmodels.stats.power` (Python), the required sample size for a two-sample t-test with d=0.5, alpha=0.05, and power=0.80 is approximately **128 participants** (64 per group) for the contrast. To account for the three-group design and potential exclusions (attention check failures), we will target **180-200 participants** (approx. 60-67 per group).

*   **Output**: The results of this calculation will be stored in `research/power_calculation.json`.

### Power Calculation Results (JSON Structure)

```json
{
  "parameters": {
    "effect_size": 0.5,
    "alpha": 0.05,
    "power": 0.80,
    "test_type": "t-test (planned contrast)"
  },
  "results": {
    "sample_size_per_group_contrast": 64,
    "total_sample_size_target": 192,
    "adjustment_reason": "Three-group design + 10% attrition buffer"
  },
  "metadata": {
    "calculation_timestamp": "2024-05-21T00:00:00Z",
    "method": "statsmodels.stats.power.TTestIndPower",
    "reference": "Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences."
  }
}
```

## Decision/Rationale

*   **CPU vs. GPU**: The statistical analysis (ANOVA, contrasts, power analysis) is computationally lightweight and will run entirely on CPU. No GPU is required.
*   **Data Strategy**: The study generates its own data, eliminating the need for external dataset downloads and ensuring full control over the experimental manipulation.
*   **Scale Items**: The exact items from Lee & See (2004) will be verified and stored in `docs/trust_scale_items.md` before being used in the survey, ensuring compliance with the "Single Source of Truth" principle. The schema will reflect the standard 7-point Likert scale (1-7).
*   **Causal Inference**: The randomized assignment to conditions (High/Low/Control) allows for **causal inference** regarding the effect of the interface manipulation on trust. The findings will be framed as causal regarding the manipulation, while the psychological mechanism (perception) is the mediator.
*   **Manipulation Check Independence**: The `perceived_agency_score` is used solely to verify that the "High Agency" condition successfully increased perceived agency. It will not be used as a covariate in the primary trust analysis to avoid circularity.