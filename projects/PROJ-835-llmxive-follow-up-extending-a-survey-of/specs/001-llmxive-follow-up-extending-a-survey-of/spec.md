# Feature Specification: LlmXive Follow-up: Latent-Space Jailbreak Detection

**Feature Branch**: `001-latent-space-jailbreak-detection`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'A Survey of Large Audio Language Models: Generalization, Trustworthine'"

## User Scenarios & Testing

### User Story 1 - CPU-Only Embedding Extraction Pipeline (Priority: P1)

As a researcher, I need to extract fixed-dimensional latent embeddings from a dataset of audio samples using a frozen, lightweight audio encoder (e.g., distilled Whisper Base) on a CPU-only environment, so that I can generate the feature vectors required for downstream analysis without exceeding the available RAM or compute time limits of the free-tier CI runner.

**Why this priority**: This is the foundational data engineering step. Without successfully extracting embeddings within the resource constraints, no classification or statistical analysis can occur. It addresses the core "Compute Feasibility" constraint.

**Independent Test**: The pipeline can be fully tested by running the extraction script on a representative subset of samples on a local CPU machine with ≤ 7 GB RAM, verifying that the output is a valid matrix of floats with the expected dimensions and that the process completes within a proportional time limit.

**Acceptance Scenarios**:

1. **Given** a CSV manifest of [deferred] audio file paths and labels, **When** the extraction script runs on a CPU-only runner with 2 cores, **Then** it outputs a single `.npy` or `.parquet` file containing [deferred] embedding vectors, the process completes without OOM (Out Of Memory) errors, and the throughput is ≥ 10 samples/hour.
2. **Given** the extraction process is running, **When** the memory usage is monitored, **Then** the peak RAM usage remains ≤ 6.5 GB ([deferred] of the 7 GB limit), ensuring a safety margin for the environment.
3. **Given** a sample of 100 adversarial audio files, **When** processed, **Then** the resulting embeddings show no NaN or Inf values, indicating numerical stability in the frozen encoder.

---

### User Story 2 - Lightweight Binary Classifier Training & Evaluation (Priority: P2)

As a researcher, I need to train a simple binary classifier (Logistic Regression) on the extracted embeddings to distinguish between "jailbreak" and "benign" labels, and evaluate its performance (Precision, Recall, FPR) on a held-out test set, so that I can determine if latent-space anomalies are a viable proxy for detecting cross-modal jailbreaks.

**Why this priority**: This is the core hypothesis test. It directly answers the research question: "Do specific statistical anomalies... correlate with cross-modal jailbreak attempts?" It is the primary scientific output.

**Independent Test**: The model training and evaluation can be tested independently by feeding a pre-computed embedding matrix and label vector into the training script, verifying that the model converges and produces a confusion matrix with calculated metrics.

**Acceptance Scenarios**:

1. **Given** the embedding matrix and ground-truth labels are loaded, **When** the Logistic Regression model is trained with a 80/20 train-test split, **Then** the model outputs a confusion matrix and the Recall for the "jailbreak" class is calculated.
2. **Given** the trained model, **When** it predicts on the held-out test set, **Then** the False Positive Rate (FPR) is calculated and reported alongside Recall.
3. **Given** the results, **When** compared to a majority-class baseline (always predicting "benign"), **Then** the lightweight classifier demonstrates a statistically significant improvement (via Binomial Test) in detection capability with p < 0.05.

---

### User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

As a researcher, I need to perform a sensitivity analysis on the classification decision threshold and apply multiple-comparison corrections if multiple hypotheses are tested, so that the findings are methodologically robust and not artifacts of arbitrary cutoff choices or statistical noise.

**Why this priority**: This ensures the scientific validity of the results, addressing the "Methodological Soundness" requirements regarding threshold justification and multiplicity. It prevents the rejection of the spec by the methodology panel.

**Independent Test**: The analysis script can be tested by running it against a synthetic dataset with known properties, verifying that the sensitivity sweep produces a trend line and that the p-values are correctly adjusted.

**Acceptance Scenarios**:

1. **Given** the trained classifier scores, **When** the decision threshold is swept across values {0.3, 0.4, 0.5, 0.6, 0.7}, **Then** a report is generated showing how Recall and FPR vary across these thresholds.
2. **Given** multiple performance metrics are calculated, **When** the statistical significance is evaluated, **Then** the Bonferroni correction is applied if ≥ 2 distinct performance metrics are reported, and the adjusted p-value is explicitly stated.
3. **Given** the final results, **When** the threshold of 0.5 is used, **Then** the justification for this default is documented, and the sensitivity analysis confirms that minor deviations do not drastically alter the headline "high recall" conclusion.

---

### Edge Cases

- What happens when the dataset contains audio files with missing metadata or corrupted headers? (System must skip and log, not crash).
- How does the system handle the scenario where the frozen encoder produces identical embeddings for distinct adversarial inputs (embedding collapse)?
- What happens if the test set contains zero "jailbreak" samples due to random split variance? (System must enforce a stratified split to ensure class balance).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract latent embeddings from the [deferred] audio samples using a frozen, CPU-compatible audio encoder (e.g., Whisper Base) without fine-tuning. (See US-1)
- **FR-002**: System MUST train a binary classifier (Logistic Regression) on the extracted embeddings to distinguish between "jailbreak" and "benign" classes. (See US-2)
- **FR-003**: System MUST evaluate the classifier using a stratified 80/20 train-test split to ensure class balance in the test set. (See US-2)
- **FR-004**: System MUST compute Precision, Recall, and False Positive Rate (FPR) on the held-out test set. (See US-2)
- **FR-005**: System MUST perform a sensitivity analysis by sweeping the classification threshold over the set {0.3, 0.4, 0.5, 0.6, 0.7} and report the variation in Recall and FPR. (See US-3)
- **FR-006**: System MUST apply a Binomial Test to determine if the detection accuracy of the lightweight classifier is statistically significantly higher than the expected accuracy of a majority-class baseline (p < 0.05). (See US-2)
- **FR-007**: System MUST ensure all inference and training steps complete within 6 hours on a 2-core CPU, 7 GB RAM environment. (See US-1)

### Key Entities

- **Audio Sample**: A unit of data consisting of an audio file path and a ground-truth label ("jailbreak" or "benign").
- **Embedding Vector**: A fixed-dimensional numerical representation of an audio sample generated by the frozen encoder.
- **Classifier Model**: A lightweight binary classifier (Logistic Regression) trained to map embedding vectors to labels.
- **Performance Metrics**: A set of calculated values (Precision, Recall, FPR, p-value) summarizing the model's effectiveness.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Recall for the "jailbreak" class is measured against the baseline of a majority-class predictor (always predicting "benign") to determine if the method provides a viable detection signal. (See US-2)
- **SC-002**: The variation in Recall and FPR across the threshold sweep {0.3, 0.4, 0.5, 0.6, 0.7} is measured to assess the robustness of the decision boundary. (See US-3)
- **SC-003**: Statistical significance (p-value from Binomial Test) is measured against the standard alpha level of 0.05 to validate the improvement over the majority-class baseline. (See US-3)
- **SC-004**: Peak memory usage is measured against the 7 GB limit to confirm CPU-only feasibility. (See US-1)
- **SC-005**: Total execution time is measured against the 6-hour limit to confirm the method fits the free-tier CI constraints. (See US-1)

## Assumptions

- The public benchmark repositories (AudioBench, ALFRED) contain the required known cross-modal jailbreak samples and benign samples with reliable ground-truth labels.
- The chosen frozen audio encoder (e.g., distilled Whisper Base) is available via a CPU-optimized library (e.g., `transformers` with `torch` CPU backend) and does not require CUDA.
- The "jailbreak" vs. "benign" labels provided by the benchmark repositories are independent of the *current experiment's* model training (avoiding circular validation), but the latent embeddings generated by the frozen encoder *must* contain statistical signal correlated with these labels for the detection hypothesis to be valid.
- The dataset size (a sufficiently large sample) and embedding dimensionality will fit within the 7 GB RAM limit when loaded in batches or as a single matrix.
- The statistical anomalies in the latent space, if they exist, are detectable by linear models (Logistic Regression) without requiring complex non-linear feature engineering.
- The "threshold of 0.5" is a standard community default for binary classification, but the sensitivity analysis (FR-005) is required to justify its stability for this specific task.