# Implementation Plan: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Branch**: `001-predict-material-properties-compositional-gnn` | **Date**: 2026-10-13 (rev. 2) | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `specs/001-predict-material-properties-compositional-gnn/spec.md`

## Summary

The project delivers a reproducible, CPU-only pipeline that (1) ingests a Materials-Project-style dataset of chemical formulas, band gap, hardness, and crystal system, (2) builds a composition-only fully-connected element graph per material (with stoichiometry encoded as an element-fraction node feature), (3) trains a lightweight GNN (≤3 GCN layers, hidden ≤128) with 5-fold crystal-system-stratified cross-validation, (4) compares against a Random Forest baseline, (5) provides a formula-inference entry point, and (6) performs PCA/correlation interpretability analysis of learned embeddings against genuinely held-out elemental properties.

**Blocking data-availability finding (scope revision required — kickback).** The verified-datasets block provided for this planning round contains **no dataset with the required variables** (chemical formula, band gap, hardness, crystal system). The two "DFT" parquet URLs and the "IQR" CSV/parquet URLs do not correspond to a materials-property dataset with those columns, and no other source may be cited or invented. Additionally, the Materials Project REST API (FR-005/FR-011) is credential-gated (API key required), so CIF retrieval cannot run unattended on the CI runner. Consequences:

- **FR-005, FR-006 (structure-aware portion), FR-011** cannot be executed: no verified open CIF source and a gated API. The ΔR² information-loss comparison (SC-002) is therefore **not computable** and is recorded as a limitation, not fabricated.
- **The scientific training/evaluation run is blocked** until a verified open dataset containing `formula`, `band_gap`, `hardness`, `crystal_system` is supplied. This means **no success criterion (SC-001 through SC-006) is currently computable**, not only SC-002. The plan below therefore builds the **complete, tested pipeline** against a strict data contract (`contracts/materials_dataset.schema.yaml`), with unit/contract tests running on small hand-crafted fixtures (a handful of well-known compounds with literature property values used only for software validation, never reported as study results). No synthetic data will be presented as scientific results; the fabrication gate applies.

## Spec revision required (kickback to clarified)

The spec and this plan are mutually incompatible as written. Before scientific task generation, the spec must be revised in one of the following ways:

1. **Data path**: supply/verify an open dataset with `material_id, formula, band_gap, hardness, crystal_system` AND an open, ungated CIF source, keeping FR-005/FR-011/SC-002 and US-2's `results_structure_aware.json` / `comparison_summary.csv` deliverables; or
2. **Re-scope**: remove or re-scope FR-005, FR-011, SC-002, the FR-006 ΔR² clause, and US-2's structure-aware deliverables to what a verified open source supports, and amend **constitution Principle VI** (which currently requires the structure-aware comparison for every reported metric) accordingly; and
3. **FR-002 feature list**: the spec mandates exactly [atomic number, electronegativity, valence electrons, atomic radius]; this plan adds **element fraction** as a fifth node feature because without it the graph for FeO and Fe2O3 is identical and the model cannot learn composition-dependent properties (see Phase 2 deviation note). The spec's FR-002 should be amended to include the element-fraction feature.
4. **FR-007 interval semantics**: the spec's "95% confidence interval = mean ± 1.96 × std across folds" is a fold-disagreement band, not a calibrated prediction interval; the spec wording should be revised (see Phase 6 deviation note).

Until the kickback lands, the tasks below marked *(code-path stub)* implement real, tested code paths but make **no scientific claim**; the tasks marked *(gated)* execute only when a conforming verified dataset is attached (a one-line loader change).

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `pymatgen==2024.7.0`, `matplotlib==3.9.0`, `psutil==5.9.8`, `pytest==8.3.2`
- **Storage**: files under `data/` (raw, processed, results), model checkpoints under `outputs/`
- **Testing**: pytest (unit + contract tests against `contracts/`)
- **Target Platform**: GitHub Actions free-tier Linux runner (2 CPU, ~7 GB RAM, CPU-only)
- **Performance Goals**: peak RAM ≤ 6 GB (SC-003); total runtime ≤ 6 h (SC-004); per-epoch ≤ 30 min with warning-and-continue (FR-009)
- **Constraints**: CPU-only; pinned seeds; no credentials; no fabricated data
- **Project Type**: research pipeline (library + CLI scripts)
- **Compute choice**: all methods (GCN on small element-clique graphs, Random Forest, PCA, Pearson correlation) run faithfully on CPU; no GPU escape hatch needed.

## Constitution Check

| Principle | Status | How addressed |
|---|---|---|
| I. Reproducibility | **PARTIAL — flagged** | Seeds pinned (`seed=42` everywhere) and all code paths are reproducible, but **no canonical dataset source currently exists to re-download** — the verified-datasets block contains no conforming dataset. Reproducibility of scientific results becomes PASS only after the scope revision attaches a canonical, contract-validated source. |
| II. Verified Accuracy | PASS | Only the verified-dataset block is consulted; since none matches, **no dataset URL is cited** and the gap is reported rather than papered over with an invented source. |
| III. Data Hygiene | PASS | Raw files SHA-256 checksummed and recorded in `state/projects/PROJ-033-predicting-material-properties-from-comp.yaml`; all transformations (including 1.5×IQR outlier filtering) write new files with documented derivation. |
| IV. Single Source of Truth | PASS | Every metric/figure traces to one named artifact (e.g., the `delta_vs_rf` block of `data/results_composition_only.json`); nothing hand-typed. Deviations from spec wording (FR-002 feature list, FR-006 shared test set, FR-007 interval) are noted in their phase mappings. |
| V. Versioning Discipline | PASS | Artifacts carry content hashes (`gnn_checkpoint_<hash>.pt`); `updated_at` maintained on change. |
| VI. Compositional vs. Structural Quantification | **PARTIAL — flagged** | The constitution requires a structure-aware baseline for every comparative claim. No verified open CIF source exists and the MP API is gated, so ΔR² (SC-002) cannot be computed. The plan reports this explicitly as a limitation, makes **no** sufficiency-of-composition claim, and requests a Principle VI amendment via the kickback above. |
| VII. Crystal-System Stratified Evaluation | PASS | Splits stratified by `crystal_system`; per-system metrics emitted (`data/metrics_by_system.csv`). |

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
└── tasks.md   # generated by /speckit-tasks

src/
├── data/
│   ├── loader.py            # chunked ingestion + schema validation + checksums + 1.5×IQR cleaning
│   ├── cif_fetch.py         # CIF download/checksum wrapper with skip-and-warn (code-path stub)
│   └── periodic_table.py    # element feature lookup
├── graphs/
│   ├── composition.py       # composition-only graph builder (graphs built in-memory,
│   │                        #   cached under data/processed/graphs/)
│   └── structure.py         # crystal-graph builder from CIFs (code-path stub)
├── models/
│   ├── gnn.py               # CompositionGNN (≤3 GCNConv with edge_weight, hidden ≤128)
│   └── rf_baseline.py       # RandomForest baseline
├── training/
│   ├── split.py             # crystal-system-stratified 80/10/10 + 5-fold CV
│   ├── train_gnn.py         # Adam lr=1e-3, early stopping patience=10, runtime guards
│   └── evaluate.py          # R²/MAE/RMSE, per-system metrics, fold-disagreement bands
├── inference/
│   └── predict.py           # predict new formula: band gap + hardness + timestamp + band
├── interpret/
│   ├── extract_embeddings.py
│   └── pca_correlation.py
└── utils/
    ├── runtime_guard.py     # 30-min/epoch warn, 6-h halt (FR-009)
    └── seeds.py

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_metrics_schema.py
├── unit/
│   ├── test_graph_builder.py
│   ├── test_structure_graph.py
│   ├── test_split.py
│   ├── test_runtime_guard.py
│   └── test_inference.py
└── fixtures/
    ├── tiny_materials.csv   # ~20 hand-crafted rows for software tests only
    └── tiny.cif             # minimal CIF fixture for the structure-graph code path
```

**Structure Decision**: single-project `src/` layout; research pipeline only, no web/mobile components. Composition graphs are constructed **in-memory** by `src/graphs/composition.py` and optionally cached as serialized PyG `Data` files under `data/processed/graphs/`; no per-material `.pt` files live under `src/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Structure-aware baseline omitted (FR-005/FR-006/FR-011, SC-002) | No verified open CIF source; MP REST API is credential-gated and cannot run on CI. | A synthetic or imputed structure baseline would fabricate the central scientific comparison. |
| Scientific run gated on data availability | No verified dataset with `formula`/`band_gap`/`hardness`/`crystal_system` exists in the verified block. | Running on an unrelated verified dataset would not answer the research question; synthesizing data would breach the fabrication gate. |
| FR-002 feature list extended with element fraction | Without stoichiometry the graph is invariant to element ratios (FeO ≡ Fe2O3), breaking construct validity. | Keeping the exact 4-feature list would make the model provably unable to learn composition-dependent targets. |

## Phased Implementation Tasks

| Phase | Tasks | FR/SC addressed |
|---|---|---|
| **0 Setup** | Pin `requirements.txt`; seed module (`src/utils/seeds.py`). | Principle I |
| **1 Data contract & ingestion** | Implement `contracts/materials_dataset.schema.yaml`; chunked loader (`pandas`, chunks ≤ 5,000 rows) with peak-RAM logging via `psutil` and ≤6 GB assertion; SHA-256 checksum recording; column validation; drop-and-warn on missing values; **1.5×IQR outlier rule per target (per spec Assumptions): rows outside 1.5×IQR of `band_gap` or `hardness` dropped with a logged count, written to a new derived file**; skip-and-warn on unknown elements (edge case). *(gated on conforming data)* | FR-001, FR-004 (ID uniqueness), SC-003 |
| **2 Composition graph builder** | Parse formulas with `pymatgen` `Composition`; node features **[element fraction, atomic number, electronegativity, valence electrons, atomic radius]** (5 features; **deviation from FR-002**, which lists only the last 4 — see kickback item 3); fully-connected clique with self-loops; edge weight = Euclidean distance in the 4-D periodic-property space, **explicitly wired into `GCNConv` via `edge_weight`**; graphs built in-memory, cached under `data/processed/graphs/`. **Representational caveat**: clique edge weights are a deterministic function of the node features and carry no independent information; stoichiometry enters only via the element-fraction feature and pooling. The GNN-vs-RF comparison therefore tests learned message-passing over element features, not additional "graph" information. Unit-tested on fixtures. | FR-002 (with noted deviation) |
| **3 Stratified split & CV** | Crystal-system-stratified 80/10/10 split with material-ID disjointness check; 5-fold CV layered on training portion. | FR-004, FR-007, SC-006 |
| **4 Models** | `CompositionGNN` (≤3 `GCNConv` with `edge_weight`, hidden ≤128, ReLU, global mean pooling, two linear heads); Adam lr=1e-3, early stopping patience=10, max 200 epochs; `RandomForestRegressor` baseline on composition-weighted elemental feature aggregates (including element fractions). | FR-003, SC-001 |
| **5 Runtime guardrails** | `runtime_guard.py`: warn-and-continue if epoch >30 min; log warning and halt if total >6 h; peak-RAM monitor. | FR-009, SC-003, SC-004 |
| **6 Training & evaluation** *(gated)* | Train GNN + RF per fold; compute R²/MAE/RMSE per target per fold; mean ± std; **fold-disagreement band** = mean ± 1.96 × std of fold predictions (**deviation note**: FR-007 calls this a "95% confidence interval"; it is a fold-disagreement band, not a calibrated prediction interval — it does not capture residual/aleatoric error; **deviation note**: FR-006 specifies a shared held-out test set; the plan reports 5-fold CV means on the stratified splits instead); per-crystal-system metrics; zero-band-gap (metal) rows retained and reported descriptively (edge case); polymorph dedup by `material_id` with formula-duplicate counting (edge case). Δmetrics vs. the RF baseline are carried in the **`delta_vs_rf` block of `data/results_composition_only.json`** (schema-validated, single SSoT artifact), clearly labeled as a *baseline gap*, **not** a structure information-loss ΔR². | FR-006 (RF-baseline portion, with noted deviations), FR-007 (with noted deviation), SC-001, SC-004, SC-006 |
| **6b Inference entry point** | `src/inference/predict.py --formula "Fe2O3"`: builds the composition graph for a new formula, loads the 5 fold checkpoints, returns predicted band gap and hardness with a timestamp and the fold-disagreement band; emits `data/predictions.json`. | US-1 scenario 2 |
| **7 Interpretability** *(gated)* | Extract node embeddings; PCA; Pearson correlation of PCs with properties **not used as inputs and not targets**: thermal conductivity, sound velocity, first ionization energy (from the periodic-table lookup; atomic mass and bulk modulus are **excluded** — atomic mass is monotone in atomic number, an input feature, and bulk modulus is the physical basis of the hardness target); two-tailed p-values; Bonferroni correction across tested correlations; `interpretability_report.md` flags "Low Interpretability" when no p < 0.05. | FR-008, SC-005 |
| **8 Structure-aware path (code-path stub)** | `src/data/cif_fetch.py`: CIF fetch/checksum/skip-and-warn logic that, given the gated MP API, logs a warning and excludes materials lacking obtainable CIFs without terminating (FR-010/FR-011 code path); `src/graphs/structure.py`: crystal-graph builder implemented and unit-tested on the bundled `tests/fixtures/tiny.cif` so the code path is real, but **no scientific structure-aware run is claimed**. If the kickback restores a verified open CIF source, this phase extends to emit `results_structure_aware.json` and `comparison_summary.csv` per US-2. | FR-005 (code path only), FR-010, FR-011 (code path only) |
| **9 Tests & docs** | Contract tests validating both schemas; unit tests on fixtures (graph builder, structure graph, splits, runtime guards, inference); quickstart; limitations section documenting the data gap, the SC-001–SC-006 non-computability pending scope revision, and all noted spec deviations. | Principle II–V |

**Ordering**: data contract/loader (Phase 1) precedes graph construction (2) and training (4–6); models are fitted before evaluation and before inference (6b); reports (7) generated after metrics exist.

## Limitations & Open Issues (blocking, surfaced for scope revision)

1. **No verified dataset — no success criteria computable.** The verified-datasets block contains no materials-property dataset. The end-to-end scientific run is blocked, so **SC-001, SC-003 (measurement), SC-004 (measurement), SC-005, and SC-006 are as uncomputable as SC-002** until data arrives. The pipeline is delivered and contract-tested against `contracts/materials_dataset.schema.yaml` so a verified source plugs in directly. Scope revision options: (a) supply a verified open dataset with the four required columns, or (b) reframe the question to the data actually verified.
2. **Structure-aware baseline unavailable.** MP REST API requires an API key (access-gated); no open CIF mirror is verified. SC-002 (ΔR² information loss) is not computable; constitution Principle VI is only partially satisfiable and an amendment is requested via the kickback. No composition-sufficiency claim will be made.
3. **Power / comparison procedure.** Model comparison uses a paired analysis of per-fold R² across the 5 folds (corrected resampled t-test style). With only 5 paired observations this is itself weakly powered; detectable effect sizes are reported descriptively from the observed fold variance rather than asserted in advance.
4. **Spec deviations noted**: FR-002 feature list extended with element fraction; FR-006 evaluated via 5-fold CV rather than a single shared test set; FR-007 interval relabeled a fold-disagreement band. All are listed in the kickback section for spec revision.