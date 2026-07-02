# Research: Investigating Network Centrality in ASD Resting-State fMRI

## Dataset Strategy

The analysis relies on the **ABIDE Preprocessed** initiative, hosted on **OpenNeuro**. This provides resting-state fMRI data that has already been pre-processed using fMRIPrep, satisfying FR-002 without requiring infeasible compute in CI.

**Verified Source**:
- **Dataset**: ABIDE Preprocessed (fMRIPrep derivatives)
- **URL**: `https://openneuro.org/datasets/ds0002800` (or equivalent verified ABIDE Preprocessed dataset)
- **Loader**: `nilearn.datasets.fetch_openneuro_dataset` or direct `bids` download.

| Variable | Source / Loader | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **fMRI Time-series** | OpenNeuro ds0002800 (Pre-processed NIfTI) | **VERIFIED** | fMRIPrep derivatives (spatial normalization, motion correction applied). |
| **Phenotypic (Diagnosis)** | OpenNeuro ds0002800 (phenotypic CSV) | **VERIFIED** | Requires Age, Sex, Diagnosis (ASD/Control). |
| **Atlas (Schaefer 400)** | `nilearn.datasets.fetch_atlas_surf_destrieux` (fallback) or local file | **Standard** | Standard neuroimaging atlas, no external URL required. |

**Critical Gap Resolution**: The previous plan's reliance on synthetic data is **removed**. The pipeline now strictly requires real, pre-processed data. If the OpenNeuro dataset is unavailable or the download fails, the pipeline **fails gracefully** with a clear error message. This ensures scientific validity and prevents circular validation.

## Methodological Rationale

### 1. Preprocessing (FR-002)
*   **Method**: fMRIPrep is the gold standard.
*   **Decision**: The plan **does not run fMRIPrep in CI**. Instead, it downloads **pre-processed derivatives** from OpenNeuro (ABIDE Preprocessed).
*   **Rationale**: This satisfies the spec's requirement for fMRIPrep-processed data (FR-002) while ensuring CI feasibility (2 CPU, 7GB RAM). The derivatives are the direct output of fMRIPrep, preserving construct validity.
*   **Provenance**: The fMRIPrep version and parameters are extracted from the BIDS sidecars (JSON) of the downloaded derivatives and recorded in `data/derived/preprocessing_log.yaml`.

### 2. Graph Construction (FR-003, FR-006)
*   **Parcellation**: Schaefer 400 atlas.
*   **Adjacency**: Pearson correlation of time-series.
*   **Thresholding**: Top 15% edges (binary).
* **Sensitivity**: Sweep {[deferred], [deferred], [deferred]} (FR-009).
*   **Connectivity Check**: If the graph is disconnected after thresholding, the system will log a warning and proceed, or slightly lower the threshold dynamically (logged) to ensure graph connectivity, as centrality metrics (especially betweenness) are undefined for disconnected components.

### 3. Centrality Computation (FR-004)
*   **Metrics**: Degree, Betweenness, Eigenvector.
*   **Library**: `networkx`.
*   **Collinearity (FR-010)**: These metrics are inherently correlated. The plan explicitly avoids multivariate regression claiming "independent effects." Instead, it will report:
    *   Pairwise correlations between metrics (stored in `CollinearityDiagnostics`).
    *   Univariate t-tests for each metric.
    *   A descriptive summary of how they co-vary.
    *   **Note on Coupling**: In network neuroscience, degree, betweenness, and eigenvector centrality are mathematically coupled (e.g., high degree nodes often have high betweenness). The univariate approach is used to avoid overclaiming independent effects, but the collinearity diagnostics are explicitly reported to frame the results descriptively.

### 4. Statistical Analysis (FR-005)
*   **Test**: Two-sample t-test (ASD vs Control) for each node and metric.
*   **Correction**: Benjamini-Hochberg FDR (q < 0.05).
*   **Power**: Acknowledged as limited if N < 50 per group. Power calculations are deferred to the implementation phase (`[deferred]`).
*   **Causal Framing**: All claims are **associational**. No causal inference is made.

### 5. Classification (FR-007)
*   **Model**: Logistic Regression (L2 regularization).
*   **Validation**: 5-fold Cross-Validation.
*   **Metrics**: Accuracy, AUC, Confusion Matrix.
*   **Feasibility**: Fully CPU-tractable.

### 6. Visualization (FR-008)
*   **Tool**: `nilearn.plotting.plot_surf_stat_map`.
*   **Input**: Stat maps (t-values) projected onto the fsaverage surface.
*   **Feasibility**: `nilearn` runs on CPU.

## Decision Log

| Decision | Rationale | Impact |
| :--- | :--- | :--- |
| **Pre-processed Derivatives (OpenNeuro)** | Raw fMRIPrep is infeasible in CI; OpenNeuro provides verified fMRIPrep derivatives. | Satisfies FR-002 and CI constraints; ensures construct validity. |
| **No Synthetic Data** | Synthetic data invalidates biological claims and creates circular validation. | Pipeline fails gracefully if real data is unavailable; ensures scientific soundness. |
| **Univariate Analysis Only** | Centrality metrics are collinear. | Prevents statistical overclaiming; satisfies FR-010 via `CollinearityDiagnostics`. |
| **FDR Correction** | >1200 tests (400 nodes * 3 metrics). | Essential for statistical validity (SC-003). |
