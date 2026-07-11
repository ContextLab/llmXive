# Feature Specification: llmXive Follow-up: Extending MulTaBench

**Feature Branch**: `001-llmxive-mulTabench-extension`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Ima'"

## User Scenarios & Testing

### User Story 1 - CPU-Tractable Baseline Generation (Priority: P1)

**Journey**: As a researcher, I want to generate frozen embeddings for images and text using off-the-shelf models (CLIP ViT-B/32, Sentence-BERT) on a CPU-only environment without modifying the model weights, so that I can establish a consistent, non-adaptive baseline for multimodal data.

**Why this priority**: This is the foundational step. Without frozen, reproducible embeddings, no comparison against the "GPU-Tuned" TAR baseline or the "CPU-Conditioned" approach is possible. It directly addresses the "frozen-encoder" constraint of the research question.

**Independent Test**: Can be fully tested by running the embedding generation script on a sample of the MulTaBench dataset and verifying that (1) the output vectors are generated within the 60-minute CI time limit, (2) no CUDA/GPU errors occur, and (3) gradient tracking is disabled for the encoder weights.

**Acceptance Scenarios**:

1. **Given** a subset of the first 10 datasets (alphabetically) from MulTaBench, **When** the embedding script is executed on a CPU-only runner with `random_seed=42`, **Then** the script must complete within 60 minutes and output a JSON/Parquet file containing the frozen vector representations.
2. **Given** the generated embeddings on the first 10 datasets, **When** a downstream classifier is trained using only these embeddings (no tabular conditioning) with `random_seed=42`, **Then** the resulting performance metrics must be reproducible within the deterministic pipeline (verified by re-running the script and checking bit-wise identical output or identical metric values to 4 decimal places).

---

### User Story 2 - Tabular-Conditioned Projection Implementation (Priority: P2)

**Journey**: As a researcher, I want to implement and train a lightweight projection module (MLP or single-head attention) that takes normalized tabular features as a query to modulate the frozen unstructured embeddings, so that I can inject "task-awareness" without fine-tuning the large backbone.

**Why this priority**: This is the core innovation of the project. It tests the hypothesis that structured features can recover lost signal. It is independent of the baseline generation (US-001) but relies on its output.

**Independent Test**: Can be fully tested by training the projection layer on a single dataset from the subset and verifying that the model converges (loss decreases) and that the tabular metadata (cardinality, missingness) is correctly processed as the conditioning query.

**Acceptance Scenarios**:

1. **Given** the frozen embeddings from US-001 and normalized tabular features, **When** the projection module is trained for 10 epochs on a CPU, **Then** the training loss must converge to a local minimum (defined as the absolute change in loss over 5 consecutive epochs being < 0.001), and the total memory usage must not exceed 7 GB.
2. **Given** the trained projection model, **When** it is evaluated on the held-out test set of a specific dataset, **Then** the performance metric (e.g., AUC) must be recorded and stored for comparison against the TAR baseline.

---

### User Story 3 - Efficacy Correlation & Statistical Analysis (Priority: P3)

**Journey**: As a researcher, I want to run a statistical analysis that correlates the performance recovery ratio (CPU-Conditioned vs. GPU-Tuned) with tabular metadata statistics (cardinality, sparsity), so that I can identify which structural properties of the data enable or hinder the conditioning mechanism.

**Why this priority**: This fulfills the second part of the research question ("what structural properties... determine efficacy"). It depends on the results of US-001 and US-002.

**Independent Test**: Can be fully tested by executing the analysis script on the collected metrics from multiple datasets and verifying that a regression model is fitted and that a correlation coefficient (and p-value) is output for each metadata feature.

**Acceptance Scenarios**:

1. **Given** the performance metrics and metadata statistics for the first 20 available datasets (alphabetically) with complete data, **When** the correlation analysis script is run, **Then** it must output a table listing the Pearson correlation coefficient and p-value for "Recovery Ratio" vs. each of the following features: "Tabular Cardinality", "Missingness Rate", "Sparsity", and "Variance". If fewer than 20 datasets are available, the system must use all available and flag the shortfall in the report.
2. **Given** the computed metrics, **When** a one-sample t-test (or Wilcoxon signed-rank test if normality assumptions fail) is performed between the "CPU-Conditioned" performance and the fixed "GPU-Tuned" baseline, **Then** the script must report the test statistic, p-value, and a boolean flag indicating statistical significance (p < 0.05).

---

### Edge Cases

- What happens when a dataset in MulTaBench has zero variance in a key tabular feature? (The system must handle this by skipping the feature in the conditioning query or imputing a constant, without crashing).
- How does the system handle datasets where the "GPU-Tuned" baseline is not reported in the original MulTaBench paper? (The system must flag these datasets as excluded from the primary correlation analysis and list them in a 'Data Availability Gap' section of the final report).
- What happens if the CPU runner runs out of memory during the embedding generation for a large image? (The system must implement a batch processing strategy with a maximum batch size to ensure memory safety).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate frozen embeddings for images and text using pre-trained CLIP ViT-B/32 and Sentence-BERT models on CPU without enabling gradient tracking. The system MUST re-compute the 'Frozen Baseline' for ALL datasets in the current pipeline using the same `random_seed=42` and preprocessing steps as the 'CPU-Conditioned' generation to ensure consistency in the Recovery Ratio denominator (See US-001).
- **FR-002**: System MUST implement a lightweight projection layer (MLP or single-head attention) that accepts normalized tabular features as a query to re-weight frozen embeddings, ensuring no modification to the backbone weights occurs (See US-002).
- **FR-003**: System MUST compute metadata statistics (cardinality, missingness rate, sparsity, variance) for all structured tabular features prior to model training, to enable the correlation analysis (See US-003).
- **FR-004**: System MUST execute the entire training and evaluation pipeline within a 6-hour time limit and 7 GB RAM constraint on a standard GitHub Actions CPU runner. This limit is decomposed as: ≤ 60 minutes for embedding generation (US-001) and ≤ 5 hours for training and evaluation (US-002/003) (See US-001, US-002).
- **FR-005**: System MUST perform a one-sample t-test (or Wilcoxon signed-rank test if normality is rejected by Shapiro-Wilk test, p < 0.05) to compare the mean difference between 'CPU-Conditioned' performance and the fixed 'GPU-Tuned' baseline against zero. The test must treat the 'GPU-Tuned' baseline as a constant, not a random variable (See US-003).
- **FR-006**: System MUST apply the Benjamini-Hochberg (FDR) procedure to correct for multiple comparisons when testing correlations across the family of tabular metadata features (cardinality, missingness, sparsity, variance) to control the false discovery rate at α ≤ 0.05 (See US-003).

### Key Entities

- **FrozenEmbedding**: Vector representation of unstructured data (image/text) generated by a non-trainable encoder.
- **TabularMetadata**: Statistical summary (cardinality, sparsity, missingness, variance) of the structured features for a given dataset.
- **ProjectionLayer**: The trainable MLP or attention module that fuses tabular features with frozen embeddings.
- **Recovery Ratio**: The metric calculated as (CPU-Conditioned Performance - Frozen Baseline) / (GPU-Tuned Baseline - Frozen Baseline). Note: The 'Frozen Baseline' in the denominator MUST be the value re-computed in the current pipeline (FR-001), not the historical value from the paper.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The "Recovery Ratio" is successfully calculated and reported for all datasets where 'GPU-Tuned' and 'Frozen' baselines exist (See US-002).
- **SC-002**: A correlation table containing Pearson coefficients and p-values for "Recovery Ratio" vs. "Tabular Cardinality", "Missingness", "Sparsity", and "Variance" is successfully generated (See US-003).
- **SC-003**: The statistical significance of the difference between CPU-Conditioned performance and the fixed GPU-Tuned baseline is measured using a one-sample t-test (or Wilcoxon) with p < 0.05 threshold, with FDR correction applied for multiple features (See US-003).
- **SC-004**: The total runtime of the end-to-end pipeline is measured against the 6-hour CI limit to verify compute feasibility (See US-001, US-002).
- **SC-005**: The memory peak usage of the embedding generation and training steps is measured against the 7 GB RAM constraint (See US-002).

## Assumptions

- **Assumption about data availability**: The MulTaBench repository (arXiv:2605.10616 supplementary material) contains the 40 multimodal tabular datasets and the corresponding "GPU-Tuned" baseline performance metrics required for comparison.
- **Assumption about model compatibility**: Standard off-the-shelf models (CLIP ViT-B/32, Sentence-BERT) can be loaded and run in default precision on a CPU-only environment without requiring CUDA-specific quantization libraries (e.g., bitsandbytes).
- **Assumption about dataset variability**: The selected subset of datasets exhibits sufficient variance in tabular metadata (cardinality, sparsity) to allow for a meaningful correlation analysis.
- **Assumption about inference framing**: The study is observational; therefore, any observed correlations between tabular properties and performance recovery are treated as associational, not causal.
- **Assumption about power**: The sample size of a sufficient number of datasets (or the filtered subset) is sufficient to detect a moderate effect size (Cohen's d ≈ 0.5) with [deferred] power, given the paired design; if the subset is smaller, the power limitation will be explicitly acknowledged in the final report.
- **The system will compute the 'Recovery Ratio' only for datasets where the 'GPU-Tuned TAR' baseline is reported in the MulTaBench supplementary material. For any of the datasets missing this metric, the system will flag them as excluded from the primary correlation analysis and list them in a 'Data Availability Gap' section of the final report. Crucially, the 'Frozen Baseline' used in the denominator MUST be re-computed in the current pipeline (FR-001) for all valid datasets to ensure consistency with the 'CPU-Conditioned' generation context.**
- **The 'GPU-Tuned TAR' baseline is available for both classification and regression tasks as per the MulTaBench specification. However, the system will restrict the primary correlation analysis to the subset of datasets where the task type matches the available baseline metric (e.g., AUC for classification, RMSE/MAE for regression). If a dataset's task type is ambiguous or the baseline is missing for that specific task, it will be excluded from the statistical comparison and documented in the 'Data Availability Gap' section.**
- **The MulTaBench dataset provides the raw tabular values (or the necessary intermediate CSV/Parquet files) required to compute cardinality, missingness rates, and sparsity. The system will load these raw tabular files directly to calculate the metadata statistics. If only pre-processed embeddings were available, the system would be unable to compute these structural properties, but the benchmark specification confirms the inclusion of structured tabular data sources.**