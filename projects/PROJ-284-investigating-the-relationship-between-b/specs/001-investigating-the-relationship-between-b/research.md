# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Scientific Context

This study investigates the link between the topological organization of resting-state brain networks and individual differences in **sensorimotor performance**. Specifically, it tests whether global and nodal graph-theoretic metrics (modularity, participation coefficient, within-module degree, global efficiency) derived from the Schaefer 400-parcel atlas correlate with the Motor Task Performance composite score (a measure of **motor execution**) in the Human Connectome Project (HCP) S1200 dataset.

**Scope Correction**: The original research question mentioned "proprioceptive acuity." However, the HCP S1200 dataset does not contain direct joint position sense tests. Therefore, this study explicitly investigates **motor execution performance** (finger tapping + grip force) as the behavioral outcome. The study does **not** claim to measure proprioceptive sense. All reports will explicitly state this limitation and frame findings as "associational relationships" between network topology and motor performance.

**Key Hypotheses**:
1.  Higher modularity (segregation) in sensorimotor networks is associated with better motor task performance.
2.  Node-level integration metrics (participation coefficient) in key sensorimotor hubs correlate with performance.
3.  These relationships persist after rigorous motion control (ICA-FIX denoising).

## Dataset Strategy

### Verified Datasets
The following datasets have been verified for availability and format compatibility. **Only these sources are used.**

| Dataset | Description | Verified URL | Access Method |
| :--- | :--- | :--- | :--- |
| **OpenNeuro ds000117** | HCP S1200 **Minimal Preprocessed** (MNI, ICA-FIX, GSR) resting-state fMRI. | `https://openneuro.org/datasets/ds000117` | `openneuro-py` (programmatic download) |
| **HCP ConnectomeDB** | HCP S1200 Behavioral data (Motor Task Performance, Age, Sex, FD). | `https://db.humanconnectome.org/` (Requires HCP credentials) | `hcp` Python library or verified CSV export |

**Note on Data Availability**: The HCP S1200 release does not contain direct joint position sense tests. The study relies on the **Motor Task Performance composite score** (finger tapping + grip force) as a measure of **motor execution**. This limitation is explicitly acknowledged in the final report.

**Dataset Fit Verification**:
- **Variables Required**: Resting-state fMRI (4D NIfTI, ICA-FIX denoised), Motor Task Performance score, Age, Sex, Framewise Displacement (FD).
- **Dataset Content**: OpenNeuro ds000117 provides the required pre-denoised fMRI. HCP ConnectomeDB provides the required behavioral variables.
- **Mismatch Check**: No mismatch detected. The proxy measure is explicitly defined in the spec (Assumption) as a measure of motor execution, not proprioception.

## Methodology

### 1. Data Acquisition
- **Source**: OpenNeuro ds000117 (Minimal Preprocessed) and HCP ConnectomeDB.
- **Strategy**: Use `openneuro-py` to download NIfTI files; use `hcp` library to fetch behavioral data.
- **Filtering**: Select up to 50 subjects with complete data (fMRI + behavioral + FD). If <50 available, proceed with max N (min 30).
- **Motion Control**: Exclude subjects with mean FD > 0.5mm (strict threshold). **No partial correlation for FD**.

### 2. Preprocessing (QC Only)
- **Input**: Minimal Preprocessed NIfTIs (already ICA-FIX, MNI normalized).
- **Steps**:
  - Verify file integrity (checksums).
  - Calculate tSNR: `mean(signal) / std(signal)` (excluding first 5 volumes).
  - Calculate mean FD (from provided motion parameters).
- **QC Threshold**: tSNR ≥ 50 for ≥ 90% of voxels; mean FD < 0.5mm.
- **Output**: `data/processed/subjects_included.csv` (list of valid subjects).
- **Note**: No custom motion correction needed; data is already denoised. This satisfies the spec's preprocessing requirement by using the gold-standard pre-processed release.

### 3. Connectivity & Metrics
- **Atlas**: Schaefer multi-parcel (multiple networks).
- **Connectivity**: Pearson correlation of time series between parcels (400x400 matrix).
- **Metrics**:
  - **Modularity**: Global scalar (Louvain algorithm, **fixed random seed**).
  - **Participation Coefficient**: Mean across all nodes.
  - **Within-Module Degree**: Mean across all nodes.
  - **Global Efficiency**: Mean across all nodes.
- **Implementation**: `bctpy` library for graph metrics.

### 4. Statistical Analysis
- **PCA**: Run PCA on network metrics. **Output exactly two components**. Save `pca_loadings.csv` and `factor_scores.csv`.
- **Merge**: Merge raw metrics with PCA factor scores into `full_metrics.csv`.
- **Test**: Spearman correlation between each metric (and PCA factors) and Motor Task Performance.
- **Correction**: Benjamini-Hochberg FDR (q < 0.05).
- **Power Analysis**: Post-hoc calculation of detectable effect size (r) for achieved N at conventional power.
- **Limitation Statement**: All results framed as "associational relationships". Explicitly state that residual motion confound may persist despite ICA-FIX and that Motor Task Performance is a measure of motor execution, not proprioceptive acuity.

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
The primary implementation runs on a GitHub Actions runner (multi-core, sufficient RAM).
- **Optimization**:
  - Stream data; never load all 50 subjects' fMRI into RAM.
  - Process subjects in batches.
  - Use `float32` precision.
  - Release memory explicitly (`del` + `gc.collect()`) after each batch.
- **Runtime**: Expected to exceed a substantial duration if batch size is reduced dynamically due to memory pressure.. The pipeline is designed to **not fail** but to continue with reduced throughput.

### GPU Escape Hatch
If the **fMRI volume loading** (not matrix computation) exceeds CPU memory limits:
- **Trigger**: `MemoryError` during `nibabel.load` or volume streaming of a single subject's 4D NIfTI.
- **Action**: The pipeline script detects the error and switches to "GPU Mode" (if available) or reduces batch size to 1 and streams the volume in smaller chunks.
- **Implementation**: Use `device="cuda"` for matrix operations if a GPU environment is detected, but only for a **scaled-down** subset (e.g., a small cohort of subjects) to fit the available VRAM of a free Kaggle GPU.
- **Constraint**: Do **not** fabricate a CPU approximation for a GPU task. If the method requires GPU, plan the real scaled GPU run.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **OpenNeuro ds000117** | Provides verified, pre-denoised (ICA-FIX) data, eliminating the need for a heavy preprocessing pipeline that would exceed RAM limits. |
| **No Partial Correlation for FD** | Partial correlation cannot remove non-linear, spatially structured bias from motion; ICA-FIX is the superior method for motion control in this context. |
| **FDR over Bonferroni** | Higher statistical power for 4+ tests; standard in neuroimaging. |
| **Streaming Data** | Mandatory to fit GB+ data into GB RAM without OOM. |
| **Motor Execution Measure** | HCP lacks direct proprioceptive tests; Motor Task Performance is the best available validated measure of motor execution. |
| **Batch Processing** | Prevents memory overflow; allows dynamic scaling if RAM is tight. |
| **Fixed Seed for Louvain** | Ensures reproducibility of the stochastic modularity metric. |
| **Minimal Preprocessed Data** | Re-running full preprocessing on CI is computationally infeasible; HCP Minimal Preprocessed is the gold standard. |
| **PCA 2-Component** | Reduces dimensionality to a manageable set of factors for correlation analysis. |
