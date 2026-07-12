# Feature Specification: LLMXive Follow-up: Extending "A Survey of Large Audio Language Models: Generalization, Trustworthine"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'A Survey of Large Audio Language Models: Generalization, Trustworthine' - Do statistical anomalies in the latent embedding space of pre-trained audio encoders correlate with cross-modal jailbreak attempts, enabling lightweight, rule-based detection without requiring model retraining or GPU resources?"

## User Scenarios & Testing

### User Story 1 - CPU-Only Latent Embedding Extraction (Priority: P1)

A researcher needs to extract fixed-dimensional latent embeddings from a dataset of [N_samples] audio-text pairs using a frozen, lightweight audio encoder (e.g., distilled Whisper Base) running entirely on a CPU-only environment to prepare data for safety analysis without requiring GPU hardware.

**Why this priority**: This is the foundational data acquisition step. Without embeddings, no subsequent analysis or classification can occur. It directly addresses the core constraint of "no GPU resources" and enables the entire study.

**Independent Test**: The system can be tested by running the extraction pipeline on a subset of 100 benign audio files on a standard 2-core CPU runner and verifying that fixed-size vector outputs are generated without CUDA errors or OOM crashes within 15 minutes.

**Acceptance Scenarios**:

1. **Given** a directory of 100 benign audio files, **When** the extraction script runs on a CPU-only runner, **Then** it produces a JSON file containing 100 fixed-dimensional vectors without triggering any GPU/CUDA errors.
2. **Given** a standard 2-core CPU environment with 7 GB RAM, **When** processing a batch of 32 audio samples sequentially, **Then** the total memory usage per batch never exceeds 6 GB and the process completes within 3 hours.

---

### User Story 2 - Lightweight Binary Classifier Training (Priority: P2)

A researcher needs to train a simple, interpretable binary classifier (Logistic Regression) on the extracted embeddings to distinguish between jailbreak and benign samples, using an 80/20 train/test split, to evaluate if latent-space anomalies are detectable.

**Why this priority**: This implements the core hypothesis testing mechanism. It transforms raw embeddings into a testable model for detecting adversarial inputs, fulfilling the "lightweight detection" goal.

**Independent Test**: The system can be tested by training the classifier on the [N_samples]-sample subset and verifying that the model converges (loss stabilizes) and outputs probability scores for the held-out test set within 5 minutes on CPU.

**Acceptance Scenarios**:

1. **Given** the extracted embeddings with [N_samples] training labels, **When** the Logistic Regression model is trained, **Then** the training process completes without GPU acceleration, outputs a model artifact file with non-zero weights, and achieves a training loss < 1.0.
2. **Given** a held-out test set of [N_samples] samples, **When** the trained model performs inference, **Then** it produces a CSV file with predicted probabilities and binary flags for every sample.

---

### User Story 3 - Performance Evaluation and Resource Profiling (Priority: P3)

A researcher needs to evaluate the classifier's performance (precision, recall, F1-score) against a stratified random baseline classifier and verify that the total analysis pipeline (extraction + training + inference) fits within the 6-hour, 7 GB RAM, 2-core CPU constraint to confirm feasibility for edge deployment.

**Why this priority**: This validates the research success criteria and confirms the "compute feasibility" constraint, ensuring the method is practically deployable as a "defense-in-depth" layer on edge devices.

**Independent Test**: The system can be tested by running the full evaluation script and verifying that the output report contains calculated metrics and resource usage logs, confirming the total runtime is [N_samples] dependent but within the 6-hour limit.

**Acceptance Scenarios**:

1. **Given** the model predictions and ground truth labels, **When** the evaluation script runs, **Then** it generates a report containing Precision, Recall, and F1-score values, explicitly comparing them to a stratified random baseline classifier (predicting labels proportional to training set class distribution).
2. **Given** the full pipeline execution on a 2-core CPU runner, **When** the job completes, **Then** the resource log confirms total RAM usage < 7 GB and total wall-clock time < 6 hours.

### Edge Cases

- What happens if the audio encoder fails to process a corrupted audio file? (System must skip the file, log the error, and continue with the remaining dataset to ensure robustness).
- How does the system handle a dataset where the number of jailbreak samples is significantly lower than expected? (System must still train the classifier but flag a potential class imbalance issue in the results report).
- How does the system behave if the latent embedding dimension changes between encoder versions? (System must validate input dimensionality against the expected shape before training and fail gracefully if mismatched).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract latent embeddings from audio inputs using a frozen, lightweight encoder (e.g., distilled Whisper Base) running in CPU-only mode without invoking CUDA or GPU libraries. (See US-1)
- **FR-002**: System MUST train a binary Logistic Regression classifier on the extracted embeddings using an 80/20 train/test split to distinguish between jailbreak and benign inputs. (See US-2)
- **FR-003**: System MUST evaluate the classifier's performance by calculating Precision, Recall, and F1-score, and explicitly compare these metrics against a stratified random baseline classifier. (See US-3)
- **FR-004**: System MUST profile and log the total RAM usage and wall-clock time of the entire pipeline to ensure it remains within 7 GB RAM and 6 hours on a 2-core CPU runner. (See US-3)
- **FR-005**: System MUST handle corrupted or unprocessable audio files by skipping them, logging the specific error, and continuing processing of the remaining dataset without crashing. (See US-1)
- **FR-006**: System MUST calculate and report the Mahalanobis distance of each sample from the benign class centroid to serve as the primary metric for the raw anomaly correlation hypothesis. (See Research Question)
- **FR-007**: System MUST verify that the source benchmark's labeling methodology did not utilize the same or a correlated encoder's latent space statistics to define the 'jailbreak' class, ensuring ground truth independence. (See US-2)

### Key Entities

- **AudioEmbedding**: A fixed-dimensional vector representation of an audio input, derived from a frozen encoder.
- **SafetyLabel**: A binary classification (jailbreak vs. benign) derived from external benchmark metadata, independent of embedding statistics.
- **ClassifierModel**: A trained Logistic Regression instance mapping embeddings to safety labels.
- **ResourceLog**: A record of memory and time consumption for the analysis pipeline.
- **AnomalyScore**: A scalar value representing the Mahalanobis distance of a sample from the benign centroid.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The recall rate of the lightweight classifier is measured against the ground truth labels of the held-out test set to verify detection capability. (See US-2, US-3)
- **SC-002**: The total inference and training time is measured against the 6-hour maximum constraint to confirm CPU-only feasibility. (See US-3)
- **SC-003**: The peak RAM usage during the full pipeline execution is measured against the 7 GB limit to ensure edge-device compatibility. (See US-3)
- **SC-004**: The performance improvement (F1-score delta) of the latent-space classifier is measured against a stratified random baseline classifier to quantify the value of the anomaly detection approach. (See US-3)
- **SC-005**: The Pearson correlation coefficient (r) between the Mahalanobis distance from the benign centroid and the presence of jailbreak labels is measured against the threshold p < 0.05 or effect size r > 0.3 to validate the core hypothesis. (See Research Question, FR-006)

## Assumptions

- **Assumption about data availability**: Publicly available labeled datasets (e.g., LALM benchmarks) contain a sufficient number of labeled cross-modal jailbreak samples and benign samples accessible via direct download. Specific dataset names and counts are deferred to the implementation phase.
- **Assumption about model compatibility**: The chosen lightweight audio encoder (e.g., distilled Whisper Base) can be loaded and executed in full precision on a CPU without requiring specific hardware acceleration or quantization libraries that demand CUDA.
- **Assumption about dataset-variable fit**: The selected benchmark datasets contain the necessary semantic labels (jailbreak vs. benign) that are independent of the latent embedding statistics, ensuring no circularity in the validation.
- **Assumption about methodological framing**: Since the study uses observational data (no random assignment of adversarial attacks), findings will be framed as associational correlations between embedding anomalies and jailbreak labels, not causal effects.
- **Assumption about computational limits**: The total dataset size ([N_samples] samples) and the complexity of the Logistic Regression model will fit within the 7 GB RAM and 6-hour time budget of a standard GitHub Actions free-tier runner.
- **Assumption about threshold justification**: Any decision cutoffs for anomaly detection (if derived post-hoc) will be justified by community standards or sensitivity analysis, though the primary method (Logistic Regression) uses probabilistic thresholds determined by the training data.