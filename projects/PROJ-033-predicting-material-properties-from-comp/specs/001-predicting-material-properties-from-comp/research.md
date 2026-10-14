# Research: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Feature**: `001-predict-material-properties-compositional-gnn` | **Date**: 2026-10-13 (rev. 2)

## Objective

Quantify predictive performance of a composition-only GNN for band gap and hardness, benchmarked against a Random Forest baseline, with crystal-system-stratified evaluation and embedding interpretability. The spec's ultimate goal — quantifying information loss vs. a structure-aware model — is **blocked** (see Dataset Strategy), and with it, pending data availability, all measurable success criteria.

## Dataset Strategy

| Role | Source | Access Method | Verified URL |
|---|---|---|---|
| Primary compositional & property data | **NONE AVAILABLE** | Contract-validated loader (`src/data/loader.py`) ready for any conforming source | — |

**Explicit finding**: the verified-datasets block for this planning round lists only (a) two "DFT" parquet files and (b) "IQR" CSV/parquet files (GPT prompts, medbot, TTS). **None** contains chemical formulas, band gap, hardness, or crystal system. Per the no-fabrication rule, no dataset URL is cited and none is substituted. The Materials Project REST API for CIFs is credential-gated (API key) and cannot be fetched unattended on CI.

**Variable fit check**: no candidate dataset can be checked for variable fit because no verified source claims the required variables (`material_id`, `formula`, `band_gap`, `hardness`, `crystal_system`). This is a **fatal data-availability flaw** for the scientific run; the pipeline is built against `contracts/materials_dataset.schema.yaml` so a verified conforming source integrates without redesign.

## Methodology

1. **Chunked loading & cleaning** — `pandas.read_csv/read_parquet` in chunks ≤ 5,000 rows; peak RAM logged with `psutil`, asserted ≤ 6 GB (FR-001, SC-003). Rows missing required fields are dropped with warnings; **1.5×IQR outlier rule applied per target (`band_gap`, `hardness`) per the spec's Assumptions, with dropped-row counts logged and the cleaned data written to a new derived file**.
2. **Composition-only graph** — one node per unique element; features **[element fraction (stoichiometry, from `pymatgen` `Composition`), atomic number, electronegativity, valence electrons, atomic radius]** (5 features — a noted deviation from FR-002's 4-feature list, flagged for spec kickback); fully-connected clique with self-loops; edge weight = Euclidean distance in the 4-D periodic-property space, explicitly wired into `GCNConv` via `edge_weight` (FR-002). Materials with elements missing from the lookup are skipped with a warning (edge case). Graphs are built in-memory by `src/graphs/composition.py` and cached under `data/processed/graphs/`. **Representational caveat**: the clique edge weights are a deterministic function of the node features and carry no independent information; stoichiometry enters only via the element-fraction feature and mean pooling. The GNN-vs-RF comparison therefore tests learned message-passing over element features, not additional "graph" information.
3. **Stratified split & CV** — crystal-system-stratified 80/10/10 split, material-ID disjointness asserted; 5-fold CV on the training portion (FR-004, FR-007, SC-006).
4. **GNN** — ≤3 `GCNConv` layers (with `edge_weight`), hidden ≤128, ReLU, global mean pooling, two linear heads (band gap, hardness); Adam lr=1e-3, early stopping patience=10, max 200 epochs, CPU-only (FR-003).
5. **Random Forest baseline** — `RandomForestRegressor` (n_estimators=200, seed=42) on composition-weighted elemental feature aggregates including element fractions, same folds (SC-001).
6. **Metrics** — R², MAE, RMSE per target per fold; mean ± std; **fold-disagreement band** = mean ± 1.96 × std of fold predictions (FR-007 convention; **labeled a fold-disagreement band, not a calibrated [deferred] prediction interval** — it captures fold-to-fold model variance only, not residual/aleatoric error, and with 5 folds its coverage is poor). **Deviation note**: FR-006 specifies a shared held-out test set; the plan reports 5-fold CV means on stratified splits instead. Δmetrics vs. the RF baseline are carried in the `delta_vs_rf` block of `data/results_composition_only.json` (schema-validated SSoT artifact), clearly labeled as a *baseline gap*, not a structure information-loss ΔR². Zero-band-gap metals retained; their fraction reported descriptively (edge case). Polymorph deduplication by `material_id` with formula-duplicate counting reported (edge case).
7. **Runtime guards** — warn-and-continue if epoch >30 min; halt if total >6 h (FR-009, SC-004).
8. **Interpretability** — node embeddings → PCA → Pearson correlation of PCs with properties **not used as inputs and not targets**: thermal conductivity, sound velocity, first ionization energy (from the periodic-table lookup). **Atomic mass and bulk modulus are excluded**: atomic mass is essentially monotone in atomic number (an input feature), and bulk modulus is the physical basis of the hardness training target — either would make significance near-guaranteed by construction. Two-tailed p-values, Bonferroni-corrected; "Low Interpretability" flag when nothing is significant (FR-008, SC-005).
9. **Inference** — `src/inference/predict.py` builds the composition graph for a new formula, runs the 5 fold checkpoints, and returns predicted band gap/hardness with a timestamp and the fold-disagreement band (US-1 scenario 2).
10. **Structure-aware path** — CIF fetch/checksum/skip-and-warn logic (`src/data/cif_fetch.py`) and a crystal-graph builder (`src/graphs/structure.py`) are implemented and unit-tested on a bundled CIF fixture (`tests/fixtures/tiny.cif`), but no scientific structure-aware run is performed (FR-005/FR-010/FR-011 code paths only).

## Statistical Rigor

- **Multiple comparisons**: interpretability correlations Bonferroni-corrected (α_adj = 0.05 / number of tested correlations, [deferred] at run time).
- **Model comparison procedure**: GNN vs. RF (and, if ever available, composition vs. structure) is compared via a **paired analysis of per-fold R² across the 5 folds** (corrected resampled t-test style, acknowledging the folds share training data). With only 5 paired observations this test is itself weakly powered; no numeric power claim is made in advance. Detectable effect sizes are reported descriptively from the observed fold variance (SC-006) once data exists.
- **Causal framing**: purely associational prediction; no causal claims.
- **Measurement validity**: band gap is a standard DFT output; hardness provenance in the source dataset will be documented when a verified dataset is attached — if hardness is model-derived rather than measured/computed independently, that will be flagged.
- **Collinearity**: node features (atomic number, valence electrons) are definitionally correlated across elements; effects are interpreted jointly, not as independent contributions.

## Decision/Rationale (compute feasibility)

All methods — GCN over tiny element-clique graphs (≤ ~10 nodes each), Random Forest, PCA, Pearson tests — run faithfully on the 2-CPU CI box within 6 GB RAM and 6 h. **No GPU escape hatch is required**; no method is planned that lacks a faithful CPU form. No synthetic stand-in for the dataset is planned; the scientific run is gated on verified data availability.

## Expected Deliverables

- `data/processed/materials_processed.csv` (contract-validated, checksummed, IQR-cleaned)
- Composition graphs built in-memory by `src/graphs/composition.py`, cached under `data/processed/graphs/`; `outputs/gnn_checkpoint_<hash>.pt`
- `data/results_composition_only.json` (per `contracts/model_metrics.schema.yaml`, including the `delta_vs_rf` block)
- `data/metrics_by_system.csv`; `data/predictions.json`; `outputs/node_embeddings.npy`; `interpretability_report.md`
- Passing pytest suite (contract + unit, fixture-based)

## Limitations & Open Issues

1. No verified dataset with required variables — the scientific run and **all** success criteria (SC-001–SC-006) are blocked pending scope revision or a verified source.
2. Structure-aware baseline unavailable (gated API, no open verified CIF source) — SC-002 not computable; Principle VI partially unmet; spec kickback requested (FR-005/FR-011/SC-002/FR-006 ΔR² clause/US-2 deliverables).
3. Model comparison uses 5 paired fold observations — weakly powered by construction; reported descriptively.
4. Spec deviations noted for kickback: FR-002 feature list (element fraction added), FR-006 (CV means vs. shared test set), FR-007 (fold-disagreement band vs. "95% CI").