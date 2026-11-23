# Implementation Plan: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Branch**: `001-statistical-chess-elo-analysis` | **Date**: 2026-10-16 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-statistical-chess-elo-analysis/spec.md`

## Summary
Implement a reproducible, CPU‑only pipeline that (1) downloads an open chess PGN dataset, (2) extracts the required features, (3) computes Elo‑based expected win probabilities and outcome deviations **(if the dataset provides ratings and move‑time metadata; otherwise the pipeline aborts and the research question is revised)**, (4) fits **Beta Regression** and Ridge regression models, (5) applies Benjamini‑Hochberg FDR correction, (6) performs 5‑fold cross‑validation with explicit variance targets, (7) generates diagnostic visualizations, (8) outputs schema‑validated artifacts, and (9) records checksums for all data files. All steps respect the project's constitution and explicitly abort if the dataset does not contain the required variables.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `python-chess`, `matplotlib`, `seaborn`, `datasets`, `requests`, `tqdm`, `checksumdir`  
- **Storage**: CSV/Parquet files under `data/` (raw, processed, outputs)  
- **Testing**: `pytest` (contract, unit, integration)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤6 h)  
- **Project Type**: Batch data‑science pipeline (no GPU required)  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed `requirements.txt`, seeded randomness, deterministic parsing. |
| II. Verified Accuracy | ✅ | All external data sources are from the verified HuggingFace URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | ✅ | Raw files are checksummed; each transformation writes a new file; no in‑place edits. |
| IV. Single Source of Truth | ✅ | Every figure/table derives from a single row in `data/` and a single block in `code/`. |
| V. Versioning Discipline | ✅ | Content hashes recorded in the project state file (handled by CI). |
| VI. PGN Parsing Consistency | ✅ | One deterministic parser (`src/data/parse.py`) for all games. |
| VII. Outcome Deviation Integrity | ✅ | Expected probabilities use only pre‑game ratings; no leakage from game‑specific features. |

## Project Structure
```text
specs/001-statistical-chess-elo-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── game_record.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

src/
├── data/
│   ├── download.py          # Handles dataset download with verification & backoff, checksum generation
│   ├── parse.py             # `parse_pgn_stream` → TypedDict `GameRecord`
│   └── process.py           # Cleaning, feature engineering, inclusion metrics, ECO collapsing
├── models/
│   ├── fit.py               # Beta Regression & Ridge regression
│   ├── validate.py          # CV, diagnostics, sensitivity sweep
│   └── metrics.py           # Wald/LRT tests, Benjamini‑Hochberg correction
├── reports/
│   ├── generate_plots.py    # Residuals, predicted vs actual, feature importance
│   └── sensitivity.py       # Threshold sweep reporting
├── validation/
│   └── validate_contracts.py
├── main.py                  # Orchestration script
└── config.py                # Global config (seeds, thresholds, paths)

tests/
├── contract/
│   ├── test_game_record.py
│   └── test_model_output.py
├── unit/
│   ├── test_parsers.py
│   └── test_calculations.py
└── integration/
    └── test_pipeline.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **0️⃣ Dataset Verification** | Download verified dataset, **generate SHA256 checksums** for raw files, confirm presence of `white_rating`, `black_rating`, `eco_code`, `move_times`, `outcome`. Abort with clear error if any are missing. | FR‑001, FR‑002, FR‑003, FR‑004, **SC‑001 (≥ 95 % inclusion)** | SC‑001 |
| **1️⃣ Ingestion & Parsing** (`src/data/download.py` + `src/data/parse.py`) | Stream PGN, extract ECO, per‑move times, **material_imbalance_move10**, compute Elo expectation & deviation **if ratings are present**. | FR‑001‑FR‑004 | SC‑001 |
| **2️⃣ Cleaning & Inclusion Metrics** (`src/data/process.py`) | Drop games missing move‑time metadata, compute inclusion counts JSON, record inclusion rate (must be ≥ 95 %). | FR‑001, Edge‑Case 3 | SC‑001 |
| **3️⃣ Contract Validation** (`src/validation/validate_contracts.py`) | Validate `GameRecord` against `game_record.schema.yaml` (mapped to FR‑001 as a data‑integrity check). | — | — |
| **4️⃣ Feature Collapsing** (`src/data/process.py`) | Map ECO codes to families, create one‑hot or ordinal encoding, compute time‑control covariate. | FR‑011 | — |
| **5️⃣ Modeling** (`src/models/fit.py`) | Fit **Beta Regression** (statsmodels) on the transformed outcome ( `(outcome_deviation+1)/2` ) and **Ridge Regression** (scikit‑learn). Exclude raw `white_rating`/`black_rating` from predictor set to avoid circularity. | FR‑005, **FR‑005 (Beta)**, FR‑007 (significance) | SC‑002 |
| **6️⃣ Significance Testing** (`src/models/metrics.py`) | Wald Z‑tests for Beta coefficients, bootstrapped t‑stats for Ridge; **Benjamini‑Hochberg FDR** across all raw p‑values (FR‑009). | FR‑007, FR‑009 | SC‑002 |
| **7️⃣ Cross‑Validation** (`src/models/validate.py`) | 5‑fold CV (k=5) on the full feature set; record R², AIC, and CV‑score distribution. **Target:** standard deviation of R² < 0.05 (SC‑003). | FR‑006 | SC‑003 |
| **8️⃣ Sensitivity Analysis** (`src/models/validate.py`) | Sweep corrected p‑thresholds `{0.005, 0.01, 0.05}`; compute Jaccard index of significant‑feature sets (target ≥ 0.8, SC‑004). | FR‑010 | SC‑004 |
| **9️⃣ Diagnostics** (`src/reports/generate_plots.py`) | Residual, predicted‑vs‑actual, feature‑importance plots (Ridge coefficient magnitude). | FR‑008 | — |
| **🔟 Output & Reporting** | Write `model_output.schema.yaml`‑validated CSV/JSON, store plots, generate inclusion metrics JSON, **record checksums** for all outputs. | FR‑009‑FR‑010 | SC‑005 |
| **⚙️ Runtime Guardrails** | Memory profiling (`memory_profiler`), ruff linting (`ruff check --select T20`), exponential backoff for API. Mapped to FR‑001 (data hygiene) and Constitution Principle III. | — | — |

## Compute Feasibility
- **Memory**: Streaming ingestion; if total size > 7 GB, a stratified random sample of 100 k games (≈ 1 GB) is taken. All DataFrames use `float32`/`int16` where possible.
- **CPU**: All libraries are pure‑CPU; no CUDA imports. Estimated total runtime < 2 h for 100 k games.
- **GPU**: Not required. (If future extensions need a transformer, the plan would switch to the Kaggle GPU escape hatch—but not needed now.)

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified dataset lacks required columns (ratings or move times) | Fatal – cannot compute Elo expectations | Phase 0 aborts with clear error; issue logged for downstream revision. |
| Missing move‑time metadata | Reduced sample size; may affect power | Exclude such games; pilot power analysis (20 k sample) will flag insufficient power. |
| Memory overflow | CI crash | Streaming + optional stratified sampling; dtype optimization. |
| Numerical instability in probability caps | Division‑by‑zero / log‑of‑zero errors | Clamp expected probabilities to `[0.0001, 0.9999]`. |
| Under‑powered analysis | Non‑significant results | Larger pilot (20 k) and explicit power‑analysis gate; report limitation if needed. |
| Confounding by time‑control or rating distribution | Spurious associations | Include time‑control and rating‑distribution covariates; later exclude them from primary inference. |
| Dataset unavailability | Blocking | Pipeline aborts and research question is revised (see Research). |

---

