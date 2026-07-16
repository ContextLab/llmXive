# Feature Specification: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Feature Branch**: `001-llmxive-drift-detection`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Agent Safety and Security' to detect novel, emergent agent attack vectors via semantic divergence from a fixed safety taxonomy."

## User Scenarios & Testing

### User Story 1 - Zero-Shot Drift Scoring (Priority: P1)

**User Journey**: A safety researcher needs to process a batch of raw, unlabeled agent interaction logs and immediately identify which ones semantically diverge from the known AgentDoG 1.5 safety taxonomy to flag potential novel threats without retraining a model.

**Why this priority**: This is the core value proposition of the project. Without the ability to compute a "Drift Score" for arbitrary logs, the system cannot function as an early warning mechanism. It represents the minimum viable product (MVP) of the research tool.

**Independent Test**: The system can be tested by feeding a static JSON file of a sufficient number of known benign logs and a comparable number of known novel attack logs. (where novelty is defined by human annotation from the US-02 process, not merely by absence from the taxonomy) and verifying that the "Drift Score" distribution is statistically distinguishable between the two groups with p < 0.05 and an effect size (Cohen's d) ≥ 0.5.

**Acceptance Scenarios**:
1. **Given** a JSON file containing 100 agent interaction logs and the static AgentDoG 1.5 taxonomy definitions, **When** the system computes cosine distances to taxonomy centroids, **Then** it outputs a CSV where each row contains the log ID and its calculated Drift Score (minimum distance to any centroid).
2. **Given** a log containing a novel prompt injection pattern not present in the taxonomy, **When** the Drift Score is calculated, **Then** the score is ≥ 2 standard deviations above the Benign Baseline Average.

---

### User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**User Journey**: A safety annotator needs to review a stratified sample of high-drift and low-drift logs to verify if the semantic divergence metric actually correlates with human-identified "novel attacks" rather than just semantic noise or benign complexity.

**Why this priority**: This step validates the scientific hypothesis. While the scoring (US-01) generates data, this story ensures the data is meaningful by establishing ground truth via human annotation, which is required for the statistical validation phase.

**Independent Test**: The system can be tested by generating a CSV with a stratified sample (top [deferred] percentile and bottom [deferred] percentile of Drift Scores) and verifying that the output format matches the requirements for a standard annotation interface (CSV must contain columns: log_id, text, label).

**Acceptance Scenarios**:
1. **Given** the full set of Drift Scores for 500 logs, **When** the system stratifies the data into high-drift (top [deferred] percentile) and low-drift (bottom [deferred] percentile) bins, **Then** it outputs two distinct CSV files ready for human annotation, each containing N logs (where N is the [deferred] stratification count).
2. **Given** a human-annotated CSV file with "novel attack" labels (derived from an independent safety taxonomy and with annotators blinded to Drift Scores), **When** the system correlates these labels with the Drift Score bins, **Then** it outputs a logistic regression model (odds ratio) and a Mann-Whitney U test p-value indicating the statistical significance of the association.

---

### User Story 3 - Baseline Performance Comparison (Priority: P3)

**User Journey**: A safety engineer needs to compare the efficiency and accuracy of the new Drift Score detector against a standard zero-shot LLM classifier to determine if the lightweight approach offers a viable trade-off for real-time monitoring.

**Why this priority**: This provides context for the utility of the method. It is secondary to establishing the validity of the drift metric itself (US-01, US-02) but essential for the "lightweight" claim in the motivation.

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs. where both the Drift Score and a zero-shot LLM inference (using model: 'gpt-4o-mini', temperature: 0.0, prompt: standard safety prompt v1) are available, and verifying the output includes AUC-ROC and inference time metrics against the human-annotated ground truth from US-02.

**Acceptance Scenarios**:
1. **Given** a subset of 50 logs with ground-truth "novel attack" labels, **When** the system compares the Drift Score classifier against a zero-shot LLM classifier, **Then** it outputs a report containing the AUC-ROC for both methods and the average inference time per log.
2. **Given** the comparison results, **When** the Drift Score method shows an AUC-ROC where the absolute difference |AUC_drift - AUC_llm| ≤ 0.10 (calculated as the mean over 5 bootstrap iterations), **Then** the system flags this as a "computationally efficient alternative" in the final summary report.

---

### Edge Cases

- **What happens when** the input log is empty or contains only whitespace (string length == 0 or all characters match the Unicode whitespace regex pattern `\p{Zs}`)? The system MUST assign a Drift Score at the maximum distance and flag it for manual review, as it cannot be semantically mapped to any centroid.
- **How does the system handle** logs that are semantically identical to a taxonomy category but syntactically obfuscated (e.g., leetspeak)? The system MUST rely on the embedding model's ability to normalize syntax; if the embedding fails to map close to the centroid, the log is treated as high-drift. This behavior is a testable hypothesis to be validated in US-02, not a guaranteed design constraint.
- **What happens when** the number of novel logs exceeds the RAM limit of the GitHub Actions runner (7GB)? The system MUST process logs in batches of a size sufficient to ensure memory usage remains within acceptable limits., logging a warning if the total dataset size exceeds a predefined threshold.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate centroid embeddings for every risk category in the AgentDoG 1.5 taxonomy using the `all-MiniLM-L6-v2` model, ensuring the entire embedding matrix fits within 100MB of RAM (See US-01).
- **FR-002**: System MUST compute the cosine distance between every input agent log and all taxonomy centroids, returning the minimum distance as the "Drift Score" for that log (See US-01).
- **FR-003**: System MUST stratify the processed logs into high-drift (top [deferred] percentile) and low-drift (bottom [deferred] percentile) bins and export them as separate CSV files for human annotation (See US-02).
- **FR-004**: System MUST perform a logistic regression analysis (estimating odds ratios) and a Mann-Whitney U test on the Drift Score vs. Human Annotation labels (where labels are blinded and derived from an independent source) to determine statistical significance (p < 0.05) (See US-02).
- **FR-005**: System MUST calculate and report the AUC-ROC of the Drift Score as a binary classifier for novel attacks, comparing it against a baseline zero-shot classifier (See US-03).

### Key Entities

- **TaxonomyCentroid**: A fixed vector representation of a known risk category from the AgentDoG 1.5 taxonomy.
- **AgentLog**: An unstructured text string representing an interaction between an AI agent and a user/environment.
- **DriftScore**: A scalar value (0.0 to 2.0) representing the minimum cosine distance between an AgentLog and the nearest TaxonomyCentroid.
- **AnnotationLabel**: A categorical label assigned by a human annotator (e.g., "novel attack", "known attack", "benign"), derived from an independent safety taxonomy and assigned while blinded to the Drift Score.
- **BenignBaselineAverage**: The arithmetic mean of Drift Scores calculated from a verified set of benign logs, used as a reference point for anomaly detection.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation between Drift Scores and human-verified novel attack labels is measured against a logistic regression odds ratio > 1.5 or a Mann-Whitney U test p-value < 0.05 to confirm statistical significance (See US-02).
- **SC-002**: The predictive power of the Drift Score is measured against the AUC-ROC metric, with a target of ≥ 0.70 to demonstrate viability as a detection proxy (See US-03).
- **SC-003**: The computational overhead of the Drift Score calculation is measured against the available GitHub Actions job limit., ensuring the full analysis of 500 logs completes in ≤ 30 minutes on a 2-core CPU (See US-01, US-02).
- **SC-004**: The inter-annotator agreement (Kappa statistic) for the "novel attack" classification is measured against a threshold of > 0.6 to ensure ground truth reliability (See US-02).
- **SC-005**: The memory footprint of the embedding computation is measured against the 7GB RAM limit of the free-tier runner, ensuring peak usage remains ≤ 4GB (See US-01).

## Assumptions

- The `all-MiniLM-L6-v2` model is available on Hugging Face and can be loaded entirely into CPU memory without requiring GPU acceleration or quantization.
- The AgentDoG 1.5 taxonomy definitions (JSON/Markdown) are publicly accessible and can be parsed to extract category names for embedding generation.
- The "novel" attack patterns in the scraped logs are indeed absent from the original AgentDoG 1.5 training data, ensuring the validity of the "drift" detection hypothesis.
- The GitHub Actions free-tier runner (standard CPU allocation, standard RAM) is sufficient to process 500 logs in batches without exceeding the 6-hour time limit.
- **Testable Hypothesis**: The semantic distance metric (cosine similarity) is a valid proxy for "novelty" in the context of safety taxonomy. This is not assumed to be true a priori but is the primary hypothesis to be validated by the human-annotated ground truth in US-02. The system treats high drift as a signal for review, but the "correctness" of this signal for obfuscated attacks is an empirical outcome of the validation phase.