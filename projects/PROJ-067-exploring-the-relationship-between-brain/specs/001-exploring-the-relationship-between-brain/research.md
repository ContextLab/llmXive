# Research: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

## Dataset Strategy

| Dataset Name | Source URL | Usage | Verification Status |
|--------------|------------|-------|---------------------|
| OpenNeuro ds000228 | https://openneuro.org/datasets/ds000228 | Primary source for resting-state fMRI data. | **Verified** (HCP 1200 Subjects). |
| Dream Recall Metadata | **NOT PRESENT** in ds000228 | Required for target variable. | **MISMATCH**: ds000228 (HCP) does NOT contain dream recall frequency. |
| Alternative (Hypothetical) | N/A | If ds000228 lacks data, pipeline halts. | **Action**: Halt or pivot to a verified sleep-dream dataset (e.g., specific OpenNeuro sleep studies) if available. |

**Critical Note on Dataset Fit**:
The source spec assumes OpenNeuro `ds000228` contains a "dream recall frequency" field. **This is factually incorrect.** `ds000228` is the HCP 1200 Subjects release and does not include dream recall questionnaires.
- **Protocol**: The pipeline includes a **Phase 0: Dataset Validation** step.
- **Outcome**: If the field is missing (as expected), the pipeline will **HALT** with a "Fatal Dataset Mismatch" error.
- **Pivot**: The study cannot proceed with `ds000228` for this specific research question. A pivot to a dataset that actually contains sleep/dream phenotyping is required. This plan documents the pipeline logic assuming a valid dataset is found or substituted.

## Methodology & Statistical Rigor

### 1. Data Preprocessing (FR-001, FR-002, Edge Case: Motion)
- **Source**: OpenNeuro `ds000228` (or substituted valid dataset).
- **Denoising**: ICA-AROMA (Automatic Removal of Motion Artifacts).
- **Normalization**: Spatial normalization to standard MNI space.
- **Motion Exclusion**: Calculate **Framewise Displacement (FD)**. Exclude subjects with FD > 0.5mm (Edge Case handling).
- **Memory Safety**: Peak RSS monitored via `/proc/self/status`. If >7GB, the process fails gracefully.
- **Sampling**: Limit to N=50 subjects to ensure runtime <6h.

### 2. Dynamic Connectivity Extraction (FR-003, FR-004 - Modified)
- **Parcellation**: **Schaefer-100** atlas (100 regions).
  - *Rationale*: Schaefer-400 (as per spec) creates 400x400 matrices. With a 30s window (~15 timepoints at TR=2s), the correlation matrix is rank-deficient and unstable. Schaefer-100 ensures statistical validity.
- **Sliding Window**: Fixed window = 30s, step = 10s.
- **Clustering**: Louvain algorithm applied to time-varying connectivity matrices to generate discrete community partitions.
- **Metrics**:
  - **Flexibility**: Number of state transitions per unit time for DMN, Salience, and Hippocampal-Memory networks.
  - **Stability**: **Mean Dwell Time** (average duration of a state).
    - *Rationale*: Defined as Mean Dwell Time rather than "inverse of flexibility" to avoid mathematical tautology and ensure statistical independence between metrics.

### 3. Statistical Analysis (FR-005, FR-006, FR-007, FR-009)
- **Primary Test**: Spearman correlation (rho) between network metrics (flexibility/stability) and dream recall frequency.
- **Multiple Comparisons**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied to p-values across the networks and 2 metrics (6 tests total).
- **Robustness**: A sufficient number of iterations of permutation testing to generate null distribution.
- **Power Analysis**:
  - **A Priori**: Acknowledges N=50 is underpowered for small effects. Justifies study as a feasibility test for medium effects (r=0.3).
  - **Post-hoc**: FR-009 mandates calculation of **Minimum Detectable Effect (MDE)** given N=50 and alpha=0.05. This will be reported in `stats.json`.
- **Causal Assumption**: Observational study. Claims will be framed as **associational**. No causal inference will be made without randomization.

### 4. Multiple Comparison & Power Limitations
- **Multiple Comparisons**: With 6 tests (3 networks × 2 metrics), family-wise error rate is controlled via FDR.
- **Power Limitation**: N=50 is a small sample for fMRI. The plan explicitly acknowledges this limitation. Power analysis will quantify the ability to detect r=0.3.
- **Collinearity**: If DMN and Hippocampal networks show high definition overlap, independent effects will not be claimed; descriptive reporting will be used.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (CPU, 7GB RAM, no GPU).
- **Strategy**:
  - Process subjects sequentially to minimize memory footprint.
  - Use `joblib` for parallelizing sliding window calculations only if memory allows (otherwise sequential).
  - Sample data if necessary (e.g., downsample timepoints) to fit RAM, but maintain 30s window integrity.
  - Avoid deep learning models; rely on `scikit-learn` and `scipy` which are CPU-tractable.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| OpenNeuro metadata lacks "dream recall frequency" | **Phase 0** checks immediately after download; fail gracefully with specific "Fatal Dataset Mismatch" error. |
| Memory usage exceeds 7GB | Implement chunked loading of NIfTI files; monitor RSS; process one subject at a time. |
| Runtime exceeds 6 hours | Limit N to 50; optimize sliding window implementation; use `joblib` for parallelization only if safe. |
| Null result (p > 0.05) | Report full results including null distribution plot and correlation coefficient; do not suppress output. |
| Schaefer-400 Instability | **Switch to Schaefer-100** to ensure rank-sufficient correlation matrices. |
| Tautological Metrics | Define Stability as **Mean Dwell Time** instead of inverse flexibility. |