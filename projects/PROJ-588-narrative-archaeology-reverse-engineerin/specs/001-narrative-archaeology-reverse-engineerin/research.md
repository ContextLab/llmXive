# Research: Narrative Archaeology

## Executive Summary

This research investigates the neural correlates of story memory by analyzing fMRI data from the Natural Stories dataset (OpenNeuro ds000234). The primary goal is to determine if neural patterns during **early encoding events** differ from those during **late encoding events** (within-session stability), and whether these patterns can be decoded to reconstruct specific narrative elements (plot, character, theme). Given the constraints of the GitHub Actions free-tier (2 vCPU, 7GB RAM, 6 hours), the pipeline employs CPU-optimized preprocessing (nilearn/niworkflows) and linear decoding models (ridge regression) with semantic feature extraction.

**Dataset Constraint**: OpenNeuro ds is a single-session story-listening dataset. It does not contain a distinct "recognition" fMRI phase. The analysis is therefore scoped to **within-session pattern stability** (early vs. late encoding events) to test for temporal drift or semantic stabilization, rather than memory reconfiguration between distinct sessions. This is a necessary adaptation to data constraints.

## Dataset Strategy

The project relies on the **Natural Stories fMRI dataset** (OpenNeuro ds000234).

**Verified Source**:
- **OpenNeuro ds000234**: Accessed via a verified HuggingFace mirror to ensure reachability and format compatibility on CI.
  - Repository: `clane9/openneuro-fslr64k` (verified HuggingFace source).
  - Access: `datasets.load_dataset("clane9/openneuro-fslr64k")`.

**Dataset Characteristics**:
- **Subjects**: ~50 total; analysis will use a 10-subject subset for CI feasibility.
- **Phases**: Single encoding session (listening). **No recognition phase**.
- **Annotations**: Event onset/duration files provided for story segmentation.
- **Variables**: BOLD timecourses, event labels (plot, character, theme), ROI masks.

**Data Access Strategy**:
1. Use `datasets.load_dataset("clane9/openneuro-fslr64k")` to fetch the data.
2. Validate the presence of required files (NIfTI, JSON event tables).
3. Select first 10 subjects with motion < 0.5mm.

## Methodology

### 1. Data Ingestion & Preprocessing (FR-001, FR-002)
- **Download**: Fetch data from the verified HuggingFace repository.
- **Preprocessing**: Use `nilearn` and `niworkflows` (CPU-optimized) instead of fMRIPrep due to Docker/RAM constraints.
  - Steps: Realignment, slice-time correction, normalization to MNI space, smoothing with an appropriate kernel width.
  - **Deviation Note**: fMRIPrep is the standard (FR-001), but `nilearn` is used here to meet the 6-hour/7GB constraint. This deviation is documented in `data-model.md` and justified by Constitution Principle VI. The source spec requires amendment.
- **Segmentation**: Align event labels (from JSON) to the BOLD timecourse using **HRF convolution** (canonical HRF).

### 2. Within-Session Pattern Stability (FR-003, FR-004, US-2)
- **ROI Extraction**: Extract timecourses from hippocampus, mPFC, PCC, lateral temporal cortex for **early** and **late** segments of the story.
- **RSA**: Compute dissimilarity matrices for early vs. late segments.
- **Statistical Test**: Permutation test (**1000 iterations**, pinned as `PERMUTATIONS=1000`) to compare early-late dissimilarity against early-early dissimilarity.
- **Correction**: FDR correction (q < 0.05) across ROIs.
- **Hypothesis**: Hippocampus and mPFC will show significant **temporal drift** (dissimilarity difference) compared to sensory cortices. **Effect size (Cohen's d)** will be reported; no fixed threshold.

### 3. Narrative Element Reconstruction (FR-005, FR-006, FR-007, US-3)
- **Semantic Features**: Extract features from story text using a pre-trained BERT model (`bert-base-uncased`, 768-dim). **Dimensionality Reduction**: Reduce to 50-dim via **PCA** to address the curse of dimensionality.
- **Alignment**: Use **Canonical Correlation Analysis (CCA)** to align semantic space with neural patterns.
- **Decoding**: Train **binary classifiers** (e.g., Plot vs. Non-Plot) using Ridge Regression to predict narrative labels from neural patterns. **Fallback**: Merge categories with count < 5 into "miscellaneous" to address class imbalance.
- **Validation**: **Subject-level Leave-One-Out (10 folds)** cross-validation with **blocking by event** to handle temporal autocorrelation.
- **Null Model**: Shuffle labels to establish chance baseline (1/N for binary classification) with **1000 permutations**.
- **Correction**: FDR correction for multiple comparisons across categories and ROIs.
- **Aggregation**: Merge categories with count < 5 into "miscellaneous" to address class imbalance.

## Statistical Rigor

- **Multiple Comparisons**: FDR correction (q < 0.05) applied to RSA and decoding results across ROIs and categories.
- **Power**: Acknowledged limitation: A small sample size is insufficient for group-level inference. **Within-subject permutation tests** are prioritized. **Effect sizes (Cohen's d)** are reported alongside p-values.
- **Causal Inference**: Observational study; claims limited to associational patterns.
- **Measurement Validity**: BOLD signal is an indirect measure of neural activity; semantic features are approximations.
- **Collinearity**: Plot, character, and theme labels may be correlated; models will report feature importance and acknowledge potential confounding.
- **Circular Validation Mitigation**: Narrative labels are derived from **human-annotated event types** (independent ground truth), not from the BERT features used for prediction. BERT features are predictors, not the labels themselves.
- **Temporal Autocorrelation**: Handled by **blocking by event** in cross-validation splits.

## Decision Rationale

- **CPU-Only**: Chosen to ensure the pipeline runs on GitHub Actions free-tier.
- **nilearn vs fMRIPrep**: fMRIPrep is too heavy for CI; nilearn provides a valid, documented alternative.
- **Linear Models**: Ridge regression/SVM are interpretable and computationally feasible; deep learning is excluded.
- **Permutation Testing**: Non-parametric approach avoids assumptions about data distribution. **1000 iterations** are pinned.
- **Early vs. Late Encoding**: Dataset ds000234 lacks a recognition phase; within-session stability is the only viable proxy.
- **Binary Classification**: Addresses class imbalance and under-sampling problems with N=10.
- **Dimensionality Reduction**: PCA to 50-dim is necessary to avoid the curse of dimensionality.

## Limitations

- **Dataset**: The dataset lacks a distinct "recognition" phase; analysis is scoped to within-session stability.
- **Sample Size**: A limited number of subjects limits generalizability; results are preliminary.
- **Semantic Features**: BERT features are a proxy for narrative meaning; may not capture all nuances.
- **Temporal Resolution**: HRF convolution is an approximation; rapid event transitions may be blurred.
- **Effect Size**: No fixed effect-size threshold is imposed; results are reported as empirical measurements.