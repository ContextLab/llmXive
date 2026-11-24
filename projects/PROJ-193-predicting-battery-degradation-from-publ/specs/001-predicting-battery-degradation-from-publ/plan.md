# Implementation Plan: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Branch**: `001-predict-battery-degradation` | **Date**: 2026-10-25 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-predict-battery-degradation/spec.md`

## Summary
The project must ingest the **NASA Ames Battery Dataset** (public CSV bundle) or fall back to the **University of Wisconsin Battery Repository** if the primary dataset fails validation, build normalized early‑cycle sequences (initial early cycles, a uniform set of time‑steps per cycle, three channels), train a CPU‑only 2‑layer Bi‑LSTM with an attention head (64 units per layer) on the processed sequences, and generate interpretability artefacts (SHAP, permutation importance, attention‑weight analysis, Integrated Gradients) that support the scientific question: *Which early‑cycle electrochemical signatures are **associated with** later capacity fade?* All steps respect the functional requirements (FR‑001‑FR‑018) as defined in the specification. The plan also satisfies every success‑criterion (SC‑001‑SC‑013) and adheres to the project constitution.

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
| I. Reproducibility | All random seeds are pinned; data is fetched from a canonical URL (NASA Ames) or fallback (UW). Pipelines are deterministic. |
| II. Verified Accuracy | Dataset source is a verified public URL; no new citations introduced. |
| III. Data Hygiene | Raw CSVs are checksummed, and every transformation produces a new file with provenance metadata. |
| IV. Single Source of Truth | Figures, tables, and metrics are generated directly from pipeline artefacts; no hand‑typed numbers. |
| V. Versioning Discipline | Every artifact (`data/processed/*.npz`, `models/*.pt`) is named with a content hash; `state/projects/...yaml` is updated on change. |
| VI. Temporal Sequence Integrity | Input sequences preserve full cycle order; resampling only interpolates within each cycle. |
| VII. Protocol‑Agnostic Validation | Held‑out test set contains entire protocol families unseen during training (≥ 10 cells, ≥ 2 protocols). |
| VIII. Causal Framing | All attribution results (SHAP, permutation, attention) are reported **as associational**. The propensity‑score analysis (FR‑018) is exploratory; any “causal effect” language is avoided and results are labelled as **associational** with an explicit disclaimer (see research.md). |

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
│   ├── ingest.py          # download with retry×3, checksum, filter incomplete cells, **validate dataset size & protocol diversity (FR‑011)**, fallback to UW repo
│   ├── preprocess.py      # resample, leak‑free normalization (first 50 cycles) per FR‑002, split, **create calibration split** for split‑conformal prediction, **create causal‑analysis split**
│   └── utils.py
├── model/
│   ├── bilstm.py          # 2‑layer Bi‑LSTM (64 units) + attention head
│   ├── train.py           # Adam, early stopping, 30‑min hyper‑parameter sweep
│   ├── evaluate.py        # R², RMSE, MC‑dropout intervals, **split‑conformal calibration**, **causal‑analysis split** handling
│   └── baseline.py        # incremental‑capacity baseline (cycles 1‑50 only, FR‑016)
├── interpret/
│   ├── shap_analysis.py
│   ├── permutation_importance.py
│   ├── integrated_gradients.py
│   ├── attention_attribution.py   # extracts attention weights per time‑step/channel
│   ├── feature_aggregation.py     # aggregates raw attributions to per‑cycle/channel & derives signatures
│   ├── literature_mapping.py      # maps derived signatures to literature‑cited features
│   └── causal_analysis.py         # propensity‑score matching on **causal‑analysis split**; results reported as associational
└── cli/
    └── main.py
```

## Complexity Tracking
All functional requirements are directly mapped to concrete phases. No constitution violations beyond the **data‑availability gap** (now mitigated by dataset validation and fallback). All other FR/SC items are directly addressed.

## Task Mapping (FR / SC Coverage)

| ID | Plan Phase / Script | Notes |
|----|--------------------|-------|
| **FR-001** | `src/data/ingest.py` | Downloads NASA Ames dataset (verified URL) and validates that it contains **≥ 30 cells**, **≥ 2 protocols**, and **≥ 150 cycles** per cell (FR‑011). Falls back to UW repository if validation fails. aborts with clear error if both fail. |
| **FR-002** | `src/data/preprocess.py` | Resamples to 100 steps/cycle, normalizes using stats from cycles 1‑50 only, builds `(N, 50, 100, 3)` tensors, computes fade using **cycle 150** (or first > 100). |
| **FR-003** | `src/model/bilstm.py` | Plain Bi‑LSTM, CPU‑only, no GPU. |
| **FR-004** | `src/model/train.py` | Adam optimizer, early stopping, 30‑min hyper‑parameter sweep (lr & hidden size). Fallback defaults on timeout. |
| **FR-005** | `src/interpret/*` | SHAP, permutation importance, Integrated Gradients, **attention‑weight analysis**. |
| **FR-006** | `src/model/evaluate.py` | Computes R², RMSE on full test set and unseen‑protocol subset. |
| **FR-007** | `src/model/evaluate.py` | Monte‑Carlo dropout (10 passes) + **split‑conformal calibration** (using dedicated calibration split) → prediction intervals. |
| **FR-008** | `src/interpret/attention_attribution.py` | Extracts attention weights from the Bi‑LSTM attention head for interpretability. |
| **FR-011** | `src/data/preprocess.py` | Protocol‑family hold‑out split (≥ 30 cells, ≥ 2 protocols, ≥ 10 cells in unseen set). |
| **FR-012** | Whole pipeline | No synthetic data; fixtures used only for unit tests. |
| **FR-015** | `src/interpret/feature_selection.py` | Performs feature‑selection **only** on the training split; downstream linear regression evaluated on a distinct held‑out validation subset (≥ 5 cells). |
| **FR-016** | `src/model/evaluate.py` | Computes baseline R² (incremental‑capacity) and verifies Bi‑LSTM improvement ≥ 5 % absolute (SC‑011). |
| **FR-017** | `src/interpret/feature_aggregation.py` | Generates protocol‑specific top‑5 signature rankings (SC‑012). |
| **FR-018** | `src/interpret/causal_analysis.py` | Propensity‑score matching across protocols using **all observed covariates** (chemistry, manufacturer, initial capacity, protocol metadata, cell dimensions, electrode composition). Results are reported **as associational** with an explicit disclaimer (see Constitution Check). |
| **SC-001** | `src/model/evaluate.py` | R² measured against real measured fade (NASA Ames). |
| **SC-002** | `src/model/train.py` & `src/model/evaluate.py` | Logs runtime, peak RAM, disk usage; reported after real run. |
| **SC-004** | `src/model/evaluate.py` | R² ≥ 0.80 on unseen‑protocol test set (≥ 10 cells). |
| **SC-005** | `src/data/ingest.py` | Completeness ratio logged (processed / downloaded). |
| **SC-006** | `src/model/evaluate.py` | Coverage of calibrated intervals; target ≥ 0.90. |
| **SC-009** | `src/interpret/feature_aggregation.py` & `src/model/evaluate.py` | Linear regression on top‑aggregated features (selected on training split, evaluated on distinct held‑out set); BH‑FDR correction applied. |
| **SC-010** | `src/interpret/literature_mapping.py` | Checks that ≥ 3 of the top‑5 aggregated features match known early‑cycle degradation markers (Severson et al. 2019, etc.). |
| **SC-011** | `src/model/evaluate.py` | Baseline R² ≥ 5 % lower than Bi‑LSTM R² (FR‑016). |
| **SC-012** | `src/interpret/feature_aggregation.py` | Protocol‑specific ranking variance quantified (Kendall‑τ ≥ 0.3). |
| **SC-013** | `src/interpret/causal_analysis.py` | Reports average treatment effect estimates with 95 % CI; at least one feature shows a **significant association** (p < 0.05). Results are labeled **associational**, not causal. |

## Execution Plan Summary

1. **Phase 0 – Scaffolding**: Pin requirements, create module skeletons, configure logger.  
2. **Phase 1 – Data Pipeline** (`ingest.py`, `preprocess.py`):  
   - Download NASA Ames CSV bundle with retry ×3 (60 s back‑off), checksum raw files.  
   - **Validate** that the dataset meets FR‑011 (≥ 30 cells, ≥ 2 protocols, ≥ 150 cycles each). If the primary source fails, automatically switch to the University of Wisconsin Battery Repository (verified open URL). Abort with clear error if both sources fail.  
   - Filter cells lacking required cycles or missing end‑of‑life capacity.  
   - Resample each cycle to **100 uniform time‑steps**.  
   - Normalize **per cell** using statistics from **cycles 1‑50** only (FR‑002).  
   - Compute `target_fade` using **cycle 150** (or first > 100) per the revised definition.  
   - Create train/val split, **held‑out protocol test split**, **calibration split** (for split‑conformal prediction), and **causal‑analysis split** (distinct from training/validation/test).  
3. **Phase 2 – Model** (`bilstm.py`, `train.py`):  
   - Plain 2‑layer Bi‑LSTM (CPU) with an attention head (FR‑003, FR‑008).  
   - Adam, early stopping on validation loss.  
   - 30‑min hyper‑parameter sweep (learning rate ∈ {1e‑3, 5e‑4}, hidden size ∈ {64, 128}); defaults used if sweep exceeds 30 min.  
4. **Phase 3 – Evaluation & Interpretation** (`evaluate.py`, `baseline.py`, `interpret/*`):  
   - R²/RMSE on full test and unseen‑protocol subsets (SC‑004).  
   - MC‑dropout (10 passes) + **split‑conformal calibration** (using the dedicated calibration split) → [deferred] prediction‑interval coverage (SC‑006).  
   - Power analysis for ΔR² = 0.05 (statistical‑rigor, not a FR).  
   - SHAP (KernelExplainer, ≤ 100 background, ≤ 500 eval), permutation importance, Integrated Gradients, **attention‑weight analysis**.  
   - `feature_aggregation.py` collapses raw attributions to per‑cycle/channel scores and derives early‑cycle signatures.  
   - Linear regression on top‑5 aggregated signatures (selected on training split) evaluated on a distinct held‑out validation set; BH‑FDR correction applied.  
   - `causal_analysis.py` performs propensity‑score matching on the **causal‑analysis split** using **all observed covariates**; results are reported **as associational** with an explicit disclaimer.  
5. **Phase 4 – Contracts & reporting**:  
   - Validate processed dataset and model output against JSON‑Schema contracts.  
   - Generate `results/predictions.json`, figures, and a concise evidence summary.

Ordering respects data download → preprocessing → model fitting → evaluation → figure generation.

## Constitution Alignment Summary
All steps obey the seven core principles. The **data‑availability gap** is closed by the explicit dataset‑validation step and fallback dataset. All FR/SC items are directly addressed.
