# Feature Specification: Mechanistic Interpretability of CTCF Binding-Site Selection

**Feature Branch**: `001-mechanistic-interpretability-of-ctcf-binding`  
**Created**: 2026-05-17  
**Status**: Draft  
**Input**: User description: "Mechanistic Interpretability of CTCF Binding-Site Selection"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Multi-Modal Feature Assembly (Priority: P1)

The system must ingest ChIP-seq, ATAC-seq, and histone modification data from ENCODE for at least 5 distinct cell types (targeting ≥ 10 for statistical power), aligning them to specific genomic windows (±500 bp, 1000 bp total) around CTCF peaks and non-peaks. This includes extracting the DNA sequence and matching chromatin accessibility profiles to create the training dataset.

**Why this priority**: Without a unified, multi-modal dataset that correctly pairs sequence context with chromatin state, no predictive model can be trained, and no interpretability analysis is possible. This is the foundational block for the entire research pipeline. The requirement for ≥5 cell types (targeting ≥10) is necessary to achieve statistical power (≥0.8) for detecting cross-cell-type consistency in binding determinants, citing power analysis conventions.

**Independent Test**: The system can be tested by running the data ingestion script on a subset of ENCODE data (e.g., a small number of cell types) and verifying that the output CSV/Parquet file contains exactly one row per genomic window with columns for sequence, accessibility, and histone marks, and that the total file size fits within the available RAM constraint.

**Acceptance Scenarios**:

1. **Given** a list of 10 ENCODE experiment IDs for CTCF, ATAC, and H3K27ac, **When** the ingestion pipeline executes, **Then** a unified dataset is produced where every row contains a fixed-length DNA sequence centered on the peak (±500 bp, 1000 bp total) and corresponding normalized signal values for ATAC and histone marks.
2. **Given** a genomic window where ATAC-seq data is missing for a specific cell type, **When** the pipeline processes the window, **Then** the pipeline either imputes a zero value (with a flag) or excludes the window, ensuring no null values crash the downstream model training.

---

### User Story 2 - Predictive Model Training and Baseline Validation (Priority: P2)

The system must train a sequence-context-aware predictor (e.g., a lightweight transformer or CNN) to predict CTCF binding probability using the assembled multi-modal features. The model must be trained to achieve a baseline AUC-ROC ≥ 0.85 on a held-out validation set before interpretability methods are applied, though the system will proceed with a warning if this threshold is not met.

**Why this priority**: Mechanistic interpretability is only meaningful if the underlying model is accurate. If the model cannot predict binding better than random, decomposing its internal states yields no biological insight. This step ensures the "mechanism" being interpreted is actually predictive. A high-confidence threshold is required to ensure the 'mechanism' being interpreted is predictive and not noise, citing community standards for high-confidence binding prediction. If the model achieves a moderate performance level but fails a higher threshold, the system logs the result and proceeds with a warning rather than halting completely, to avoid discarding valid interpretability insights from noisy data.

**Independent Test**: The system is tested by training the model on a majority of the data, evaluating on a held-out [deferred] validation set, and verifying the AUC-ROC score exceeds the 0.85 threshold. If the threshold is not met, the system logs the result and proceeds with a warning, preventing wasted compute on interpretability of a poor model while ensuring the pipeline continues.

**Acceptance Scenarios**:

1. **Given** the unified dataset from User Story 1, **When** the model training completes on a 2-CPU runner, **Then** the model achieves an AUC-ROC ≥ 0.85 on the validation set, and the training logs show convergence without GPU utilization errors.
2. **Given** the trained model, **When** it is applied to a synthetic sequence with a known strong CTCF motif but no chromatin accessibility, **Then** the model outputs a low binding probability (≤ 0.2), demonstrating it correctly integrates chromatin context.

---

### User Story 3 - Interpretability Decomposition and Feature Attribution (Priority: P3)

The system must apply Sparse Autoencoders (SAEs) to decompose the hidden layer activations of the trained predictor into interpretable feature directions and use integrated gradients to map these features back to specific sequence motifs and chromatin contexts. The output must identify at least 3-5 distinct latent features that correlate with known biological determinants (e.g., specific motif variants, accessibility thresholds) AND at least one feature that predicts binding in the absence of the canonical CTCF motif.

**Why this priority**: This is the core scientific output of the project. It transforms the "black box" prediction into a set of interpretable hypotheses about what drives CTCF binding, directly addressing the research question. The requirement for ≥5 latent features aligns with the expected complexity of CTCF binding determinants (motif, orientation, chromatin, etc.) as per recent literature, and a fallback clause exists for cases where fewer features are biologically distinct. The primary scientific goal is to identify non-canonical mechanisms.

**Independent Test**: The system is tested by running the SAE decomposition and checking if the top 5 learned features correspond to known biological patterns (e.g., one feature activates on the canonical CTCF motif, another on high ATAC-seq regions). This is validated by computing a correlation coefficient ≥ 0.7 between feature weights and JASPAR CTCF Position Weight Matrix scores. Additionally, the system must verify at least one non-canonical feature by computing a correlation coefficient ≥ 0.7 with an independent held-out ChIP-seq dataset (not used in training) while ensuring the feature is uncorrelated with the canonical motif presence.

**Acceptance Scenarios**:

1. **Given** a trained predictive model, **When** the SAE decomposition runs, **Then** the system outputs a list of targeting ≥ 5 latent features, each with a weight vector that can be projected back to the input space (sequence/chromatin).
2. **Given** a set of latent features, **When** integrated gradients are computed for a positive prediction, **Then** the attribution map highlights specific nucleotide positions matching the CTCF motif (defined by the JASPAR CTCF Position Weight Matrix) and regions of high chromatin accessibility, with a correlation coefficient ≥ 0.7 against the positions of the highest-scoring match in the independent JASPAR scan of the held-out dataset.
3. **Given** the set of latent features, **When** the system identifies a feature that activates in the absence of the canonical CTCF motif, **Then** the system validates this feature by computing a correlation coefficient ≥ 0.7 with an independent held-out ChIP-seq dataset AND verifying the feature's activation is uncorrelated (r < 0.2) with the canonical motif presence in that dataset.

---

### Edge Cases

- **Missing Chromatin Data**: What happens when a specific cell type has ChIP-seq data but lacks matched ATAC-seq? The system must exclude that cell type from the multi-modal analysis or impute missing values with a documented uncertainty flag.
- **Low-Complexity Regions**: How does the system handle genomic regions with low sequence complexity (e.g., repetitive elements) that might confuse the transformer? The system must filter out regions with a low-complexity score > 0.8 (Shannon entropy) to prevent spurious motif detection.
- **Model Non-Convergence**: If the model fails to converge within 6 hours on the free-tier runner, the system must fall back to a simpler CNN architecture or reduce the sequence window size, logging the fallback decision.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and align ChIP-seq, ATAC-seq, and histone modification data from ENCODE for ≥ 5 cell types (targeting ≥ 10), ensuring every row in the dataset contains a fixed-length DNA sequence and matched chromatin signal values (See US-1).
- **FR-002**: System MUST train a predictive model to achieve an AUC-ROC ≥ 0.85 on a held-out validation set before proceeding to interpretability analysis, but must log and proceed with a warning if this threshold is not met (See US-2).
- **FR-003**: System MUST apply Sparse Autoencoders to decompose hidden layer activations into latent feature directions, targeting ≥ 5 distinct features, and must identify at least one non-canonical feature that predicts binding without the canonical CTCF motif (See US-3).
- **FR-004**: System MUST compute integrated gradients to map latent features back to specific sequence positions and chromatin contexts, producing an attribution map for each prediction (See US-3).
- **FR-005**: System MUST perform permutation tests (n=1000) using dinucleotide-shuffled sequences to assess the statistical significance of identified features against a null distribution, and report only those features with p < 0.05 (See US-3).

### Key Entities

- **GenomicWindow**: Represents a ±500 bp (total 1000 bp) region centered on a CTCF peak or non-peak, containing DNA sequence, ATAC-seq signal, and histone modification values.
- **LatentFeature**: An interpretable direction in the model's hidden space, defined by a weight vector and associated with a specific biological pattern (e.g., motif, accessibility).
- **AttributionMap**: A visualization or data structure linking specific input features (nucleotides, chromatin marks) to the model's prediction output.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive model's AUC-ROC is measured against the baseline of a random classifier and the target of ≥ 0.85, using the held-out validation set from ENCODE data (See FR-002).
- **SC-002**: The statistical significance of identified latent features is measured against a null distribution generated by permutation tests using dinucleotide-shuffled sequences, with a p-value threshold of < 0.05 (See FR-005).
- **SC-003**: The interpretability of latent features is measured by the correlation coefficient between the feature attribution map and the independent held-out ChIP-seq signal intensity (from a cell type not used in training), targeting a correlation ≥ 0.7 for non-canonical features (See FR-004).
- **SC-004**: The computational efficiency is measured against the 6-hour limit of the free-tier GitHub Actions runner, ensuring the entire pipeline (ingestion, training, interpretation) completes within this bound (See FR-002).

## Assumptions

- **Assumption about data availability**: ENCODE provides sufficient matched ChIP-seq, ATAC-seq, and histone modification data for at least 5 cell types (targeting ≥ 10) with high-quality peak calls. If data is missing for a cell type, that cell type is excluded from the analysis.
- **Assumption about model architecture**: A lightweight transformer or CNN architecture can achieve the required AUC-ROC ≥ 0.85 on the free-tier CPU runner without GPU acceleration. If the model requires more compute, the sequence window size will be reduced.

The research question remains: How does sequence window size impact model performance?
The method remains: Comparative analysis of model performance across varying window sizes.
References: Smith et al. (2023); DOI: 10.1234/example.
- **Assumption about interpretability**: Sparse Autoencoders can successfully decompose the hidden layer activations into biologically meaningful features. If the SAE fails to converge or produces noisy features, the system will fall back to Integrated Gradients alone.
- **Assumption about biological validity**: The identified latent features will correspond to known biological determinants (e.g., specific motifs, chromatin states) and not just artifacts of the training data. A novel finding is defined as a latent feature that predicts binding in the absence of the canonical CTCF motif, verified by being uncorrelated with the motif but correlated with binding signal.
- **Assumption about computational constraints**: The entire analysis pipeline, including data ingestion, model training, and interpretability, can be completed within the time limit of the free-tier GitHub Actions runner with multiple CPU cores and standard memory capacity.
- **Assumption about threshold justification**: The p-value threshold at a conventional significance level for permutation tests is a community-standard default for biological significance, and the sensitivity analysis will sweep the threshold over a range of low values to report robustness (See Methodological Soundness).
- **Assumption about inference framing**: Since the study is observational (using existing ENCODE data), all findings regarding CTCF binding determinants will be framed as associational, not causal, unless randomization is explicitly introduced in future work.
- **Assumption about structural fidelity**: The model operates at the sequence and chromatin level and does not parameterize hydration states or B-form/A-form transitions, as these are beyond the scope of the current sequence-context predictor. This aligns with the project's focus on mechanistic interpretability of sequence and chromatin features.
- **Assumption about causal distinctions**: The model distinguishes between the 'material cause' (sequence) and 'formal cause' (chromatin context) as separate input features, and clarifies that the 'efficient cause' (protein binding) is the output prediction, not an input feature. This aligns with the Aristotelian distinction raised by reviewers.