# Implementation Plan: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Branch**: `001-neural-correlates-of-simulated-social-ex` | **Date**: 2026-10-18 | **Spec**: `specs/001-neural-correlates-of-simulated-social-ex/spec.md`  
**Input**: Feature specification from `/specs/001-neural-correlates-of-simulated-social-ex/spec.md`

## Summary
The project will test whether acute simulated social exclusion (Cyberball) modulates functional connectivity within the Default Mode Network (DMN). The pipeline will:

1. Download the verified OpenNeuro Cyberball dataset (`ds000030`).
2. Perform motion QC (exclude subjects with mean FD > 0.2 mm) and verify presence of “Inclusion” and “Exclusion” event markers.
3. Extract mean BOLD time‑series from **three** DMN ROIs (PCC, mPFC, bilateral Angular Gyrus) using the Harvard‑Oxford atlas (the angular mask is combined bilateral to yield a single ROI).
4. Compute Pearson correlation matrices **separately** for Inclusion and Exclusion conditions.
5. Derive a “connectivity strength” metric per condition by **averaging the absolute Pearson correlations** across the three unique ROI‑pair edges. The primary outcome is the **difference** (Exclusion – Inclusion) in connectivity strength.
6. Perform sliding‑window (30 s window, 5 s step) correlation analysis, producing a time‑resolved connectivity‑strength series for each condition (no multiple‑comparison correction across windows; series are reported descriptively).
7. Run a non‑parametric paired permutation test (using a sufficiently large number of permutations) on the per‑subject strength differences (Exclusion – Inclusion), reporting a two‑tailed p‑value, Cohen’s d effect size, and 95 % CI.
8. Generate required visualizations: null‑distribution histogram, bar plot of mean difference with 95 % CI, and ROI‑wise correlation‑matrix heatmaps for each condition.
9. Conduct a sensitivity analysis over motion thresholds (0.2 mm, 0.3 mm, 0.4 mm, 0.5 mm).

All steps run on a CPU‑only GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scipy`, `nilearn`, `matplotlib`, `seaborn`, `tqdm`, `jsonschema`  
- **Storage**: `data/` for raw/processed files; `results/` for figures and reports  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`)  
- **Target Platform**: Linux CI runner (several CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Constraints**: CPU‑first; motion threshold 0.2 mm; minimum retained subjects ≥ 10  

## Constitution Check
| Principle | Reference in Plan | Compliance |
|-----------|-------------------|------------|
| **I. Reproducibility** | Random seeds pinned (`--seed` flag); `requirements.txt` version‑locked; deterministic streaming download. | PASS |
| **II. Verified Accuracy** | Dataset URL for `ds000030` drawn from the verified‑datasets block. | PASS |
| **III. Data Hygiene** | Raw files immutable under `data/raw/`; checksums recorded; derived artifacts written to new files (`data/processed/`). | PASS |
| **IV. Single Source of Truth** | All statistics derived from `data/processed/` Parquet files; figures reference those files only. | PASS |
| **V. Versioning Discipline** | Artifact hashes recorded in `state/…yaml`; any change updates `updated_at`. | PASS |
| **VI. fMRI Motion Artifact Exclusion** | Exclusion rule uses mean FD ≤ 0.2 mm (stricter than the 3 mm constitutional limit). | PASS |
| **VII. State‑Dependent Connectivity Quantification** | Connectivity strength defined as **mean absolute correlation** across the three DMN edges (preserves sign requirement of FR‑005). | PASS |

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **II. Verified Accuracy** | Required a verified URL for `ds000030`. | Using an unverified source would breach the constitution. |

## Methodology Mapping to Functional Requirements

| FR | Pipeline Phase | Description |
|----|----------------|-------------|
| FR‑001 | `data_loader.py` | Download pre‑processed fMRI from a **verified** source (`ds000030`). |
| FR‑002 | `qc.py` | Compute mean FD; exclude subjects with > 0.2 mm. |
| FR‑003 | `roi_extractor.py` | Extract mean BOLD from **three** DMN ROIs (PCC, mPFC, bilateral Angular Gyrus) using Harvard‑Oxford masks. |
| FR‑004 | `connectivity.py` | Compute Pearson correlation matrices per condition (Inclusion, Exclusion). |
| FR‑005 | `connectivity.py` | Derive **mean absolute** connectivity strength across the three ROI‑pair edges; primary outcome is the difference (Exclusion – Inclusion). |
| FR‑006 | `stats.py` | Paired permutation test (10 000 permutations) on strength differences. |
| FR‑009 | `main.py` | Halt with error `101897696` if retained subjects < 10. |
| FR‑010 | `data_loader.py` | Abort with error `101897695` if either Inclusion or Exclusion markers are missing. |
| FR‑011 | `qc.py` | Exclude any subject lacking valid time‑series for **any** required ROI. |
| FR‑013 | `data_loader.py` | Exponential backoff (1 s → 2 s → 4 s) up to 3 attempts; final failure emits `ERR_DATA_UNAVAILABLE`. |
| FR‑014 | `roi_extractor.py` | Subject excluded from downstream analyses if any ROI extraction fails. |
| FR‑015 | `viz.py` | Generate null‑distribution histogram and bar plot with 95 % CI (PNG). |
| FR‑016 | `stats.py` | Accept explicit `--seed` argument for reproducibility. |
| FR‑017 | `viz.py` | Produce ROI‑wise correlation‑matrix heatmaps for Inclusion and Exclusion (PNG). |
| FR‑018 | `connectivity.py` | Sliding‑window (30 s, 5 s step) series per condition; report mean ± SD per subject (no FDR across windows). |

## Success Criteria Mapping
| SC | Verification |
|----|--------------|
| SC‑001 | Compute retention rate after QC; assert ≥ 80 % (checked in `qc.py`). |
| SC‑002 | Run permutation test 5 times with different seeds; compute std ≤ 0.01 (automated in `stats_test.py`). |
| SC‑003 | Verify existence and correct labeling of histogram & bar‑plot PNGs (unit test). |
| SC‑004 | Ensure per‑subject strength metrics and cohort difference saved (CSV) and N ≥ 10. |
| SC‑005 | Verify heatmaps exist, include colorbars & axis labels (visual test). |
| SC‑006 | Compute mean ± SD of dynamic series per subject; store in `results/dynamic_summary.csv`. |
| SC‑007 | **Power note**: With N≈10 the analysis can reliably detect large effects (Cohen’s d≈0.8) at α = 0.05; smaller effects may be under‑powered and are reported as a limitation. |
| SC‑008 | **Dynamic multiple‑comparison control**: No formal correction across windows due to temporal autocorrelation; series are reported descriptively. |

## Compute Feasibility
All steps are CPU‑tractable. Streaming NIfTI via `nibabel` keeps RAM < 7 GB. Permutation test (≤ 10 000 permutations, N ≈ 10–30) finishes within minutes on 2 CPU cores. No GPU required.

## Statistical Rigor
- **Multiple Comparisons**: FDR applied only to the three edge‑wise correlation values *if* edge‑wise reporting is desired (optional); not applied across sliding‑window time points.
- **Power**: Minimum retained N ≈ 10 gives [deferred] power to detect large effects (Cohen’s d≈0.8); this limitation is explicitly acknowledged (SC‑007).
- **Causal Claims**: Results framed as *associational* (no randomization).  
- **Collinearity**: DMN ROIs are inherently correlated; we report a single composite **mean absolute** strength metric rather than interpreting individual edges independently.  
- **Effect Size**: Cohen’s d computed from observed difference distribution.  

## Dataset Availability & Feasibility
The required Cyberball dataset `ds000030` is **verified** (URL: https://openneuro.org/datasets/ds000030) and can be programmatically downloaded via the OpenNeuro API. If the API is unreachable, the pipeline retries up to three times with exponential backoff before raising `ERR_DATA_UNAVAILABLE`. All other resources are open‑source and CPU‑compatible.

---

