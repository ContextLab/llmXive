# Methodological Documentation: Embodied Curriculum Learning Analysis

## Overview

This document provides a detailed explanation of the statistical methods, data handling procedures, and philosophical constraints implemented in the `PROJ-560` pipeline. It is intended for researchers, auditors, and developers who require a deep understanding of the system's analytical capabilities and limitations.

## Statistical Framework

### Gain Score Analysis
The primary metric of interest is the **Gain Score**, calculated as the difference between post-intervention and pre-intervention scores:
$$ \text{Gain} = \text{Post} - \text{Pre} $$
This metric isolates the change attributable to the intervention period, controlling for baseline ability.

### Hypothesis Testing
The system employs **Independent Samples t-tests** to compare the mean gain scores between two groups (e.g., "embodied" vs. "static" instruction).
- **Variance Assumption**: The system automatically performs Levene's Test for equality of variances. If variances are unequal (p < 0.05), Welch's t-test is used; otherwise, Student's t-test is applied.
- **Effect Size**: Cohen's d is calculated to quantify the magnitude of the difference, independent of sample size.
- **Confidence Intervals**: 95% confidence intervals are provided for the mean difference.

### Multiple Comparison Correction
When testing multiple concepts or hypotheses simultaneously, the **Bonferroni correction** is applied to control the Family-Wise Error Rate (FWER). The significance threshold ($\alpha$) is divided by the number of tests performed.

### Power Analysis
The system calculates the achieved statistical power for the observed effect size. Results with power < 0.80 are flagged as "underpowered," indicating a high risk of Type II errors (false negatives).

## Data Integrity and Sourcing

### Real Data Requirement
The pipeline is designed to operate on **real, empirical data**. Users must provide datasets that meet the following criteria:
- **Format**: CSV or JSON.
- **Required Columns**: `pre_test_score`, `post_test_score`, `instruction_type`.
- **Source**: Public repositories (e.g., OpenML) or internal experimental logs.

### Synthetic Data Fallback
If a provided public dataset lacks the `instruction_type` column, the system invokes a **Synthetic Data Generator**.
- **Purpose**: This is strictly a **validation mode** to ensure the statistical engine functions correctly.
- **Mechanism**: The generator creates a dataset with known statistical properties (mean differences, standard deviations) based on user-defined parameters.
- **Mapping Log**: A `mapping_log.json` is produced to document the derivation of synthetic parameters, satisfying Constitution Principle VI (Simulation-Pedagogy Alignment).
- **Limitation**: Synthetic data cannot be used to draw conclusions about the efficacy of embodied learning in the real world.

## Philosophical and Pedagogical Scope

### Associational Framing
In accordance with FR-003, all statistical findings are explicitly framed as **associational**. The system does not make causal claims (e.g., "teaching causes learning"). Instead, it reports on the correlation between instructional method and gain scores.

### Training vs. Teaching
The system distinguishes between **training** (habituation through repetition) and **teaching** (intellectual engagement). However, the current MVP treats these as categorical labels within the `instruction_type` field. The philosophical implications of this distinction are out of scope for the statistical engine but are noted in the results output.

### Abstract Concepts
The term "abstract concept" is used to describe the target of the learning intervention. The system does not define or validate the nature of these concepts (e.g., mathematics, justice). It assumes the input data correctly reflects the experimental design regarding these concepts.

## Sensitivity Analysis

To ensure the robustness of the headline effect size, the system supports a **Sensitivity Sweep**.
- **Process**: The analysis is re-run across a range of significance thresholds (e.g., 0.01, 0.05, 0.10).
- **Robustness Warning**: If the effect size drops below a negligible threshold at any point in the sweep, a `robustness_warning: true` flag is set in the output.
- **Sample Size Constraint**: Sensitivity analysis requires a minimum sample size of N=30. If N < 30, the sweep is skipped, and a warning is issued.

## Collinearity Diagnostics

The system checks for multicollinearity between predictors (if applicable) using Pearson correlation. If $|r| > 0.8$, a diagnostic is reported to alert the user to potential instability in the estimates.

## Reproducibility

All analyses are deterministic when a random seed is provided. The system logs all parameters, including the seed, to ensure that results can be exactly reproduced.
- **Seed Management**: Controlled via the `--seed` CLI argument.
- **Logging**: Detailed logs are written to `data/derivation_logs/`.

## Conclusion

This tool provides a rigorous, statistically sound framework for analyzing educational intervention data. By enforcing strict data requirements, automatic fallbacks for validation, and transparent associational framing, it ensures that research conclusions are both robust and methodologically sound.