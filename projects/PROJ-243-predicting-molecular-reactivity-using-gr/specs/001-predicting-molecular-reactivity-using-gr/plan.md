# Implementation Plan: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Branch**: `001-predicting-molecular-reactivity` | **Date**: 2026-07-11 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-reactivity/spec.md`

## Summary

This project implements a CPU-feasible pipeline to predict molecular reactivity using Graph Neural Networks (GNNs) trained on the QM9 dataset. The technical approach involves ingesting QM9 data, converting SMILES to molecular graphs with RDKit, training lightweight Spectral and Heterophily-aware GNNs, and comparing them against a Random Forest baseline. The plan addresses the "compute feasibility" constraint by strictly adhering to CPU-only execution on GitHub Actions runners, utilizing streaming for large datasets, and employing a "GPU escape hatch" only as a failure recovery mechanism. The plan explicitly maps to all Functional Requirements (FR-001 to FR-009) and Success Criteria (SC-001 to SC-006).

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric` (CPU-only), `scikit-learn`, `pandas`, `pyyaml`, `requests`, `datasets` (HuggingFace), `pytest`, `black`, `ruff`
**Storage**: Local file system (`data/raw`, `data/processed`, `artifacts`)
**Testing**: `pytest` with `pytest-cov`
**Target Platform**: GitHub Actions Free Tier Runner (Linux, multiple vCPU, sufficient RAM)
**Project Type**: Computational Research Pipeline / Library
**Performance Goals**: End-to-end pipeline ≤ 6 hours; Memory usage ≤ 4 GB during peak training.
**Constraints**: No local GPU; datasets must be streamable or sampleable to fit RAM; all external data must be reproducible via public URLs or manual curation from cited literature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Evidence/Mapping in Plan |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins versions; random seeds fixed in `code/`; external datasets fetched from verified URLs (QM9 via `torch_geometric`) or curated from specific DOIs; `data/` directory structure defined with checksums. |
| **II. Verified Accuracy** | **PASS** | T005 'Run Reference Validator' is a blocking task in Phase 0. All dataset URLs cited in `research.md` are from the "Verified datasets" block. Static assets are curated from specific DOIs. |
| **III. Data Hygiene** | **PASS** | `data/raw` for immutable downloads; `data/processed` for derivations; `checksums.json` to be generated and tracked; no in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | T025 'SSoT Validator' explicitly compares `artifacts/metrics.json` against `contracts/output.schema.yaml` and asserts no other data sources are used. |
| **V. Versioning Discipline** | **PASS** | `state/` updates and content hashing logic defined in `quickstart.md` and `data-model.md`. |
| **VI. CPU-First Feasibility** | **PASS** | Methodology explicitly uses `device='cpu'` for PyTorch; streaming dataset loading; subset sampling strategy defined for memory safety. GPU escape hatch is strictly a failure recovery mechanism (CPU error required). |
| **VII. Heterophily-Aware Graph Rep** | **PASS** | Preprocessing explicitly includes node features (atomic number, hybridization, formal charge) and edge features (bond type, conjugation) to support Heterophily-aware GNNs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-reactivity/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
└── tasks.md # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
data/
├── raw/ # Immutable downloads (QM9, reference sets)
│ ├── qm9_subset.parquet
│ ├── reference_substructures_raw.csv
│ └── kinetic_dataset_raw.csv
├── processed/ # Derived graphs and splits
│ ├── graphs.pt # Serialized PyTorch Geometric graphs
│ └── splits/ # Murcko scaffold splits
└── assets/ # Curated static data
 └──...
code/
├── __init__.py
├── config.py # Paths, seeds, hyperparameters
├── data/
│ ├── download.py # QM9 fetcher
│ ├── preprocess.py # SMILES -> Graph conversion (RDKit)
│ └── splits.py # Murcko scaffold splitting
├── models/
│ ├── __init__.py
│ ├── spectral_gnn.py # Lightweight Spectral GNN
│ ├── hetero_gnn.py # Heterophily-aware GNN
│ └── rf_baseline.py # Random Forest baseline
├── train/
│ ├── trainer.py # Training loop (CPU)
│ └── eval.py # Evaluation and metrics
├── interpret/
│ └── explainer.py # GNNExplainer implementation
├── utils/
│ ├── logging.py # Structured logging
│ ├── checksums.py # Checksum generation/verification
│ └── ssot.py # Single Source of Truth validator
└── tests/
 ├── unit/
 ├── integration/
 └── contract/
artifacts/
├── logs/
├── metrics.json
├── predictions.parquet
├── attribution_maps.json
└── exclusion_report.json
```

**Structure Decision**: The "Single project" structure is selected to maintain a monolithic research pipeline that is easier to reproduce on a single runner. All modules are colocated under `code/` to ensure imports are relative and environment setup is centralized in `requirements.txt`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Heterophily-Aware GNN** | Standard GNNs fail on molecular graphs due to low homophily in electronic properties (HOMO/LUMO) across bonds. | Standard Message Passing Neural Networks (MPNN) would yield poor performance, failing SC-002. |
| **Streaming Dataset Loading** | The full QM dataset exceeds available RAM capacity.; direct loading causes OOM on GitHub Actions. | Loading full dataset into memory would crash the runner; streaming is required for feasibility. |
| **Dual Baseline (RF + GNN)** | Need to prove graph structure adds value over traditional descriptors. | A single model baseline would not address the research question of "graph vs. descriptor" advantage. |
| **GPU Escape Hatch** | Required for failure recovery if CPU OOM/timeout occurs. | Not a standard path; only triggers on failure to maintain CPU-first compliance. |

## Implementation Tasks

### Phase 0: Data Curation & Setup (Dependencies: None)

- **T001a** — **Create Data Directories**: Create `data/raw`, `data/processed`, `data/assets`, `artifacts/logs` directories. Add `.gitkeep` files to ensure they are committed.
- **T001b** — **Create Code Directories**: Create `code`, `artifacts`, `tests` directories with `.gitkeep`.
- **T002** — **Setup Configuration**: Create `.flake8`, `ruff.toml`, `pyproject.toml` (Black config), and `requirements.txt` with pinned versions.
- **T003** — **Setup Logging**: Create `logging.conf` and `code/utils/logging.py` to ensure structured logging to `artifacts/logs/pipeline.log`.
- **T004** — **Setup Checksum Schema**: Create `contracts/checksum.schema.yaml` defining the structure for `data/raw/checksums.json`.
- **T005** — **Run Reference Validator**: Implement and run `code/utils/validator.py` to verify all citations in `research.md` against primary sources (DOIs/URLs). **BLOCKING**: Must pass before T010a.
- **T010g** — **Create Checksums Schema**: Define the schema for `checksums.json` (T004).
- **T010a** — **Curate Reference Substructures**: Manually create `data/raw/reference_substructures_raw.csv` (entries) based on specific literature (DOIs in research.md). Columns: `smiles`, `source_doi`, `description`. **Source**: Extract from Table 2 of DOI.
- **T010d** — **Curate Kinetic Dataset**: Manually create `data/raw/kinetic_dataset_raw.csv` (≥20 entries) based on specific literature (DOIs in research.md). Columns: `smiles`, `reaction_rate`, `reaction_type`, `source_doi`. **Source**: Extract from Table 3 of DOI.
- **T010h** — **Populate Checksums**: Compute SHA-256 hashes for `data/raw/qm9_subset.parquet`, `reference_substructures_raw.csv`, and `kinetic_dataset_raw.csv`. Write to `data/raw/checksums.json`. **Dependencies**: T010a, T010d.
- **T010b** — **Verify Reference Checksum**: Verify `reference_substructures_raw.csv` against `checksums.json`.
- **T010e** — **Verify Kinetic Checksum**: Verify `kinetic_dataset_raw.csv` against `checksums.json`.

### Phase 1: Data Ingestion & Preprocessing (Dependencies: T001a, T010h, T010b, T010e)

- **T013** — **Download QM9**: Stream QM9 from `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet`.
- **T014a** — **Preprocess Graphs**: Convert SMILES to graphs. Log invalid SMILES to `artifacts/exclusion_report.json`. Log memory adjustments to `artifacts/memory_adjustment.log` if sampling occurs. **Output**: `artifacts/exclusion_report.json`, `artifacts/memory_adjustment.log`.
- **T014b** — **Generate Graphs**: Save `data/processed/graphs.pt`.
- **T014c** — **Validate Exclusions**: Verify `artifacts/exclusion_report.json` exists and count < 0.1%. Verify `artifacts/memory_adjustment.log` if applicable.
- **T016** — **Serialize Data**: Ensure `graphs.pt` is valid and loadable. **Dependencies**: T014b, T014c.
- **T017** — **Split Data**: Generate Murcko scaffold splits for Train/Val/Test sets.. Apply Tanimoto similarity filter (>0.8 exclusion) to ensure true generalization. **Note**: The [deferred] Validation is carved from the [deferred] Train set; the [deferred] Test is held out completely. Save splits to `data/processed/splits/`.

### Phase 2: Model Training (Dependencies: T016, T017)

- **T021** — **Train Spectral GNN**: Train for a sufficient number of epochs to ensure convergence. with early stopping on **validation loss** ([deferred] split). Save weights to `artifacts/models/spectral_gnn.pt`. **Note**: GPU escape hatch triggers only on CPU MemoryError or timeout.
- **T022** — **Train Heterophily GNN**: Train for a sufficient number of epochs to ensure convergence. with early stopping. Save weights to `artifacts/models/hetero_gnn.pt`.
- **T023a** — **Train RF Baseline**: Train on Morgan fingerprints. Save model to `artifacts/models/rf_baseline.pkl`.
- **T023b** — **Generate Predictions**: Run inference on test set for all three models. Save to `artifacts/predictions.parquet`. **Dependencies**: T021, T022, T023a.
- **T023c** — **Compute Metrics**: Calculate MSE, MAE, Pearson R. Save to `artifacts/metrics.json`. **Dependencies**: T023b.
- **T023d** — **Statistical Tests**: Perform paired t-test (GNN vs RF) with Bonferroni correction. Log results to `artifacts/metrics.json`. **Dependencies**: T023c.
- **T023e** — **Validate Attribution Schema**: Ensure `explainer.py` output matches `contracts/attribution.schema.yaml`.

### Phase 3: Interpretability & Validation (Dependencies: T023a, T023b, T023c, T023d, T010d)

- **T024** — **Generate Attribution**: Run GNNExplainer on test set. Save `artifacts/attribution_maps.json` conforming to `contracts/attribution.schema.yaml`.
- **T025** — **Validate SSoT**: Run `ssot.py` to ensure all metrics/predictions match the schema and are the exclusive source for the paper.
- **T031** — **Validate Correlation**: Filter kinetic dataset to thermodynamically controlled reactions. Correlate predicted gaps with experimental rates. **Note**: Only for trend confirmation, not statistical validation. **Dependencies**: T010d.
- **T032** — **Post-Hoc Independence Check**: Calculate pairwise Tanimoto similarity of errors. If correlated, flag t-test and use Wilcoxon.

### Phase 4: Logging & Archiving (Dependencies: T024, T025, T031, T032)

- **T024** — **Archive Artifacts**: Ensure all model weights, attribution maps, and metrics are saved to `artifacts/`.
- **T026** — **Final Checksum**: Generate checksums for all `artifacts/` files.
