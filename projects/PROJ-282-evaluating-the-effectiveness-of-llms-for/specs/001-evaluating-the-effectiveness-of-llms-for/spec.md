# Feature Specification: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-19  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code"

## User Scenarios & Testing

### User Story 1 - Zero-Shot Vulnerability Detection Pipeline (Priority: P1)

The system MUST ingest a dataset of code snippets (C, Python, JavaScript), run them through zero-shot LLM inference, and generate a binary correctness flag (1 if prediction matches ground-truth label, 0 otherwise) and a specific category label for each snippet, comparing these results against ground-truth labels.

**Why this priority**: This is the core empirical engine of the research. Without a functioning pipeline that can execute inference and align predictions with ground truth, no statistical analysis of feature-performance relationships is possible. It delivers the primary dataset (predictions vs. labels) required for the study.

**Independent Test**: Can be fully tested by processing a small, fixed subset of known vulnerable and known safe snippets, verifying that the system outputs a JSON record for each with a predicted label, a confidence score (if available), and a match/mismatch flag against the ground truth.

**Acceptance Scenarios**:

1. **Given** a batch of 50 code snippets with known `ground_truth_label` and `ground_truth_category`, **When** the system runs zero-shot inference using a selected LLM, **Then** the system outputs a structured result file containing the predicted label, the actual `ground_truth_label`, and a binary `is_correct` flag for every snippet.
2. **Given** a code snippet containing a known SQL injection vulnerability, **When** the LLM processes it, **Then** the output must include either "SQLi" (or a mapped equivalent) or "none", and the system must correctly set the `is_correct` flag based on the `ground_truth_label`.
3. **Given** the total dataset size exceeds the runner's memory limits, **When** the system processes the data, **Then** the system must automatically chunk the data into batches of ≤50 samples and aggregate results without data loss or memory overflow.

---

### User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

The system MUST parse every code snippet to extract structural metrics (AST depth, cyclomatic complexity), semantic metrics (taint-source API frequency, sanitization presence), and embedding-based similarity to known vulnerable patterns (using a small pre-trained code encoder) to serve as predictors for the regression analysis.

**Why this priority**: The research question specifically asks which features are predictive. Without these extracted variables, the second half of the study (correlating features with accuracy) cannot proceed. This is a distinct data transformation step from the inference step.

**Independent Test**: Can be fully tested by running the parser on a single file with known complexity (e.g., a deeply nested function) and verifying the output JSON contains non-null, numeric values for AST depth, node count, cyclomatic complexity, and embedding similarity score.

**Acceptance Scenarios**:

1. **Given** a C or Python code snippet, **When** the feature extractor processes it, **Then** the output must include numeric values for cyclomatic complexity, AST depth, and a list of identified taint-source APIs, plus a vector for embedding similarity.
2. **Given** a code snippet that contains no known taint-source APIs, **When** the extractor runs, **Then** the taint-source frequency metric must be recorded as 0, not null or omitted.
3. **Given** a malformed code snippet that causes a parsing error, **When** the extractor runs, **Then** the system must log the error, record the feature vector as null/invalid, and continue processing the remaining batch without crashing.

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

The system MUST compute precision, recall, F1-scores, and ROC-AUC per vulnerability category; perform correlation analysis between extracted features and per-sample binary correctness; fit a multiple linear regression model predicting per-sample correctness from features; and perform McNemar's test comparing LLM predictions against the static analyzer baseline.

**Why this priority**: This transforms the raw data into the scientific findings. It addresses the "Expected Results" of the idea by quantifying the relationship between code features and LLM success and comparing against baselines.

**Independent Test**: Can be fully tested by providing a synthetic CSV of features and binary correctness labels, then verifying the script outputs a correlation matrix with p-values, a regression summary with an adjusted R² value, and a McNemar's test statistic.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 samples with extracted features and binary `is_correct` labels, **When** the analysis script runs, **Then** it must output a Pearson correlation coefficient (r) and p-value for every feature against the `is_correct` outcome.
2. **Given** the full feature set and `is_correct` outcomes, **When** the regression model is fitted, **Then** the system must report the adjusted R² and the significance (p < 0.05) of at least one predictor variable.
3. **Given** multiple hypothesis tests are performed (e.g., correlations for a representative set of features per category), **When** the analysis completes, **Then** the system must apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to the family of tests for each category and report adjusted p-values.
4. **Given** LLM predictions and static analyzer predictions on the same set of samples, **When** the analysis runs, **Then** the system must compute and report McNemar's test statistic and p-value to determine if the difference in performance is significant.

---

### User Story 4 - Static Analyzer Baseline Comparison (Priority: P2)

The system MUST execute standard static analysis tools (Bandit for Python, cppcheck for C) on the same dataset of code snippets, recording their vulnerability predictions and metrics (precision, recall, F1) to serve as a baseline for comparison against the LLM results.

**Why this priority**: Constitution Principle VII requires a baseline comparison. Without a static analyzer baseline, the claim of "effectiveness" relative to existing tools cannot be established.

**Independent Test**: Can be fully tested by running Bandit on a known vulnerable Python script and verifying the tool correctly flags the vulnerability and outputs a structured result file.

**Acceptance Scenarios**:

1. **Given** a Python code snippet with a known vulnerability, **When** the system runs Bandit, **Then** the output must include a vulnerability category and a confidence score.
2. **Given** a C code snippet with a known buffer overflow, **When** the system runs cppcheck, **Then** the output must include a vulnerability category and a confidence score.
3. **Given** the full dataset, **When** the system runs the static analyzers, **Then** it must produce a result file with the same schema as the LLM predictions (snippet_id, predicted_label, is_correct) to enable direct comparison.

---

### Edge Cases

- What happens when the LLM returns a response that does not match any standard vulnerability category (e.g., "maybe", "unclear")? The system must map these to a "uncertain" category or treat them as negative predictions depending on a strict threshold.
- How does the system handle code snippets that are too large for the LLM's context window? The system must truncate the input to the most recent N tokens or the first N tokens, recording the truncation event.
- How does the system handle the case where a dataset snippet lacks a ground-truth label (e.g., ambiguous labeling in the source)? The system must exclude these samples from the accuracy calculation but include them in feature extraction logs.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and parse the VulDeePecker and Juliet datasets, extracting code snippets and their `ground_truth_label` and `ground_truth_category`, ensuring all available labeled samples (up to a maximum of 5,000) are processed (See US-1).
- **FR-002**: System MUST execute zero-shot LLM inference on code snippets in batches using CPU-only execution (no GPU acceleration), ensuring the total memory footprint remains within standard system RAM limits. (See US-1).
- **FR-003**: System MUST compute structural metrics (AST depth, node count, cyclomatic complexity) for every code snippet using `tree-sitter` or an equivalent CPU-tractable parser (See US-2).
- **FR-004**: System MUST compute semantic metrics (frequency of known taint-source APIs, presence of sanitization functions) AND embedding-based similarity to known vulnerable patterns (using a pre-trained code encoder) for every code snippet (See US-2).
- **FR-005**: System MUST calculate precision, recall, F1-scores, and ROC-AUC for each vulnerability category and model. For correlation analysis, the system MUST test the correlation between each feature and the per-sample binary `is_correct` outcome for each category, applying a multiple-comparison correction (e.g., Bonferroni) to the family of tests for each category to control family-wise error (See US-3).
- **FR-006**: System MUST fit a multiple linear regression model predicting per-sample binary `is_correct` (1 or 0) from the full set of structural, semantic, and embedding features, reporting the adjusted R² and coefficient significance (See US-3).
- **FR-007**: System MUST log the inference time per sample and total runtime, ensuring the entire pipeline completes within 6 hours on a 2-core CPU environment (Constitution Principle VI, FR-030), with a per-sample inference time budget of ≤ 43 seconds to guarantee feasibility for the [deferred] sample cap (See US-1).
- **FR-008**: System MUST execute static analysis tools (Bandit for Python, cppcheck for C) on the full dataset, recording predictions and `is_correct` flags against ground truth (See US-4).
- **FR-009**: System MUST record precision, recall, F1, and ROC-AUC metrics for the static analyzer baseline to enable comparison (See US-4).
- **FR-010**: System MUST perform McNemar's test comparing LLM predictions against static analyzer predictions on the same samples to determine statistical significance of performance differences (See US-3).
- **FR-011**: System MUST perform a sensitivity analysis on a human-verified subset (n=100) to validate the impact of potential ground-truth label noise on the calculated metrics (See Assumptions).

### Key Entities

- **CodeSnippet**: Represents a single unit of source code with attributes: `id`, `language` (C/Python/JS), `source_code`, `ground_truth_label`, `ground_truth_category`.
- **FeatureVector**: Represents the extracted properties of a snippet: `ast_depth`, `cyclomatic_complexity`, `node_count`, `taint_api_count`, `sanitization_present`, `embedding_similarity_score`.
- **PredictionResult**: Represents the LLM or Analyzer's output: `snippet_id`, `predicted_label`, `predicted_category`, `is_correct` (boolean), `inference_time_ms`.
- **AnalysisMetric**: Represents a statistical result: `metric_name` (e.g., "Pearson_r"), `feature_name`, `value`, `p_value`, `adjusted_p_value`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between specific structural features (e.g., AST depth) and LLM detection accuracy is measured against the hypothesis that deeper/nested code correlates with lower accuracy, specifically testing the correlation between the feature and the per-sample binary `is_correct` outcome (See US-3).
- **SC-002**: The adjusted R² of the multiple linear regression model (predicting per-sample correctness) is measured to determine if it is statistically significantly greater than zero (p < 0.05) OR if the model explains a meaningful portion of variance (adjusted R² > 0.10) (See US-3).
- **SC-003**: The precision, recall, F1, and ROC-AUC of the zero-shot LLM are measured against the ground-truth labels from the VulDeePecker and Juliet datasets to establish a baseline for zero-shot efficacy (See US-1).
- **SC-004**: The family-wise error rate is controlled such that the adjusted p-values for all reported correlations are < 0.05, ensuring statistical validity of the feature correlations (See US-3).
- **SC-005**: The total inference time and memory usage are measured against the GitHub Actions runner constraints (≤6 hours, ≤7 GB RAM) to verify compute feasibility (See US-1).
- **SC-006**: The performance of the LLM is compared against the static analyzer baseline using McNemar's test, with a p-value < 0.05 required to claim a statistically significant difference (See US-3).

## Assumptions

- The VulDeePecker dataset and Juliet test suite are publicly available and can be downloaded via `wget` or `git clone` within the CI environment without authentication.
- The selected open-source LLMs (CodeLlamaB, StarCoder-Base, distilled Llama-2) can be loaded and run in 4-bit or default precision on a CPU-only environment without exceeding a reasonable amount of RAM, assuming the model weights are quantized or the implementation uses `bitsandbytes` in a CPU-compatible mode (if available) or a smaller distilled variant.
- The `tree-sitter` parser supports the C, Python, and JavaScript languages required by the datasets and can run within a multi-core CPU limit without significant overhead.
- The "ground truth" labels provided by the datasets are treated as the primary reference for the purpose of this study, acknowledging that community-curated datasets may contain labeling noise. A sensitivity analysis (FR-011) is conducted to assess the impact of this noise.
- The "zero-shot" prompt format ("Identify any security vulnerability...") is sufficient to elicit a structured response that can be parsed into a category label without few-shot examples.
- The dataset size is small enough to fit entirely in memory after feature extraction., or can be processed in chunks without losing statistical power for the regression analysis.
- The 6-hour runtime constraint (FR-007) is achievable given the [deferred] sample cap and the per-sample time budget of ≤ 43 seconds.