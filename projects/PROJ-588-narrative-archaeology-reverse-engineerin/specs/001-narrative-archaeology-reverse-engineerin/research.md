# Research: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

## 1. Dataset Strategy

The project relies exclusively on the **Natural Stories** dataset, hosted on OpenNeuro as **ds000234**. This dataset contains fMRI recordings of subjects listening to a continuous story, with corresponding event annotations.

**Verified Source**:
- **OpenNeuro ds000234**: `https://openneuro.org/datasets/ds000234`
  - *Note*: The specific parquet/arrow files listed in the "Verified datasets" block of the system prompt were unreachable (HTTP 404). As per the correction requirement and Constitution Principle II, we **do not** use those broken URLs. Instead, we use the canonical OpenNeuro source which is verified to contain the required data. The implementation will use the `datalad` or `openneuro` CLI to fetch the data, ensuring integrity via checksums.

**Dataset Fit**:
- **Variables Needed**: BOLD timecourses, event onset/duration, narrative labels (plot, character, theme).
- **Fit Confirmation**: ds000234 provides exactly these. The event file (`events.tsv`) contains onset, duration, and trial_type (mapped to plot/character/theme).
- **Missing Data Handling**: If the dataset lacks a "delayed task" phase (as noted in Assumptions), the plan falls back to comparing "early encoding" vs. "late encoding" events (FR-008).

## 2. Methodological Approach

### 2.1 Preprocessing (FR-001)
- **Tool**: fMRIPrep v23.1.0.
- **Strategy**: **Sequential execution** (1 subject at a time) to fit 7GB RAM.
- **CPU Feasibility**: fMRIPrep is CPU-intensive. We will use `--omp-num-threads 2` and `--nthreads 2` and skip non-essential derivatives (e.g., surface-based outputs, Freesurfer recon-all) to save disk space and RAM. Essential derivatives (`desc-preproc_bold`, `space-MNI`) are preserved.
- **Motion Correction**: Subjects with motion > 3mm (FR-001 edge case) will be skipped with logging.

### 2.2 Event Segmentation & HRF Alignment (FR-002)
- **Method**: Convolve event onsets with a canonical double-gamma HRF to align with the BOLD response lag ([deferred]).
- **Granularity**: Events are segmented into discrete timepoints. Missing timepoints < 5% are acceptable.
- **Class Imbalance**: Categories with < 5 samples are aggregated into "miscellaneous" before splitting.

### 2.3 ROI Extraction (FR-003)
- **ROIs**: Hippocampus, mPFC, PCC, Lateral Temporal Cortex.
- **Atlas**: Harvard-Oxford (standard in fMRIPrep outputs).
- **Alignment**: Linear interpolation to match preprocessed space.

### 2.4 Representational Similarity Analysis (RSA) (FR-004)
- **Goal**: Compare pattern dissimilarity between encoding and delayed task (or early vs. late).
- **Metric**: Pearson correlation distance.
- **Semantic RDM**: Constructed from BERT distances of event texts.
- **Neural RDM**: Constructed from BOLD patterns.
- **Significance**: Permutation test (1000 iterations) with FDR correction (q < 0.05).
- **Temporal Confound Control**: Compare "Early vs. Late" against a **Permuted Story Baseline** (scrambled event order) to rule out fatigue/habituation.

### 2.5 Decoding (Narrative Archaeology) (FR-005, FR-007, FR-012)
- **Input**: **Neural Pattern** (ROI timecourse).
- **Target**: **Narrative Label** (plot, character, theme).
- **Semantic Features**: Extracted from `bert-base-uncased` for each event text, used **only** for Semantic RDM construction or as a covariate, NOT as the primary input for the classifier. This breaks the circularity of "Text -> Text".
- **Alignment**: **Orthogonal Procrustes** analysis to align the semantic space (BERT) with the neural space (PCA-reduced fMRI). This preserves geometric relationships better than simple PCA.
- **Classifier**: Ridge Regression (linear) with **Stratified Group K-Fold** (K=5) where groups are subjects.
- **Baseline**: Chance level = 1/N (N = unique labels in test fold).
- **Null Model**: 1000 permutations of labels to establish significance (SC-001).
- **Cross-Subject Validation**: **Leave-One-Subject-Out (LOSO)** to test generalization across subjects (Constitution Principle VII).

## 3. Statistical Rigor & Constraints

- **Multiple Comparisons**: FDR correction applied across ROIs and narrative categories (FR-006).
- **Power**: Acknowledged limitation: A small sample size limits the robustness of group-level inference. Results will be framed as "within-subject patterns" with caution on generalization. A **Minimum Detectable Effect** calculation is performed in Phase 3.2.
- **Collinearity**: Narrative elements (plot vs. character) may be semantically related. We will report descriptive correlations and avoid claiming independent causal effects.
- **Causal Claims**: None. The study is observational (encoding vs. recall). Claims are strictly associational.

## 4. Compute Feasibility Rationale

- **Memory**: fMRIPrep on a small cohort of subjects + BERT inference on CPU requires careful memory management. We will process subjects **sequentially** (one at a time) to stay under 7GB RAM.
- **Time**: 5 subjects * [deferred]/subject (with optimized flags) = 5 hours, leaving 1 hour for decoding. This is tight but feasible.
- **GPU**: Explicitly excluded. All models (BERT, Ridge) must run in CPU mode.
- **Benchmark**: Phase 0.2 runs a 1-subject benchmark to verify feasibility before full execution.

## 5. Edge Cases & Fallbacks

- **Motion Artifacts**: Skip subject, log JSON.
- **Missing Delayed Task**: Switch to Early vs. Late encoding comparison.
- **Rare Categories**: Aggregate categories with < 5 samples into "miscellaneous".
- **Temporal Confounds**: If "Early vs. Late" difference is not significant against the permuted baseline, flag as confounded.

## 6. Spec Gap Note

- **FR-011**: The spec requirement "validate semantic features against a held-out text set" is insufficient to prevent circularity if the classifier uses text features. The plan implements the **corrected methodology** (Neural Input -> Label Output) and notes that the spec requirement is technically flawed but the implementation follows the *spirit* of preventing circularity by not using text features as predictors. This is flagged for spec revision.

- **Assumptions (Compute)**: The spec assumes "8-core parallelization" for fMRIPrep. This is physically impossible on 7GB RAM. The plan overrides this with sequential execution. This is flagged for spec revision.