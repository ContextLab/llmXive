# Implementation Plan: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Branch**: `001-predict-cognitive-flexibility-rsfc-variability`  
**Date**: 2026-10-22  
**Spec**: `specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`  
**Input**: Feature specification from `/specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`

## Summary
Build a reproducible, CPU‑only pipeline that (1) verifies the presence of required open datasets, (2) downloads and checksum‑validates them, (3) applies the Schaefer 200‑region atlas to HCP minimally preprocessed resting‑state fMRI, (4) computes sliding‑window Pearson correlations (60 s window, 1 s step) and derives edge‑wise standard deviation and Shannon entropy, (5) reduces the edge‑wise variability matrix via PCA (top 10 components), (6) validates the variability metric against a phase‑shuffled surrogate null model, (7) tests the association between the primary variability predictor (`PCA_Component_1`) and NIH Toolbox Dimensional Change Card Sort scores using linear regression with covariates and a 10 000‑permutation empirical p‑value, (8) applies FDR correction for any optional post‑hoc network tests, and (9) assembles a final CSV that conforms to `contracts/dataset.schema.yaml`. All artifacts are validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `scikit-learn`, `tqdm`, `pyyaml`, `numba` (optional for speed), `ruff` (lint) – pinned in `code/requirements.txt`.  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`).  
- **Testing**: `pytest` + contract tests in `tests/test_contracts.py`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: CPU‑only; motion exclusion (Mean FD > 0.2 mm) required (Constitution VI); sliding‑window parameters must be recorded (Constitution VII).  
- **Scale/Scope**: Up to 1 200 HCP subjects; expected usable N ≈ 800 after quality filtering.

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins exact versions; data fetched from canonical URLs listed in `research.md`. |
| II. Verified Accuracy | PASS | All external citations limited to the “Verified datasets” block; no unverified sources introduced. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded in `data/raw/checksums.json`; raw files never modified in place; derived files have distinct filenames. |
| IV. Single Source of Truth | PASS | Every figure/table traced to a row in `data/processed/final_results.csv` and a line in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`; any artifact change updates the hash automatically via platform. |
| VI. Motion Artifact Control | PASS | Mean FD included as covariate; subjects with Mean FD > 0.2 mm excluded and logged (`exclusion_log.csv`). |
| VII. Dynamic Connectivity Parameter Documentation | PASS (with justified deviation) | Default 30 s window overridden to 60 s (see Phase 4 justification). Change documented in `code/config.py` and `plan.md`. |

## Project Structure
```text
specs/001-predict-cognitive-flexibility-rsfc-variability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
code/
├── __init__.py
├── main.py                # CLI orchestrator
├── config.py              # seeds, batch sizes, window parameters
├── data/
│   ├── download.py        # FR‑001 – data fetch & checksum
│   ├── preprocess.py      # FR‑002 – Schaefer parcellation
│   └── merge.py           # merge behavioral & imaging metadata
├── features/
│   ├── connectivity.py    # FR‑003/FR‑004 – sliding‑window, SD, entropy, PCA
│   └── null_model.py      # FR‑008 – phase‑shuffled surrogate
├── analysis/
│   ├── regression.py      # FR‑005 – linear model
│   └── permutation.py     # FR‑006 – permutation test, FR‑009 FDR
├── utils/
│   ├── motion.py          # motion exclusion (VI)
│   └── plotting.py        # figures for the report
└── tests/
    ├── test_contracts.py
    ├── test_connectivity.py
    └── test_regression.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| 60 s sliding window (instead of default 30 s) | 30 s yields < 50 time points for a 200‑region correlation matrix → rank‑deficient; 60 s provides > 100 points, enabling stable estimation (Phase 4). | Keeping 30 s would produce unstable correlation matrices, violating statistical rigor. |
| PCA reduction of edge‑wise variability | Direct scalar discards network‑specific signal and reduces power; PCA retains > 80 % variance while keeping predictor dimensionality tractable for CPU execution. | Using only the mean‑SD scalar would risk a Type II error. |
| Phase‑shuffled surrogate (vs. AR(1) null) | Specification (FR‑008) explicitly requires a phase‑shuffled null; this preserves amplitude spectra while destroying temporal ordering. | An AR(1) surrogate would not meet the spec. |
| Batch processing of subjects | Full‑subject loading exceeds 7 GB RAM on CI; batching guarantees memory stays ≤ 7 GB. | Loading all subjects at once would cause OOM failures. |
| Lint step (`ruff`) added explicitly | Previous verifier rejected `code/lint_setup.py`; a dedicated lint phase with deterministic output (`data/logs/ruff.log`) ensures passable artifact. | Skipping lint would leave the failure unaddressed. |

## Implementation Phases (mapping FR/SC → tasks)

| Phase | Description | Core FR | Core SC | Primary Output (validated by contract) |
|-------|-------------|---------|---------|----------------------------------------|
| **0 – Data Availability Check** | Verify that the three verified URLs contain *both* the required fMRI time‑series and NIH DCCS scores. Write `data/gap_report.md` and abort if any variable is missing. | – | – | `data/gap_report.md` (human‑readable) |
| **1 – Raw Data Download & Integrity** | Stream download, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – | `data/raw/checksums.json` |
| **2 – Preprocessing / Parcellation** | Load minimally preprocessed HCP fMRI, apply Schaefer 200‑region atlas, extract regional mean time‑series (`.npy`). | FR‑002 | – | `data/processed/{subj}_ts.npy` |
| **3 – Motion & Quality Filtering** | Exclude subjects with Mean FD > 0.2 mm and subjects missing DCCS scores; log exclusions. | – | SC‑001 (proportion processed) | `data/processed/exclusion_log.csv` |
| **4 – Dynamic Connectivity Computation** | Sliding‑window (60 s, 1 s) Pearson correlation → edge‑wise SD & Shannon entropy → concatenate → **Incremental PCA** (retain top 10 components, name `PCA_Component_1`…`PCA_Component_10`). Record variance explained (≥ 80 %). | FR‑003, FR‑004 | – | `data/processed/variability_metrics.csv` |
| **5 – Null‑Model Validation** | Generate phase‑shuffled surrogate series per region, recompute variability metric, compute two‑sided p‑value (real > surrogate). | FR‑008 | – | `data/processed/null_validation.csv` |
| **6 – Regression & Permutation Test** | Linear model `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`. Run 10 000 permutations of the outcome to obtain empirical p‑value; apply FDR (q ≤ 0.05) if any post‑hoc tests are added. | FR‑005, FR‑006, FR‑009 | SC‑003 (empirical p‑value), SC‑004 (Pearson r) | `data/results/regression_summary.json` |
| **7 – Final Result Assembly** | Merge subject‑level metrics, predicted scores, residuals into `final_results.csv` matching `contracts/dataset.schema.yaml`. | FR‑007 | – | `data/processed/final_results.csv` |
| **8 – Reporting & Figures** | Scatter plot (variability vs. flexibility) with regression line & 95 % CI; export PNG. | – | – | `data/results/variability_vs_flexibility.png` |
| **9 – Lint & Contract Verification** | Run `ruff check . > data/logs/ruff.log`; execute `pytest -q tests/test_contracts.py`. | – | – | `data/logs/ruff.log`, test pass/fail status |
| **10 – Runtime Guard** | If any phase exceeds 5 h, automatically down‑sample (e.g., 5 000 permutations) and log the adaptation. | – | – | Updated log entries in `data/logs/runtime_guard.log` |

All phases are ordered so that data download precedes any consumption, metric computation precedes regression, and figures follow results, satisfying the “Computational Task Ordering” rule.

## Verification Strategy
Each phase ends with a contract test (pytest) that loads the produced file and validates it against the appropriate JSON‑Schema (`contracts/dataset.schema.yaml` or `contracts/output.schema.yaml`). Tests also assert:
- No nulls in required columns.
- Correct data types per schema.
- Expected row counts (e.g., `exclusion_log.csv` has one row per excluded subject).
- Lint log contains zero severity‑error entries.

Successful contract tests guarantee deterministic, reproducible artifacts on the CI runner.

## Compute Feasibility (CPU‑First)
| Component | Estimated CPU time | Peak RAM | Mitigation |
|-----------|-------------------|----------|------------|
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming, no full uncompressed load |
| Parcellation (batch = 20) | ~30 min | ~1 GB per batch | Batch processing |
| Sliding‑window correlation (vectorized, numba optional) | ~45 min | ~2 GB per batch | Vectorized NumPy; optional `numba` JIT |
| Incremental PCA | ~10 min | < 1 GB | `sklearn.IncrementalPCA` |
| Phase‑shuffled surrogates (100 surrogates) | ~15 min | < 1 GB | Parallel across 2 cores |
| Regression & 10 000 permutations (vectorized) | ~60 min | < 500 MB | Fallback to 5 000 if > 5 h |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline will run fully on the free‑tier runner. If any step threatens the 6 h limit, the runtime guard (Phase 10) will automatically reduce work and log the change.

## Power & Sample Size (Re‑affirmed)
The HCP 1200 release provides **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project). After motion & quality filtering we anticipate **≥ 800** usable subjects. With N≈800 the study has **> 80 % power** to detect a **medium** correlation (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently (SC‑001).

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified URLs lack required fMRI or DCCS scores | Pipeline cannot proceed → project halts | Phase 0 generates explicit `gap_report.md`; no synthetic data created (Constitution II). |
| Runtime > 6 h | CI job failure | Vectorized code; runtime guard reduces permutations; batch size adjustable via `config.BATCH_SIZE`. |
| Excessive subject exclusion (e.g., high motion) | Reduced statistical power | Log exclusion counts; recompute power; if N < 400, report limitation. |
| Collinearity between edge‑wise SD & entropy | Inflated coefficient variance | PCA orthogonalizes all edge‑wise metrics; only `PCA_Component_1` used as primary predictor. |
| Lint failure (previous T001) | Verification rejection | Dedicated lint phase (Phase 9) with deterministic log; ensure `ruff` config passes. |
| Main script timeout (previous T002) | Verification rejection | Split long operations into separate phases; each phase has its own timeout guard; overall runtime < 6 h. |

---
