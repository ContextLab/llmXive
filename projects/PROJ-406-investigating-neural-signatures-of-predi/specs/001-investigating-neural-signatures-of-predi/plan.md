# Implementation Plan: Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Branch**: `001-predictive-coding-cross-illusion` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-predictive-coding-cross-illusion/spec.md)  
**Input**: Feature specification from `/specs/001-predictive-coding-cross-illusion/spec.md`

## Summary
The pipeline must first download two publicly‑available illusion‑behavioral datasets, (2) validate that each dataset contains the required variables, (3) clean the data, (4) fit a hierarchical predictive‑coding model to the Müller‑Lyer training data to obtain per‑subject precision‑weighting parameters (λ), (5) compute a Ponzo susceptibility score (β) per subject using a simple linear generative model, and (6) test the primary hypothesis that λ predicts β via a Pearson correlation, bootstrap confidence intervals, shuffled‑ID control, and a Ponzo‑specific null‑model comparison. All steps are deterministic, reproducible, and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `datasets==2.18.*`, `statsmodels==0.14.*`  
- **Storage**: Flat files under `data/` (raw parquet, cleaned CSV, derived CSV/JSON)  
- **Testing**: `pytest==8.2.*` + contract validation (`jsonschema`)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB, CPU‑only  
- **Constraints**: No GPU required; all randomness seeded.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed random seeds via `src.utils.seed.set_global_seed`; deterministic loaders; `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | Only the two OpenNeuro/HF URLs listed in the “Verified Datasets” block are used; no invented sources. |
| **III. Data Hygiene** | Raw parquet files are never mutated; each transformation writes a new file with a SHA‑256 checksum recorded in the project state file. |
| **IV. Single Source of Truth** | All derived numbers trace back to rows in `data/clean/*.csv` and scripts in `src/`. Provenance is recorded in `data/manifest.yaml`. |
| **V. Versioning Discipline** | Every artifact’s content hash is stored in `state/projects/…yaml`; any change updates the timestamp. |
| **VI. Cross‑Illusion Generalizability** | Phase 6 validates λ (Müller‑Lyer) against β (Ponzo), a structurally distinct illusion. |
| **VII. Statistical Robustness via Resampling** | Bootstrap (≥ 1000 iterations) and shuffled‑ID control are mandatory in Phase 6. |

## Verified Datasets
| Role | Dataset | Verified URL | Loader | Expected key columns (required) |
|------|---------|--------------|--------|---------------------------------|
| Training (Müller‑Lyer) | OpenNeuro parquet shard | ` | `datasets.load_dataset(..., streaming=False)` | `subject_id`, `trial_id`, `stimulus_length`, `response_length`, `stimulus_parameters` |
| Test (Ponzo) | Ponzo illusion dataset (HuggingFace) | `https://huggingface.co/datasets/psychology/ponzo_illusion/resolve/main/data/ponzo.parquet` | same as above | `subject_id`, `trial_id`, `arrow_angle`, `depth_cue`, `perceived_length` |
| SusceptibilityScore | Computed internally (no external source) | – | – | – |

> **Note:** If any required column is missing, the ingestion script aborts with a clear error (fulfilling FR‑001).

## Project Structure
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
│   ├── clean-ponzo.schema.yaml
│   └── correlation-results.schema.yaml
└── tasks.md   # generated later

src/
├── ingest/
│   └── load_illusions.py          # download → verify → clean
├── model/
│   └── predictive_coding.py       # hierarchical MLE fit
├── analysis/
│   ├── correlation.py             # primary & bootstrap
│   ├── null_model.py              # Ponzo‑specific baseline
│   └── utils.py                   # helper functions
├── utils/
│   └── seed.py                    # set_global_seed implementation
└── __init__.py
```

## Phase Breakdown & FR/SC Coverage
| Phase | Core Tasks | FR(s) addressed | SC(s) addressed |
|-------|------------|-----------------|-----------------|
| **1 – Data Ingestion & Validation** | Download parquet files, compute SHA‑256, verify against state, load with `datasets`, check required columns, drop rows with missing critical fields, write `clean_muller_lyer.csv` & `clean_ponzo.csv` | FR‑001, FR‑002 (cleaning), FR‑003 (bounds check) | SC‑001 (valid input) |
| **2 – Hierarchical Predictive‑Coding Fit** | Fit per‑subject λ using `scipy.optimize.minimize` (L‑BFGS‑B) with bounds `[0.01, 10.0]`; convergence criteria (grad < 1e‑6, ΔLL > 1e‑4, no NaN/Inf); store log‑likelihood, AIC, BIC | FR‑002, FR‑003, FR‑004 (fit diagnostics) | SC‑004 (convergence) |
| **3 – Ponzo Susceptibility Scoring** | Fit per‑subject β via ordinary least squares on the generative model; store R² | FR‑009 | SC‑004 (validity) |
| **4 – Cross‑Illusion Prediction & Validation** | 1. **Power analysis** – compute required N for effect size *r*≈0.30 (α = 0.05, power = 0.80). If actual paired N < required, abort with message and switch to a Bayesian correlation estimate. 2. **Confound regression** – regress λ and β on age, gender, trial count per subject, and within‑subject response SD; retain residuals. 3. **Linearity diagnostics** – generate scatter plot, compute Spearman ρ, fit linear model and inspect residuals; if non‑linear, log warning and optionally report Spearman instead of Pearson. 4. **Merge** – join `precision_parameters.csv` and `ponzo_susceptibility.csv` on `subject_id`; exclude unmatched subjects (log count). 5. **Primary Pearson correlation** – compute r, two‑tailed p‑value on residuals. 6. **Bootstrap CI** – 1000 resamples → 95 % CI for r. 7. **Shuffled‑ID control** – permute Ponzo IDs 1000 times → null distribution centered at 0. 8. **Null model validation** – fit a Ponzo‑specific predictive‑coding model (independent λ′), compute AIC/BIC, store as `null_model_aic` and `null_model_bic` in the merged results. 9. **Diagnostics** – scatter plot (λ vs. β residuals), histogram of bootstrap r, residuals plot for Ponzo model; save PNGs. 10. **Output JSON** – `outputs/correlation_results.json` containing r, p_value, ci_lower, ci_upper, n_subjects, and note on linearity test. | FR‑004, FR‑005, FR‑006, FR‑007, FR‑008, FR‑009 | SC‑001 (null dist), SC‑002 (bootstrap CI), SC‑003 (power enforcement), SC‑005 (single‑test acknowledgment), SC‑006 (trait hypothesis) |
| **5 – Reporting & Artifact Registration** | Compute SHA‑256 for all outputs; update `state/projects/…yaml`; ensure all contracts validate. | All FRs indirectly | SC‑003 (runtime) |

### Methodological Details (Phase 4)
* **Power analysis** – `statsmodels.stats.power.NormalIndPower` with assumed *r*≈0.30. Required N is logged; pipeline aborts if actual N < required, falling back to Bayesian correlation (`scipy.stats.bayes_mvs` or equivalent).  
* **Confound control** – Linear regression of λ and β on age, gender, trial count, and response SD; residuals used for primary correlation.  
* **Linearity check** – Compute Pearson *r* and Spearman ρ; fit OLS λ ~ β and inspect residuals (Durbin‑Watson, visual). If residuals show strong non‑linearity (p < 0.05 for a quadratic term), the pipeline reports the Spearman result alongside Pearson.  
* **Multiple‑comparison handling** – Only the primary λ–β correlation is pre‑registered; we explicitly note its single‑test nature (SC‑005). Any exploratory extensions would be Bonferroni/FDR corrected.  
* **Causal framing** – Observational design; results described as associational per Principle VI.  

### Edge‑Case Handling (implemented in `load_illusions.py`)
| Situation | Response |
|-----------|----------|
| Download fails (e.g., 404) | Abort with clear message; suggest manual download to `data/raw/`. |
| Checksum mismatch | Abort; log expected vs. observed checksum. |
| Required column missing | Abort; list missing columns. |
| Subject present only in one dataset | Exclude from merged analysis; log exclusion count. |
| Model non‑convergence for a subject | Record subject ID in `fit_diagnostics.csv`; exclude from correlation. |
| Bootstrap or permutation fails (e.g., insufficient subjects) | Log warning and skip that step, noting the limitation. |

## Complexity Tracking
All requirements are satisfied with a pure‑CPU pipeline that fits comfortably within the 6 h, 7 GB RAM budget. No GPU‑only components are needed, avoiding the GPU escape hatch.

---

