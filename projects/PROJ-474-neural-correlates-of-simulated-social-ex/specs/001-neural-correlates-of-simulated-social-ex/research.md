# Research: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Research Question
Does acute simulated social exclusion (Cyberball) modulate functional connectivity dynamics within the Default Mode Network (DMN), specifically altering the signed mean correlation among PCC, mPFC, and bilateral angular gyrus between Inclusion and Exclusion conditions?

## Dataset Strategy

Only verified datasets listed in the project’s “# Verified datasets” block may be used. The required Cyberball dataset (`ds000030`) is **not** present, making the primary analysis infeasible under the verification policy.

| Dataset | Intended Use | Verified Source URL | Status |
|---|---|---|---|
| ds000030 (Cyberball) | Primary fMRI data (Inclusion/Exclusion) | **Not in verified block** | **Critical Gap – study blocked** |
| clane9/openneuro-fslr64k | Structural/functional test data (fallback) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet | **Unsuitable** – lacks Cyberball event markers |

**Conclusion**: Without a verified Cyberball source, the pipeline will terminate with `ERR_DATA_UNVERIFIED`. No alternative open dataset in the verified block matches the required task design.

## Methodology

### 1. Data Ingestion & Quality Control (FR‑001, FR‑002, FR‑010, FR‑013)
- **Download**: Attempt to fetch `ds000030` from the verified block; on failure, raise `ERR_DATA_UNVERIFIED`.  
- **Motion QC**: Compute mean framewise displacement (FD) per subject; exclude if **mean FD > 0.2 mm** (stricter than constitutional 3 mm).  
- **Event Verification**: Parse `events.tsv`; abort with error `101897695` if either “Inclusion” or “Exclusion” markers are missing.  
- **Retry Logic**: Up to three attempts with exponential backoff (1 s → 2 s → 4 s); final failure emits `ERR_DATA_UNAVAILABLE`.

### 2. ROI Extraction (FR‑003)
- Apply Harvard‑Oxford cortical atlas masks to pre‑processed, motion‑corrected NIfTI images.  
- Extract mean BOLD time‑series for PCC, mPFC, left angular gyrus, right angular gyrus.  
- If any ROI fails for a subject, flag the subject as excluded (FR‑014).

### 3. Connectivity Computation (FR‑004, FR‑005, FR‑011, FR‑018)
- **Static**: Pearson correlation among the three ROI pairs for each condition.  
- **Strength Metric**: Average the three signed correlation coefficients → “connectivity strength”.  
- **Dynamic**: Sliding‑window (30 s window, 5 s step) Pearson correlations; compute window‑wise strength series per condition.  
- Store all matrices and series in `data/processed/`.

### 4. Statistical Hypothesis Testing (FR‑006, FR‑016, FR‑015, FR‑017)
- **Paired permutation test**: 10 000 permutations on per‑subject strength differences (Exclusion – Inclusion).  
- **Random Seed**: Accept explicit `--seed` argument for reproducibility.  
- **Outputs**: Two‑tailed p‑value, Cohen’s d, 95 % CI, null‑distribution histogram, bar plot with CI, ROI‑wise heatmaps (PNG).  
- **Edge‑wise Tests**: Separate permutation tests for each of the three ROI edges; apply FDR correction.

### 5. Sensitivity Analysis (SC‑005)
- Re‑run the pipeline across motion thresholds (0.2 mm, 0.3 mm, 0.4 mm, 0.5 mm).  
- Plot p‑value vs. threshold curve; include in final report.

### 6. Edge Cases & Error Handling
- **Insufficient Subjects**: Halt with `101897696` if retained N < 10.  
- **Missing Condition**: Exclude subject from paired analysis.  
- **API Failure**: Exponential backoff then `ERR_DATA_UNAVAILABLE`.  
- **No Verified Source**: Immediate abort with `ERR_DATA_UNVERIFIED`.

## Compute Feasibility
All steps are CPU‑only and compatible with the GitHub Actions free tier (a modest CPU allocation and a modest amount of RAM). Streaming NIfTI access ensures memory stays within acceptable limits. The permutation test (≤ 10 000 permutations, N ≈ 10–30) completes within minutes.

## Statistical Rigor
- **Multiple Comparisons**: FDR correction for the three edge‑wise tests.  
- **Power**: Acknowledge limited power if N ≈ 10; permutation test is robust for small samples.  
- **Causal Framing**: Results reported as *associational* (no randomization).  
- **Collinearity**: Use signed mean correlation; do not claim independent edge effects.  

## Expected Deliverables (if data were available)
- `results/figures/null_distribution.png`  
- `results/figures/strength_difference_bar.png`  
- `results/figures/heatmap_inclusion.png` & `heatmap_exclusion.png`  
- `results/dynamic_summary.csv` (mean ± SD per subject)  
- `results/report.md` summarizing statistics, effect sizes, and sensitivity curves.

**Current Status**: Blocked pending a verified Cyberball dataset. No synthetic data will be generated.

---
