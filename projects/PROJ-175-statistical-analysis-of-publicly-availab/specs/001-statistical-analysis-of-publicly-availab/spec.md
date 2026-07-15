# Feature Specification: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Feature Branch**: `001-statistical-analysis-of-recipe-data`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

The research pipeline must successfully ingest the Recipe1M corpus, FlavorDB chemical profiles, and the Counterfactual Recipe Generation dataset, normalize ingredient names, and construct the required co-occurrence matrix and chemical similarity vectors within the constraints of the GitHub Actions free-tier runner (≤7 GB RAM, ≤6 hours).

**Why this priority**: Without a reproducible, memory-safe data pipeline, no statistical modeling can occur. This is the foundational block for all downstream analysis.

**Independent Test**: The pipeline can be executed in isolation to produce a single, validated CSV file containing pairs of ingredients with their log-transformed co-occurrence counts, cosine similarity scores, and functional role labels, without requiring the model fitting step.

**Acceptance Scenarios**:

1. **Given** the Recipe1M dataset, FlavorDB matrix, and Counterfactual Recipe Generation dataset are available via the configured URLs, **When** the pre-processing script runs on a standard GitHub Actions runner, **Then** it outputs a normalized dataset file within 2 hours and consumes less than 6 GB of RAM.
2. **Given** the raw ingredient lists contain variations like "butter" and "unsalted butter", **When** the normalization step executes using mapping to the FlavorDB canonical list with a Levenshtein distance threshold ≤ 2, **Then** these are mapped to a single canonical ID, and the resulting co-occurrence matrix $C$ reflects the aggregated counts.
3. **Given** an ingredient pair exists in the corpus but lacks a FlavorDB entry, **When** the feature engineering step processes the pair, **Then** it is either excluded from the analysis or assigned a default similarity score of zero, with a count logged in the summary report.

---

### User Story 2 - Statistical Model Fitting and Validation (Priority: P2)

The system must fit a regularized logistic regression model and a hierarchical Bayesian model to predict culinary compatibility, explicitly controlling for co-occurrence frequency while isolating the effects of flavor similarity and functional role. The dependent variable (binary compatibility) is derived from independent sensory evaluation scores in the Counterfactual Recipe Generation dataset, ensuring no circularity with the co-occurrence predictor.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by quantifying the independent predictive power of chemistry and function.

**Independent Test**: The model fitting process can be run on a downsampled subset (e.g., random stratified sampling by ingredient frequency to achieve [deferred] percentage of pairs) to verify that the coefficients for flavor similarity and functional role are statistically significant (p < 0.05), that the VIF diagnostics confirm no multicollinearity, and that the sample size is sufficient for a power analysis to detect an effect size ≥ 0.1 with [deferred] power.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with binary compatibility labels derived from independent sensory scores, **When** the logistic regression model is trained with L2 regularization, **Then** the output includes a coefficient plot showing the magnitude and direction of each predictor, and the p-value for "flavor similarity" is < 0.05.
2. **Given** the full model including all predictors, **When** a likelihood-ratio test is performed against a null model containing only co-occurrence frequency, **Then** the test statistic indicates a significant improvement in model fit (p < 0.05), valid because outcome labels are derived from an independent dataset.
3. **Given** the hierarchical Bayesian model specification, **When** it is fit using CPU-based sampling (e.g., PyMC with NUTS) on the stratified downsampled subset, **Then** the posterior distributions for the effect sizes are generated within 3 hours, and the credible intervals for flavor and role predictors do not overlap zero.

---

### User Story 3 - Evaluation and Reporting of Generalization (Priority: P3)

The system must evaluate the models on a held-out test set, calculating AUC, precision, recall, and calibration metrics, and generate a report comparing the full model's performance against the frequency-only baseline.

**Why this priority**: This validates the generalizability of the findings and quantifies the practical value of adding flavor/role data to substitution recommendations.

**Independent Test**: The evaluation script runs on the test split and produces a summary table and calibration plot, demonstrating whether the full model achieves a statistically significant improvement over the frequency-only baseline.

**Acceptance Scenarios**:

1. **Given** the trained models and a held-out test set, **When** the evaluation step runs, **Then** it outputs a CSV with AUC, precision, and recall for both the full model and the baseline, and the report explicitly tests the hypothesis that the full model's AUC exceeds the baseline by a meaningful margin (e.g., ≥ 0.05).
2. **Given** the predicted probabilities from the logistic regression, **When** a calibration plot is generated, **Then** the curve remains within ±0.1 of the ideal diagonal line, indicating reliable probability estimates.
3. **Given** the final results, **When** the summary report is generated, **Then** it explicitly states whether the hypothesis that "flavor and role predict compatibility beyond frequency" is supported, citing the specific statistical evidence (p-values, AUC delta).

---

### Edge Cases

- **What happens when** the Recipe1M dataset is too large to fit in memory? The system MUST stream data or downsample the corpus to ensure execution within 7 GB RAM, logging the sampling ratio.
- **How does system handle** ingredients present in the recipe corpus but missing from FlavorDB? These pairs MUST be excluded from the flavor-similarity analysis or imputed with a neutral value, with the exclusion count reported.
- **What happens when** the co-occurrence frequency for a pair is zero? The log-transform MUST handle this by adding a small epsilon or excluding the pair to avoid undefined values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the Recipe1M dataset, FlavorDB chemical matrix, and the Counterfactual Recipe Generation dataset from the specified URLs (See US-1).
- **FR-001b**: System MUST verify the availability and schema of the Counterfactual Recipe Generation dataset (specifically the presence of independent sensory compatibility labels) before pipeline execution (See US-2).
- **FR-002**: System MUST normalize ingredient names and map them to canonical IDs to ensure consistent co-occurrence counting (See US-1).
- **FR-003**: System MUST construct a global co-occurrence matrix $C$ where $C_{ij}$ is the log-transformed count (with epsilon smoothing for zero counts) of recipes containing both ingredients $i$ and $j$ (See US-1).
- **FR-004**: System MUST calculate cosine similarity between chemical vectors for ingredient pairs to derive the flavor-profile similarity feature (See US-1).
- **FR-005**: System MUST derive a categorical functional role (primary, secondary, garnish) for each ingredient based on its position in the ingredient list and frequency in the corpus, explicitly excluding co-occurrence frequency to prevent multicollinearity (See US-1).
- **FR-006**: System MUST fit a regularized logistic regression model where the dependent variable is binary culinary compatibility (derived from independent sensory scores) and independent variables are flavor similarity, functional role, and co-occurrence frequency (See US-2).
- **FR-007**: System MUST calculate Variance Inflation Factors (VIF) for all predictors to ensure no multicollinearity exists before interpreting coefficients (See US-2).
- **FR-008**: System MUST perform a likelihood-ratio test comparing the full model against a null model containing only co-occurrence frequency (See US-2).
- **FR-009**: System MUST evaluate model performance on a held-out test set using AUC, precision, recall, and calibration plots (See US-3).
- **FR-010**: System MUST generate a final report comparing the full model's AUC to the frequency-only baseline, explicitly testing the hypothesis that flavor and role add predictive value (See US-3).

### Key Entities

- **IngredientPair**: Represents a unique pair of ingredients $(i, j)$ with attributes: `log_co_occurrence`, `flavor_similarity`, `functional_role`, `compatibility_label`.
- **ModelResult**: Represents the output of the statistical fitting process, containing `coefficients`, `p_values`, `vif_scores`, and `posterior_distributions`.
- **EvaluationMetrics**: Represents the performance summary, containing `auc`, `precision`, `recall`, `calibration_curve`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The independent explanatory power of flavor and role is measured against the null model (co-occurrence only) via likelihood-ratio test p-values (See FR-008, US-2).
- **SC-002**: The generalization performance of the full model is measured against the frequency-only baseline via the delta in AUC, with a hypothesis test for a delta ≥ 0.05 (See FR-009, US-3).
- **SC-003**: The stability of the model is measured against the requirement for independent predictors via Variance Inflation Factors (VIF) (See FR-007, US-2).
- **SC-004**: The reliability of probability estimates is measured against the ideal diagonal in calibration plots (See FR-009, US-3).

## Assumptions

- The Recipe1M dataset, FlavorDB matrix, and Counterfactual Recipe Generation dataset are available via the specified HuggingFace and Zenodo URLs and are accessible from the GitHub Actions environment without authentication.
- The "Counterfactual Recipe Generation" dataset provides independent sensory evaluation scores or crowd-sourced preference ratings that can be used as a binary label for culinary compatibility, distinct from the co-occurrence counts.
- A downsampled subset of the Recipe1M corpus (determined by power analysis to detect effect size ≥ 0.1 with [deferred] power) will be sufficient to train the logistic regression and Bayesian models within a defined runtime limit.
- The GitHub Actions free-tier runner (limited CPU cores, ~7 GB RAM) is sufficient for the CPU-based sampling of the hierarchical Bayesian model if the dataset is appropriately downsampled.
- The functional role of an ingredient can be reliably inferred from its position in the ingredient list and its frequency in the corpus (excluding co-occurrence counts), serving as a valid proxy for "primary" vs. "garnish" roles.
- The flavor-profile similarity derived from FlavorDB chemical vectors is a valid proxy for the sensory compatibility of ingredient pairs.