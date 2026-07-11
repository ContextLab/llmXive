# Feature Specification: llmXive follow-up: extending "MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image"

**Feature Branch**: `001-llmxive-multitab-ext`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image'"

## User Scenarios & Testing

### User Story 1 - Data Pipeline and Baseline Generation (Priority: P1)

The researcher MUST be able to download the top 15 high-impact datasets from the MulTaBench repository, compute static frozen embeddings (CLIP for images, Sentence-BERT for text), and train a LightGBM classifier to establish a "Frozen" baseline performance metric.

**Why this priority**: This is the foundational step. Without a reproducible baseline and the processed dataset, no comparison can be made. It validates data availability and the CPU-tractable nature of the embedding extraction.

**Independent Test**: The system can be tested by running the pipeline on a single dataset (e.g., the first from the filtered list) and verifying that a baseline accuracy/AUC score is generated and logged without GPU usage.

**Acceptance Scenarios**:

1. **Given** the MulTaBench repository URL and a filter for top 15 datasets by task-awareness gap, **When** the pipeline executes, **Then** it successfully downloads the data and outputs a CSV of static embeddings and a baseline performance score.
2. **Given** a dataset with missing modalities (e.g., image-only or text-only entries), **When** the pipeline processes it, **Then** it handles the missing modality by masking the corresponding feature vector without crashing the job.
3. **Given** a standard CPU-only environment (no CUDA), **When** the embedding extraction runs, **Then** it completes within 60 minutes for the first dataset and consumes ≤ 7 GB RAM.

---

### User Story 2 - CPU-Conditioned Projection Training (Priority: P2)

The researcher MUST be able to train a lightweight "Tabular-Conditioned Projection" module (MLP or cross-attention) that takes tabular features as queries to modulate the frozen embeddings, and evaluate it on the held-out test sets.

**Why this priority**: This implements the core hypothesis: that task signal can be recovered via cheap interaction. It is the primary experimental variable against the baseline.

**Independent Test**: The system can be tested by training the projection module on the top 3 datasets and verifying that the training loss converges and a test metric is produced, distinct from the baseline.

**Acceptance Scenarios**:

1. **Given** the static embeddings and tabular features from User Story 1, **When** the projection module is trained for 50 epochs on CPU, **Then** the training log shows a decreasing loss and a final test accuracy is recorded.
2. **Given** a dataset where the tabular features are purely random noise, **When** the projection module is trained, **Then** the performance degradation is minimal (within 5% of the baseline), indicating the model is not overfitting to noise.
3. **Given** the 6-hour GitHub Actions time limit, **When** the training runs on the full set of 15 datasets, **Then** the total wall-clock time is ≤ 5 hours, leaving a 1-hour buffer for analysis.

---

### User Story 3 - Statistical Analysis and Alignment Correlation (Priority: P3)

The researcher MUST be able to compute a "Modality Alignment Score" for each dataset and perform a mixed-effects regression to determine if the performance gain of the conditioned model correlates with this alignment score.

**Why this priority**: This addresses the scientific question: "Does recoverability depend on intrinsic alignment?" It transforms raw performance numbers into a scientific conclusion.

**Independent Test**: The system can be tested by running the regression analysis on the generated metrics and verifying that a p-value and interaction effect coefficient are output.

**Acceptance Scenarios**:

1. **Given** the performance metrics from the Frozen and Conditioned models, **When** the alignment score is computed (via CCA or Mutual Information), **Then** a dataset-level correlation coefficient is generated.
2. **Given** the full results, **When** the mixed-effects regression is executed, **Then** the output includes the interaction term p-value and indicates statistical significance (p < 0.05) or lack thereof.
3. **Given** multiple hypothesis tests across different alignment thresholds, **When** the analysis runs, **Then** a multiple-comparison correction (e.g., Bonferroni or FDR) is applied to the final p-values.

### Edge Cases

- **Dataset Variance**: What happens if a dataset in the top 15 has extremely high class imbalance (>90% majority class)? The system must apply stratified sampling or SMOTE (CPU-tractable) to ensure the baseline is not trivial.
- **Embedding Dimension Mismatch**: How does the system handle datasets where the CLIP and SBERT embedding dimensions differ? The projection layer must dynamically resize or pad inputs to a fixed dimension (e.g., 768) before modulation.
- **Memory Overflow**: How does the system handle a dataset that exceeds the 7 GB RAM limit when loading all embeddings at once? The pipeline must implement batched processing for the projection training step.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the top 15 datasets from the MulTaBench repository based on the largest performance gap between frozen and tuned embeddings (See US-1).
- **FR-002**: System MUST generate static, frozen embeddings for images using CLIP and text using Sentence-BERT without updating any encoder weights (See US-1).
- **FR-003**: System MUST implement a "Tabular-Conditioned Projection" module that accepts tabular features as a query to modulate frozen embeddings via a lightweight MLP or cross-attention mechanism (See US-2).
- **FR-004**: System MUST train the projection module and final classifier end-to-end using only CPU-based optimization for a fixed 50 epochs (See US-2).
- **FR-005**: System MUST compute a "Modality Alignment Score" for each dataset using Canonical Correlation Analysis (CCA) or Mutual Information between frozen embeddings and labels (See US-3).
- **FR-006**: System MUST perform a mixed-effects regression analysis with performance as the dependent variable and conditioning method and alignment score as predictors (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg) to all statistical test results involving >1 hypothesis (See US-3).

### Key Entities

- **Dataset**: A multimodal tabular instance containing image, text, tabular features, and a ground-truth label.
- **Embedding**: A fixed-dimensional vector representation of unstructured data (image/text) generated by frozen encoders.
- **Alignment Score**: A scalar metric quantifying the intrinsic correlation between unstructured modalities and the target label.
- **Projection Model**: The lightweight, trainable neural module that modulates embeddings based on tabular context.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The performance recovery ratio (Conditioned Model Accuracy / Fine-tuned Baseline Accuracy) is measured against the theoretical target of 0.70–0.80 in high-alignment domains (See FR-003, FR-004).
- **SC-002**: The statistical significance of the interaction term (Conditioning Method × Alignment Score) is measured against a threshold of p < 0.05 after multiple-comparison correction (See FR-006, FR-007).
- **SC-003**: The total computational runtime for the full 15-dataset experiment is measured against the 6-hour GitHub Actions free-tier limit (See FR-004).
- **SC-004**: The peak memory usage during embedding extraction and training is measured against the 7 GB RAM constraint of the runner (See FR-002, FR-004).
- **SC-005**: The sensitivity of the performance gain to the alignment score threshold is measured by sweeping the alignment cutoff (e.g., top [deferred], top [deferred], top [deferred]) and reporting the variance in recovery rates (See FR-005, FR-006).

## Assumptions

- **Assumption about data availability**: The MulTaBench repository remains accessible and the top 15 datasets by "task-awareness gap" can be programmatically identified and downloaded without authentication barriers.
- **Assumption about CPU feasibility**: The "Tabular-Conditioned Projection" module, defined as a lightweight MLP or single-layer cross-attention, is computationally tractable on a 2-core CPU for the selected dataset sizes (≤ 100k rows) within the 6-hour window.
- **Assumption about alignment metric**: Canonical Correlation Analysis (CCA) or Mutual Information is a valid and stable proxy for "intrinsic modality alignment" across the diverse domains in MulTaBench, and can be computed without GPU acceleration.
- **Assumption about threshold justification**: The selection of 50 epochs for training is a community-standard default for lightweight convergence in this context; a sensitivity analysis will sweep epochs ∈ {25, 50, 75} to verify stability.
- **Assumption about dataset variables**: The MulTaBench datasets contain all necessary tabular features and ground-truth labels required to compute the alignment score and train the classifier; no external data sources are needed.
