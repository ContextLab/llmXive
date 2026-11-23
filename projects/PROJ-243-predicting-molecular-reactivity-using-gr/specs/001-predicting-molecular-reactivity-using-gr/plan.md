# Implementation Plan: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Branch**: `001-predicting-molecular-reactivity` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-predicting-molecular-reactivity/spec.md`

## Summary
Implement a fully reproducible, CPU‑first pipeline that (1) downloads a **100 000‑molecule QM9 subset** ([deferred] of the full set) fitting within the GitHub Actions free‑tier memory and runtime limits, (2) converts SMILES to graph objects with RDKit, (3) trains two lightweight heterophily‑aware GNNs and a Random‑Forest baseline on the HOMO‑LUMO gap (proxy for reactivity), (4) evaluates performance with rigorous statistical testing (paired t‑test on error metrics, Fisher‑Z test on Pearson R, Bonferroni correction using the verified α = 0.05 threshold from 2203.15897), (5) conducts GNNExplainer attribution validated against a curated a representative substructure reference set (MMTS ≥ 0.7, null‑model defined via a substantial number of random subgraph samplings), (6) performs a **power‑analysis‑driven** correlation study between predicted HOMO‑LUMO gaps and experimental reaction rates (sample‑size estimation for detecting r ≈ 0.5 with 80 % power at α = 0.05), and (7) archives all artifacts with SHA‑256 checksums. All steps respect the GitHub Actions free‑tier compute limits and the project constitution.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `pandas`, `pyyaml`, `datasets`, `ruff`, `black`, `pytest`  
- **Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only training; memory ≤ 4 GB during graph construction & training; total runtime ≤ 6 h; all external data fetched from verified URLs.

## Constitution Check
| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Reproducibility | PASS | `requirements.txt` pins exact versions; random seeds fixed in `code/config.py`; deterministic download URLs. |
| II. Verified Accuracy | PASS | All external citations reference URLs in the “Verified datasets” block. |
| III. Data Hygiene | PASS | Raw files are immutable; checksums recorded in `data/raw/checksums.json`; transformations write new files. |
| IV. Single Source of Truth | PASS | `contracts/output.schema.yaml` enforces a single‑artifact aggregate. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`; any change triggers a version bump. |
| VI. CPU‑First Feasibility | PASS | All model code runs with `device='cpu'`; batch size auto‑adjusts; GPU escape hatch only a fallback for unexpected OOM (not used in primary path). |
| VII. Heterophily‑Aware Graph Representation | PASS | Node/edge feature set follows FR‑001 and supports VR‑GNN‑style heterophily handling. |

## Project Structure

```text
specs/001-predicting-molecular-reactivity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── attribution.schema.yaml
│   ├── checksums.schema.yaml
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   ├── model-output.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later
```

```text
data/
├── raw/
│   ├── qm9_subset.parquet
│   ├── reference_substructures_raw.csv
│   ├── kinetic_dataset_raw.csv
│   └── checksums.json            # initially [] (empty array)
├── processed/
│   ├── graphs.pt
│   ├── dataset.json               # conforms to contracts/dataset.schema.yaml
│   └── splits/
└── assets/
    └── (static README, licenses)

code/
├── __init__.py
├── config.py                # seeds, hyper‑params, paths
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
├── predictions.json            # conforms to contracts/model-output.schema.yaml
├── predictions.parquet          # optional, for downstream analysis
├── attribution_maps.json
├── exclusion_report.json
├── memory_adjustment.log
├── ruff_report.json
├── black_report.txt
├── checksums_artifacts.json
├── ssot.log
├── kinetic_correlation.png
├── kinetic_report.txt
├── final_output.json           # conforms to contracts/output.schema.yaml
└── ... (other logs)
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Heterophily‑aware GNN | Molecular graphs exhibit low homophily; standard GNNs under‑perform (SC‑002). | Standard MPNN would likely fail the paired‑test significance criterion. |
| Streaming QM9 | Full QM9 > 7 GB; streaming avoids OOM (SC‑005). | Loading the whole dataset would exceed RAM limits. |
| Dual Baseline (RF + GNN) | Enables paired statistical comparison (FR‑006). | A single baseline would not satisfy the significance‑test requirement. |
| Explicit Lint/Format Check | Satisfies FR‑007 (artifact logging) and Constitution I (reproducibility). | Skipping lint would leave an unverifiable step. |
| Empty `checksums.json` → Populated later | Meets FR‑007 (checksum artifact) while obeying the “empty first” rule. | Direct full population would violate the “empty first” rule. |

## Implementation Tasks

### Phase 0 – Repository & Environment Setup
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T001a** | Create `data/raw`, `data/processed`, `data/assets`, `artifacts/logs` directories with `.gitkeep`. | None | Directories exist. |
| **T001b** | Create `code/` and `tests/` directories with `.gitkeep`. | None | Directories exist. |
| **T002a** | Add a minimal `.flake8` configuration file (`[flake8]\nmax-line-length = 88\nexclude = .git,__pycache__,venv`). | T001a | `.flake8` file committed. |
| **T002b** | Execute **ruff** (`ruff check . --output-format=json > artifacts/ruff_report.json`) and **black** (`black --check . > artifacts/black_report.txt`). Fail the pipeline if either command exits non‑zero. | T002a | `artifacts/ruff_report.json`, `artifacts/black_report.txt`. |
| **T003** | Create an **empty** `data/raw/checksums.json` containing `[]`. | T001a | `data/raw/checksums.json` (empty array). |
| **T004** | Populate `requirements.txt` (pins all packages) and optional `pyproject.toml`. | T001a | Dependency files committed. |
| **T005** | Add static assets to `data/raw/`:<br>• `reference_substructures_raw.csv` (50 rows, columns `smiles,source_doi,description`).<br>• `kinetic_dataset_raw.csv` (≥20 rows, columns `smiles,reaction_rate,reaction_type,source_doi`). | T001a | Two CSV files in `data/raw/`. |
| **T006** | Compute **SHA‑256** checksums for **every** file in `data/raw/` (including `qm9_subset.parquet`, `reference_substructures_raw.csv`, `kinetic_dataset_raw.csv`) and **append** entries to `data/raw/checksums.json` using `code/utils/checksums.py`. Each entry must have fields `file_path` and `sha256` as required by `contracts/checksums.schema.yaml`. | T003, T005 | Updated `data/raw/checksums.json` with correct entries. |
| **T007** | Validate `data/raw/checksums.json` against `contracts/checksums.schema.yaml`. Write validation log to `artifacts/checksum_validation.log`. | T006 | Validation log. |

### Phase 1 – Data Ingestion & Preprocessing
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T010** | Download **a 100 k‑molecule QM9 subset** via `torch_geometric.datasets.QM9` with `download=True`, streaming directly to `data/raw/qm9_subset.parquet`. This size fits the 4 GB RAM budget and ≤ 6 h runtime on the free tier. | T001a, T004 | `data/raw/qm9_subset.parquet`. |
| **T011** | Convert SMILES → `torch_geometric.data.Data` objects with node features (atomic number, hybridization, formal charge) and edge features (bond type, conjugation, in‑ring flag). Log any SMILES that RDKit cannot parse to `artifacts/exclusion_report.json`. If RAM usage exceeds 4 GB, automatically reduce batch size and record the adjustment in `artifacts/memory_adjustment.log`. | T010, T006 | `data/processed/graphs.pt`, exclusion & memory logs. |
| **T012** | Serialize the list of graph objects to `data/processed/graphs.pt`. | T011 | Serialized graph file. |
| **T013** | Perform Murcko scaffold split ([deferred] train / [deferred] test) and enforce a Tanimoto similarity filter (≤ 0.8) to create a true generalization hold‑out. Save split indices under `data/processed/splits/`. | T012 | `splits/train.json`, `splits/val.json`, `splits/test.json`. |
| **T014** | Write a JSON dataset `data/processed/dataset.json` that includes required `metadata` (source URL, version, checksum) and a `graphs` array adhering to `contracts/dataset.schema.yaml`. This file is the single source of truth for downstream tasks. | T011, T013 | `data/processed/dataset.json`. |
| **T015b** | Validate `data/processed/dataset.json` against `contracts/dataset.schema.yaml`. Log results to `artifacts/dataset_validation.log`. | T014 | Validation log. |

### Phase 2 – Model Training & Hyper‑parameter Search
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T027** | Perform a **shared hyper‑parameter grid search** (learning rate ∈ {1e‑3,5e‑4}, hidden dim ∈ {64,128}) using 5‑fold CV on the training split. Select the best config for all three models to ensure comparable training budgets. | T013 | `code/config.py` updated with selected hyper‑params. |
| **T020** | Train **Spectral GNN** (Chebyshev convolution, 3 layers, hidden dim = selected) on the training split; early‑stop on validation loss (patience = 5, max = 50 epochs). Save weights to `artifacts/models/spectral_gnn.pt`. | T027, T013 | Model checkpoint. |
| **T021** | Train **Heterophily‑aware GNN** (VR‑GNN style) under identical constraints; save to `artifacts/models/hetero_gnn.pt`. | T027, T013 | Model checkpoint. |
| **T022** | Train **Random Forest** on Morgan fingerprints (radius 2, nBits = 2048) using the same early‑stopping logic (via validation MAE) and max = 50 epochs of tree growth. Save to `artifacts/models/rf_baseline.pkl`. | T027, T013 | Model checkpoint. |
| **T023** | Generate predictions for the test set for all three models **directly as JSON** (`artifacts/predictions.json`) matching `contracts/model-output.schema.yaml`. Optionally also write `artifacts/predictions.parquet` for downstream analysis. | T020, T021, T022 | Prediction files. |
| **T024** | Compute **MSE**, **MAE**, and **Pearson R** for each model; store in `artifacts/metrics.json`. | T023 | Metrics file. |
| **T025** | Perform **paired t‑tests** on the **error vectors** (MSE & MAE) of each GNN vs. RF. Apply **Bonferroni** correction for the two error‑metric comparisons (α = 0.05 → α_adj ≈ 0.025) as recommended by 2203.15897. | T024 | Updated metrics with statistical‑test results (paired t‑test only on error metrics). |
| **T028** | Conduct a **Fisher‑Z test** to compare Pearson R of each GNN against the RF baseline; include Bonferroni‑adjusted α (same α_adj). | T024 | Updated metrics with correlation‑comparison results. |
| **T026** | **Power analysis**: estimate required test‑set size for detecting a medium effect (Cohen’s d = 0.5) with 80 % power at α = 0.05 for the paired t‑test; if current split is insufficient, down‑sample training set to enlarge test split accordingly. Document the achieved power in `artifacts/power_analysis.log`. | T013 | Power‑analysis log. |

### Phase 3 – Interpretability & External Validation
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T030** | Run **GNNExplainer** on a random 100‑molecule subset of the test set; output `artifacts/attribution_maps.json` validated against `contracts/attribution.schema.yaml`. | T023, T005 | Attribution file. |
| **T031** | Compute **Mean‑max Tanimoto Similarity (MMTS)** between each explained substructure and any entry in the curated reference set; also compute a **null‑model baseline** by random subgraph sampling (1 000 repetitions). Store the average MMTS as `alignment_score` and the null‑model mean in `artifacts/metrics.json`. Threshold ≥ 0.7 is justified by Bioinformatics 2021 37 22 4105. | T030, T005 | Updated metrics with interpretability scores. |
| **T032** | Correlate predicted HOMO‑LUMO gaps with experimental reaction rates from `kinetic_dataset_raw.csv` using a **permutation test** (10 000 permutations) to obtain a p‑value and a 95 % confidence interval. Produce scatter plot `artifacts/kinetic_correlation.png` and brief narrative `artifacts/kinetic_report.txt`. The result is reported as **exploratory**; no causal claim is made. | T023, T005 | Correlation artifacts. |
| **T034** | **Power analysis for kinetic correlation**: estimate the minimum number of molecules required to detect a correlation of r ≈ 0.5 with 80 % power at α = 0.05. If the kinetic dataset (≥20 molecules) falls short, the analysis will be flagged as under‑powered and reported as exploratory. Document calculations in `artifacts/kinetic_power.log`. | T005 | Power‑analysis log for external validation. |
| **T033** | Run **Single‑Source‑of‑Truth (SSoT) validator** (`code/utils/ssot.py`) to ensure every figure/number in the eventual paper traces back to a single artifact; log to `artifacts/ssot.log`. | T024, T031 | Validation log. |

### Phase 4 – Final Archiving & Reporting
| ID | Description | Dependencies | Outputs |
|----|-------------|--------------|---------|
| **T040** | Compute **SHA‑256** checksums for **all** files under `artifacts/` and store in `artifacts/checksums_artifacts.json`; validate against `contracts/checksums.schema.yaml`. | T033 | Artifact checksum file. |
| **T040b** | Validate `artifacts/checksums_artifacts.json` against `contracts/checksums.schema.yaml` (jsonschema). Write validation log to `artifacts/checksums_artifacts_validation.log`. | T040 | Validation log. |
| **T045** | Aggregate `metrics.json`, `statistical_tests` (including Fisher‑Z), `predictions.json`, and `attribution_maps.json` into a single `artifacts/final_output.json` that conforms to `contracts/output.schema.yaml`. | T024, T028, T023, T030 | Final output file. |
| **T045a** | Validate `artifacts/final_output.json` against `contracts/output.schema.yaml`. Log results to `artifacts/final_output_validation.log`. | T045 | Validation log. |
| **T041** | Write a concise **README** in `docs/` that lists all artifacts, their schemas, and reproducibility instructions. | T045 | Documentation file. |
| **T042** | Tag the repository with `v0.1.0` and update `state/projects/PROJ-243-...yaml` with a new `updated_at` timestamp. | T041 | Version bump and state update. |

## Mapping FRs & SCs to Tasks
| FR / SC | Covered By |
|---------|------------|
| FR‑001 | T011, T012 |
| FR‑002 | T020, T021 |
| FR‑003 | T020‑T022 (early stopping, scaffold split) |
| FR‑004 | T022 |
| FR‑005 | T030 |
| FR‑006 | T025, T028 |
| FR‑007 | All `artifacts/` generation tasks (T023‑T045) |
| FR‑008 | T005 (curated reference set) + T031 (alignment score) |
| FR‑009 | T005 (kinetic dataset) + T032 + T034 |
| SC‑001 | T024 (Pearson R) |
| SC‑002 | T025 (paired t‑test), T028 (Fisher‑Z), T026 (power analysis) |
| SC‑003 | T031 (MMTS ≥ 0.7, null‑model defined) |
| SC‑004 | Entire pipeline respects the 6‑hour CI timeout; monitored via GitHub Actions. |
| SC‑005 | T011 enforces ≤ 4 GB RAM; adjustments logged. |
| SC‑006 | T032 (permutation test) – acknowledges n ≥ 20 limitation; T034 provides power context. |

---


