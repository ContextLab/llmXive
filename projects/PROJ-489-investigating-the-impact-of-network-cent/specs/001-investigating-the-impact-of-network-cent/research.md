# Research: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Research Question
Do waking‑state network centrality metrics (degree, betweenness, eigenvector) predict the magnitude of neural synchrony (Phase‑Lag Index) observed during each sleep stage (N1, N2, N3, REM), after accounting for age, gender, and total sleep time?

## Methodological Approach

### 1. Data Acquisition & Preprocessing
- **Source**: `ronaldvandenbroek/physionet-sleep-data` (Hugging Face mirror of PhysioNet Sleep‑EDF).  
  URL: `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` (verified).  
- **Inclusion Criteria**:  
  - At least **2 minutes** of continuous, artifact‑free **wake** recording (required for stable resting‑state connectivity).  
  - At least 30 minutes of annotated sleep (any stage).  
  - Presence of the standard EEG electrode set (including frontal electrodes needed for coherence/PLI).  
- **Filtering Strategy**: Subjects not meeting the ≥ 2 min wake criterion are excluded. After filtering, we require **N ≥ 30** subjects; if fewer remain, the pipeline halts with an “Insufficient Sample Size” warning (FR‑010).  
- **Preprocessing** (`preprocess.py`):  
  - Band‑pass 0.5–45 Hz (SciPy FIR).  
  - ICA artifact removal: reject components with kurtosis > 5.0 **or** high‑frequency power > 3 × baseline.  
  - Epoching: non‑overlapping **30‑second** windows (verified length = 30 s, source: 1908.11463).  
  - Night‑ID extraction from EDF header; stored as `waking_night_id` / `sleep_night_id`.  

**Dataset Fit Note**: The original Sleep‑EDF recordings contain only brief pre‑sleep wake periods. By enforcing the ≥ 2 min wake filter we mitigate the instability risk, but we acknowledge that this reduces the usable subject pool and may limit statistical power. This limitation is documented in the final report.

### 2. Metric Computation
- **Waking Functional Connectivity** (`connectivity.py`):  
  - Magnitude‑squared coherence for each electrode pair in **theta (4–8 Hz)** and **alpha (8–13 Hz)** bands using Welch’s method (SciPy).  
  - Resulting matrices are symmetric, values strictly between 0 and 1.
- **Centrality** (`centrality.py`):  
  - Build undirected weighted graphs from coherence matrices.  
  - Compute **degree**, **betweenness**, **eigenvector** centrality via NetworkX.
- **Sleep‑Stage Synchrony** (`pli.py`):  
  - Compute Phase‑Lag Index for each epoch across all electrode pairs (MNE implementation).  
  - Aggregate to a **mean global PLI** per stage per subject (float ∈ [0, 1]).  

### 3. Aggregation
- **Metric Assembly** (`aggregate.py`):  
  - Consolidate all per‑subject centrality means and per‑stage mean PLIs into a single `SubjectMetrics.csv`.  
  - Include covariates (age, gender, total sleep time) and night IDs for confounding checks.

### 4. Collinearity Diagnostics
- Compute **global Variance Inflation Factor (VIF)** across all subjects for the three centrality predictors using `statsmodels`.  
- Report the overall VIF values; flag any VIF > 5.0 in the final report (FR‑009).  

### 5. Sample‑Size Validation
- After filtering for ≥ 2 min wake, count subjects with both valid waking centrality and sleep‑stage PLI.  
- If **N < 30**, abort analysis and emit a clear “Insufficient Sample Size” warning (FR‑010).  

### 6. Normality & Correlation Selection
- For each centrality‑PLI pair, perform **Shapiro‑Wilk** test on both vectors (SciPy).  
- If *p* ≥ 0.05 → use **Pearson**; else → **Spearman** (FR‑012).  

### 7. Confounder Adjustment
- Compute **partial correlations** controlling for age, gender, and total sleep time (derived from sleep‑stage durations).  
- If covariate data are missing for a subject, fall back to the bivariate correlation.  

### 8. Correlation Analysis
- Compute correlation coefficient and raw *p*‑value for every combination:  
  - 3 centrality metrics × 5 sleep stages × 2 frequency bands = **30 tests** (FR‑006).  

### 9. Multiple‑Comparison Control
- Apply **Bonferroni correction**: `p_corrected = min(p_raw * 30, 1.0)` (FR‑007).  

### 10. Aggregated Metrics Validation
- **Validate** `SubjectMetrics.csv` against `contracts/dataset.schema.yaml` using `validate.py`.

### 11. Reporting
- Produce `analysis_results.json` containing: metric name, stage, band, correlation coefficient, raw *p*, Bonferroni‑adjusted *p*, significance flag, correlation method, and global VIF flag.  
- Generate a Markdown report (`report.md`) that:  
  - Lists all results in a table.  
  - Highlights significant findings (`p_corrected < 0.05`).  
  - Includes a **Confounding Limitation** paragraph if any subject’s `waking_night_id == sleep_night_id`.  
  - Summarizes global VIF diagnostics.  
  - Discusses the instability of centrality metrics due to short wake segments and the impact of the ≥ 2 min filter on sample size.

## Dataset Strategy

| Dataset | Description | Verified URL | Fit Verification |
|---------|-------------|--------------|------------------|
| **PhysioNet Sleep‑EDF (via Hugging Face mirror)** | EEG recordings with sleep‑stage annotations and brief pre‑sleep wake periods. | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` | Contains required electrodes and both sleep and wake; **wake duration is limited** – mitigated by ≥ 2 min filtering and explicit limitation note. |
| **EEG (csv)** | General EEG event data – **not** used (does not contain sleep stages). | `https://huggingface.co/datasets/EEGDash/eeg-mi-datasets/resolve/main/Dreyer2023/MNE-dreyer2023-data/performance.csv` | Excluded – insufficient for current analysis. |
| **PLI** | No verified source – **not** used directly; PLI is computed from the EEG data. | *None* | Not applicable (computed in‑house). |

**Decision/Rationale**: The Hugging Face mirror provides programmatic access to the required Sleep‑EDF recordings while satisfying the “Verified datasets” rule. Because the dataset’s wake segments are short, we enforce a ≥ 2 min wake filter and adjust the required subject count to N ≥ 30. This ensures a feasible, reproducible analysis while being transparent about the methodological limitation.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction (family‑wise α = 0.05).  
- **Power**: Minimum **N ≥ 30** subjects enforced (FR‑010).  
- **Causal Inference**: Observational only; all statements are correlational (Constitution Principle VII).  
- **Collinearity**: Global VIF computed across subjects; high VIF reported but not interpreted as independent effects.  
- **Missing Sleep Stages**: Omit missing stage‑subject pairs from correlation (edge‑case handling).  
- **Data Corruption**: Corrupted EDF files are logged, skipped, and checksum‑verified (FR‑001).  
- **Temporal Confounding**: If waking and sleep recordings are from the same night, the report flags this limitation (FR‑011).  

## Limitations
- **Wake Duration**: Even after filtering, the remaining wake segments may still be relatively brief, potentially affecting the stability of centrality estimates. This is explicitly acknowledged in the report.  
- **Computational Load**: ICA on full‑length recordings can be time‑consuming on 2 CPU cores; processing is performed subject‑by‑subject to stay within RAM limits.  
- **Dataset Availability**: We rely on the Hugging Face mirror; if it becomes unavailable, a new open EEG sleep dataset will need to be selected.  

## Constitution Check
- **I. Reproducibility** – All steps are scripted, seeds pinned, and dataset fetched from a fixed URL.  
- **II. Verified Accuracy** – No external citations beyond the verified dataset URL.  
- **III. Data Hygiene** – Checksums recorded; transformations write new files.  
- **IV. Single Source of Truth** – Every figure/table derives from `SubjectMetrics.csv` or `analysis_results.json`.  
- **V. Versioning** – Artifact hashes updated automatically by the pipeline.  
- **VI. Signal‑Processing Transparency** – Parameters stored in `code/config.yaml`.  
- **VII. Statistical Rigor** – Bonferroni correction, normality testing, VIF diagnostics, and clear limitation statements are all implemented.
