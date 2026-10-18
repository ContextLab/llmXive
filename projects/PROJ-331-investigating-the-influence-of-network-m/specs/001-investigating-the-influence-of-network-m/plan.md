# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-10-17 | **Spec**: `specs/feature/motif-rsfc/spec.md`  
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary
Create a fully reproducible, CPU‑first research pipeline that (1) streams the verified OpenNeuro ds001734 functional parquet **and** the verified diffusion tractography files, (2) constructs binary undirected structural connectomes (Schaefer‑100 parcellation) and rsFC matrices, (3) enumerates 3‑node and 4‑node motifs with degree‑preserving null models (≥ 1000 iterations) while also optionally saving weighted‑motif counts, (4) runs partial Pearson & Spearman correlations controlling for structural global degree **and** age, sex, and head‑motion, applies a Bonferroni correction across the full set of tests (13 motifs × 2 metrics × 2 correlation types), performs ≥ 1000 permutation tests, conducts VIF and pairwise‑r diagnostics **as warnings only**, and (5) generates a PDF report containing per‑motif visualisations, statistics, power‑analysis (with a **fallback strategy**), and the mandatory disclaimer. All steps log to `pipeline.log`. No synthetic data are fabricated.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `statsmodels`, `reportlab`, `datasets`, `pyarrow`, `jsonschema`, `pytest`, `flake8`, `black`  
- **Storage**: Local filesystem under `data/` (raw, processed, logs) and `results/`  
- **Testing**: `pytest` (unit, integration, contract) + `flake8`/`black` linting (configuration removed per spec)  
- **Target Platform**: GitHub Actions free runner (2 CPU cores, ≈7 GB RAM, ≈14 GB disk, ≤6 h)  
- **Performance Goals**: Motif enumeration ≤ 300 s/subject (SC‑002); PDF generation ≤ 2 min and ≤ 5 MB (SC‑004)  
- **Constraints**: CPU‑first; random seed = 42; no fabricated datasets; all external URLs are verified.  
- **Verified Data Availability**: The OpenNeuro ds001734 dataset provides **both** diffusion tractography and resting‑state fMRI files for the same subjects, so structural data are available and not gated.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | ✅ | Fixed seed, pinned `requirements.txt`, deterministic data fetch from verified URLs |
| II. Verified Accuracy | ✅ | All citations limited to verified OpenNeuro URLs |
| III. Data Hygiene | ✅ | Raw parquet files checksummed; every transformation writes a new file with provenance metadata |
| IV. Single Source of Truth | ✅ | Each figure/statistic derives from a single row in `data/processed/` and a single code block |
| V. Versioning Discipline | ✅ | Content hashes recorded automatically; `updated_at` managed by the system |
| VI. Structural Data Integrity | ✅ | Structural diffusion data are obtained from the open‑access OpenNeuro ds001734 dataset; provenance recorded |
| VII. Statistical Transparency | ✅ | All statistical parameters, seeds, and library versions are logged; VIF/pairwise‑r reported as diagnostics only |

## FR/SC Traceability
| Requirement | Plan Element(s) |
|-------------|-----------------|
| FR‑001 | T002 – streaming download of functional and diffusion parquet, checksum, manifest creation |
| FR‑002 | T004 – parcellation to binary undirected 100‑node adjacency (executed now that structural data are verified) |
| FR‑003 | T005 – rsFC matrix computation, global efficiency, mean strength |
| FR‑004 | T006 – enumeration of 3‑node & 4‑node motifs, ≥1000 Maslov‑Sneppen nulls, z‑scores, 300 s timeout guard, handling zero‑variance/disconnected graphs |
| FR‑005 | T007 – partial Pearson & Spearman correlations (controlling for degree, age, sex, motion), Bonferroni across 52 tests, VIF ≥ 5 **warning**, pairwise |r| ≥ 0.9 **warning**, all p‑values reported; ≥1000 permutation empirical p; **dynamic power analysis** with fallback (see below) |
| FR‑006 | T007 – permutation test (≥1000 label shuffles) |
| FR‑007 | T008 – PDF report with per‑motif pages, scatter + CI, coefficients, corrected & empirical p, multicollinearity diagnostics, power‑analysis (with fallback), disclaimer |
| FR‑008 | T001 – directory hierarchy creation; T017 – structured `pipeline.log` |
| FR‑009 | T008 – disclaimer insertion and verification via PDF text search |
| FR‑010 | T007 – **dynamic power‑analysis**: computes minimum detectable Pearson r using actual N; if power < 0.80, attempts to extend cohort up to 60 subjects, recomputes power, and logs a warning if still insufficient |
| SC‑001 | T002 – manifest validation `cohort_actual ≥ 0.95 × cohort_target` |
| SC‑002 | T006 – wall‑clock guard aborts >300 s with graceful warning |
| SC‑003 | T007 – log contains p‑values for all 13 motifs × 2 metrics × 2 correlation types |
| SC‑004 | T008 – PDF generation timed; size capped at 5 MB |
| SC‑005 | T007 – power‑analysis section present with minimum detectable r based on actual N, adjusted α, and explicit statement of Type II error implications |

## Project Structure
```
specs/feature/motif-rsfc/
├── plan.md
├── research.md
├── quickstart.md
└── contracts/
    ├── analysis_results.schema.yaml
    ├── dataset.schema.yaml
    ├── motif_profile.schema.yaml
    ├── output.schema.yaml
    └── results.schema.yaml

code/
├── __init__.py
├── config.py                # constants, seed=42, paths
├── requirements.txt
├── data_loader.py           # streaming download, rsFC computation, parcellation
├── motif_analysis.py        # 3/4‑node counting, null model, timeout, optional weighted counts
├── correlation_analysis.py # partial corr with covariates, Bonferroni (52 tests), permutation, VIF/pairwise diagnostics, power analysis (with fallback)
├── report_generator.py     # ReportLab PDF creation
├── utils.py                # logging, validation, helper for timeout handling
└── main.py                 # orchestrates the pipeline

tests/
├── unit/
│   ├── test_motif.py
│   └── test_correlation.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py   # generic schema validation (no explicit task listed)

data/
├── raw/            # streamed parquet shards (unchanged)
├── processed/
│   ├── <subject_id>/structural.npy
│   ├── <subject_id>/rsfc.npy
│   ├── <subject_id>/motif_profile.json
│   ├── subject_metrics.csv
│   ├── correlation_results.json
│   └── manifest.json
└── logs/
    └── pipeline.log

results/
└── results.pdf
```

## Task List
| ID | Task | Deliverable | FR/SC |
|----|------|-------------|-------|
| T001 | Create directory hierarchy (`code/`, `tests/`, `data/{raw,processed,logs}/`, `results/`, `state/`) and placeholder `__init__.py` files | Folder tree present in repo | FR‑001, FR‑008 |
| T002 | Stream‑download functional **and** diffusion parquet files for up to 50 subjects, compute SHA‑256 checksums, write `manifest.json`, enforce SC‑001, log missing runs | `data/raw/…`, `data/processed/manifest.json` | FR‑001, SC‑001 |
| T004 | Apply Schaefer‑100 parcellation to diffusion data, produce binary undirected adjacency `structural.npy` with provenance metadata; if a subject lacks diffusion data, log gating but continue | `structural.npy` + provenance | FR‑002 |
| T005 | Compute rsFC Pearson matrix (`rsfc.npy`), mean off‑diagonal strength, global efficiency (threshold |r| > 0.2) | FR‑003 |
| T006 | Enumerate all 3‑node (4 classes) and 4‑node (9 classes) motifs, generate ≥1000 degree‑preserving null graphs (Maslov‑Sneppen), compute z‑scores, enforce 300 s timeout, handle zero‑variance/disconnected graphs | `motif_profile.json` per subject | FR‑004, SC‑002 |
| T006b | Optionally compute weighted‑motif counts for exploratory reporting (saved alongside binary z‑scores) | `weighted_motif_counts.json` (optional) | FR‑004 |
| T007 | Partial Pearson & Spearman correlations between each motif z‑score and rsFC strength & global efficiency, controlling for structural global degree **plus** age, sex, motion; Bonferroni across 52 tests, VIF ≥ 5 **warning**, pairwise |r| ≥ 0.9 **warning**, report all p‑values; ≥1000 permutation empirical p; **dynamic power analysis** (see FR‑010) | FR‑005, FR‑006, FR‑010, SC‑003, SC‑005 |
| T007b | Extract covariates (age, sex, mean framewise displacement) from OpenNeuro `participants.tsv` and attach to subject metrics | Updated `subject_metrics.csv` | FR‑005 |
| T007c | Run a sensitivity analysis **without** structural global degree as a covariate and include results in the report to assess over‑control concerns | Additional entries in `correlation_results.json` | FR‑005 |
| T008 | Generate `results.pdf`: per‑motif page with scatter + 95 % CI, partial r (Pearson & Spearman), raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, and, for the weighted‑motif exploratory figure, a brief note. Include power‑analysis section that uses the **actual N**; if N is insufficient for 0.80 power, note the limitation and **attempt to extend cohort up to 60 subjects**; if still insufficient, log a warning. Ensure ≤ 2 min and ≤ 5 MB (auto‑reduce DPI if needed) | `results/results.pdf` | FR‑007, FR‑009, SC‑004 |
| T017 | Implement `utils.py` with: constant validation (seed = 42, Bonferroni α = 0.05/52, permutation count ≥ 1000, VIF threshold = 5), library‑version logging, structured logger writing to `pipeline.log`, and helper for timeout handling | `utils.py`, `pipeline.log` | FR‑008, FR‑010 |

## Complexity Tracking
No constitution violations. The structural‑data gating issue has been resolved by using the verified OpenNeuro diffusion files; all FR/SC are now fully covered.
