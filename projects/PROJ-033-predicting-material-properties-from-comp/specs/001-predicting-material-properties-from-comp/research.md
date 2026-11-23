# Research: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Feature**: `001-predict-material-properties-compositional-gnn` | **Date**: 2026-10-24

## Objective

Quantify the predictive performance of a **composition‑only GNN** for **band‑gap** (hardness is omitted due to lack of open data) and benchmark it against (a) a Random Forest baseline and (b) a **structure‑aware GNN** trained on the same Matbench Expt Gap subset. The primary scientific goal—measuring information loss when crystal structure is excluded—is therefore addressed by computing **ΔR²** (and ΔMAE, ΔRMSE) between the composition‑only and structure‑aware models for band‑gap. Hardness will be added once an open dataset with verified hardness values becomes available (spec amendment required).

## Dataset Strategy

| Role | Source | Access Method | Verified URL |
|---|---|---|---|
| Primary compositional & property data | **Matbench Expt Gap** (open, CC‑BY‑4.0) – includes `material_id`, `formula`, `band_gap`, `crystal_system`, and crystal structures (CIFs) | `datasets.load_dataset("matbench_expt_gap")` (HuggingFace) | https://huggingface.co/datasets/matbench/expt_gap |
| Hardness target | **None (placeholder)** – column present but values are null; provenance not available in any open source. | – | — |

**Finding**: The verified‑datasets block lists only DFT parquet files and unrelated IQR datasets; none provide the required hardness column. Consequently, the pipeline can only compute band‑gap metrics at present. This is a **fatal data‑availability flaw** for the hardness target; the schema has been relaxed to allow null hardness, and the limitation is documented for future amendment.

## Methodology

1. **Chunked loading & cleaning** – `pandas` reads CSV/Parquet in ≤5 000‑row chunks; RAM usage logged via `psutil` and asserted ≤ 6 GB (FR‑001, SC‑003). Loader decomposes into:
   - `validate_row()` – schema check per row.
   - `drop_outliers_iqr()` – 1.5 × IQR filter **per target independently**; since hardness is null, only band‑gap is filtered.
   - `load_and_clean()` – checksum, duplicate‑ID deduplication, unknown‑element skip‑and‑warn.  
   **Metals (`band_gap == 0`) are retained** – a bug in the prior implementation is corrected and pinned by unit tests.

2. **Composition‑only graph** – one node per unique element; node features = **[element fraction, atomic number, electronegativity, valence electrons, atomic radius]** (5 features; deviation from FR‑002 noted). Fully‑connected clique with self‑loops; edge weight = Euclidean distance in the 4‑D periodic‑property space; built in‑memory and optionally cached.

3. **Stratified split & 5‑fold CV** – crystal‑system‑stratified 80/10/10 train/val/test split with disjoint material IDs; k‑fold cross‑validation on the training portion (FR‑004, FR‑007, SC‑006).

4. **GNN** – ≤3 `GCNConv` layers (edge‑weight aware), hidden ≤128, ReLU, global mean pooling, two linear heads (band gap, hardness placeholder). Adam lr = 1e‑3, early stopping patience = 10, max 200 epochs, CPU‑only (FR‑003). A 2‑epoch smoke test on the fixture runs before any full training.

5. **Random Forest baseline** – `RandomForestRegressor` (n_estimators = 200, seed = 42) trained on the same compositional features and CV folds (SC‑001).

6. **Structure‑aware baseline** – using the same Matbench Expt Gap dataset, `training/train_structure_gnn.py` builds **full crystal graphs** (atom positions, coordination) via `src/graphs/structure.py` and trains an identical GNN architecture. This satisfies FR‑005 without external API keys because structures are bundled with Matbench.

7. **Metrics** – R², MAE, RMSE per target per fold; mean ± std reported. **ΔR², ΔMAE, ΔRMSE** are computed **between the composition‑only GNN and the structure‑aware GNN** for band‑gap (hardness omitted). The `delta_vs_rf` block remains as a secondary baseline gap. Per‑crystal‑system CSV files are also generated.

8. **Runtime guards** – `runtime_guard.py` warns if any epoch exceeds 30 min and halts the whole job if total runtime > 6 h (FR‑009, SC‑004). Peak RAM logged and compared to the 6 GB limit.

9. **Interpretability** – node embeddings extracted, PCA performed, Pearson correlations computed between PCs and **properties not used as inputs nor targets** (thermal conductivity, sound velocity, first ionization energy). Bonferroni correction applied; “Low Interpretability” flag added when no p < 0.05.

10. **Inference** – `inference/predict.py --formula "Fe2O3"` builds the composition graph, loads the 5 checkpoints, returns predictions with a timestamp and the fold‑disagreement band (mean ± 1.96 × std across folds) for band‑gap; hardness field is null.

## Verification‑evidence protocol (re‑plan addition)

Every promised test or script run is logged via **pytest junit XML + tee‑ed stdout/stderr** under `outputs/test_logs/`. The XML file is the authoritative verification artifact; a run without its log is considered not executed. Script logs record exit codes; any non‑zero exit fails the associated task.

## Statistical Rigor

- **Multiple comparisons**: interpretability correlations Bonferroni‑corrected (α_adj = 0.05 / #tests).  
- **Model comparison**: paired analysis of per‑fold R² (composition vs. structure) using a corrected resampled t‑test; with only a limited number of pairs the test is weakly powered, so effect sizes are reported descriptively (SC‑006).  
- **Causal framing**: purely associational; no causal claims.  
- **Measurement validity**: band‑gap values come from the Matbench Expt Gap DFT calculations (validated in the Matbench benchmark paper). Hardness provenance is absent; hardness metrics are null.  
- **Collinearity**: node features (e.g., atomic number, valence electrons) are correlated; effects are interpreted jointly, not as independent contributions.

## Decision/Rationale (compute feasibility)

All components (GCN on ≤10‑node graphs, Random Forest, PCA, Pearson tests) run comfortably on the 2‑CPU GitHub Actions runner within memory and time limits. No GPU escape hatch is needed. The plan deliberately avoids any synthetic data substitution; the scientific run is gated on the presence of the **Matbench Expt Gap** dataset.

## Expected Deliverables

- `data/processed/materials_processed.csv` (contract‑validated, checksum‑recorded, IQR‑cleaned).  
- Composition graphs cached under `data/processed/graphs/`.  
- Model checkpoints `outputs/gnn_checkpoint_<hash>.pt` and `outputs/structure_gnn_checkpoint_<hash>.pt`.  
- `data/results_composition_only.json` (conforms to `contracts/model_metrics.schema.yaml`; hardness fields null).  
- `data/results_structure_aware.json` (same schema; hardness may be null).  
- `data/comparison_summary.csv` (ΔR², ΔMAE, ΔRMSE for band‑gap).  
- `data/metrics_by_system.csv` (per‑system performance).  
- `data/predictions.json` for a user‑provided formula (hardness null).  
- `outputs/node_embeddings.npy`.  
- `interpretability_report.md`.  
- `outputs/test_logs/` containing pytest junit XML + tee‑ed logs for every verification step.  

## Limitations & Open Issues

1. **Hardness data unavailable** – No open dataset provides a verified hardness column. The schema now permits null hardness; results for hardness are omitted. A future open dataset or spec amendment is required.  
2. **Structure‑aware baseline now relies on Matbench** – this satisfies FR‑005 without external API keys.  
3. **Spec deviations**: (a) element‑fraction added to node features; (b) hardness omitted (null) pending data; (c) “95 % CI” reinterpreted as a fold‑disagreement band. All are flagged for spec amendment.  
4. **Statistical power** – model‑comparison based on 5 CV folds is weakly powered; results are reported descriptively with effect sizes.  

---


