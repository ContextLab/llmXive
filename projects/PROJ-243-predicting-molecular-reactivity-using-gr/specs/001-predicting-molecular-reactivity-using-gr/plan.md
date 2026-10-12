# Implementation Plan: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Branch**: `001-predicting-molecular-reactivity` | **Date**: 2026-10-11 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-predicting-molecular-reactivity/spec.md`

## Summary
Implement a CPU‑first pipeline that (1) downloads a verified QM9 subset, (2) converts SMILES to graph objects with RDKit, (3) trains two lightweight heterophily‑aware GNNs and a Random‑Forest baseline on the HOMO‑LUMO gap, (4) evaluates performance with rigorous statistical testing, and (5) conducts GNNExplainer attribution validated against curated reactive‑substructure and kinetic datasets. All steps are deterministic, reproducible, and respect the project's constitution.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `pandas`, `pyyaml`, `datasets`, `ruff`, `black`, `pytest`  
- **Storage**: Local file system (`data/raw`, `data/processed`, `artifacts`)  
- **Testing**: `pytest` + contract validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤6 h)  
- **Project Type**: Computational research pipeline (single‑project layout)  
- **Constraints**: CPU‑only training; memory ≤ 4 GB; total runtime ≤ 6 h; all external data fetched from verified URLs.  

## Constitution Check
| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Reproducibility | PASS | `requirements.txt` pins exact versions; random seeds fixed in `code/config.py`; deterministic data download via HuggingFace URLs. |
| II. Verified Accuracy | PASS | All citations in `research.md` reference URLs from the “Verified datasets” block. |
| III. Data Hygiene | PASS | Raw files are immutable; checksums recorded in `data/raw/checksums.json`; transformations write new files under `data/processed`. |
| IV. Single Source of Truth | PASS | `contracts/output.schema.yaml` enforces that every figure/metric originates from `artifacts/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`; any change triggers a version bump. |
| VI. CPU‑First Feasibility | PASS | All model code sets `device='cpu'`; batch size auto‑adjusts; GPU escape hatch only triggers on OOM/time‑out. |
| VII. Heterophily‑Aware Graph Rep | PASS | Node/edge feature set follows FR‑001 and explicitly supports VR‑GNN‑style heterophily handling. |

## Project Structure

```text
specs/001-predicting-molecular-reactivity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── attribution.schema.yaml
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   ├── model-output.schema.yaml
│   ├── output.schema.yaml
│   └── checksums.schema.yaml
└── tasks.md   # generated later
```

```text
data/
├── raw/               # immutable downloads & curated assets
│   ├── qm9_subset.parquet
│   ├── reference_substructures_raw.csv
│   ├── kinetic_dataset_raw.csv
│   └── checksums.json   # created empty → later populated
├── processed/         # derived graphs, splits
│   ├── graphs.pt
│   └── splits/
└── assets/            # static assets (e.g., README, licenses)

code/
├── __init__.py
├── config.py           # seeds, hyper‑params, paths
├── data/
│   ├── download.py
│   ├── preprocess.py
│   └── splits.py
├── models/
│   ├── spectral_gnn.py
│   ├── hetero_gnn.py
│   └── rf_baseline.py
├── train/
│   ├── trainer.py
│   └── eval.py
├── interpret/
│   └── explainer.py
└── utils/
    ├── logging.py
    ├── checksums.py
    └── ssot.py

artifacts/
├── logs/
├── metrics.json
├── predictions.parquet
├── attribution_maps.json
├── exclusion_report.json
└── checksums_artifacts.json
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Heterophily‑aware GNN | Molecular electronic properties exhibit low homophily; standard GNNs under‑perform (SC‑002). | Standard MPNN would likely fail the significance test. |
| Streaming QM9 | Full QM9 > 7 GB; streaming avoids OOM (SC‑005). | Loading whole dataset would exceed RAM limit. |
| Dual Baseline (RF + GNN) | Directly addresses FR‑006 (paired test). | Single baseline would not allow statistical comparison. |
| Explicit Lint/Format Check | Satisfies T002 verification requirement. | Skipping lint would leave a non‑verifiable step. |
| Empty `checksums.json` → Populated | Meets T003 (empty file) and T005 (checksum entries) sequentially. | One‑shot population would violate the “empty first” rule. |

## Implementation Tasks

### Phase 0 – Repository & Environment Setup
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T001a** | Create `data/raw`, `data/processed`, `data/assets`, `artifacts/logs` directories with `.gitkeep`. | None | Directories exist. |
| **T001b** | Create `code/`, `tests/` directories with `.gitkeep`. | None | Directories exist. |
| **T002** | **Add `.flake8` config** (`[flake8]\nmax-line-length = 88\nexclude = .git,__pycache__,venv`).<br>Run **ruff** (`ruff check . --output-format=json > artifacts/ruff_report.json`) and **black** (`black --check . > artifacts/black_report.txt`).<br>Fail the pipeline if either report indicates errors. | T001a, T001b | `.flake8` file, `artifacts/ruff_report.json`, `artifacts/black_report.txt`. |
| **T003** | Initialize an **empty** `data/raw/checksums.json` (`{}`) to satisfy the “empty file” verification. | T001a | `data/raw/checksums.json` (empty object). |
| **T004** | Populate `requirements.txt`, `pyproject.toml`, `ruff.toml` (already present). No code changes. | T001a | Files committed. |
| **T005** | **Curate static assets**:<br>• `reference_substructures_raw.csv` (50 rows, columns `smiles,source_doi,description`).<br>• `kinetic_dataset_raw.csv` (≥20 rows, columns `smiles,reaction_rate,reaction_type,source_doi`). | T001a | Two CSV files in `data/raw/`. |
| **T006** | Compute **SHA‑256** checksums for every file in `data/raw` (including the two CSVs and the eventual QM9 parquet). Append entries to `data/raw/checksums.json` using `code/utils/checksums.py`. The schema expects fields `file_path` and `sha256`. | T003, T005 | Updated `data/raw/checksums.json` with correct entries. |
| **T007** | Verify that `checksums.json` conforms to `contracts/checksums.schema.yaml` (validation step). | T006 | Validation log `artifacts/checksum_validation.log`. |

### Phase 1 – Data Ingestion & Preprocessing
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T010** | Download QM9 subset via `torch_geometric.datasets.QM9` with `download=True`, streaming to `data/raw/qm9_subset.parquet`. | T001a, T004 | `data/raw/qm9_subset.parquet`. |
| **T011** | Convert SMILES → `torch_geometric.data.Data` objects (node/edge features per FR‑001). Log invalid SMILES to `artifacts/exclusion_report.json`. If memory > 4 GB, automatically reduce batch size and record in `artifacts/memory_adjustment.log`. | T010, T006 | `data/processed/graphs.pt`, exclusion & memory logs. |
| **T012** | Serialize graph list to `data/processed/graphs.pt`. | T011 | Serialized graph file. |
| **T013** | Perform Murcko scaffold split (80 % train, 20 % test) and generate similarity filter (Tanimoto ≤ 0.8). Save JSON split indices under `data/processed/splits/`. | T012 | `splits/train.json`, `splits/val.json`, `splits/test.json`. |

### Phase 2 – Model Training
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T020** | Train **Spectral GNN** (ChebNet style) on training split; early‑stop on validation loss; `device='cpu'`. Save weights `artifacts/models/spectral_gnn.pt`. | T013 | Model checkpoint. |
| **T021** | Train **Heterophily‑aware GNN** (VR‑GNN‑style) under same constraints; save `artifacts/models/hetero_gnn.pt`. | T013 | Model checkpoint. |
| **T022** | Train **Random Forest** on Morgan fingerprints (radius 2, nBits 2048); save `artifacts/models/rf_baseline.pkl`. | T013 | Model checkpoint. |
| **T023** | Generate predictions for the test set for all three models; write `artifacts/predictions.parquet`. | T020, T021, T022 | Prediction file. |
| **T024** | Compute **MSE, MAE, Pearson R** for each model; store in `artifacts/metrics.json`. | T023 | Metrics file. |
| **T025** | Perform **paired t‑test** (GNN vs. RF) on test‑set errors; apply **Bonferroni** correction for the three metric comparisons; append results to `artifacts/metrics.json`. | T024 | Updated metrics with statistical test. |

### Phase 3 – Interpretability & External Validation
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T030** | Run **GNNExplainer** on a random 100‑molecule subset of the test set; output `artifacts/attribution_maps.json` conforming to `contracts/attribution.schema.yaml`. | T023 | Attribution file. |
| **T031** | Compute **alignment score** (Mean‑max Tanimoto similarity) between top‑k substructures and the curated reference set; store `alignment_score` in `artifacts/metrics.json`. | T030, T005 | Updated metrics. |
| **T032** | Correlate predicted HOMO‑LUMO gaps with experimental rates from `kinetic_dataset_raw.csv`; produce a scatter plot saved as `artifacts/kinetic_correlation.png` and a brief text summary in `artifacts/kinetic_report.txt`. | T023, T005 | Correlation artifacts. |
| **T033** | Run **SSoT validator** (`code/utils/ssot.py`) to ensure every figure/number in the eventual paper traces back to a single artifact; output log `artifacts/ssot.log`. | T024, T031 | Validation log. |

### Phase 4 – Final Archiving & Reporting
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T040** | Generate **checksums for all artifacts** (`artifacts/`) and store in `artifacts/checksums_artifacts.json` (validated against `contracts/checksums.schema.yaml`). | T033 | Artifact checksum file. |
| **T041** | Create a concise **README** in `docs/` that lists all artifacts, their schemas, and how to reproduce each step. | T040 | Documentation file. |
| **T042** | Tag the repository with a version bump (`v0.1.0`) and update `state/projects/PROJ-243-...yaml` with new `updated_at`. | T041 | Versioned state. |

## Mapping FRs & SCs to Tasks
| FR / SC | Covered By |
|---------|------------|
| FR‑001 | T011, T012 |
| FR‑002 | T020, T021 |
| FR‑003 | T020‑T022 (early stopping, scaffold split) |
| FR‑004 | T022 |
| FR‑005 | T030 |
| FR‑006 | T025 |
| FR‑007 | All `artifacts/` generation tasks (T023‑T040) |
| FR‑008 | T005 (curated reference set) + T031 (alignment score) |
| FR‑009 | T005 (kinetic dataset) + T032 |
| SC‑001 | T024 (Pearson R) |
| SC‑002 | T025 (paired t‑test, Bonferroni) |
| SC‑003 | T031 (alignment ≥ 0.7) |
| SC‑004 | All tasks respect the 6‑hour runtime; monitored via GitHub Actions timeout. |
| SC‑005 | T011 enforces ≤ 4 GB RAM; logs in `memory_adjustment.log`. |
| SC‑006 | T032 (trend check) – acknowledges n = 20 limitation. |

---
