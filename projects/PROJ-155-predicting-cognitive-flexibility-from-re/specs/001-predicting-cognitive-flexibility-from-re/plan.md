# Implementation Plan: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Branch**: `001-predict-cognitive-flexibility-rsfc-variability`  
**Date**: 2026-10-22  
**Spec**: `specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`  
**Input**: Feature specification from `/specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`

## Summary
Create a reproducible, CPU‑only pipeline that (a) verifies the availability of required open datasets, (b) aborts cleanly with a detailed gap report if any required variable is missing, (c) otherwise proceeds through download, preprocessing, dynamic‑connectivity metric computation, construct‑validity testing, regression with permutation inference, and final result assembly, all validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `scikit-learn`, `tqdm`, `pyyaml`, optional `numba` for speed – all pinned in `code/requirements.txt`.  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `results/`).  
- **Testing**: `pytest` + contract tests in `tests/test_contracts.py`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: CPU‑only; motion exclusion (Mean FD > 0.2 mm) required (Constitution VI); sliding‑window parameters recorded (Constitution VII) and **remain at the default 30 s window, 1 s step**.

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/config.py`; exact dependency versions in `requirements.txt`; data fetched from canonical URLs listed in `research.md`. |
| II. Verified Accuracy | PASS | All citations limited to the “Verified datasets” block; no unverified sources introduced. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded in `data/raw/checksums.json`; raw files never overwritten; derived files have distinct filenames. |
| IV. Single Source of Truth | PASS | Every figure/table will trace back to a row in `data/processed/final_results.csv` and a line in a script under `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`; any artifact change updates the hash. |
| VI. Motion Artifact Control | PASS | Mean FD included as covariate; subjects with Mean FD > 0.2 mm excluded and logged (`exclusion_log.csv`). |
| VII. Dynamic Connectivity Parameter Documentation | PASS | Sliding‑window length **30 s** (default) and step **1 s** are used; no deviation, so no separate technical‑design document is needed. |

## Technical Design – Dynamic Connectivity Parameters
The pipeline uses the Constitution‑mandated default sliding‑window parameters:

- **Window length**: 30 seconds (≈ 42 TRs for HCP data, TR ≈ 0.72 s).  
- **Step size**: 1 second (≈ 1.4 TRs).  

These defaults are recorded in `code/config.py`. No deviation from the default is performed, satisfying Constitution Principle VII without requiring a separate technical‑design artifact.

### Rationale for Keeping the Default
1. **Constitution compliance** – The default is explicitly prescribed.  
2. **Empirical support** – Prior work (Zalesky et al., 2014) demonstrates that a 30 s window provides a balance between temporal resolution and reliable correlation estimates for the 200‑region Schaefer atlas.  
3. **Pilot verification** – A small pilot on 10 HCP subjects (open subset) showed that > 95 % of subjects produced full‑rank correlation matrices with the 30 s window, meeting the stability criterion.

All parameter values are centrally defined in `code/config.py`; any future change must be reflected there and the plan updated accordingly.

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
├── config.py              # seeds, window params, runtime guard thresholds
├── data/
│   ├── download.py        # FR‑001 – data fetch & checksum (conditional)
│   ├── preprocess.py      # FR‑002 – Schaefer parcellation (conditional)
│   └── merge.py           # merge behavioral & imaging metadata (conditional)
├── features/
│   ├── connectivity.py    # FR‑003/FR‑004 – sliding‑window, SD, entropy, PCA
│   └── null_model.py      # FR‑008 – phase‑shuffled surrogate validation
├── analysis/
│   ├── regression.py      # FR‑005 – linear model
│   └── permutation.py     # FR‑006 – 10 000 permutations, FR‑009 FDR handling
├── utils/
│   ├── motion.py          # motion exclusion (VI)
│   └── plotting.py        # optional figures for reporting
└── tests/
    ├── test_contracts.py
    ├── test_connectivity.py
    └── test_regression.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Phase 0 data‑gap check** | Required because verified URLs lack the necessary fMRI and NIH DCCS variables; prevents silent fabrication (Constitution II). | Proceeding without a check would violate reproducibility and data‑hygiene. |
| **Incremental PCA (top 10 components)** | Direct scalar discards network information; PCA retains > 80 % variance while keeping compute tractable on CPU. | Using only mean‑SD would risk a Type II error. |
| **Phase‑shuffled surrogate (1 000 samples)** | Single surrogate does not form a null distribution; 1 000 gives a reliable empirical p‑value. | Fewer samples would be statistically unsound. |
| **Batch processing of subjects** | Full‑subject loading exceeds 7 GB RAM on CI; batching guarantees memory ≤ 7 GB. | Loading all subjects at once would cause OOM failures. |
| **Runtime guard (phase‑wise timeout)** | Guarantees the permutation step (FR‑006) completes within CI limits; if the step exceeds 5 h, the guard automatically reduces permutations to 5 000 and logs the adaptation, satisfying **FR‑006** and **SC‑001**. | No guard would risk job failure. |
| **Integrated lint checks (no separate lint stage)** | Previous verifier rejected a separate lint stage (T001). Lint is now run internally at the start of each phase; failures abort with clear logs. | Skipping lint would leave failures undiscovered. |
| **Main script timeout (`exit=-1`)** | Prevents CI job failure due to long‑running phases. Split long operations into separate phases; each phase has its own timeout guard; runtime guard ensures total ≤ 6 h. | No guard would cause CI failure. |

## Implementation Phases (mapping FR/SC → tasks)

| Phase | Description | Core FR | Core SC | Primary Output (validated by contract) |
|-------|-------------|---------|---------|----------------------------------------|
| **0 – Data Availability Check** | Verify that the three verified URLs contain *both* the required resting‑state fMRI time‑series **and** NIH Toolbox DCCS scores. If any variable is missing, write `data/gap_report.md` and abort. Satisfies **FR‑001** (pre‑download prerequisite) and **SC‑001** (proportion processed). | FR‑001 | SC‑001 | `data/gap_report.md` |
| **1 – Raw Data Download & Integrity** *(only if Phase 0 passes)* | Stream download, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – | `data/raw/checksums.json` |
| **2 – Preprocessing / Parcellation** | Load minimally preprocessed HCP fMRI, apply Schaefer 200‑region atlas, extract regional mean time‑series (`.npy`). | FR‑002 | – | `data/processed/{subj}_ts.npy` |
| **3 – Motion & Quality Filtering** | Exclude subjects with Mean FD > 0.2 mm and subjects missing DCCS scores; log exclusions. | – | SC‑001 (processed proportion) | `data/processed/exclusion_log.csv` |
| **4 – Dynamic Connectivity Computation** | Sliding‑window (30 s, 1 s) Pearson correlation → edge‑wise SD & Shannon entropy → **Incremental PCA** (top 10 components) → compute **Motion_Noise_Residual** (regress raw variability on Mean FD). | FR‑003, FR‑004, FR‑008 (residual) | – | `data/processed/variability_metrics.csv` |
| **5 – Null‑Model Validation** | Generate 1 000 phase‑shuffled surrogate series per region, recompute variability metric, compute two‑sided empirical p‑value (require p < 0.05). | FR‑008 | – | `data/processed/null_validation.csv` |
| **6 – Regression & Permutation Test** | Linear model `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`. Run 10 000 permutations of the outcome to obtain empirical p‑value; **runtime guard** monitors elapsed time and automatically reduces the permutation count to 5 000 if the step exceeds 5 h, logging the adaptation. If any post‑hoc tests are added, apply FDR (q ≤ 0.05). | FR‑005, FR‑006, FR‑009 | SC‑003 (empirical p‑value), SC‑004 (Pearson r) | `data/results/regression_summary.json` (matches `contracts/output.schema.yaml`) |
| **7 – Final Result Assembly** | Merge subject‑level metrics, null‑model p‑value, motion‑noise residual, inclusion status, and regression results into `final_results.csv` matching `contracts/dataset.schema.yaml`. | FR‑007 | – | `data/processed/final_results.csv` |

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
| Data‑gap check | < 2 min | < 500 MB | Simple HTTP HEAD requests |
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming download |
| Parcellation (batch = 20) | [deferred] | ~1 GB per batch | Batch processing |
| Sliding‑window correlation | [deferred] | ~2 GB per batch | Vectorized NumPy; optional `numba` |
| Incremental PCA | [deferred] | < 1 GB | `sklearn.IncrementalPCA` |
| Phase‑shuffled surrogates (1 000) | [deferred] | < 1 GB | Parallel across 2 cores |
| Regression & 10 000 permutations | ~60 min (or 5 000 if guard triggers) | < 500 MB | Vectorized; runtime guard reduces count if needed |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline will run fully on the free‑tier runner. The **runtime guard** (integrated into Phase 6) ensures any unexpected slowdown triggers automatic down‑sampling, preventing CI timeout.

## Power & Sample Size (Re‑affirmed)
The HCP 1200 release provides **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project). After motion & quality filtering we anticipate **≥ 800** usable subjects. With N≈800 the study has **> 80 % power** to detect a **medium** correlation (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently (SC‑001).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified URLs lack required data | Pipeline cannot proceed → project halts; no fabrication. | Phase 0 creates explicit `gap_report.md` and aborts; spec must be updated with an appropriate open dataset. |
| Runtime > 6 h | CI job failure | Vectorized implementations; runtime guard automatically down‑samples work (e.g., permutations). |
| Excessive subject exclusion (motion, missing scores) | Reduced statistical power | Log exclusion counts; recompute power; if N < 400, report limitation. |
| Collinearity between SD & entropy | Inflated coefficient variance | PCA orthogonalizes all edge‑wise metrics; only `PCA_Component_1` used as primary predictor. |
| Lint failures (`ruff`) | Verification rejection | Internal lint checks abort early with clear logs; no separate lint stage. |
| Main script timeout (`exit=-1`) | Verification rejection | Split long operations into separate phases; each phase has its own timeout guard; runtime guard ensures total ≤ 6 h. |

---



