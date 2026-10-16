# Research: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Research Question

Do waking‑state network centrality metrics (degree, betweenness, eigenvector) predict the magnitude of neural synchrony (Phase‑Lag Index) observed during each sleep stage (N1, N2, N3, REM), after accounting for age, gender, and total sleep time?

## Methodological Approach

### 1. Data Acquisition & Preprocessing

**Source**: PhysioNet Sleep‑EDF (via Hugging Face mirror `ronaldvandenbroek/physionet-sleep-data`)  
**Verified URL**: `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip`  
**Format**: ZIP archive containing `.edf` files with EEG recordings and sleep‑stage annotations.

**Inclusion Criteria**:
- At least **2 minutes** of continuous, artifact‑free **waking** recording (required for stable resting‑state coherence estimation per standard EEG practice).
- At least 30 minutes of annotated sleep (any stage).
- Presence of the standard EEG electrode set (≥8 electrodes including frontal, central, parietal, occipital regions).

**Filtering Strategy**: Subjects not meeting the ≥ 2 min wake criterion are excluded. After filtering, we validate **N ≥ 30** subjects (FR‑010); if fewer remain, the pipeline aborts with an explicit "Insufficient Sample Size" warning. This is transparent about the power limitation.

**Preprocessing Steps** (`preprocess.py`):
1. Load `.edf` file using `pyedflib`.
2. Extract waking and sleep segments from annotations.
3. **Band‑pass filter** (0.5–45 Hz) using SciPy FIR filter (zero‑phase, order [deferred]).
4. **ICA artifact removal** (MNE `ICA`):
   - Fit ICA on the full signal.
   - Reject components with **kurtosis > 5.0** **OR** **high‑frequency power > 3 × baseline** (baseline = median power in 0.5–2 Hz band).
   - Reconstruct signal without flagged components.
5. **Epoching**: Segment into non‑overlapping 30‑second windows (per verified reference 1908.11463).
6. **Sleep‑stage labeling**: Assign each epoch the sleep stage from the annotation file.
7. **Night‑ID extraction**: Store the date/ID from the EDF header as `waking_night_id` and `sleep_night_id` for temporal confounding checks.

**Output**: `data/processed/epochs_{subj}.npz` (cleaned EEG epochs) + `metadata_{subj}.json` (covariates, night IDs, wake duration).

### 2. Waking Functional Connectivity

**Source**: Waking segment from preprocessed EEG.

**Method** (`connectivity.py`):
- Compute **magnitude‑squared coherence** for each electrode pair in **theta (4–8 Hz)** and **alpha (8–13 Hz)** bands using Welch's method (SciPy `csd` + `psd`, Hann window, [deferred] overlap).
- Resulting matrices are symmetric, values strictly between 0 and 1.
- Store as `data/processed/connectivity_{band}_{subj}.npy`.

**Rationale**: Coherence is a standard measure of functional connectivity in resting‑state EEG; theta and alpha bands are well‑established in sleep research.

### 3. Network Centrality Metrics

**Source**: Waking functional connectivity matrices (theta & alpha).

**Method** (`centrality.py`):
1. Build an undirected weighted graph from each coherence matrix (nodes = electrodes, edge weights = coherence values).
2. Compute three centrality measures via NetworkX:
   - **Degree centrality**: Sum of edge weights incident to a node.
   - **Betweenness centrality**: Fraction of shortest paths passing through a node (weighted).
   - **Eigenvector centrality**: Influence proportional to the influence of neighbors.
3. **Aggregate to per‑subject mean**: For each metric, compute the mean across all nodes (FR‑004).
4. Store as `data/processed/centrality_{subj}.json` (one row per subject with three aggregated values).

**Rationale**: Centrality metrics quantify the importance of nodes in a network; aggregating to per‑subject means provides a single predictor per metric for correlation analysis.

### 4. Sleep‑Stage Neural Synchrony

**Source**: Sleep epochs from preprocessed EEG.

**Method** (`pli.py`):
1. For each 30‑second epoch, compute **Phase‑Lag Index (PLI)** across all electrode pairs (MNE `phase_lag_index`).
2. Aggregate to **mean global PLI** per stage per subject (float ∈ [0, 1]).
3. Store as `data/processed/pli_{stage}_{subj}.npy`.

**Rationale**: PLI is a robust measure of phase synchronization that is less sensitive to volume conduction than coherence; it directly quantifies neural synchrony during sleep.

### 5. Aggregation & Validation

**Method** (`aggregate.py`):
- Consolidate all per‑subject centrality means and per‑stage mean PLIs into a single `SubjectMetrics.csv`.
- Include covariates (age, gender, total sleep time) and night IDs.
- Each row represents one subject × one sleep stage (e.g., 30 subjects × 4 stages = 120 rows).

**Validation** (`validate.py`):
- Validate `SubjectMetrics.csv` against `contracts/dataset.schema.yaml` (FR‑013).
- Check for missing values, out‑of‑range values, and schema compliance.

### 6. Collinearity Diagnostics

**Method** (`vif.py`):
- Compute **global Variance Inflation Factor (VIF)** across all subjects for the three centrality predictors (degree, betweenness, eigenvector) using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
- Report VIF values; flag any global VIF > 5.0 (FR‑009).

**Rationale**: VIF detects collinearity among predictors. High VIF indicates that centrality metrics are not independent; we report this but do NOT claim independent predictive effects.

### 7. Sample‑Size Validation

**Method** (`analysis.py`, validation step):
- After filtering for ≥ 2 min wake, count subjects with both valid waking centrality and sleep‑stage PLI.
- If **N < 30**, abort analysis and emit "Insufficient Sample Size" warning (FR‑010).

### 8. Normality Testing & Correlation Method Selection

**Method** (`analysis.py`):
- For each centrality‑PLI pair, perform **Shapiro‑Wilk test** on both vectors (SciPy `shapiro`).
- If *p* ≥ 0.05 for both → use **Pearson**; else → **Spearman** (FR‑012).

**Rationale**: Pearson assumes normality; Spearman is robust to deviations. This adaptive approach respects the data distribution.

### 9. Covariate Adjustment & Partial Correlation

**Method** (`analysis.py`):
- Compute **partial correlations** controlling for age, gender, and total sleep time using `statsmodels.stats.outliers_influence.partial_correlation`.
- If covariate data are missing for a subject, fall back to bivariate correlation and flag in the report.

**Rationale**: Age, gender, and sleep duration are known correlates of both network structure and sleep physiology; controlling for them isolates the centrality–synchrony relationship.

### 10. Correlation Analysis

**Method** (`analysis.py`):
- For each combination of centrality metric, sleep stage, and frequency band:
  - Compute correlation coefficient (Pearson, Spearman, or partial) and raw *p*‑value.
  - Store results: metric, stage, band, coefficient, raw *p*, method.
- **Total tests**: 3 centrality metrics × 5 sleep stages × 2 bands = **30 tests** (FR‑006).

**Rationale**: This exhaustive analysis tests the hypothesis across all sleep stages and frequency bands, providing a comprehensive view of centrality–synchrony associations.

### 11. Multiple‑Comparison Control

**Method** (`analysis.py`):
- Apply **Bonferroni correction** across all 30 tests: `p_corrected = min(p_raw × 30, 1.0)` (FR‑007).
- Family‑wise error rate controlled at α = 0.05.

**Rationale**: Bonferroni is conservative but appropriate for exploratory analyses; it controls the probability of any false positive across all tests.

### 12. Reporting

**Method** (`report.py`):
- Produce `data/results/analysis_results.json` containing all results (metric, stage, band, coefficient, raw *p*, corrected *p*, significance flag, method, global VIF flag) (FR‑008).
- Produce `report.md` (Markdown):
  - Summary of dataset and filtering.
  - Table of all results, highlighting significant findings (`p_corrected < 0.05`).
  - **Confounding Limitation** section: If any subject's `waking_night_id == sleep_night_id`, note that same‑night recordings may introduce confounds (FR‑011).
  - **VIF Diagnostics** section: Report global VIF values and flag collinearity if VIF > 5.0.
  - **Wake Duration Limitation** section: Acknowledge that enforcing ≥ 2 min wake may reduce sample size and that short wake segments limit centrality stability.
  - **Causal Inference Disclaimer**: "This is an observational analysis; all reported correlations are associational and do not imply causation."

## Dataset Strategy

| Dataset | Description | Verified URL | Fit Verification |
|---------|-------------|--------------|------------------|
| **PhysioNet Sleep‑EDF (Hugging Face mirror)** | EEG recordings with sleep‑stage annotations and pre‑sleep wake periods. | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` | Contains required electrodes, sleep stages, and EEG data. **Wake duration is limited** (typically 2–5 min); mitigated by ≥ 2 min filtering and explicit limitation note. |

**Decision/Rationale**: The Hugging Face mirror provides programmatic access to the required Sleep‑EDF recordings, satisfying the "Verified datasets" rule and the open‑data constraint. Because wake segments are inherently short in this dataset, we enforce a ≥ 2 min wake filter and validate N ≥ 30 subjects. If insufficient subjects meet the filter, we abort rather than fabricate or synthesize data. This approach is honest about the methodological limitation while preserving reproducibility and scientific rigor.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction (family‑wise α = 0.05) across 30 tests.
- **Power**: Minimum **N ≥ 30** subjects enforced. After Bonferroni adjustment, per‑test α ≈ 0.0017; effect sizes will be reported to contextualize practical significance.
- **Causal Inference**: Observational only; all statements are correlational (Constitution Principle VII).
- **Collinearity**: Global VIF computed across subjects; high VIF reported but not interpreted as independent effects.
- **Missing Sleep Stages**: Omit missing stage‑subject pairs from correlation (edge‑case handling).
- **Data Corruption**: Corrupted EDF files are logged, skipped, and checksum‑verified (FR‑001).
- **Temporal Confounding**: If waking and sleep recordings are from the same night, the report flags this limitation (FR‑011).
- **Normality**: Shapiro‑Wilk test guides Pearson vs. Spearman selection (FR‑012).
- **Covariate Adjustment**: Partial correlations control for age, gender, and total sleep time.

## Limitations

1. **Wake Duration**: Even after filtering for ≥ 2 min wake, the remaining segments may be relatively brief, potentially affecting the stability of centrality estimates. This is explicitly acknowledged in the report.
2. **Sample Size Reduction**: The ≥ 2 min wake filter may reduce the usable subject pool, limiting statistical power. The final report will state the number of subjects excluded and retained.
3. **Temporal Confounding**: If waking and sleep recordings are from the same night, circadian state and fatigue may confound the centrality–synchrony relationship. This is flagged in the report.
4. **Collinearity**: If global VIF is high, centrality metrics are not independent; the report will note that joint effects should be interpreted jointly, not as separate predictors.
5. **Dataset Availability**: We rely on the Hugging Face mirror; if it becomes unavailable, a new open EEG sleep dataset will need to be selected (e.g., OpenNeuro, Zenodo).

## Constitution Check

✓ **I. Reproducibility** – All steps are scripted, random seeds pinned in `code/config.yaml`, and dataset fetched from a fixed verified URL with checksum validation.  
✓ **II. Verified Accuracy** – All external citations verified (e.g., 30 s epoch length from 1908.11463).  
✓ **III. Data Hygiene** – Checksums recorded; transformations write new files with documented derivation.  
✓ **IV. Single Source of Truth** – Every figure/table derives from `SubjectMetrics.csv` or `analysis_results.json`.  
✓ **V. Versioning** – Artifact hashes updated automatically.  
✓ **VI. Signal‑Processing Transparency** – Parameters stored in `code/config.yaml` with explicit version pins.  
✓ **VII. Statistical Rigor** – Bonferroni correction, normality testing, VIF diagnostics, partial correlations, and causal‑inference framing all in place.

---
