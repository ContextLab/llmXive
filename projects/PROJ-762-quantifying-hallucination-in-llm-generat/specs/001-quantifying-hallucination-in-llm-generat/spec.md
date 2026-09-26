# Feature Specification: Quantifying Hallucination in LLM-Generated API Documentation

**Feature Branch**: `001-quantify-hallucination`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Quantifying Hallucination in LLM-Generated API Documentation"

## User Scenarios & Testing

### User Story 1 - Automated Metric Calculation Pipeline (Priority: P1)

**Journey**: As a researcher, I want the system to automatically ingest a stratified random sample of the CodeSearchNet Python dataset, generate descriptions using CPU-tractable LLMs (`codegen-350M` and `starcoderbase-1b`), and compute a composite hallucination index based on real entity-overlap F1 metrics derived from the source code AST, so that I can quantify factual accuracy without manual intervention or simulated data.

**Why this priority**: This is the core data generation engine. Without the ability to generate descriptions and compute the hallucination index from *actual* model outputs, no statistical analysis can occur. It delivers the primary dataset required for the research question.

**Independent Test**: Can be fully tested by running the pipeline on a small sample (e.g., 100 functions) and verifying that a CSV is produced containing the original code metrics and the real entity-overlap F1 score plus the composite index, with no placeholder or simulated values.

**Acceptance Scenarios**:
1. **Given** a CSV of 100 Python functions with source code and reference docstrings, **When** the generation script is executed with `codegen-350M` and `starcoderbase-1b` (CPU-only), **Then** a results CSV is produced where every row contains a valid hallucination index (entity F1) between 0 and 1, derived from actual LLM text generation.
2. **Given** a function with a complex signature, **When** the entity extraction module runs, **Then** the system correctly identifies parameter names and return types in the source code AST and the *actual* generated text to calculate the F1 score using `spacy` with the `en_core_web_sm` model.
3. **Given** the system is running on a GitHub Actions free-tier runner (2 CPU, ~7GB RAM), **When** processing 1000 functions, **Then** the job completes within 4 hours without exceeding memory limits, processing real tokens rather than placeholders.

---

### User Story 2 - Correlation Analysis & Visualization (Priority: P2)

**Journey**: As a researcher, I want the system to compute Spearman rank-correlation coefficients and fit a multiple linear regression model between the *real* hallucination index and intrinsic code characteristics (function length, naming style, cyclomatic complexity), and generate a summary report, so that I can determine if specific code attributes drive hallucinations while controlling for confounders.

**Why this priority**: This addresses the primary research question. It transforms the raw metrics from User Story 1 into the scientific findings (correlations and regression coefficients) required to validate the hypothesis and control for text length bias.

**Independent Test**: Can be tested by providing a pre-computed CSV of metrics and verifying that the script outputs a JSON or text report listing the correlation coefficients (ρ), p-values, and regression coefficients for each code characteristic against the hallucination index.

**Acceptance Scenarios**:
1. **Given** a dataset with 1000 records of code metrics and *real* hallucination indices, **When** the analysis script runs, **Then** it outputs a Spearman correlation coefficient and p-value for the relationship between token count and hallucination index, controlling for generated text length.
2. **Given** a dataset where function names are mixed (camelCase/snake_case), **When** the naming style metric is calculated, **Then** the system correctly categorizes functions and computes the correlation between naming style and hallucination index.
3. **Given** the analysis is observational, **When** the report is generated, **Then** it explicitly frames findings as associational (e.g., "correlation observed") rather than causal.

---

### User Story 3 - Robustness & Sensitivity Verification (Priority: P3)

**Journey**: As a researcher, I want the system to perform a sensitivity analysis on the hallucination index threshold, validate the automated index against a manually verified ground-truth subset, and apply multiplicity correction on the hypothesis tests, so that I can ensure the findings are robust to parameter choices and statistical artifacts.

**Why this priority**: This ensures methodological soundness. Without sensitivity analysis, manual validation, and multiplicity correction, the results may be artifacts of arbitrary cutoffs, circular metrics, or false positives from multiple testing, which the methodology panel would reject.

**Independent Test**: Can be tested by verifying that the output includes a sensitivity table showing how the "high hallucination" rate changes when the index threshold is swept from 0.01 to 0.1, a validation report comparing automated scores to manual ground truth, and a corrected p-value table for the correlation tests.

**Acceptance Scenarios**:
1. **Given** a calculated hallucination index, **When** the sensitivity analysis runs, **Then** it reports the "high hallucination" rate (defined as index ≥ threshold) for thresholds ∈ {0.01, 0.05, 0.1} and confirms the headline rate varies predictably.
2. **Given** a manually verified subset of 30 items, **When** the validation runs, **Then** it reports the correlation between the automated index and the manual ground-truth score (normalized 0-1 Likert average) and the Krippendorff's alpha for inter-rater reliability.
3. **Given** three hypothesis tests (length, naming, complexity) are performed, **When** the multiple-comparison correction runs, **Then** it applies a family-wise error correction (e.g., Bonferroni) and reports the adjusted p-values.
4. **Given** the dataset is observational, **When** the final report is generated, **Then** it includes a disclaimer that no causal claims are made regarding code complexity causing hallucinations.

### Edge Cases

- **What happens when** the LLM generates an empty string or non-text output? **How does system handle** the calculation of entity F1 scores (should default to 0.0 and flag the row).
- **How does system handle** functions with no reference docstrings in the dataset (should skip or flag as missing data, not crash).
- **What happens when** the code complexity metric (radon) fails to parse a specific Python syntax? **How does system handle** the error (log warning, set complexity to -1 or NaN, and exclude from regression).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Python subset of CodeSearchNet, extracting source code, reference docstrings, and function names, and calculate cyclomatic complexity using the `radon` library (See US-1).
- **FR-002**: System MUST generate a one-sentence description for each function using the `codegen-350M` model AND the `bigcode/starcoderbase-1b` model via Hugging Face Transformers in CPU-only mode. The system MUST use a fixed prompt template enforcing a one-sentence output. The system MUST enforce the one-sentence constraint by: (1) applying a regex check for sentence delimiters (`.`, `!`, `?`); if multiple are found, truncate to the first sentence; if none, truncate to 64 tokens. This mechanism MUST be deterministic and verifiable (See US-1).
- **FR-003**: System MUST compute a hallucination index defined as an **entity-overlap F1 score** (0.0 to 1.0). The calculation proceeds in two steps: (1) Extract entities (parameters, return types, function names) from the *actual* generated text and the source code AST using `spacy` (`en_core_web_sm`); (2) Calculate the raw F1 score. The metric is explicitly defined as the raw F1 score divided by 1.0 (the theoretical maximum), making the "length-normalized" label a semantic descriptor of the intent (to be length-invariant) rather than a complex mathematical operation. This index is the sole component of the hallucination metric (See US-1).
- **FR-004**: System MUST perform Spearman rank-correlation tests between the hallucination index and three predictors: source code token count, naming style metric, and cyclomatic complexity. These tests MUST control for the length of the generated description (generated text token count) as a covariate to ensure robustness against any residual length bias in the empirical data (See US-2).
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the p-values of the correlation tests and report the adjusted significance (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the hallucination index classification threshold (defined as `index >= threshold`) over the set {0.01, 0.05, 0.1} and report the variation in the "high hallucination" rate (See US-3).
- **FR-007**: System MUST output a final JSON/CSV report containing the correlation coefficients, p-values (raw and adjusted), and sensitivity analysis results. The report MUST contain the phrase "correlation observed" to explicitly frame findings as associational (See US-2, US-3).
- **FR-008**: System MUST fit a multiple linear regression (or generalized additive model) with the hallucination index as the dependent variable and source code token count, naming style, and cyclomatic complexity as independent predictors. The model MUST include the generated description's token count as a covariate to control for length bias as an empirical safeguard (See US-2).
- **FR-009**: System MUST randomly select a stratified subset of items for manual verification.. For this subset, human annotators MUST verify factual accuracy against the **source code's actual behavior/signature** (ground truth) using the following protocol:
    1. **Recruitment & Training**: Engage independent annotators. Conduct a 1-hour calibration session to ensure a Kappa score > 0.6 on a pilot set of 10 items.
    2. **Scoring Rubric**: Annotators score each item on a 0-3 scale based **exclusively on entity-level accuracy** (parameters, return types, function names), matching the automated metric:
        - **Score 3**: Description correctly identifies all parameters/return types.
        - **Score 2**: Minor discrepancies (e.g., missing one optional parameter) but core signature is correct.
        - **Score 1**: Major discrepancies (e.g., wrong return type, missing required parameters).
        - **Score 0**: Hallucinated parameters, return types, or logic not present in the code or comments.
        *Note: Logic/behavior description is explicitly excluded from scoring to ensure construct validity.*
    3. **Scoring Calculation**: The system MUST calculate the **manual score** as the median of the three normalized scores (Score/3).
    4. **Reliability Check**: The system MUST calculate Krippendorff's alpha. If alpha < 0.6, the system MUST flag the dataset for review. If the range of the three scores (max - min) > 1.0, the system MUST select the two original scores closest to the median (tie-breaker: prefer the higher score if equidistant) and average them with the third score to produce the final score.
    This value is used for correlation (See US-3).
- **FR-010**: System MUST compare the hallucination indices and correlation results generated by `codegen-350M` and `starcoderbase-1b` to test generality and isolate model-specific variance (See US-1, US-2).
- **FR-011**: System MUST report the validation metrics from FR-009. If the Pearson correlation between the automated index (entity F1) and the manual score (normalized rubric average) is < 0.7 (a standard benchmark for good inter-method reliability), the system MUST flag the index calibration as "needs review" and report the 95% confidence interval for the correlation (See US-3).
- **FR-012**: System MUST explicitly reject any mode of operation that generates placeholder, simulated, or hardcoded hallucination scores. All metrics MUST be derived from actual LLM inference and real entity comparison. The system MUST NOT support a `--simulate` flag or any similar mechanism for generating synthetic data (See US-1).
- **FR-013**: System MUST orchestrate the manual verification workflow described in FR-009, including generating the adjudication report based on the senior reviewer input (if applicable) and calculating Krippendorff's alpha (See US-3).

### Key Entities

- **FunctionRecord**: Represents a single code unit; attributes include `source_code`, `reference_docstring`, `token_count`, `naming_style` (categorical), `cyclomatic_complexity`, `generated_description` (from both models).
- **HallucinationMetrics**: Derived values for a `FunctionRecord`; attributes include `entity_f1` (computed against source code entities), `normalized_entity_f1` (equal to entity_f1, representing the final hallucination index).
- **AnalysisResult**: Aggregated statistical output; attributes include `correlation_coefficient`, `p_value`, `adjusted_p_value`, `regression_coefficients`, `threshold_sensitivity_data`, `manual_validation_correlation`, `krippendorff_alpha`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The pipeline's memory usage is measured against the GitHub Actions free-tier RAM limit during the generation of 1000 descriptions. (See US-1).
- **SC-002**: The total execution time is measured against the job limit for processing the full sample dataset. (See US-1).
- **SC-003**: The validity of the entity-overlap metric is measured against a manual verification of a random stratified sample of items., comparing them against the source code's actual behavior using **Pearson's correlation coefficient** (See US-3).
- **SC-004**: The robustness of the correlation findings is measured against the variation in "high hallucination" rates across the threshold sweep {0.01, 0.05, 0.1} (See US-3).
- **SC-005**: The statistical rigor is measured by the presence of adjusted p-values for all hypothesis tests to control family-wise error (See US-3).
- **SC-006**: The generalizability of findings is measured by the consistency of regression coefficients between the `codegen-350M` and `starcoderbase-1b` models, defined as: coefficients must have the same sign AND the absolute difference between coefficients must be ≤ 0.15 (a community-standard threshold for negligible variance in NLP evaluation). CI overlap is noted as a secondary observation but does not override the sign/difference requirement (See US-2).
- **SC-007**: The integrity of the results is measured by the absence of any simulated, placeholder, or hardcoded metric values in the final output dataset; all values must be traceable to a real LLM generation event (See US-1).

## Assumptions

- The `codegen-350M` and `bigcode/starcoderbase-1b` models can be loaded and run in 16-bit (default) precision on a CPU-only runner without exceeding 7 GB RAM, given a batch size of 1 or small batches.
- The CodeSearchNet Python subset contains a sufficient number of functions with valid reference docstrings to support a statistical power of ≥ 0.8 for detecting a small effect size (ρ > 0.1), assuming a sample size of 1000+ functions.
- The `radon` library successfully parses the vast majority of Python functions in the dataset; functions that fail to parse will be excluded from the complexity analysis without biasing the overall results.
- The entity extraction logic (using `spacy` with `en_core_web_sm`) correctly identifies API parameters and return types in standard Python docstring formats (Google, NumPy, reStructuredText) and source code ASTs.
- The "naming style" metric (presence of verbs, camelCase vs snake_case) is a valid proxy for "descriptiveness" as hypothesized in the research question.
- The dataset variables (token count, complexity, docstring) are sufficient to test the hypothesis; no additional external variables (e.g., developer experience, library age) are required for this specific correlation study.
- The manual verification process described in FR-009 will yield a real, non-simulated dataset for validation; no placeholder or simulated scores will be generated or used.
- The GitHub Actions free-tier runner provides sufficient disk space to store the dataset, model weights, and intermediate CSVs. without requiring external storage solutions.
- The sample size for manual verification is sufficient to achieve a stable Krippendorff's alpha estimate for the prototype scope.