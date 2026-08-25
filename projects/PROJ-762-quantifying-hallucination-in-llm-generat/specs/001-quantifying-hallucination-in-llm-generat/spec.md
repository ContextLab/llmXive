# Feature Specification: Quantifying Hallucination in LLM-Generated API Documentation

**Feature Branch**: `001-quantify-hallucination`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Quantifying Hallucination in LLM-Generated API Documentation"

## User Scenarios & Testing

### User Story 1 - Automated Metric Calculation Pipeline (Priority: P1)

**Journey**: As a researcher, I want the system to automatically ingest a subset of the CodeSearchNet Python dataset, generate descriptions using a CPU-tractable LLM, and compute a composite hallucination index based on lexical, semantic, and entity-overlap metrics, so that I can quantify factual accuracy without manual intervention.

**Why this priority**: This is the core data generation engine. Without the ability to generate descriptions and compute the hallucination index, no statistical analysis can occur. It delivers the primary dataset required for the research question.

**Independent Test**: Can be fully tested by running the pipeline on a small sample (e.g., 100 functions) and verifying that a CSV is produced containing the original code metrics and the three component scores (BLEU, cosine similarity, entity F1) plus the composite index.

**Acceptance Scenarios**:
1. **Given** a CSV of 100 Python functions with source code and reference docstrings, **When** the generation script is executed with `codegen-350M`, **Then** a results CSV is produced where every row contains a valid hallucination index between 0 and 1.
2. **Given** a function with a complex signature, **When** the entity extraction module runs, **Then** the system correctly identifies parameter names and return types in both the reference and generated text to calculate the F1 score.
3. **Given** the system is running on a GitHub Actions free-tier runner (2 CPU, ~7GB RAM), **When** processing [deferred] functions, **Then** the job completes within 4 hours without exceeding memory limits.

---

### User Story 2 - Correlation Analysis & Visualization (Priority: P2)

**Journey**: As a researcher, I want the system to compute Spearman rank-correlation coefficients between the hallucination index and intrinsic code characteristics (function length, naming style, cyclomatic complexity), and generate a summary report, so that I can determine if specific code attributes drive hallucinations.

**Why this priority**: This addresses the primary research question. It transforms the raw metrics from User Story 1 into the scientific findings (correlations) required to validate the hypothesis.

**Independent Test**: Can be tested by providing a pre-computed CSV of metrics and verifying that the script outputs a JSON or text report listing the correlation coefficients (ρ) and p-values for each code characteristic against the hallucination index.

**Acceptance Scenarios**:
1. **Given** a dataset with [deferred] records of code metrics and hallucination indices, **When** the analysis script runs, **Then** it outputs a Spearman correlation coefficient and p-value for the relationship between token count and hallucination index.
2. **Given** a dataset where function names are mixed (camelCase/snake_case), **When** the naming style metric is calculated, **Then** the system correctly categorizes functions and computes the correlation between naming style and hallucination rate.
3. **Given** the analysis is observational, **When** the report is generated, **Then** it explicitly frames findings as associational (e.g., "correlation observed") rather than causal.

---

### User Story 3 - Robustness & Sensitivity Verification (Priority: P3)

**Journey**: As a researcher, I want the system to perform a sensitivity analysis on the hallucination index threshold and a multiplicity correction on the hypothesis tests, so that I can ensure the findings are robust to parameter choices and statistical artifacts.

**Why this priority**: This ensures methodological soundness. Without sensitivity analysis and multiplicity correction, the results may be artifacts of arbitrary cutoffs or false positives from multiple testing, which the methodology panel would reject.

**Independent Test**: Can be tested by verifying that the output includes a sensitivity table showing how the "high hallucination" rate changes when the index threshold is swept from 0.01 to 0.1, and a corrected p-value table for the correlation tests.

**Acceptance Scenarios**:
1. **Given** a calculated hallucination index, **When** the sensitivity analysis runs, **Then** it reports the false-positive rate for thresholds ∈ {0.01, 0.05, 0.1} and confirms the headline rate varies predictably.
2. **Given** three hypothesis tests (length, naming, complexity) are performed, **When** the multiple-comparison correction runs, **Then** it applies a family-wise error correction (e.g., Bonferroni) and reports the adjusted p-values.
3. **Given** the dataset is observational, **When** the final report is generated, **Then** it includes a disclaimer that no causal claims are made regarding code complexity causing hallucinations.

### Edge Cases

- **What happens when** the LLM generates an empty string or non-text output? **How does system handle** the calculation of BLEU/ROUGE scores (should default to 0 or exclude the row).
- **How does system handle** functions with no reference docstrings in the dataset (should skip or flag as missing data, not crash).
- **What happens when** the code complexity metric (radon) fails to parse a specific Python syntax? **How does system handle** the error (log warning, set complexity to -1 or NaN, and exclude from regression).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Python subset of CodeSearchNet, extracting source code, reference docstrings, and function names, and calculate cyclomatic complexity using the `radon` library (See US-1).
- **FR-002**: System MUST generate a one-sentence description for each function using the `codegen-350M` model via Hugging Face Transformers in CPU-only mode (See US-1).
- **FR-003**: System MUST compute a composite hallucination index as a weighted average of BLEU score, ROUGE-L score, semantic cosine similarity (via `all-MiniLM-L6-v2`), and entity-overlap F1 score (See US-1).
- **FR-004**: System MUST perform Spearman rank-correlation tests between the hallucination index and three predictors: token count, naming style metric, and cyclomatic complexity (See US-2).
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the p-values of the correlation tests and report the adjusted significance (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the hallucination index classification threshold over the set {0.01, 0.05, 0.1} and report the variation in the "high hallucination" rate (See US-3).
- **FR-007**: System MUST output a final JSON/CSV report containing the correlation coefficients, p-values (raw and adjusted), and sensitivity analysis results, explicitly framing findings as associational (See US-2, US-3).

### Key Entities

- **FunctionRecord**: Represents a single code unit; attributes include `source_code`, `reference_docstring`, `token_count`, `naming_style` (categorical), `cyclomatic_complexity`, `generated_description`.
- **HallucinationMetrics**: Derived values for a `FunctionRecord`; attributes include `bleu_score`, `rouge_l_score`, `semantic_similarity`, `entity_f1`, `composite_index`.
- **AnalysisResult**: Aggregated statistical output; attributes include `correlation_coefficient`, `p_value`, `adjusted_p_value`, `threshold_sensitivity_data`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The pipeline's memory usage is measured against the GitHub Actions free-tier limit of ~7 GB RAM during the generation of [deferred] descriptions (See US-1).
- **SC-002**: The total execution time is measured against the 6-hour job limit for processing the full sample dataset (See US-1).
- **SC-003**: The validity of the entity-overlap metric is measured against a manual verification of [deferred] of the generated descriptions (See US-1).
- **SC-004**: The robustness of the correlation findings is measured against the variation in false-positive rates across the threshold sweep {0.01, 0.05, 0.1} (See US-3).
- **SC-005**: The statistical rigor is measured by the presence of adjusted p-values for all hypothesis tests to control family-wise error (See US-3).

## Assumptions

- The `codegen-350M` model can be loaded and run in 16-bit (default) precision on a CPU-only runner without exceeding 7 GB RAM, given a batch size of 1 or small batches.
- The CodeSearchNet Python subset contains a sufficient number of functions with valid reference docstrings to support a statistical power of ≥ 0.8 for detecting a small effect size (ρ > 0.1), assuming a sample size of [deferred]+ functions.
- The `radon` library successfully parses the vast majority of Python functions in the dataset; functions that fail to parse will be excluded from the complexity analysis without biasing the overall results.
- The entity extraction logic (using `spacy` or similar) correctly identifies API parameters and return types in standard Python docstring formats (Google, NumPy, reStructuredText).
- The "naming style" metric (presence of verbs, camelCase vs snake_case) is a valid proxy for "descriptiveness" as hypothesized in the research question.
- The dataset variables (token count, complexity, docstring) are sufficient to test the hypothesis; no additional external variables (e.g., developer experience, library age) are required for this specific correlation study.
