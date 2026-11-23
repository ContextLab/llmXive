# Research: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

## Research Question
How do neural activity patterns during story recall differ from those during initial encoding, and to what extent can these patterns be decoded to reconstruct specific narrative elements (plot points, characters, themes) using publicly available fMRI datasets?

**Dataset Limitation Note**: The Natural Stories dataset (ds000234) does NOT contain a distinct 'delayed task' fMRI run. Therefore, the focus is now on measuring 'Semantic Drift' rather than testing 'Memory Reconfiguration'.

## Dataset Strategy

The project relies on the **OpenNeuro ds000234** (Natural Stories) dataset. This dataset is the only verified source for the specific "story listening" paradigm required by the spec.

| Dataset Name | Source URL | Access Method | Variables Verified |
|:--- |:--- |:--- |:--- |
| OpenNeuro ds000234 | ` | `datasets.load_dataset(..., streaming=True)` | fMRI BOLD timecourses, Event onsets/durations (sentence/paragraph boundaries), Subject metadata. |

**Dataset Fit Verification**:
The dataset contains the necessary variables:
1. **Outcome**: BOLD signal in ROIs (Hippocampus, mPFC, etc.).
2. **Predictors**: Event labels (derived from story script) and semantic content (text).
3. **Covariates**: Motion parameters (for exclusion).

**Label Derivation Strategy**:
The dataset provides event onsets/durations but does not natively contain 'plot', 'character', or 'theme' categorical labels for every event. To ensure ground truth independence from the BERT feature extractor, these labels will be derived from the official story script (provided with the dataset) using a deterministic, rule-based parser (e.g., keyword matching and heuristics) implemented in `code/data/segmentation.py`. This prevents circular validation where the model's own semantic processing generates its own labels.

## Methodological Rationale

### 1. Preprocessing (fMRIPrep)
* **Method**: fMRIPrep v.0.
* **Rationale**: Standardized, reproducible preprocessing. Essential for aligning data across subjects.
* **Constraint**: Must run within 6 hours for a 2-subject subset initially, with escalation to 5 if needed. Parallelization (multiple workers) is used for subject-level tasks.

### 2. Event Alignment (HRF Convolution)
* **Method**: Double-gamma HRF convolution applied to event onset times.
* **Rationale**: fMRI BOLD signal is sluggish. Direct alignment of event labels would introduce noise. Convolution aligns the neural response with the hemodynamic delay.

### 3. Representational Similarity Analysis (RSA)
* **Method**: Compute pairwise dissimilarity (1 - correlation) between neural patterns for different events. Compare **Early vs. Late Encoding** patterns to measure Semantic Drift.
* **Rationale**: RSA does not require decoding specific labels; it measures the *structure* of the neural representation. This is ideal for testing semantic drift without assuming a linear mapping exists.
* **Statistical Rigor**:
 * **Permutation Test**: Dynamic Stopping Criterion (p-value stability < 0.001 over 100 iterations, max 5000) to ensure robust FDR correction.
 * **Multiple Comparison Correction**: FDR (q < 0.05) applied across ROIs to control family-wise error.
 * **Group Aggregation**: Fisher's Z transformation applied to RSA dissimilarity values across subjects to enable group-level inference.

### 4. Decoding (Ridge Regression)
* **Method**: Linear Ridge Regression with subject-level K=3 Stratified Folds, using scrambled text as a control.
* **Rationale**: Linear models are interpretable and computationally feasible on CPU. Non-linear models are excluded to ensure reproducibility within the 6-hour window.
* **Semantic Features**: BERT-base-uncased embeddings of event text.
 * PCA (a sufficient number of components) reduces dimensionality.
 * **Validation**: Features extracted from *text only*, preventing circularity.

## Statistical Rigor & Constraints

* **Multiple Comparisons**: FDR correction is mandatory for RSA and decoding results across ROIs and categories.
* **Sample Size**: Limited to a small number of subjects for default CI run, with escalation as needed.
* **Causal Inference**: No causal claims are made. The study is observational/correlational.
* **Collinearity**: Semantic features may be correlated. Descriptive statistics will report correlations and acknowledge potential collinearity.

## Compute Feasibility Decision

* **CPU-First**: All tasks are designed for the GitHub Actions free-tier (vCPU, standard RAM allocation) for a 2-subject subset initially, with escalation to 5 if needed.
* **Streaming**: Data is streamed to avoid memory overflow.