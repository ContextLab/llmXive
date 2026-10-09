# Implementation Plan: Quantifying Neural Representation Drift During Skill Learning

**Branch**: `001-quantify-neural-drift` | **Date**: 2026-10-09 | **Spec**: `specs/001-quantify-neural-drift/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-neural-drift/spec.md`

## Summary
The MVP is a reproducible, CPU‑only pipeline that (1) ingests raw electrophysiology (via a synthetic generator to ensure modality fit) and behavioral logs, (2) builds stable neural population matrices, (3) computes pairwise distances to form Representational Dissimilarity Matrices (RDMs), (4) implements **both** a linear drift model `drift(t)=a+b·t` (primary for FR‑005) and an exponential drift model `drift(t)=a·exp(−b·t)+c` (primary for Constitution VII), (5) correlates both drift rates with individual learning speeds using Pearson correlation, permutation testing, and a linear mixed‑effects model (FR‑006), and (6) runs a full sensitivity suite (FR‑008). All steps are mapped to functional requirements (FR‑001‑FR‑010) and success criteria (SC‑001‑SC‑005).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0`, `numpy>=1.24`, `scikit-learn>=1.3`, `statsmodels>=0.14`, `scipy>=1.11`, `datasets>=2.16`, `matplotlib`, `seaborn`  
- **Storage**: Local filesystem (Parquet for matrices, CSV/JSON for results)  
- **Testing**: `pytest`, `pytest-cov`, `pytest-randomly`  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU, ≤7 GB RAM)  
- **Constraints**: CPU‑only execution, ≤6 h runtime, ≤7 GB RAM, ≥80 % unit stability, no GPU libraries invoked.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, seeded randomness, deterministic scripts. |
| II. Verified Accuracy | PASS | All citations are from the verified list; incorrect fMRI dataset removed. |
| III. Data Hygiene | PASS | Checksums recorded, immutable raw files, derived files get new names. |
| IV. Single Source of Truth | PASS | Every figure/table traces to a single row in `data/processed/` and a single code block. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`. |
| VI. Neural Data Integrity | PASS | Unit‑stability ≥80 % enforced; performance‑modulated units excluded per spec. |
| VII. Computational Robustness | PASS | Exponential drift model used as the primary metric for learning-speed prediction. |

## Project Structure
```text
specs/001-quantify-neural-drift/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── input_schema.schema.yaml
│   ├── neural_population.schema.yaml
│   ├── drift_result.schema.yaml
│   └── correlation_result.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── __init__.py
├── main.py                # CLI entry point
├── config.py              # Configurable flags (e.g., primary_model)
├── data/
│   ├── loader.py          # Streaming synthetic generation
│   ├── preprocessor.py    # Unit filtering, performance‑modulated exclusion, alignment
│   └── imputer.py         # Linear interpolation for missing behavioral logs
├── analysis/
│   ├── drift.py           # RDM creation, linear fit (FR-005), exponential fit (Const VII)
│   └── correlation.py     # Pearson r, permutation test, LMM
├── validation/
│   ├── sensitivity.py     # Threshold sweep, metric comparison, split‑half reliability
│   └── synthetic.py       # Ground‑truth synthetic generator (SC‑001)
├── utils/
│   ├── metrics.py         # Pearson, Cosine, Mahalanobis distances
│   └── plots.py           # Figure generation
└── models/
    └── schemas.py         # Pydantic wrappers for contract validation
```

## Complexity Tracking
No constitution violations remain after this revision.

## Phase Breakdown & FR/SC Mapping

| Phase | Goal | Primary Tasks (mapped to FR/SC) | Deliverable |
|-------|------|--------------------------------|-------------|
| **0 – Data Acquisition & Validation** | Secure synthetic data, verify required variables. | FR‑001, FR‑009; verify presence of `spike_counts`, `trial_success`, `subject_id`, `day_index`. | Raw synthetic data streamed to `data/raw/`. |
| **1 – Preprocessing & Population Matrix** | Build stable matrices, exclude confounds. | FR‑002 (≥80 % stability), FR‑003 (exclude performance‑modulated units), FR‑009 (impute missing logs). | `NeuralPopulationMatrix` files (`data/processed/`). |
| **2 – Drift Quantification** | Compute RDMs and fit both Linear and Exponential models. | **FR‑004** (Pearson distance), **FR‑005** (Linear fit as primary output), **Constitution VII** (Exponential fit as primary predictor), **FR‑007** (multiple‑metric correction). **SC‑001** (synthetic validation). | `DriftResult` schema records (containing both `b_lin` and `b_exp`). |
| **3 – Behavioral Correlation & Hypothesis Testing** | Relate drift to learning speed. | FR‑006 (Pearson r, permutation test, LMM), FR‑007 (Bonferroni if >1 metric), **SC‑002** (p < 0.05 via A sizable number of k permutations.). Power check (N ≥ 15) → `power_warning` flag (SC‑005). | `CorrelationResult` schema record. |
| **4 – Robustness & Sensitivity** | Verify metric/threshold stability. | FR‑008 (threshold sweep from a moderate lower bound up to 0.90), FR‑003 (exclude performance‑modulated neurons check), FR‑009 (imputation sensitivity), **SC‑003** (sign consistency across metrics), **SC‑004** (drift stability across thresholds). | Plots in `docs/paper/`, summary CSV. |
| **5 – Reporting** | Generate reproducible outputs. | All SCs satisfied; produce CSV/JSON results, figures, and a concise markdown summary for downstream paper stage. | `data/results/`, `docs/paper/`. |

### Explicit Conflict‑Resolution Sub‑Task
- **Task T016‑A**: Implement the Linear regression fit `drift(t)=a+b·t` as the primary output to satisfy the functional requirements of the MVP (FR‑005).
- **Task T016‑B**: Implement the Exponential decay fit `drift(t)=a·exp(−b·t)+c` as the primary metric for the research hypothesis and learning-speed prediction (Constitution VII).
- **Task T016‑C**: Both fits must be computed for every subject. The `DriftResult` object will store both values. A configuration flag `config.primary_model` will determine which metric is used as the default input for the `CorrelationResult` analysis, ensuring that the pipeline can satisfy both the functional spec and the project constitution without contradiction.

All other functional requirements (FR‑001‑FR‑010) are addressed in the phases above. Success criteria (SC‑001‑SC‑005) are measured in the corresponding phases.