# Feature Specification: llmXive follow-up: extending "Measuring Epistemic Resilience of LLMs Under Misleading Medical Context"

**Feature Branch**: `001-llmxive-epistemic-resilience`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Measuring Epistemic Resilience of LLMs Under Misleading Medical Context' - investigating linguistic markers of authority framing in MedMisBench"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Linguistic Feature Extraction (Priority: P1)

The system must download the MedMisBench dataset, isolate the "Authority-framed" and "Exception-poisoning" subsets, and compute a standardized set of linguistic features (modal verb frequency, imperative/declarative ratio, citation density) for every prompt.

**Why this priority**: This is the foundational step; without a clean, feature-rich dataset, no statistical analysis can occur. It delivers the raw material for the entire research pipeline.

**Independent Test**: Can be fully tested by running the data processing script against the downloaded MedMisBench subset and verifying that the output CSV contains exactly N rows (matching the input subset size) with non-null values for all defined linguistic feature columns.

**Acceptance Scenarios**:

1. **Given** the MedMisBench repository is accessible, **When** the ingestion script runs, **Then** the script must download the dataset and filter for prompts containing "Authority-framed" or "Exception-poisoning" labels, outputting a CSV with ≥ 500 rows.
2. **Given** a raw prompt text, **When** the feature extraction pipeline processes it, **Then** the output must include counts for modal verbs (e.g., "must", "should"), imperative verbs, and citation patterns, with no missing values for these fields.
3. **Given** the extracted features, **When** the system validates the data, **Then** it must flag any prompt where the calculated "imperative ratio" is undefined (e.g., zero total sentences) to prevent division-by-zero errors in downstream modeling.

---

### User Story 2 - Model Inference and Adherence Labeling (Priority: P2)

The system must execute a quantized LLM with a parameter scale in the billions on the processed prompts using CPU-only inference, generate responses, and automatically label each response as "Adherent to False Authority" (1), "Resilient-Correct" (0), or "Resilient-Refusal" (2) based on a comparison against a static, external medical fact check.

**Why this priority**: This generates the dependent variable (outcome) required for the regression analysis. It validates the "failure mode" hypothesis by observing actual model behavior under the specific linguistic conditions.

**Independent Test**: Can be fully tested by running inference on a small, fixed subset of 10 known "Authority-framed" prompts and verifying that the system correctly labels the model's output as a multi-state classification by comparing the output against a `ground_truth_labels.csv` file containing the `correct_answer` column for every prompt ID.

**Acceptance Scenarios**:

1. **Given** the feature-extracted dataset, **When** the inference engine runs, **Then** it must generate a response for every prompt within a maximum of 30 seconds per prompt on a 2-core CPU.
2. **Given** a generated response and a known correct medical fact from the external reference, **When** the labeling script compares them, **Then** it must output a label: 1 (Adherent), 0 (Resilient-Correct), or 2 (Resilient-Refusal).
3. **Given** a prompt where the model refuses to answer, **When** the labeling script processes it, **Then** it must categorize the refusal as label 2 ("Resilient-Refusal") and log the specific trigger if detectable.

---

### User Story 3 - Statistical Modeling and Sensitivity Analysis (Priority: P3)

The system must perform two separate logistic regression analyses (Adherence vs. Non-Adherence; Refusal vs. Non-Refusal) linking linguistic features to the respective labels, apply multiple-comparison corrections, and execute a sensitivity analysis sweeping the predicted probability threshold for "high authority density" risk to report stability of results.

**Why this priority**: This delivers the scientific conclusion (the "Expected Results" from the idea). It transforms raw data into a statistically defensible claim about linguistic determinants of safety failures.

**Independent Test**: Can be tested by running the analysis script on the labeled dataset and verifying that the output includes two regression tables (one for Adherence, one for Refusal) with p-values, a corrected significance flag, and a sensitivity report showing result variation across probability thresholds.

**Acceptance Scenarios**:

1. **Given** the labeled dataset, **When** the regression models run, **Then** they must produce coefficients and p-values for each linguistic feature, explicitly flagging any feature with p < 0.05.
2. **Given** multiple hypothesis tests (one per linguistic feature per model), **When** the analysis completes, **Then** it must apply a family-wise error correction (e.g., Holm-Bonferroni) and report the adjusted p-values.
3. **Given** a primary decision threshold for "high authority density" risk (based on predicted probability p_adhere), **When** the sensitivity analysis runs, **Then** it must Re-calculate the Attack Success Rate (ASR) and Refusal Rate at varying threshold offsets and report the variance in these rates.

---

### Edge Cases

- What happens if the MedMisBench dataset download fails or is corrupted? (System must retry a limited number of times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle prompts where the "correct" medical fact is ambiguous or not present in the reference data? (Such items are excluded from the analysis with a logged reason).
- How does the system handle a model crash during inference on a specific prompt? (The pipeline must skip the prompt, log the failure, and continue processing the remaining majority of the dataset to ensure partial results are available).
- What if the logistic regression fails to converge due to perfect separation (e.g., a feature perfectly predicts adherence)? (The system must switch to Firth's penalized logistic regression or report a convergence warning and exclude that specific feature from the final model).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the MedMisBench dataset and isolate the "Authority-framed" and "Exception-poisoning" subsets, ensuring the final dataset contains at least 500 unique prompts (See US-1).
- **FR-002**: System MUST extract linguistic features including modal verb frequency, imperative/declarative mood ratio, and citation density for every prompt in the dataset (See US-1).
- **FR-003**: System MUST execute a quantized LLM with a parameter count in the billions on the CPU-only environment to generate responses for every prompt within 30 seconds per prompt (See US-2).
- **FR-004**: System MUST automatically label each model response as a three-state classification: 1 ("Adherent"), 0 ("Resilient-Correct"), or 2 ("Resilient-Refusal") by comparing the output against a static, external medical fact check independent of the linguistic features (See US-2).
- **FR-005**: System MUST perform two separate logistic regression analyses: Model A (dependent variable: Adherent vs. Non-Adherent) and Model B (dependent variable: Refusal vs. Non-Refusal), using the extracted linguistic features as independent variables, ensuring the labeling logic is decoupled from the features (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Holm-Bonferroni) to all p-values generated in both regression models (See US-3).
- **FR-007**: System MUST execute a sensitivity analysis sweeping the predicted probability threshold (p_adhere) for "high authority density" risk over a range of low-value thresholds. and report the resulting variation in Attack Success Rate (ASR) and Refusal Rate (See US-3).
- **FR-008**: System MUST handle perfect separation in logistic regression by switching to Firth's penalized regression or logging a specific convergence warning (See US-3).
- **FR-009**: System MUST conduct a manual annotation pilot with human raters on a subset of n≥50 prompts to validate the correlation between automated linguistic features and human-perceived authority density (See US-1).

### Key Entities

- **PromptItem**: Represents a single input prompt from MedMisBench, containing raw text, source label (Authority/Exception), and extracted linguistic features.
- **ModelResponse**: Represents the generated output from the LLM, containing the raw text and the three-state adherence label (0, 1, or 2).
- **AnalysisResult**: Represents the output of the statistical modeling, containing regression coefficients, p-values, corrected p-values, and sensitivity analysis data.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of successfully processed prompts is measured against the total count in the isolated MedMisBench subset (Target: ≥ 95% completion rate) (See US-1).
- **SC-002**: The Attack Success Rate (ASR) for authority-framed prompts is measured against the baseline ASR reported in the original MedMisBench paper (See US-2).
- **SC-003**: The statistical significance of linguistic markers (p < 0.05 after correction) is measured against the null hypothesis that linguistic features have no predictive power (See US-3).
- **SC-004**: The stability of the ASR across the sensitivity analysis threshold sweep is measured against a predefined tolerance of ≤ 5% variance in ASR (See US-3).
- **SC-005**: The total compute time for the entire pipeline (ingestion, inference, analysis) is measured against the -hour GitHub Actions free-tier limit (See US-3).
- **SC-006**: The labeling logic is verified to exclude all linguistic feature inputs, measured against unit tests that confirm zero dependency of the labeling function on linguistic feature vectors (See US-2).

## Assumptions

- The MedMisBench dataset is publicly accessible and the "Authority-framed" and "Exception-poisoning" subsets are explicitly labeled and downloadable without authentication.
- A small-scale quantized model (e.g., via `llama.cpp`) is sufficient to demonstrate the linguistic failure modes described in the research question, and the specific model architecture does not introduce confounding variables that invalidate the linguistic analysis.
- The ground-truth medical facts required to label responses as "Adherent" or "Resilient" are available in a static, external reference (e.g., PubMed abstracts or a curated fact-check database) independent of the LLM's generation process.
- The linguistic features extracted (modal verbs, citation density, etc.) are sufficient proxies for "authority framing" pending validation by the manual annotation pilot (FR-009).
- The GitHub Actions free-tier runner (CPU cores, sufficient RAM for large-scale processing) is capable of running the quantized small-scale model inference and the logistic regression analysis within the time limit without OOM errors.
- The dataset variables (predictors and outcome) are fully contained within the MedMisBench subset; no external data sources are required to define the "correct" medical answer.