# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-10-25 | **Spec**: `specs/001-quantifying-correlations-between-solar-w/spec.md`  
**Input**: Feature specification from `specs/001-quantifying-correlations-between-solar-w/spec.md`

## Summary
The project delivers a reproducible end‑to‑end pipeline that  

1. **Downloads** ACE solar‑wind composition (proton density `N_p`, temperature `T_p`, helium abundance `He2+_ratio`) and NOAA/Kyoto geomagnetic indices (hourly `Kp`, `Dst`) for any user‑specified date range.  
2. **Validates** the presence of all required variables (FR‑006, SC‑002).  
3. **Aligns** both sources to a common 1‑hour UTC grid, linearly interpolating gaps ≤ 6 h and logging any interpolated interval (FR‑002, SC‑004, VI). **Sensitivity analysis**: after Phase 2 we run the full correlation pipeline twice – once with interpolated rows included (primary) and once with all rows where `interpolated_flag=True` dropped – storing the alternate results as `results/full_correlations_nointerp.csv`. Discrepancies trigger a warning in the log.  
4. **Full‑Dataset Correlation** (FR‑003, FR‑010) – for each of the 30 composition‑index‑lag combos:  
   - Estimate lag‑1 autocorrelations of each series → effective sample size `N_eff` (Pyper & Peterman).  
   - Compute Pearson *r* and raw p‑value via t‑distribution with `df = N_eff‑2`.  
   - **Spearman ρ** raw p‑value via a **block‑permutation test with 10 000 permutations** (as required by FR‑010).  
     *Block length* is set to `ceil(1 / (1‑r1))`, where `r1` is the lag‑1 autocorrelation of the series, thereby preserving temporal dependence.  
   - Apply **Bonferroni** correction across all 30 tests (FR‑004).  
   - Flag significance (`p_bonf < 0.05`).  
   - Record `evaluability_flag` (≥ 30 valid observations **and** `N_eff ≥ 30`).  
   - **Runtime estimate**: the 10 000‑permutation block test on ~200 k rows is expected to take ≈ 1.5 h on the CI runner, keeping the total pipeline well under the 6 h limit.  
5. **Optional Storm‑Filtered Correlation** – same routine as Phase 3 but first filter `Dst < -50 nT`. A **disclaimer** about collider bias is logged and the results are written to `results/storm_correlations.csv`. These outputs are **exploratory only** and are **not** used to support the primary scientific claim (FR‑003).  
6. **Validation (Held‑out 2018‑2020)** – re‑run Phase 3 on the 2018‑2020 window (same pipeline, same corrections). Produce `results/validation_correlations.csv`. Generate `results/validation_report.md` summarising any pair with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05 (FR‑009, SC‑003).  
7. **Visualisation** – `plots.py` (FR‑008) creates per‑lag time‑series overlay PNGs and a correlation heatmap PNG for the validation period; each ≤ 5 MB.  
8. **Reporting** – Assemble the final Markdown validation report (FR‑009) and ensure all PNG artefacts satisfy FR‑008. This phase explicitly ties to FR‑008 (visual artefacts) and FR‑009 (validation report), closing the spec‑coverage gap.  

All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required (CPU‑first).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `cdasws`, `pyyaml`, `pytest` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/`, `results/`, `figures/`  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Performance Goals**: Full pipeline ≤ 5 h, ≤ 7 GB RAM, ≤ 4 GB disk for data download & processing (reduced permutation count keeps runtime ≈ 1.5 h).  

## Execution Plan (ordered; data before consumers)

| Phase | Tasks (mapped FR/SC) | Output |
|-------|----------------------|--------|
| **0 – Environment** | Install dependencies, set random seed (`np.random.seed(42)`) | `requirements.txt` |
| **1 – Fetch** | `fetch_ace.py` (FR‑001, FR‑006) – download ACE SWEPAM (`N_p`, `T_p`) and SWICS (`He2+_ratio`) via **cdasws**; `fetch_noaa.py` (FR‑001) – download hourly `Kp` and `Dst` via HTTP GET. Validate presence of all five variables; abort with clear error if any missing (SC‑002). | `data/raw/*.csv`, `checksums.json` |
| **2 – Synchronise** | `sync.py` (FR‑002, SC‑004) – reindex to 1‑h UTC grid, linear interpolation for gaps ≤ 6 h, log each interpolated interval, flag rows (`interpolated_flag`). Validate that the resulting CSV conforms to `contracts/dataset.schema.yaml`. Rows with gaps > 6 h are dropped and excluded from downstream analysis. | `data/processed/synced.csv` |
| **3 – Full‑Dataset Correlation** | `correlation.py` (FR‑003, FR‑010) – for each of the 30 composition‑index‑lag combos: <br>• Compute lag‑1 autocorrelations → `N_eff` (Pyper & Peterman). <br>• Pearson *r* & t‑based p‑value using `N_eff`. <br>• **Spearman ρ** & raw p‑value via **block‑permutation test (10 000 permutations)**; block length = `ceil(1/(1‑r1))`. <br>• Apply plain Bonferroni (FR‑004). <br>• Flag significance (`p_bonf < 0.05`). <br>• Record `evaluability_flag`. <br>**Sensitivity check**: repeat the entire correlation loop after dropping rows where `interpolated_flag=True` and store the alternate results as `results/full_correlations_nointerp.csv`. Discrepancies generate a warning. | `results/full_correlations.csv`, `results/full_correlations_nointerp.csv` |
| **4 – Optional Storm‑Filtered Correlation** | Same routine as Phase 3 but first filter `Dst < -50 nT`. Log a disclaimer about collider bias and store results in `results/storm_correlations.csv`. These outputs are **exploratory only** and are not used for the primary claim. | `results/storm_correlations.csv` |
| **5 – Validation (Held‑out 2018‑2020)** | Re‑run Phase 3 on the 2018‑2020 window (same pipeline, same corrections). Produce `results/validation_correlations.csv`. Generate `results/validation_report.md` summarising any pair with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05 (FR‑009, SC‑003). | `results/validation_*.csv`, `validation_report.md` |
| **6 – Visualisation** | `plots.py` (FR‑008) – create per‑lag time‑series overlay PNGs and a correlation heatmap PNG for the validation period; each ≤ 5 MB. | `figures/*.png` |
| **7 – Reporting** | Assemble the final Markdown validation report (FR‑009) and ensure all PNG artefacts satisfy FR‑008. | `results/validation_report.md`, `figures/` |
| **8 – Tests** | Unit tests for fetch (`test_fetch.py`), sync (`test_sync.py`), correlation (`test_correlation.py`), and schema contracts (`test_schema.py`). Integration test runs the full pipeline on a 1‑month real subset to verify end‑to‑end flow (SC‑001, SC‑004). | `tests/` |

All phases respect the compute ceiling: the synchronized CSV (~200 k rows, < 30 MB). Memory usage stays < 4 GB; total runtime is estimated **≈ 4.5 h** on the free runner (including the 10 000‑permutation block test). No GPU is required.

## Decision / Rationale
- **CPU‑first**: Classical statistics and a 10 000‑permutation block test run comfortably on 2 CPU cores; runtime fits CI limits.  
- **Full vs. Storm‑filtered**: Primary scientific claim (FR‑003) uses the full continuous series; the optional storm‑filtered branch satisfies the exploratory requirement while clearly flagged as non‑primary.  
- **Effective Sample Size** and **Block‑Permutation** guarantee valid p‑values under autocorrelation, meeting **VII. Statistical Rigor**.  
- **Interpolation sensitivity** addresses potential bias (methodology‑4b693a5d) via the dual‑run sensitivity analysis.  
- **Permutation count** set to the required 10 000 (FR‑010) with a realistic runtime estimate (data_resources-5730b465).  
- **Dataset sourcing** is transparent; lack of verified URLs is disclosed per **II. Verified Accuracy**.  
- **Reporting** explicitly references FR‑009 and FR‑008, closing the spec‑coverage gap.  

---


## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|--------------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic pipelines, checksums recorded. |
| II. Verified Accuracy | PASS (with disclosure) | No verified URLs for ACE/NOAA; canonical sources named and disclosed. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace to rows in `data/processed/synced.csv` and `results/*.csv`. |
| V. Versioning Discipline | PASS | Artifact hashes recorded; `updated_at` updated on change. |
| VI. Temporal Alignment and Lag Consistency | PASS | Single 1‑h UTC grid; all lags computed on aligned timestamps. |
| VII. Statistical Rigor and Multiple‑Comparison Control | PASS | Pearson uses Pyper & Peterman N_eff; Spearman uses block‑permutation (10 000); Bonferroni correction applied. |