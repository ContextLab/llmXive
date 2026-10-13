# Implementation Plan: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Branch**: `001-predict-cognitive-flexibility-rsfc-variability` | **Date**: 2026-10-13 | **Spec**: `specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`  
**Input**: Feature specification from `/specs/001-predict-cognitive-flexibility-rsfc-variability/spec.md`

## Summary
The project builds a reproducible, CPU‑only pipeline that (1) verifies the availability of the required HCP resting‑state fMRI and NIH Toolbox behavioral data, (2) preprocesses the fMRI with the Schaefer 200‑region atlas, (3) computes sliding‑window Pearson correlations (60 s window, 1 s step) and derives edge‑wise standard‑deviation and Shannon‑entropy, (4) reduces the edge‑wise variability matrix to the top 10 principal components (named `PCA_Component_1` … `PCA_Component_10`) while reporting variance explained and stability, (5) validates the variability metric against a **phase‑shuffled surrogate null model**, (6) tests the association between the **primary variability predictor** (`PCA_Component_1`) and the NIH Dimensional Change Card Sort (Flexibility) score via linear regression with covariates, and a 10 000‑permutation empirical p‑value, (7) applies FDR correction if any post‑hoc network‑specific tests are added, and (8) assembles a final CSV that matches the dataset schema. All steps produce files validated against JSON‑Schema contracts in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `scikit‑learn`, `tqdm`, `pyyaml`, `nitime` (pinned in `code/requirements.txt`)  
- **Storage**: Local filesystem (CSV/Parquet for tabular data, NIfTI for images)  
- **Testing**: `pytest` + contract tests (`tests/test_contracts.py`)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only; motion exclusion (Mean FD > 0.2 mm) required by Constitution Principle VI; sliding‑window parameters must match Constitution Principle VII (override documented and justified).  

## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|--------------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins versions; data fetched from canonical URLs. |
| II. Verified Accuracy | PASS | All external dataset citations limited to the “Verified datasets” block; no unverified sources used. |
| III. Data Hygiene | PASS | Checksums recorded in `state/`; raw files immutable; derived files written with new filenames. |
| IV. Single Source of Truth | PASS | Every figure/table traced to a row in `data/processed/final_results.csv` and a line in `code/`. |
| V. Versioning Discipline | PASS | Content hashes updated on artifact change; `state/projects/...yaml` `updated_at` managed by the platform. |
| VI. Motion Artifact Control | PASS | Mean FD included as covariate; subjects with Mean FD > 0.2 mm excluded and logged (`exclusion_log.csv`). |
| VII. Dynamic Connectivity Parameter Documentation | PASS (with justified deviation) | Default 30 s window replaced by 60 s window (see Phase 4) and documented here; change justified by rank‑deficiency analysis. |

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
├── main.py                # CLI entry point
├── config.py              # Global parameters, seeds, batch sizes
├── data/
│   ├── download.py        # FR‑001 – verifies data availability
│   ├── preprocess.py      # FR‑002 – Schaefer parcellation
│   └── merge.py           # merges behavioral & imaging metadata
├── features/
│   ├── connectivity.py    # FR‑003/FR‑004 – sliding‑window & PCA
│   └── null_model.py      # FR‑008 – **phase‑shuffled** validation
├── analysis/
│   ├── regression.py      # FR‑005 – linear model (primary predictor = PCA_Component_1)
│   └── permutation.py     # FR‑006 – permutation test, FR‑009 FDR
├── utils/
│   ├── motion.py          # motion exclusion logic (VI)
│   └── plotting.py        # figures for the report
└── tests/
    ├── test_contracts.py
    ├── test_connectivity.py
    └── test_regression.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| 60 s sliding window (instead of 30 s default) | 30 s window yields < 50 time points for a 200‑region matrix → rank‑deficient; 60 s provides > 100 points, enabling stable correlation estimation. | Keeping the 30 s default would invalidate the variability metric (statistical flaw). |
| PCA reduction of edge‑wise variability | Direct use of mean‑SD scalar discards network‑specific signal, reducing power. PCA retains > 80 % variance and orthogonalizes predictors. | Using only the scalar would risk Type II error. |
| Phase‑shuffled surrogate null model | Preserves amplitude spectrum while destroying temporal ordering, providing a stringent test of dynamic structure. | Phase‑shuffling is required by FR‑008; AR(1) would not meet the spec. |
| Batch processing of subjects | Full‑subject loading exceeds 7 GB RAM on CI. | Loading all subjects at once would cause OOM failures. |

## Implementation Phases (mapping FR/SC → tasks)

| Phase | Description | Core FR | Core SC | Primary Output (validated by contract) |
|-------|-------------|--------|--------|----------------------------------------|
| **0 – Data Availability Check** | `code/data/download.py` attempts to load the three verified URLs. If required variables (`Flexibility_Score`, raw fMRI time‑series) are absent, a `data/gap_report.md` is written and the pipeline exits gracefully. | – | – | `data/gap_report.md` (human‑readable) |
| **1 – Raw Data Download & Integrity** | Download parquet/CSV files, compute SHA‑256 checksums, store under `data/raw/`. | FR‑001 | – | `data/raw/checksums.json` |
| **2 – Preprocessing / Parcellation** | Apply Schaefer 200‑region atlas to each subject’s preprocessed fMRI (already minimally preprocessed in HCP). Produce region‑wise time‑series matrices (`.npy`). | FR‑002 | – | `data/processed/{subj}_ts.npy` |
| **3 – Motion & Quality Filtering** | Exclude subjects with Mean FD > 0.2 mm (Principle VI) and with missing Flexibility scores. Log counts. | – | SC‑001 (proportion processed) | `data/processed/exclusion_log.csv` |
| **4 – Dynamic Connectivity Computation** | Sliding‑window (60 s, 1 s) Pearson correlation → edge‑wise SD & Shannon entropy → concatenate → **PCA** (Incremental, retain the top principal components, naming them `PCA_Component_1`, `PCA_Component_2`, … up to the selected number of components.). Report variance explained (≥ 80 %) and bootstrap stability (mean ± SD of loadings). | FR‑003, FR‑004 | – | `data/processed/variability_metrics.csv` (columns: Subject_ID, Age, Sex, Mean_FD, Total_Scan_Time, Flexibility_Score, Status, PCA_Component_1 … PCA_Component_10, Null_Model_P, Motion_Noise_Residual) |
| **5 – Null‑Model Validation** | Generate **phase‑shuffled** surrogate series for each region (preserves amplitude spectrum, destroys temporal ordering), recompute variability metric, compute two‑sided p‑value comparing real vs. surrogate distribution (p < 0.05 required). | FR‑008 | – | `data/processed/null_validation.csv` |
| **6 – Regression & Permutation Test** | Linear model `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`. A large number of permutations of the outcome variable generate an empirical p‑value.; if any post‑hoc network tests are added, FDR correction (q ≤ 0.05) is applied. Output includes `FDR_Q_Value` and `FDR_Appplied`. | FR‑005, FR‑006, FR‑009 | SC‑003 (empirical p‑value), SC‑004 (Pearson r) | `data/results/regression_summary.json` |
| **7 – Final Result Assembly** | Merge subject‑level metrics, predicted scores, residuals into one CSV that **exactly matches** `contracts/dataset.schema.yaml`. | FR‑007 | – | `data/processed/final_results.csv` |
| **8 – Reporting & Figures** | Create scatter plot (variability vs. flexibility) with regression line & 95 % CI; export PNG. | – | – | `data/results/variability_vs_flexibility.png` |
| **9 – Lint & Contract Verification** | Run `ruff check .` and store log; execute `pytest -q tests/test_contracts.py`. | – | – | `data/logs/ruff.log`, test pass/fail status |

All phases are ordered so that data download precedes any consumption, metrics precede regression, and figures follow results, satisfying the “Computational Task Ordering” rule.

## Verification Strategy
Each phase ends with a contract test (pytest) that loads the produced file and validates it against the appropriate JSON‑Schema (`contracts/dataset.schema.yaml` for subject‑level tables, `contracts/output.schema.yaml` for regression summary). The tests also assert:
* No nulls in required columns.
* Correct data types per schema.
* Expected row counts (e.g., `exclusion_log.csv` contains exactly one row).

Successful contract tests guarantee that the artifacts are **deterministically verifiable** on the CI runner.

## Risk Mitigation
* **Missing verified data** – Phase 0 halts with a clear `gap_report.md`; no synthetic data is generated, complying with Constitution Principle II.  
* **Runtime > 6 h** – Permutation loop is vectorized; if runtime exceeds 5 h a fallback to 5 000 permutations is triggered (still > 0.001 empirical resolution) and logged.  
* **Memory overflow** – Batch size (`config.BATCH_SIZE`) defaults to 20 subjects; can be lowered via `--batch-size`.  
* **Excessive subject exclusion** – Logged; power recomputed; if N < 400, limitation reported.  
* **Collinearity** – PCA orthogonalizes edge‑wise metrics; regression diagnostics (VIF) are logged but not used to claim independent effects, respecting the “collinearity” warning in the methodology panel.

## Power & Sample Size (Revised)
The HCP 1200 release provides up to 1,200 healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project). After motion and quality filtering we expect ≥ 800 usable subjects. With N≈800 the study has > 80 % power to detect a **medium** correlation (r≈0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently.  

---

