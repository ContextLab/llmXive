# Implementation Plan: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Branch**: `001-predict-material-properties-compositional-gnn` | **Date**: 2026-10-24 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/001-predict-material-properties-compositional-gnn/spec.md`

## Summary

Deliver a reproducible CPU‑only pipeline that (1) loads an **open, verified Matbench Expt Gap dataset** in a memory‑safe chunked fashion, (2) builds a composition‑only fully‑connected element graph per material (including element‑fraction as a node feature), (3) trains a lightweight GNN (≤3 GCN layers, hidden ≤128) with 5‑fold crystal‑system‑stratified cross‑validation, (4) benchmarks against both a Random Forest baseline **and** a **structure‑aware GNN baseline**, (5) provides an inference entry point for arbitrary formulas, and (6) extracts node embeddings for PCA‑correlation interpretability. The hardness target is currently omitted because no open dataset provides a verified hardness column; the schema now permits null hardness, and the limitation is flagged for a future spec amendment. The plan therefore quantifies information loss for **band‑gap only**; hardness will be added once an appropriate open source is identified.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `pymatgen==2024.7.0`, `matminer==0.9.0`, `psutil==5.9.8`, `pytest==8.3.2`, `jsonschema==4.23.0`  
**Storage**: Files under `data/` (raw, processed, results) and model checkpoints under `outputs/`  
**Testing**: pytest (contract + unit) with junit XML + tee‑ed logs as verification evidence  
**Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU, ~7 GB RAM, ~tens of GB disk) – CPU‑only, no GPU escape hatch required  
**Constraints**: CPU‑only; no credentials; all random seeds pinned; no fabricated data – the pipeline runs against the **Matbench Expt Gap** dataset (publicly downloadable via `datasets.load_dataset("matbench_expt_gap")`).  

## Constitution Check

| Principle | Status | How addressed |
|-----------|--------|---------------|
| I. Reproducibility | **PASS** | Seeds pinned, deterministic code, dataset fetched from a canonical open source on every run. |
| II. Verified Accuracy | PASS | No unverified citations; dataset source is a verified HuggingFace‑hosted Matbench dataset. |
| III. Data Hygiene | PASS | Checksums recorded, transformations produce new files, no PII. |
| IV. Single Source of Truth | PASS | Each metric derives from a single JSON artifact; no hand‑typed numbers. |
| V. Versioning Discipline | PASS | Content hashes stored in project state; checkpoints named with hash. |
| VI. Compositional vs. Structural Information Quantification | **PASS** | Structure‑aware GNN baseline is trained on the same Matbench subset; ΔR², ΔMAE, ΔRMSE between composition‑only and structure‑aware models are computed and stored in `comparison_summary.csv`. |
| VII. Crystal‑System Stratified Evaluation | PASS | Stratified split and per‑system metrics implemented. |

## Project Structure

```text
specs/001-predict-material-properties-compositional-gnn/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── materials_dataset.schema.yaml
│   └── model_metrics.schema.yaml
└── tasks.md   # generated later

src/
├── data/
│   ├── loader.py            # validate_row(), drop_outliers_iqr(), load_and_clean()
│   └── periodic_table.py    # element property lookup
├── graphs/
│   ├── composition.py       # composition‑only graph builder (5 node features)
│   └── structure.py         # structure‑aware graph builder (atom positions, coordination)
├── models/
│   ├── gnn.py               # ≤3 GCNConv layers, edge_weight, hidden≤128
│   ├── rf_baseline.py       # RandomForestRegressor
│   └── gnn_structure.py     # structure‑aware GNN (uses atom positions from Matbench)
├── training/
│   ├── split.py             # crystal‑system stratified 80/10/10 + 5‑fold CV
│   ├── train_gnn.py         # Adam lr=1e‑3, early stopping patience=10, runtime guards
│   ├── train_structure_gnn.py # same config, uses structure graphs
│   └── evaluate.py          # R²/MAE/RMSE, per‑system, delta_vs_rf, delta_vs_structure
├── inference/
│   └── predict.py           # inference on new formula, fold‑disagreement band
├── interpret/
│   ├── extract_embeddings.py
│   └── pca_correlation.py
└── utils/
    ├── runtime_guard.py     # epoch & total runtime warnings/halts
    └── seeds.py

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_metrics_schema.py
├── unit/
│   ├── test_loader.py
│   ├── test_graph_builder.py
│   ├── test_split.py
│   ├── test_runtime_guard.py
│   ├── test_train_smoke.py
│   ├── test_inference.py
│   └── test_structure_gnn.py
└── fixtures/
    ├── tiny_materials.csv   # Several hand‑crafted rows for software validation
    └── tiny.cif             # minimal CIF for structure‑graph stub

outputs/test_logs/           # pytest junit XML + tee‑ed logs for every promised run
```

**Structure Decision**: single‑project layout under `src/`; no web or mobile components are needed for this research task.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Structure‑aware baseline omitted | No open CIF source was previously identified. | Synthesizing structures would fabricate the core scientific comparison. |
| Hardness data unavailable | No open dataset provides a verified hardness column. | Dropping hardness entirely would break FR‑001; instead we allow null hardness and flag for spec amendment. |
| FR‑002 feature list extended | Element‑fraction is essential for distinguishing stoichiometries (e.g., FeO vs Fe₂O₃). | Keeping the original 4‑feature list would make the model incapable of learning composition‑dependent targets. |
| FR‑006 shared test set vs. CV | With the tiny fixture we cannot guarantee a common held‑out set; CV provides robust estimates on the available fixture. | Using a single test split would risk overfitting on the toy data. |
| FR‑007 “95 % CI” wording | The spec’s interval is a fold‑disagreement band, not a calibrated prediction interval. | Claiming a calibrated CI would be statistically inaccurate. |

## Phased Implementation Tasks

| Phase | Tasks | FR/SC addressed |
|---|---|---|
| **0 Setup & contract tests** | Pin `requirements.txt`; create `seeds.py`; add both contract schemas; write `tests/contract/*`; run `pytest tests/contract/ -q --junitxml=outputs/test_logs/phase0_contract.xml 2>&1 | tee outputs/test_logs/phase0_contract.log` | I, III, IV, V |
| **1 Loader** | Implement `loader.py` with three pure functions; unit tests (`test_loader.py`) on `tiny_materials.csv` verify (a) metals retained, (b) per‑target IQR filter, (c) correct kept‑row count; run `pytest tests/unit/test_loader.py -q --junitxml=outputs/test_logs/loader.xml 2>&1 | tee ...` | FR‑001, FR‑004, SC‑003, edge cases |
| **2 Composition graph builder** | `graphs/composition.py` builds fully‑connected clique with self‑loops; node features = `[element_fraction, atomic_number, electronegativity, valence_electrons, atomic_radius]`; edge_weight = Euclidean distance in the 4‑D periodic property space; unit tests (`test_graph_builder.py`). | FR‑002 (with documented deviation) |
| **3 Stratified split & CV** | `training/split.py` creates crystal‑system‑stratified 80/10/10 split, ensures disjoint IDs, then generates 5‑fold CV indices on the training portion; unit tests (`test_split.py`). | FR‑004, FR‑007, SC‑006 |
| **4 Models + smoke test** | `models/gnn.py` (≤3 `GCNConv`, hidden ≤128, ReLU, global mean pooling, two heads); `models/rf_baseline.py` (200 trees, seed = 42). Smoke test (`test_train_smoke.py`) trains both models for a few epochs on the fixture and asserts finite loss and exit 0. | FR‑003, SC‑001 |
| **5 Runtime guardrails** | `utils/runtime_guard.py` monitors epoch time (warning if >30 min) and total runtime (halt if >6 h); unit tests (`test_runtime_guard.py`). | FR‑009, SC‑003, SC‑004 |
| **6 Training & evaluation (composition‑only)** *(gated – runs when Matbench dataset is attached)* | `training/train_gnn.py` runs full 5‑fold CV on the processed dataset, respects runtime guards, writes per‑fold checkpoints under `outputs/`; `training/evaluate.py` computes R², MAE, RMSE (mean ± std), Random Forest baseline, and the `delta_vs_rf` block; per‑system CSV generated; logs captured (`train_gnn.log`, `evaluate.log`). | FR‑006, FR‑007, SC‑001, SC‑004, SC‑006 |
| **6b Training & evaluation (structure‑aware)** *(new)* | `training/train_structure_gnn.py` trains a structure‑aware GNN on the ≤2,000‑material Matbench subset (structures provided by Matbench); `training/evaluate_structure.py` computes the same metrics and additionally **ΔR², ΔMAE, ΔRMSE** between composition‑only and structure‑aware models **for band‑gap** (hardness omitted). Results stored in `data/results_structure_aware.json` and `comparison_summary.csv`. | FR‑005, FR‑006, SC‑002 |
| **7 Inference entry point** | `inference/predict.py --formula "Fe2O3"` builds the composition graph, loads the 5 checkpoints, returns predictions with a timestamp and the fold‑disagreement band; unit test (`test_inference.py`). | US‑1 scenario 2 |
| **8 Interpretability** *(gated – runs after successful training)* | `interpret/extract_embeddings.py` saves node embeddings; `interpret/pca_correlation.py` runs PCA, Pearson correlation with external properties not used as inputs (thermal conductivity, sound velocity, first ionization energy), applies Bonferroni correction, writes `interpretability_report.md` and flags “Low Interpretability” if no p < 0.05. | FR‑008, SC‑005 |
| **9 Structure‑aware path (conditional)** | CIFs are already embedded in the Matbench dataset, so no external API call is needed. The pipeline automatically skips any material lacking a structure, logs a warning, and continues without failure. | FR‑010, FR‑011 (no API key needed) |
| **10 Full‑suite verification & documentation** | Run `pytest tests/ -q --junitxml=outputs/test_logs/full_suite.xml 2>&1 | tee outputs/test_logs/full_suite.log`; update `quickstart.md` with the exact commands; write a “Limitations” section documenting data‑availability and spec‑deviation issues. | Principles II‑V, all FR/SC traceability |

**Ordering**: contract tests → loader → graph builder → split/CV → model smoke test → runtime guard → full training/evaluation (composition) → structure‑aware training/evaluation → inference → interpretability → full verification. All data‑dependent steps occur after the dataset is present.

## Limitations & Open Issues (blocking for scientific results)

1. **Hardness data unavailable** – No open dataset provides a verified hardness column. The schema now permits null hardness; the current pipeline reports band‑gap results only. A future dataset or spec amendment is required to reinstate hardness.  
2. **Structure‑aware baseline now uses Matbench Expt Gap** – This dataset supplies crystal structures and band‑gap values, satisfying FR‑005 for the structure‑aware path.  
3. **Spec deviations**: (a) element‑fraction added to node features; (b) hardness omitted (null) pending data; (c) “95 % CI” reinterpreted as a fold‑disagreement band. All are flagged for spec amendment.  
4. **Statistical power** – model‑comparison based on 5 CV folds is weakly powered; results are reported descriptively with effect sizes.  

---


