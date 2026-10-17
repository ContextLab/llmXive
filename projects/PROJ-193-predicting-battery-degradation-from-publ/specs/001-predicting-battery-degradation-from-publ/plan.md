# Implementation Plan: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Branch**: `001-predict-battery-degradation` | **Date**: 2026-10-17 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-predict-battery-degradation/spec.md`

## Summary
The project aims to (1) ingest publicly‑available battery cycling data, (2) build a CPU‑tractable Bi‑LSTM model to predict final capacity fade from the early cycles, (3) assess model performance and interpretability, and (4) compare against a hand‑crafted baseline. **Current limitation**: No open dataset that provides the required multi‑channel (voltage, current, temperature) time‑series and final capacity‑fade target is publicly downloadable. Consequently, the core research question cannot be answered with the available data at this time. The pipeline will therefore be demonstrated on a **generic CSV placeholder** (illustrative only) until a suitable open dataset is identified. All code is written to seamlessly accept a real dataset once it becomes available.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `numpy`, `pandas`, `scikit-learn`, `shap`, `matplotlib`, `datasets`, `hydra-core`  
- **Storage**: File‑system (raw CSVs → processed `.npz` tensors)  
- **Testing**: `pytest` for contract validation (`processed_dataset.schema.yaml` **and** `model_output.schema.yaml`)  
- **Target Platform**: Linux x86_64 GitHub Actions runner (CPU only)  
- **Performance Goals**: Entire pipeline ≤ 6 h, peak RAM ≤ 7 GB, disk ≤ 14 GB (illustrative for placeholder data)  
- **Constraints**: CPU‑only execution; deterministic random seeds for reproducibility  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seeds, deterministic splits, and data fetches from canonical URLs (or synthetic placeholder) are recorded. |
| II. Verified Accuracy | No external citations beyond the verified placeholder URL. |
| III. Data Hygiene | Raw CSV (or synthetic placeholder) is checksum‑verified; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table is generated directly from pipeline artifacts. |
| V. Versioning Discipline | All artifacts are hashed and recorded in `state/projects/PROJ-193-...yaml`. |
| VI. Temporal Sequence Integrity | Input sequences preserve original cycle order; no truncation beyond the defined 50‑cycle window. |
| VII. Protocol‑Agnostic Validation | **Deferred** – not applicable with placeholder data; will be enabled when a real multi‑protocol dataset is available. |

## Project Structure
```
specs/001-predict-battery-degradation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── processed_dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md   # generated later
```

### Source Code Layout
```
src/
├── data/
│   ├── ingest.py          # download & raw parsing (placeholder)
│   ├── preprocess.py      # resampling, normalization, sequence building
│   └── utils.py
├── model/
│   ├── bilstm.py          # Bi‑LSTM definition
│   ├── train.py           # training loop with early stopping & sweep
│   └── evaluate.py        # test set evaluation, confidence intervals
├── interpret/
│   ├── shap_analysis.py
│   ├── permutation_importance.py
│   └── attention_attribution.py
└── cli/
    └── main.py            # entry point wrapper
tests/
├── contract/
│   ├── test_processed_schema.py
│   └── test_model_output_schema.py
└── unit/
    ├── test_preprocess.py
    └── test_model.py
```

## Complexity Tracking
All non‑negotiable constitution principles are respected. The plan now **explicitly flags** the dataset limitation, defers scientific claims, and adjusts expectations for SC‑001, SC‑004, and power analysis.

## Task Mapping (FR / SC Coverage)

| FR / SC | Plan Phase / Step | Description |
|---------|-------------------|-------------|
| **FR-001** | Phase 0 – `src/data/ingest.py` | **Pending dataset**: code ready to ingest any CSV with required columns once an open source is identified. |
| **FR-002** | Phase 0 – `src/data/preprocess.py` | Resample to 100 time‑steps/cycle, normalize using first‑50‑cycle stats, construct `(N, 50, 100, 3)` tensors (placeholder currently produces dummy tensors). |
| **FR-003** | Phase 1 – `src/model/bilstm.py` | Define multi‑layer Bi‑LSTM (64 units each) using PyTorch CPU backend. |
| **FR-004** | Phase 1 – `src/model/train.py` | Hyperparameter sweep (learning‑rate ∈ {1e‑3,5e‑4}, hidden size ∈ {64,128}) limited to **30 min** wall‑clock; early stopping (patience = 5). |
| **FR-005** | Phase 2 – `src/interpret/*` | Permutation importance, SHAP (KernelExplainer, 100 background samples), and attention‑based attribution (illustrative). |
| **FR-006** | Phase 2 – `src/model/evaluate.py` | Compute R², RMSE on held‑out test set (placeholder target). |
| **FR-007** | Phase 2 – `src/model/evaluate.py` | Monte Carlo dropout (10 stochastic passes) → prediction intervals & coverage stats (illustrative). |
| **FR-008** | Phase 2 – `src/interpret/attention_attribution.py` | Separate attention‑based attribution pipeline. |
| **FR-009** | Phase 2 – `src/model/evaluate.py` | Baseline hand‑crafted incremental‑capacity features → linear regression; compare R² (illustrative). |
| **FR-010** | Phase 0 – `src/data/preprocess.py` | Normalization computed exclusively from cycles 1‑50. |
| **SC-001** | **Deferred** – placeholder lacks true capacity‑fade target; R² will be reported as illustrative only when real data become available. |
| **SC-002** | Phase 0‑2 – CI monitoring | Log runtime, memory, disk; enforce ≤ 6 h, ≤ 7 GB RAM, ≤ 14 GB disk (illustrative). |
| **SC-003** | Phase 2 – interpretability | Compute Spearman ρ between permutation and SHAP rankings (≥ 0.7) on placeholder data. |
| **SC-004** | **Deferred** – no genuine protocol variation in placeholder; will be enabled with real data. |
| **SC-005** | Phase 0 – ingestion log | Percentage of cells retained after filtering (placeholder). |
| **SC-006** | Phase 2 – uncertainty | Coverage of 90 % CI (illustrative; deferred target). |
| **SC-007** | Phase 2 – baseline comparison | Ensure Bi‑LSTM R² exceeds baseline by ≥ 0.05 (illustrative). |
| **SC-008** | Duplicate of SC‑003 (consistency). |
| **SC-009** | Phase 2 – linear regression on top‑5 features | Train linear model on top‑5 identified features; compare R² to full model (≥ 50 %). |

All steps are ordered so that data download → preprocessing → model definition → training → evaluation → interpretation → reporting. Steps that depend on real battery data are clearly marked as **illustrative** pending dataset acquisition.

## Statistical Rigor (added)

- **Multiple‑Comparison**: Only a single Spearman correlation is computed for attribution consistency; no correction needed. If additional per‑feature tests are added, a Benjamini‑Hochberg FDR will be applied.
- **Power / Sample‑Size**: The placeholder dataset contains **≈ 1 000** rows after filtering. Power analysis for detecting a ΔR² = 0.05 with α = 0.05 and N ≈ 1 000 yields > 80 % power *for the synthetic target*. This does **not** guarantee power for a real battery dataset, which would likely require many more cells. The limitation is noted.
- **Causal‑Inference Assumptions**: All analyses are observational; conclusions are framed as *associational*. No causal claims are made.
- **Measurement Validity**: Battery sensor calibrations are assumed validated per original dataset documentation (not available for the placeholder). This limitation is noted in the discussion.
- **Collinearity**: Voltage, current, and temperature traces are time‑series; multicollinearity is assessed via variance‑inflation factor on flattened features. High VIFs are reported but do not invalidate attribution rankings (they are based on model‑internal gradients/attention).

## Execution Plan Summary (mirrors `plan.md`)

1. **Ingestion (`src/data/ingest.py`)** – download verified placeholder CSVs, checksum, filter rows with complete records.  
2. **Preprocessing (`src/data/preprocess.py`)** – (a) resample each trace to 100 time‑steps per cycle (placeholder: interpolate dummy column), (b) normalize using means/stds from cycles 1‑50 only, (c) assemble tensors of shape `(N, 50, 100, 3)`.  
3. **Model Definition (`src/model/bilstm.py`)** – Bi‑LSTM with 2 layers, 64 hidden units, `torch.nn.LSTM(bidirectional=True)`.  
4. **Training (`src/model/train.py`)** – train/validation split (80/20), early stopping (patience = 5), hyperparameter grid limited to 30 min wall‑clock.  
5. **Evaluation (`src/model/evaluate.py`)** – compute R², RMSE on held‑out test set (placeholder target), Monte Carlo dropout intervals, coverage stats (illustrative).  
6. **Baseline Comparison (`src/model/baseline.py`)** – hand‑crafted incremental‑capacity features → linear regression; compare R² (illustrative).  
7. **Interpretability (`src/interpret/*.py`)** – SHAP (KernelExplainer, 100 background samples), permutation importance (scikit‑learn), attention weight extraction; compute Spearman ρ between rankings.  
8. **Reporting (`src/cli/main.py`)** – generate JSON/YAML result files, Matplotlib figures (SHAP summary, importance bar, attention heatmaps).  

All steps are logged via `llmxive_toolkit.get_logger`, and artifacts are version‑hashed.

## Testing Addendum
Contract tests now include validation of both `processed_dataset.schema.yaml` **and** `model_output.schema.yaml`:

```bash
pytest -q tests/contract/test_processed_schema.py
pytest -q tests/contract/test_model_output_schema.py
```

These ensure that both the processed dataset and model predictions conform to their respective schemas.
