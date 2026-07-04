# Research: Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

## Research Question

Does embodied training through physics-based virtual manipulation improve transfer to abstract mathematical reasoning more than static visual instruction for adult learners?

**Critical Clarification**: Given the reliance on secondary analysis of observational data, this project can only identify **associations** between instruction type and reasoning scores. It **cannot** establish causal "improvement" without randomization. The research question is treated as a hypothesis for *association* in this context.

## Methodological Approach

This project employs a **secondary analysis** of existing public educational datasets where available, supplemented by **synthetic data generation** to validate the analysis pipeline.

### Statistical Rigor & Assumptions

1. **Primary Method: ANCOVA**: To address regression to the mean and baseline dependency, the primary statistical method is **Analysis of Covariance (ANCOVA)** with `pre_test_score` as the covariate. This controls for baseline differences between groups, providing a more valid estimate of the association than simple gain scores.
2. **Secondary Method: T-Test**: Independent samples t-tests on gain scores (`post_test_score - pre_test_score`) are retained as a **secondary descriptive check** but are not used for primary inference due to their susceptibility to measurement error and regression to the mean.
3. **Associational Framing**: Since secondary data is observational (quasi-experimental), all findings are framed as **associational**. No causal claims are made regarding the "embodied" condition causing improved reasoning.
4. **Multiple Comparisons**: If testing across $N$ distinct mathematical concepts (identified by `concept_id`), a **Bonferroni correction** is applied ($\alpha_{adj} = 0.05 / N$) to control family-wise error rate. If no distinct concepts are identified, no correction is applied.
5. **Power Analysis**: Achieved power is calculated for the observed effect size. Results with power < 0.80 are flagged as "underpowered" to prevent over-interpretation of null results.
6. **Collinearity**: Predictor variables with $|r| > 0.8$ are detected and reported; independent effects are not claimed for such variables.
7. **Sensitivity**: Thresholds for "valid learning gains" (0.01, 0.05, 0.10) are swept to test robustness.

## Dataset Strategy

### Verified Datasets
The project relies **exclusively** on the following verified sources for public data loading or programmatic access. If a dataset lacks the required `instruction_type` variable, the system falls back to synthetic generation.

| Dataset Name | Source URL | Status | Notes |
|:--- |:--- |:--- |:--- |
| **DatasetRecord** | ` | **Critical Blocker** | Parquet format. Contains pre/post scores and `instruction_type`? **Pending verification**. If `instruction_type` is missing, the Secondary Analysis path is **non-functional**. |
| **UCI HAR** | ` | **Unsuitable** | CSV. Human Activity Recognition. **Lacks `instruction_type` and math reasoning scores**. Excluded from primary analysis. |
| **UCI Shopper** | ` | **Unsuitable** | Parquet. E-commerce. **Lacks `instruction_type` and math reasoning scores**. Excluded from primary analysis. |
| **UCI DROP** | ` | **Unsuitable** | Parquet. Reading comprehension. **Lacks `instruction_type`**. Excluded from primary analysis. |

### Dataset Variable Fit Assessment

**Critical Check**: The research question requires `pre_test_score`, `post_test_score`, and `instruction_type` (values: "embodied", "static").

1. **DatasetRecord**: This is the **only** potential candidate. It must be inspected to confirm the presence of `instruction_type`.
 * *Risk*: If `instruction_type` is missing, the dataset is **inappropriate** for the primary analysis.
 * *Mitigation*: The system will detect missing `instruction_type` and automatically invoke the **Synthetic Data Generator** (FR-009). **Crucially**, this fallback means the project's empirical contribution is limited to **pipeline validation** (code correctness), not answering the research question.
2. **UCI/Other Datasets**: These datasets are **definitionally absent** of the "embodied" vs. "static" instruction metadata required for the comparison.
 * *Decision*: They are excluded from the primary analysis. The system will not attempt to load them for the primary statistical comparison.

### Synthetic Data Strategy

Since public datasets may lack the specific "embodied" vs. "static" labels, the **Synthetic Data Generator** is a core component.
* **Mechanism**: Generates `N` records with `pre_test_score` (Normal distribution), `post_test_score` (Normal distribution with mean shift based on condition), and `instruction_type`.
* **Ground Truth**: The generator knows the true effect size (e.g., Cohen's d = 0.5) to validate if the statistical pipeline correctly recovers it.
* **Alignment**: Physical parameters (e.g., "gravity" in simulation) map to abstract concepts (e.g., "fraction difficulty") to satisfy Constitution Principle VI **only in Synthetic Mode**.
* **Limitations of Synthetic Validation**: Synthetic data validates **code correctness** (the statistical engine calculates correctly) but **not the research hypothesis** (the phenomenon of embodied learning). Real-world confounding, non-normal distributions, and unmeasured variables are not simulated. Therefore, a successful synthetic run does not validate the claim that "embodied training improves transfer."

## Statistical Plan

1. **Data Loading**: Load CSV/Parquet. Validate columns: `pre_test_score`, `post_test_score`, `instruction_type`.
2. **Descriptive Stats**: Mean, SD, N per condition.
3. **Collinearity Check**: Compute correlation matrix for all predictors. Flag pairs with $|r| > 0.8$.
4. **Hypothesis Testing (Primary)**:
 * **ANCOVA**: Fit model: `post_test_score ~ instruction_type + pre_test_score`.
 * Report F-statistic, p-value, adjusted means, and effect size (partial eta-squared).
 * Frame results as **associational**.
5. **Hypothesis Testing (Secondary)**:
 * Calculate `gain = post - pre`.
 * Levene's Test for Equality of Variances.
 * If $p > 0.05$: Student's t-test on gain scores.
 * If $p \le \alpha$: Welch's t-test on gain scores.
 * Calculate Cohen's d.
 * Apply Bonferroni correction if $N_{concepts} > 1$ (based on `concept_id`).
6. **Power Analysis**: Compute achieved power ($1-\beta$) for observed effect. Flag if $< 0.80$.
7. **Sensitivity Sweep**: Repeat steps 4-6 for gain thresholds $\{0.01, 0.05, 0.10\}$.
8. **Output**: JSON report with ANCOVA results, t-test results, `inference_framing: "associational"`, `robustness_warning`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing `instruction_type`** | High: Cannot perform primary analysis. | System detects missing column, logs warning, and switches to Synthetic Data Mode. Report explicitly states "No public data found; results based on synthetic validation (pipeline check only)." |
| **Small Sample Size (N < 30)** | Medium: Low power, unreliable estimates. | Power analysis flags "underpowered". Sensitivity sweep is skipped (FR-005). |
| **High Collinearity** | Medium: Misleading multivariate results. | System detects $|r| > 0.8$, reports diagnostic, and refrains from claiming independent effects. |
| **Dataset Variable Mismatch** | High: Invalid results if variables don't map. | Strict column validation. If required variables are missing, the system does not impute; it fails gracefully or switches to synthetic mode. |
| **Causal Misinterpretation** | High: Users may infer causation from association. | All outputs explicitly labeled "associational". No causal language used in reports. |

## Conclusion

This research plan prioritizes methodological rigor and reproducibility. By explicitly framing results as associational, using ANCOVA to control for baseline differences, and providing a fallback to synthetic data for pipeline validation (with clear limitations), the project ensures that even if public data is insufficient, the analysis methodology remains sound and verifiable. The project's empirical contribution is limited to **pipeline validation** if no suitable public data is found.