# Implementation Plan: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Branch**: `001-predict-battery-degradation` | **Date**: 2026-10-25 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-predict-battery-degradation/spec.md`

## Summary
The project must ingest the **NASA Ames Battery Dataset** (public CSV bundle), build normalized early‑cycle sequences (initial early cycles, A uniform set of time‑steps per cycle., three channels), train a CPU‑only 2‑layer Bi‑LSTM with an attention head (64 units per layer) on the processed sequences, and generate interpretability artefacts (SHAP, permutation importance, attention‑weight analysis, Integrated Gradients) that support the scientific question: *Which early‑cycle electrochemical signatures are **associated with** later capacity fade?* All steps must be reproducible, respect data‑hygiene, and satisfy every functional (FR‑001‑FR‑015) and success‑criteria (SC‑001‑SC‑010) item.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `numpy`, `pandas`, `scikit-learn`, `shap`, `matplotlib`, `statsmodels`, `jsonschema`  
- **Storage**: `data/raw/` (immutable CSVs, checksummed), `data/processed/` (NPZ tensors, versioned)  
- **Testing**: `pytest` + contract validation (`tests/contract/`)  
- **Target Platform**: GitHub Actions free‑tier (2 CPU cores, ≤7 GB RAM, ≤14 GB disk, ≤6 h)  
- **Performance Goals**: Bi‑LSTM + attention training ≤30 min wall‑clock; full pipeline ≤5 h  
- **Constraints**: CPU‑only (FR‑003), no synthetic data (FR‑012)  

> **Reviewer‑driven adjustment** – The target fade is now defined as  
> \[
> \text{fade} = \frac{Q_{\text{initial}} - Q_{\text{final}}}{Q_{\text{initial}}}
> \]  
> where `Q_initial` is capacity at cycle 1 and `Q_final` is the capacity at **cycle 150** (or the first cycle > 100 if a cell does not reach 150). This prevents any overlap with the predictor window (cycles 1‑50) and eliminates label leakage.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned; data is fetched from a canonical URL (NASA Ames). Pipelines are deterministic. |
| II. Verified Accuracy | Dataset source is a verified public URL; no new citations introduced. |
| III. Data Hygiene | Raw CSVs are checksummed; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Figures, tables, and metrics are generated directly from pipeline artefacts; no hand‑typed numbers. |
| V. Versioning Discipline | Every artifact (`data/processed/*.npz`, `models/*.pt`) is named with a content hash; `state/projects/...yaml` is updated on change. |
| VI. Temporal Sequence Integrity | Input sequences preserve full cycle order; resampling only interpolates within each cycle. |
| VII. Protocol‑Agnostic Validation | Held‑out test split contains entire protocol families unseen during training (≥ 10 cells, ≥ 2 protocols). |
| VIII. Causal Framing | All attribution claims are explicitly labeled **associational**; we perform protocol‑stratified sensitivity analyses to assess robustness without asserting causality. |

## Project Structure
```text
specs/001-predict-battery-degradation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── processed_dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

src/
├── data/
│   ├── ingest.py          # download with retry×3, checksum, filter incomplete cells
│   ├── preprocess.py      # resample, leak‑free normalization (first several cycles), split
│   └── utils.py
├── model/
│   ├── bilstm.py          # 2‑layer Bi‑LSTM (64 units) + attention head
│   ├── train.py           # Adam, early stopping, 30‑min hyper‑parameter sweep
│   ├── evaluate.py        # R², RMSE, MC‑dropout intervals, split‑conformal calibration
│   └── baseline.py        # incremental‑capacity baseline (cycles 1‑50 only)
├── interpret/
│   ├── shap_analysis.py
│   ├── permutation_importance.py
│   ├── integrated_gradients.py
│   ├── attention_attribution.py   # extracts attention weights per time‑step/channel
│   ├── feature_aggregation.py     # aggregates raw attributions to per‑cycle/channel & derives signatures
│   └── literature_mapping.py      # maps derived signatures to literature‑cited features
└── cli/
    └── main.py
```

## Complexity Tracking
All functional requirements are directly mapped to concrete phases. No constitution violations beyond the **data‑availability gap** (now resolved by using NASA Ames). All other FR/SC items are directly addressed.

## Task Mapping (FR / SC Coverage)

| ID | Plan Phase / Script | Notes |
|----|--------------------|-------|
| **FR-001** | `src/data/ingest.py` | Downloads NASA Ames Battery Dataset (verified URL). |
| **FR-002** | `src/data/preprocess.py` | Resamples to 100 steps/cycle, normalizes using stats from first 50 cycles, builds `(N, 50, 100, 3)` tensors, computes fade using **cycle 150** (or first > 100). |
| **FR-003** | `src/model/bilstm.py` | Plain Bi‑LSTM, CPU‑only, no GPU. |
| **FR-004** | `src/model/train.py` | Adam optimizer, early stopping, 30‑min hyper‑parameter sweep (lr & hidden size). Fallback defaults on timeout. |
| **FR-005** | `src/interpret/*` | SHAP, permutation importance, Integrated Gradients, **attention‑weight analysis**. |
| **FR-006** | `src/model/evaluate.py` | Computes R², RMSE on full test set and unseen‑protocol subset. |
| **FR-007** | `src/model/evaluate.py` | Monte‑Carlo dropout (10 passes) + split‑conformal calibration → prediction intervals. |
| **FR-008** | `src/interpret/attention_attribution.py` | Extracts attention weights from the Bi‑LSTM attention head for interpretability. |
| **FR-009** | `src/model/baseline.py` & `src/model/evaluate.py` | Baseline incremental‑capacity features (cycles 1‑50) evaluated on disjoint held‑out set. |
| **FR-010** | `src/data/preprocess.py` | Normalization statistics computed **only** from cycles 1‑50. |
| **FR-011** | `src/data/preprocess.py` | Protocol‑family hold‑out split (≥ 30 cells total, ≥ 2 protocols, ≥ 10 cells in unseen set). |
| **FR-012** | Whole pipeline | No synthetic data; fixtures used only for unit tests. |
| **FR-013** | `contracts/processed_dataset.schema.yaml` & `contracts/model_output.schema.yaml` | Contract tests under `tests/contract/`. |
| **FR-014** | `src/model/evaluate.py` | Post‑hoc power analysis for detecting ΔR² = 0.05 at α = 0.05 using actual test‑set size; if achieved power < 0.8, limitation is reported and ΔR² is presented with a 95 % confidence interval (methodology‑eecdef0d). |
| **FR-015** | `src/interpret/feature_selection.py` | Performs feature‑selection **only** on the training split; downstream linear regression evaluated on a distinct held‑out validation subset (≥ 5 cells). |
| **SC-001** | `src/model/evaluate.py` | R² measured against real measured fade (NASA Ames). |
| **SC-002** | `src/model/train.py` & `src/model/evaluate.py` | Logs runtime, peak RAM, disk usage; reported after real run. |
| **SC-004** | `src/model/evaluate.py` | R² ≥ 0.80 on unseen‑protocol test set (≥ 10 cells). |
| **SC-005** | `src/data/ingest.py` | Completeness ratio logged (processed / downloaded). |
| **SC-006** | `src/model/evaluate.py` | Coverage of calibrated intervals; target ≥ 0.90. |
| **SC-009** | `src/interpret/feature_aggregation.py` & `src/model/evaluate.py` | Linear regression on top‑aggregated features (selected on training split, evaluated on distinct held‑out set); BH‑FDR correction applied. |
| **SC-010** | `src/interpret/literature_mapping.py` | Checks that ≥ 3 of the top‑5 aggregated features match literature signatures (Severson et al. 2019, etc.). |

## Execution Plan Summary
1. **Phase 0 – Scaffolding**: Pin requirements, create module skeletons, configure logger.  
2. **Phase 1 – Data Pipeline** (`ingest.py`, `preprocess.py`):  
   - Download NASA Ames CSV bundle with retry ×3 (60 s back‑off), checksum raw files.  
   - Filter cells lacking ≥ 150 cycles or missing end‑of‑life capacity.  
   - Resample each cycle to 100 uniform time‑steps, normalize using statistics from cycles 1‑50 only.  
   - Build tensors `(N, 50, 100, 3)` and compute fade using **cycle 150** (or first > 100).  
   - Split into train/val (80/20 stratified by protocol) and held‑out protocol test (≥ 10 cells, ≥ 2 protocols).  
3. **Phase 2 – Model** (`bilstm.py`, `train.py`):  
   - Plain 2‑layer Bi‑LSTM (64 units) **plus** an attention head, `device="cpu"`.  
   - Adam optimizer, early stopping on validation loss.  
   - 30‑min hyper‑parameter sweep (learning rate ∈ {1e‑3, 5e‑4}, hidden size ∈ {64, 128}); defaults used if time exceeded.  
4. **Phase 3 – Evaluation & Interpretation** (`evaluate.py`, `baseline.py`, `interpret/*`):  
   - Compute R², RMSE on full test and unseen‑protocol subsets.  
   - MC‑dropout (10 passes) + **split‑conformal calibration** → [deferred] prediction‑interval coverage (SC‑006).  
   - Power analysis for ΔR² = 0.05 (FR‑014).  
   - SHAP (KernelExplainer, ≤ 100 background, ≤ 500 eval), permutation importance, Integrated Gradients, **attention‑weight analysis**.  
   - `feature_aggregation.py` collapses raw attributions to per‑cycle/channel scores and derives early‑cycle signatures (voltage variance, current slope, temperature fluctuation).  
   - Linear regression on top‑5 aggregated features (selected on training split) evaluated on a distinct held‑out set; BH‑FDR correction applied.  
   - `literature_mapping.py` matches derived signatures to known degradation markers; reports ≥ 3 matches.  
5. **Phase 4 – Contracts & Reporting**:  
   - Validate processed dataset and model output against JSON‑Schema contracts.  
   - Generate `results/predictions.json`, figures, and a concise evidence summary.  

Ordering respects data download → preprocessing → model fitting → evaluation → figure generation.

## Constitution Alignment Summary
All steps obey the seven core principles. The **data‑availability gap** is closed by using the NASA Ames Battery Dataset, a verified open source. All other FR/SC items are directly addressed.

---

