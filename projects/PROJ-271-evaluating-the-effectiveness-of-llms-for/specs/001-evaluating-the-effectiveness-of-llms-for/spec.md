# Feature Specification: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of LLMs for Detecting Code Smells"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Data Pipeline and Static Analysis Baseline (Priority: P1)

The research system MUST ingest a sampled subset of the `codeparrot/github-code` dataset, compute structural metrics (LOC, cyclomatic complexity) using `radon`, and generate a baseline "smell label" set using standard Pylint rules.

**Why this priority**: This establishes the baseline for the "rule-based" detection mode. Without a reliable, reproducible static analysis baseline and the corresponding structural feature vectors, the comparative analysis against LLMs cannot proceed.

**Independent Test**: Can be fully tested by running the data pipeline script on a local subset (e.g., 10 functions) and verifying that a CSV output exists containing the function code, structural metrics, and a list of detected static smells (e.g., `C0111`, `R0913`).

**Acceptance Scenarios**:

1. **Given** a valid HuggingFace dataset path and a sample size of 800 functions, **When** the pipeline executes, **Then** a `data/static_baseline.csv` file is generated containing 800 rows with columns for `code`, `loc`, `cyclomatic_complexity`, and `static_smell_labels`.
2. **Given** a function with known high cyclomatic complexity, **When** the `radon` metrics are computed, **Then** the `cyclomatic_complexity` column reflects the correct integer value according to the `radon` documentation.
3. **Given** a function containing a clear variable naming violation, **When** Pylint runs, **Then** the `static_smell_labels` column includes the corresponding Pylint error code (e.g., `C0103`).

---

### User Story 2 - Semantic Feature Extraction and LLM Inference (Priority: P2)

The research system MUST compute semantic embeddings for each function using `sentence-transformers/all-MiniLM-L6-v2` and generate a "smell label" set via a CPU-quantized LLM (CodeLlama-7B-Instruct-GGUF) using a standardized prompt.

**Why this priority**: This enables the "semantic" detection mode. It validates the feasibility of running semantic analysis on CPU-only infrastructure, which is a core constraint of the project.

**Independent Test**: Can be fully tested by processing a single function through the embedding model and the LLM inference engine, verifying that a semantic vector is produced and the LLM returns a parsable list of smell categories.

**Acceptance Scenarios**:

1. **Given** a Python function string, **When** the `sentence-transformers` model processes it, **Then** a dense vector of a fixed dimension is returned without memory errors.
2. **Given** a function with a "Long Method" smell, **When** the LLM (CodeLlama-7B-4bit) processes the prompt, **Then** the parsed output includes "Long Method" in the list of detected smells.
3. **Given** the system constraints (CPU cores, 7 GB RAM), **When** the LLM inference batch (≤50 functions) runs, **Then** the process completes without exceeding a substantial duration of wall-clock time or triggering an OOM (Out of Memory) error.

---

### User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

The research system MUST correlate structural and semantic features with detection outcomes, perform McNemar's test for paired significance on a per-function basis, and generate a summary report identifying which features predict static-only vs. LLM-only detections. The system MUST also perform a sensitivity analysis on structural thresholds and a multicollinearity check on predictors.

**Why this priority**: This delivers the scientific answer to the research question. It transforms raw detection data into statistical evidence regarding the complementarity of the two methods, while rigorously addressing tautology and multicollinearity risks.

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated JSON dataset (mocked or real) and verifying that the output includes a p-value for McNemar's test, a logistic regression coefficient table, a sensitivity sweep report, and a VIF analysis result.

**Acceptance Scenarios**:

1. **Given** a dataset with paired detection outcomes (Static: Yes/No, LLM: Yes/No) per function, **When** McNemar's test is executed, **Then** a p-value is calculated and stored in `results/statistical_significance.json`.
2. **Given** a logistic regression model predicting detection mode, **When** the model is fitted (after VIF check), **Then** the output includes coefficients for `loc`, `cyclomatic_complexity`, and `semantic_embedding_mean`.
3. **Given** the analysis completes, **When** the report is generated, **Then** it explicitly lists the set of smells detected *only* by static analysis and *only* by the LLM, along with the sensitivity analysis results.

### Edge Cases

- What happens when the LLM returns malformed JSON or text that cannot be parsed into a list of smell categories? (System must log the error and record "None" or "Unparseable" for that entry).
- How does the system handle functions that are too large for the 4-bit quantized model's context window? (System must truncate or skip and log the count).
- What happens if the `radon` library fails to parse a specific Python syntax? (System must catch the exception, log the file, and exclude it from the final analysis count).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST sample a representative subset of functions from the `codeparrot/github-code` dataset to ensure the analysis fits within the 6-hour compute window. The system MUST output a CSV containing `code`, `loc`, `cyclomatic_complexity`, and `static_smell_labels` for the sampled functions. (See US-1).
- **FR-002**: System MUST compute structural metrics (LOC, cyclomatic complexity, nesting depth) for every sampled function using the `radon` library (See US-1).
- **FR-003**: System MUST execute Pylint on each function to generate a deterministic baseline set of code smell labels (See US-1).
- **FR-004**: System MUST load the CodeLlama-7B-Instruct-GGUF (4-bit quantized) model using `llama-cpp-python` on a CPU-only device to perform semantic inference (See US-2).
- **FR-005**: System MUST compute semantic embeddings for every function using `sentence-transformers/all-MiniLM-L6-v2` and store them as dense vectors (See US-2).
- **FR-006**: System MUST perform McNemar's test with a significance level of α = 0.05 on the paired detection outcomes (Static vs. LLM) for each function (See US-3).
- **FR-007**: System MUST fit a logistic regression model to predict the detection mode (Static vs. LLM) based on structural and semantic features, after verifying that the Variance Inflation Factor (VIF) for each predictor is < 5 (See US-3).
- **FR-008**: System MUST record peak RAM usage, CPU utilization, and total inference time for every batch of ≤50 functions to verify compliance with hardware constraints (See US-2).
- **FR-009**: System MUST perform a sensitivity analysis by sweeping the structural metric thresholds (e.g., LOC ∈ {50, 100, 150}) and report the variation in false-positive/false-negative rates for static-only detections (See US-3).
- **FR-010**: System MUST calculate the Variance Inflation Factor (VIF) for all predictors in the logistic regression model and flag any predictor with VIF ≥ 5 for orthogonalization or exclusion (See US-3).

### Key Entities

- **CodeFunction**: Represents a single sampled Python function. Attributes: `source_code`, `structural_metrics` (dict), `static_labels` (list), `semantic_vector` (array), `llm_labels` (list).
- **DetectionResult**: Represents the outcome of a detection attempt. Attributes: `smell_category`, `detected_by_static` (bool), `detected_by_llm` (bool), `features_at_detection` (dict).
- **StatisticalReport**: Aggregated results of the analysis. Attributes: `mcnemar_pvalues` (dict), `logistic_regression_coefficients` (dict), `complementarity_summary` (string), `sensitivity_analysis` (dict), `vif_scores` (dict).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between structural metrics (e.g., LOC) and static-only detection rates is measured against the logistic regression model coefficients (See US-3).
- **SC-002**: The correlation between semantic embeddings and LLM-only detection rates is measured against the logistic regression model coefficients (See US-3).
- **SC-003**: The statistical significance of the difference in detection rates between static analysis and LLMs is measured against the p-value from McNemar's test (See US-3).
- **SC-004**: The feasibility of the analysis on free-tier CI is measured against the constraint of ≤6 hours total runtime and ≤7 GB peak RAM usage (See US-2).
- **SC-005**: The validity of the dataset is measured by confirming that all required variables (structural metrics, semantic vectors, detection labels) are present for ≥ 95% of the 800 sampled functions (See US-1).

## Assumptions

- The `codeparrot/github-code` dataset on HuggingFace contains a sufficient number of Python functions with diverse code smells to support a random sample of functions.
- The 4-bit quantized CodeLlama-7B-Instruct model (GGUF format) is available and compatible with the `llama-cpp-python` library on a standard Linux CPU runner without requiring CUDA or GPU acceleration.
- The `radon` library correctly handles all Python syntax variations present in the GitHub code sample, or that syntax errors are rare enough to be excluded without biasing the sample.
- The `sentence-transformers/all-MiniLM-L6-v2` model fits within the 7 GB RAM limit when processing the embeddings alongside the LLM inference batch.
- The definition of "code smells" used by Pylint and the LLM prompt are semantically comparable enough to allow for meaningful overlap analysis (e.g., both identify "Long Method" as a distinct category).
- The GitHub Actions free-tier runner provides a specified number of CPU cores and 7 GB RAM consistently for the duration of the job.
- The baseline generated by Pylint is treated as a "rule-based reference" rather than an absolute ground truth, acknowledging that semantic smells may exist outside its rule set.