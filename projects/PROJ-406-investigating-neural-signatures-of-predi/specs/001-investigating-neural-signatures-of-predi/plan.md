# Implementation Plan: Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Branch**: `001-predictive-coding-cross-illusion` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-predictive-coding-cross-illusion/spec.md)  
**Input**: Feature specification from `/specs/001-predictive-coding-cross-illusion/spec.md`

## Summary
The project must download and clean two public illusion‑behavioral datasets (Müller‑Lyer training, Ponzo test)., (2) fit a hierarchical predictive‑coding model to the training data to obtain individual precision‑weighting parameters, and (3) test whether these parameters predict susceptibility scores on the held‑out Ponzo task using Pearson correlation, bootstrap confidence intervals, shuffled‑ID controls, and a task‑specific null model. 

**Single Source of Truth (SSoT)**: The master state file `state/projects/PROJ-406-investigating-neural-signatures-of-predi.yaml` is the designated SSoT for all project artifacts, checksums, and derived statistics.

All steps must be fully reproducible on a GitHub Actions free‑tier runner using only CPU‑tractable libraries.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `datasets==2.18.*` (for OpenNeuro parquet loading)  
- **Storage**: Flat files under `data/` (raw parquet, cleaned CSV, derived parameter tables)  
- **Testing**: `pytest==8.2.*` + contract validation scripts  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Research pipeline (CLI scripts under `src/`)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only; all random seeds pinned; no external GPU needed.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic (seeded RNG), datasets fetched from the same OpenNeuro URLs on every run, and a `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | Only the OpenNeuro parquet URLs listed in the **Verified Datasets** block below are cited. |
| **III. Data Hygiene** | Raw parquet files are stored unchanged; each transformation writes a new CSV with a checksum recorded in the SSoT state file. |
| **IV. Single Source of Truth** | The file `state/projects/PROJ-406-investigating-neural-signatures-of-predi.yaml` is explicitly labeled as the SSoT. |
| **V. Versioning Discipline** | All artifacts (datasets, parameters, figures) are content‑hashed; updates trigger timestamp changes in the project state file. |
| **VI. Cross‑Illusion Generalizability** | Phase 3 explicitly validates training‑derived parameters against the structurally distinct Ponzo dataset. |
| **VII. Statistical Robustness via Resampling** | Bootstrap (≥ 1000 iterations) and shuffled‑ID control analyses are required steps in Phase 3. |

## Verified Datasets
| Dataset | URL | Loader | Key Variables |
|---------|-----|--------|----------------|
| Müller‑Lyer (Shard 0) | ` | `datasets.load_dataset(..., streaming=False)` | `subject_id`, `trial_id`, `stimulus_length`, `response_length`, `stimulus_parameters` |
| Ponzo (Shard 1) | ` | same as above | `subject_id`, `trial_id`, `arrow_angle`, `depth_cue`, `perceived_length` |

## Project Structure
### Documentation (this feature)
```
specs/001-predictive-coding-cross-illusion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── merged-results.schema.yaml
│   ├── precision-parameters.schema.yaml
│   ├── ponzo-susceptibility.schema.yaml
│   ├── clean-muller-lyer.schema.yaml
│   └── clean-ponzo.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code
```
src/
├── ingest/
│   └── load_illusions.py
├── model/
│   └── predictive_coding.py
├── analysis/
│   ├── correlation.py
│   ├── bootstrap.py
│   └── null_model.py
└── utils/
    └── logger.py
```

## Phase Breakdown & FR/SC Coverage
| Phase | Description | Tasks (FR) | SC addressed |
|-------|-------------|------------|--------------|
| **0 – Data Ingestion** | Download, verify checksums, clean raw parquet, produce `clean_muller_lyer.csv` and `clean_ponzo.csv`. Validate against `clean-muller-lyer.schema.yaml` and `clean-ponzo.schema.yaml`. | FR‑001, FR‑002 (data‑cleaning part), FR‑003 (bounds check) | SC‑001 (valid input) |
| **1 – Model Fitting** | Fit hierarchical predictive‑coding model to Müller‑Lyer data via `scipy.optimize.minimize` with bounds `[0.01, 10.0]`. Export per‑subject `precision` CSV. Validate against `precision-parameters.schema.yaml`. | FR‑002, FR‑003, FR‑004 (fit diagnostics) | SC‑004 (convergence) |
| **2 – Susceptibility Scoring** | Compute Ponzo susceptibility per subject using a generative model. Export `ponzo_score.csv`. Validate against `ponzo-susceptibility.schema.yaml`. | FR‑009 | SC‑004 (validity) |
| **3 – Cross‑Illusion Prediction** | 1. Perform a priori power analysis to justify sample size (SC-003).<br>2. Regress out subject-level confounds (age, gender) from $\lambda$ and $\beta$.<br>3. Merge tables on matched IDs. Validate against `merged-results.schema.yaml`.<br>4. Pearson correlation, bootstrap (≥ 1000 iters), shuffled‑ID control, and fit Ponzo‑specific null model. Generate plots. | FR‑004, FR‑005, FR‑006, FR‑007, FR‑008 | SC‑001 (null dist), SC‑002 (bootstrap CI), SC‑003 (power), SC‑005 (single test), SC‑006 (trait hypothesis) |
| **4 – Reporting & Artifacts** | Write summary JSON with correlation results, save all figures, compute checksums, update SSoT state file. | All FRs indirectly | SC‑003 (runtime) |

### Additional Methodological Details (Phase 3)

* **A priori Power Analysis** – Before running the correlation, we estimate statistical power using the expected effect size (e.g., r ≈ 0.30) and the available sample size (N = number of subjects with paired data). Using `statsmodels.stats.power.NormalIndPower`, we compute the required N for 0.80 power; if the actual N falls short, we will explicitly acknowledge the limitation (addresses SC-003).

* **Confound Control** – To prevent spurious associations, we will regress out demographic covariates (age, gender) from both the precision parameter ($\lambda$) and the susceptibility score ($\beta$) before computing the Pearson correlation. The correlation will be performed on the residuals of these linear models (addresses methodology-48ff5a7c).

* **Multiple‑Comparison Handling** – Only the primary $\lambda$-$\beta$ correlation is pre‑registered; we will explicitly state the single‑test nature. Any exploratory extensions will be corrected using Bonferroni/FDR as appropriate (SC-005).

* **Power Considerations** – A post‑hoc power analysis will also be reported using the observed effect size and sample size. The limited N is acknowledged, and any non‑significant finding will be interpreted with this limitation in mind (SC-003).

* **Edge‑Case Handling** – See spec for dataset download failures, unmatched subjects, and non‑convergent model fits.

## Complexity Tracking
No constitution violations identified; all requirements can be satisfied with the outlined CPU‑only pipeline and the verified OpenNeuro parquet sources.

---

## Contracts Utilized
| Contract File | Purpose |
|---------------|---------|
| `contracts/merged-results.schema.yaml` | Schema for the final joined table. |
| `contracts/precision-parameters.schema.yaml` | Schema for per‑subject $\lambda$ estimates. |
| `contracts/ponzo-susceptibility.schema.yaml` | Schema for per‑subject $\beta$ scores. |
| `contracts/clean-muller-lyer.schema.yaml` | Schema for cleaned training data. |
| `contracts/clean-ponzo.schema.yaml` | Schema for cleaned test data. |