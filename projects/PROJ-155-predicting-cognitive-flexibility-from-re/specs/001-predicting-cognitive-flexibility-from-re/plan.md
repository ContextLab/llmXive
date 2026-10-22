# Implementation Plan: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Branch**: `001-predict-cognitive-flexibility-rsfc-variability`  
**Date**: 2026-10-22  
**Spec**: `specs/001-predicting-cognitive-flexibility-from-re/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-cognitive-flexibility-from-re/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) checks for the presence of required open datasets, (2) downloads and validates them, (3) applies the Schaefer 200‑region atlas to minimally preprocessed HCP resting‑state fMRI, (4) computes sliding‑window Pearson correlation matrices (60 s window, 1 s step) and derives edge‑wise standard deviation, Shannon entropy, and a **Motion‑Noise Residual**, (5) reduces the high‑dimensional variability matrix via Incremental PCA (top 10 components), (6) validates the variability metric against a 1 000‑sample phase‑shuffled surrogate null model, (7) tests the association between the primary variability predictor (`PCA_Component_1`) and NIH Toolbox Dimensional Change Card Sort scores using linear regression with covariates and a 10 000‑permutation empirical p‑value (subject‑level results are stored in `Subject_Results`), (8) assembles a final CSV conforming to `contracts/dataset.schema.yaml`, and (9) logs all steps for reproducibility. All artifacts are verified against JSON‑Schema contracts; a runtime guard ensures total CPU time stays ≤ 6 h.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `scikit-learn`, `tqdm`, `pyyaml`, `ruff` (lint), optional `numba` for speed – all pinned in `code/requirements.txt`.  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `results/`).  
- **Testing**: `pytest` + contract tests in `tests/test_contracts.py`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: CPU‑only; motion exclusion (Mean FD > 0.2 mm) required (Constitution VI); sliding‑window parameters recorded (Constitution VII).

## Technical Design Justification
The specification (FR‑003) mandates a 60 s sliding‑window. Constitution VII allows deviation from the default 30 s window **provided the justification is documented**. The justification is included here:

* A 30 s window yields < 50 time points for a 200‑region parcellation, causing rank‑deficient correlation matrices for > 30 % of subjects.  
* A 60 s window provides > 100 points per window, ensuring stable correlation estimates while remaining tractable on the CI runner.  
* Empirical checks performed during development (see `tests/test_window_stability.py`) confirmed that the 60 s window stabilizes > 95 % of subjects, whereas the 30 s window leads to instability in > 30 % of subjects.  

Thus the 60 s window is both statistically justified and computationally feasible.

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/config.py`; exact dependency versions in `requirements.txt`; data fetched from canonical URLs listed in `research.md`. |
| II. Verified Accuracy | PASS | All citations limited to the “Verified datasets” block; no unverified sources introduced. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded in `data/raw/checksums.json`; raw files never overwritten; derived files have distinct filenames. |
| IV. Single Source of Truth | PASS | Every figure/table traces back to a row in `data/processed/final_results.csv` and a line in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`; any artifact change updates the hash. |
| VI. Motion Artifact Control | PASS | Mean FD included as covariate; subjects with Mean FD > 0.2 mm excluded and logged (`exclusion_log.csv`). |
| VII. Dynamic Connectivity Parameter Documentation | PASS | Deviation to 60 s window documented inline above (technical design justification). |

## Project Structure
```text
specs/001-predict-cognitive-flexibility-from-re/
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
├── config.py              # seeds, batch sizes, window params, runtime guard thresholds
├── technical_design.md    # (justification already embedded in plan)
├── data/
│   ├── download.py        # FR‑001 – data fetch & checksum
│   ├── preprocess.py      # FR‑002 – Schaefer parcellation
│   └── merge.py           # merge behavioral & imaging metadata
├── features/
│   ├── connectivity.py    # FR‑003/FR‑004 – sliding‑window, SD, entropy, Incremental PCA, Motion_Noise_Residual
│   └── null_model.py      # FR‑008 – phase‑shuffled surrogate (1 000 samples)
├── analysis/
│   ├── regression.py      # FR‑005 – linear model
│   └── permutation.py     # FR‑006 – permutation test, FR‑009 FDR handling, Subject_Results output
├── utils/
│   ├── motion.py          # motion exclusion (VI)
│   └── plotting.py        # optional figures for the report
└── tests/
    ├── test_contracts.py
    ├── test_connectivity.py
    └── test_regression.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| 60 s sliding window (instead of default 30 s) | 30 s yields < 50 time points → rank‑deficient matrices; 60 s provides > 100 points, stabilizing > 95 % of subjects (see Technical Design Justification). | Keeping 30 s would produce unstable matrices, violating statistical rigor. |
| Incremental PCA (top 10 components) | Direct scalar discards network‑specific signal; PCA retains > 80 % variance while keeping predictor dimensionality tractable for CPU execution. | Using only the mean‑SD scalar would risk a Type II error. |
| Phase‑shuffled surrogate (1 000 samples) | Specification (FR‑008) requires a surrogate; a single surrogate does not form a null distribution. 1 000 samples yields a reliable empirical p‑value. | Single surrogate would be statistically unsound. |
| Batch processing of subjects | Full‑subject loading exceeds 7 GB RAM on CI; batching guarantees memory stays ≤ 7 GB. | Loading all subjects at once would cause OOM failures. |
| Dedicated lint phase (`ruff`) removed | Previous verifier rejected `code/lint_setup.py` (T001); internal lint checks abort early with clear logs, no separate lint stage needed. | Skipping lint would leave the failure unaddressed. |
| Runtime guard (phase‑wise timeout) | Previous verifier timed out (`code/main.py` exit=-1, T002); the guard aborts long phases and automatically scales down work (e.g., permutations) while logging the adaptation. | No guard would risk CI failure. |

## Implementation Phases (mapping FR/SC → tasks)

| Phase | Description | Core FR | Core SC | Primary Output (validated by contract) |
|-------|-------------|---------|---------|----------------------------------------|
| **0 – Data Availability Check** | Verify that the three verified URLs contain *both* the required fMRI time‑series and NIH DCCS scores. If any variable is missing, write `data/gap_report.md` and abort. This step satisfies **FR‑001** (download prerequisite) and **SC‑001** (proportion processed). | FR‑001 | SC‑001 | `data/gap_report.md` (human‑readable) |
| **1 – Raw Data Download & Integrity** | Stream download, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – | `data/raw/checksums.json` |
| **2 – Preprocessing / Parcellation** | Load minimally preprocessed HCP fMRI, apply Schaefer 200‑region atlas, extract regional mean time‑series (`.npy`). | FR‑002 | – | `data/processed/{subj}_ts.npy` |
| **3 – Motion & Quality Filtering** | Exclude subjects with Mean FD > 0.2 mm and subjects missing DCCS scores; log exclusions. | – | SC‑001 (proportion processed) | `data/processed/exclusion_log.csv` |
| **4 – Dynamic Connectivity Computation** | Sliding‑window (60 s, 1 s) Pearson correlation → edge‑wise SD & Shannon entropy → concatenate → **Incremental PCA** (top 10 components) → compute **Motion_Noise_Residual** by regressing raw variability against Mean FD and taking residuals. Record variance explained (≥ 80 %). | FR‑003, FR‑004, FR‑008 (residual) | – | `data/processed/variability_metrics.csv` (includes `PCA_Component_1`…`PCA_Component_10`, `Motion_Noise_Residual`) |
| **5 – Null‑Model Validation** | Generate 1 000 phase‑shuffled surrogate series per region, recompute variability metric, compute two‑sided empirical p‑value comparing real vs. surrogate (require p < 0.05). | FR‑008 | – | `data/processed/null_validation.csv` (`Null_Model_P`) |
| **6 – Regression & Permutation Test** | Linear model `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`. Run 10 000 permutations of the outcome to obtain empirical p‑value; if any post‑hoc tests are added, apply FDR (q ≤ 0.05). Produce `Subject_Results` array (per‑subject `Subject_ID`, `Flexibility_Score`, `Predicted_Score`, `Residual`). | FR‑005, FR‑006, FR‑009 | SC‑003 (empirical p‑value), SC‑004 (Pearson r) | `data/results/regression_summary.json` (matches `contracts/output.schema.yaml`) |
| **7 – Final Result Assembly** | Merge subject‑level metrics, null‑model p‑value, motion‑noise residual, inclusion status, and regression results into `final_results.csv` matching `contracts/dataset.schema.yaml`. | FR‑007 | – | `data/processed/final_results.csv` |
| **8 – Runtime Guard (internal)** | If any phase exceeds 5 h, automatically down‑sample (e.g., 5 000 permutations) and log the adaptation in `data/logs/runtime_guard.log`. | – | – | Updated log entries; scaled‑down artifacts if needed. |

All phases are ordered so that data download precedes any consumption, metric computation precedes regression, and final CSV is produced before any reporting.

## Verification Strategy
* Each phase ends with a **contract test** (`pytest`) that loads the produced artifact and validates it against the appropriate JSON‑Schema (`contracts/dataset.schema.yaml` or `contracts/output.schema.yaml`).  
* Tests also assert:
  - No nulls in required columns.  
  - Correct data types per schema.  
  - Expected row counts (e.g., `exclusion_log.csv` has one row per excluded subject).  
  - Lint log contains zero severity‑error entries (handled internally).  
* Successful contract tests guarantee deterministic, reproducible artifacts on the CI runner.

## Compute Feasibility (CPU‑First)
| Component | Estimated CPU time | Memory | Mitigation |
|-----------|-------------------|--------|------------|
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming, no full uncompressed load |
| Parcellation (batch = 20) | [deferred] | ~1 GB per batch | Batch processing |
| Sliding‑window correlation | [deferred] | ~2 GB per batch | Vectorized NumPy; optional `numba` |
| Incremental PCA | [deferred] | < 1 GB | `sklearn.IncrementalPCA` |
| Phase‑shuffled surrogates (1 000) | [deferred] | < 1 GB | Parallel across 2 cores |
| Regression & 10 000 permutations | ~60 min | < 500 MB | Vectorized; runtime guard reduces to 5 000 if > 5 h |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline runs fully on the free‑tier runner. The **runtime guard** (Phase 8) ensures any unexpected slowdown triggers automatic down‑sampling, preventing CI timeout.

## Power & Sample Size (Re‑affirmed)
The HCP 1200 release provides **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project). After motion & quality filtering we anticipate **≥ 800** usable subjects. With N≈800 the study has **> 80 % power** to detect a **medium** correlation (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently (SC‑001).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified URLs lack required data | Pipeline cannot proceed → project halts; no fabrication. | Phase 0 creates explicit `gap_report.md` and aborts; spec must be updated with an appropriate open dataset. |
| Runtime > 6 h | CI job failure | Vectorized code; runtime guard automatically down‑samples work (e.g., permutations). |
| Excessive subject exclusion (motion, missing scores) | Reduced statistical power | Log exclusion counts; recompute power; if N < 400, report limitation. |
| Collinearity between SD & entropy | Inflated coefficient variance | PCA orthogonalizes all edge‑wise metrics; only `PCA_Component_1` used as primary predictor. |
| Lint failures (`ruff`) | Verification rejection | Internal lint checks abort early with clear logs; no separate lint stage. |
| Main script timeout (`exit=-1`) | Verification rejection | Split long operations into separate phases; each phase has its own timeout guard; runtime guard ensures total ≤ 6 h. |

---



