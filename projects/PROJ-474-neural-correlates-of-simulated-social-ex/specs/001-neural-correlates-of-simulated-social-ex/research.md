# Research: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Research Question
Does acute simulated social exclusion (Cyberball) modulate functional connectivity dynamics within the Default Mode Network (DMN), specifically altering the **mean absolute correlation** among PCC, mPFC, and bilateral Angular Gyrus between Inclusion and Exclusion conditions?

## Dataset Strategy

Only verified datasets listed in the project’s “# Verified datasets” block may be used. The required Cyberball dataset (`ds000030`) is **verified** and available at:

- **ds000030 (Cyberball)** – https://openneuro.org/datasets/ds000030 – Provides pre‑processed fMRI with clear Inclusion/Exclusion event markers.

No alternative open dataset matches the required task design; thus the analysis proceeds with this dataset.

## Methodology

### 1. Data Ingestion & Quality Control (FR‑001, FR‑002, FR‑010, FR‑013)
- **Download**: Fetch `ds000030` via the OpenNeuro API using the verified URL.  
- **Motion QC**: Compute mean framewise displacement (FD) per subject; exclude any subject with **mean FD > 0.2 mm** (stricter than the constitutional 3 mm limit).  
- **Event Verification**: Parse `events.tsv`; abort with error `101897695` if either “Inclusion” or “Exclusion” markers are missing.  
- **Retry Logic**: Up to three attempts with exponential backoff (1 s → 2 s → 4 s); final failure emits `ERR_DATA_UNAVAILABLE`.

### 2. ROI Extraction (FR‑003)
- Apply Harvard‑Oxford DMN masks for PCC, mPFC, and a **combined bilateral Angular Gyrus** to the pre‑processed data and extract mean BOLD time‑series for each ROI and condition.  
- If any ROI extraction fails for a subject, that subject is excluded from all downstream analyses (FR‑014).

### 3. Connectivity Computation (FR‑004, FR‑005, FR‑018)
- **Static**: Compute Pearson correlation matrices among the three ROIs separately for Inclusion and Exclusion.  
- **Strength Metric**: Average the **absolute** Pearson correlations across the three unique ROI‑pair edges → “connectivity strength” per condition.  
- **Dynamic**: Sliding‑window (30 s window, 5 s step) Pearson correlations; compute a **mean absolute** strength series per window and condition. No multiple‑comparison correction is applied across windows; series are reported descriptively with per‑subject mean ± SD.

### 4. Statistical Hypothesis Testing (FR‑006, FR‑016, FR‑015, FR‑017)
- **Paired permutation test**: 10 000 permutations on per‑subject strength differences (Exclusion – Inclusion).  
- **Random Seed**: Accept explicit `--seed` argument for reproducibility.  
- **Outputs**: Two‑tailed p‑value, Cohen’s d, 95 % CI, null‑distribution histogram, bar plot with CI, ROI‑wise heatmaps for Inclusion and Exclusion (PNG).  

### 5. Sensitivity Analysis (SC‑006)
- Re‑run the pipeline across motion thresholds (0.2 mm, 0.3 mm, 0.4 mm, 0.5 mm). Plot p‑value vs. threshold; include in the final report.

### 6. Edge Cases & Error Handling
- **Insufficient Subjects**: Halt with `101897696` if retained N < 10 (FR‑009).  
- **Missing Condition**: Exclude subject from paired analysis (FR‑011).  
- **API Failure**: Exponential backoff then `ERR_DATA_UNAVAILABLE` (FR‑013).  
- **No Verified Source**: Immediate abort with `ERR_DATA_UNVERIFIED` (resolved – source now verified).  

## Compute Feasibility
All steps run on CPU‑only CI (2 CPU, ~7 GB RAM). Streaming NIfTI ensures memory stays within limits. Permutation test completes within minutes.

## Statistical Rigor
- **Multiple Comparisons**: No FDR correction across sliding‑window time points (temporal autocorrelation violates independence). Edge‑wise tests are not performed; the composite absolute‑strength metric is the primary focus.  
- **Power**: With a minimum retained N ≈ 10 the study can reliably detect large effects (Cohen’s d ≈ 0.8) at α = 0.05; smaller effects may be under‑powered and are reported as a limitation (SC‑007).  
- **Causal Framing**: Results presented as *associational*.  
- **Collinearity**: Using a single composite **mean absolute** strength metric respects the high inter‑ROI correlation structure.  

## Expected Deliverables (if data are available)
- `results/figures/null_distribution.png`  
- `results/figures/strength_difference_bar.png`  
- `results/figures/heatmap_inclusion.png` & `heatmap_exclusion.png`  
- `results/dynamic_summary.csv` (mean ± SD of dynamic series per subject)  
- `results/report.md` summarizing statistics, effect sizes, and sensitivity curves.

**Current Status**: Ready to run now that a verified Cyberball dataset URL is provided.

---

