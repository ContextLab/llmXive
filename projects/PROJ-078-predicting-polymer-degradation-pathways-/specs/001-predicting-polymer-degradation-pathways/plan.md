# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-10-25 | **Spec**: `specs/001-polymer-degradation/spec.md`  
**Input**: Feature specification from `/specs/001-polymer-degradation/spec.md`

## Summary
We will build a fully reproducible, CPU‑only research pipeline that (1) streams polymer degradation records from the open **Polymer Genome** dataset (HuggingFace) and the **Materials Project** API, (2) validates and enriches records (imputes missing temperature/pH/UV, applies rule‑based synthetic label distribution **only for augmentation**), (3) converts valid SMILES to RDKit molecular graphs and filters for polyesters, (4) expands the dataset by **exactly 2×** using bond‑rotation + atom‑masking augmentation (≤ 30 minutes) while recording augmentation metadata, (5) trains a ≤3‑layer GNN (hidden dim ≤128) with 5‑fold cross‑validation (or leave‑one‑out if *n* < 150) **using only curated labels**, (6) evaluates on an **external validation set** of ≥ 30 experimentally verified polymer degradation records **de‑duplicated** from the training sources, (7) computes Integrated Gradients attributions, (8) runs a **McNemar’s test** (α = 0.05) on the external validation predictions for significance, (9) runs a permutation test for motif importance, (10) performs an expanded confounding assessment (environmental variables **and** polymer size, degree distribution, aromatic ring count), (11) assembles a JSON‑backed markdown report satisfying all functional requirements (FR‑001 – FR‑021) and success criteria (SC‑001 – SC‑013). All steps respect the free‑tier GitHub Actions compute budget (≤ 6 h, ~7 GB RAM) and run on CPU only.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.3.0` (CPU‑only), `torch_geometric`, `pandas`, `numpy`, `scikit-learn`, `datasets`, `scipy`, `statsmodels`, `networkx`, `click`, `tqdm`, `ruff`, `pytest`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw, processed, augmented, external, reports, output) and `state/` for logs, checksums, and intermediate artifacts.  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h).  
- **Performance Goals**: End‑to‑end runtime ≤ 5.5 h; peak RAM ≤ 6.5 GB; augmentation ≤ 30 min; training ≤ 2 h.  
- **Constraints**: CPU‑only GNN (no GPU escape hatch); data limited to **Polymer Genome**, **Materials Project**, and the curated external validation set (FR‑011). Synthetic labels are generated **only for augmentation** (FR‑001, FR‑008).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | Random seeds pinned in `code/seed.py`; `requirements.txt` pins exact versions; `state/setup_log.txt` records recursive `ls -R` output with timestamp after directory creation (T001b). |
| **II. Verified Accuracy** | All citation‑containing files (`plan.md`, `research.md`, `quickstart.md`) are processed by the Reference‑Validator in task T030a. |
| **III. Data Hygiene** | Raw and processed files receive SHA‑256 checksums (tasks T016a‑c); each transformation writes a new file with its own checksum recorded in `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | `docs/reports/final_report.md` is the designated SSoT for every figure, statistic, and interpretation. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; hashes stored in `state/projects/PROJ-078-...yaml` with timestamps. |
| **VI. Computational Chemistry Validation** | Integrated Gradients for attribution; McNemar’s test (α = 0.05) for significance; permutation test (≥1 000 permutations) for motif importance; 5‑fold CV (or LOO) as mandated. |
| **VII. Small Dataset Robustness** | Bond‑rotation + atom‑masking doubles the dataset (FR‑004, FR‑019); confidence intervals derived from CV folds are reported. |

## Project Structure
```text
specs/001-polymer-degradation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   ├── molecular_graph.schema.yaml
│   ├── motif_importance.schema.yaml
│   ├── output.schema.yaml
│   └── polymer_record.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-078-predicting-polymer-degradation-pathways-/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── augmented/
│   ├── external/
│   ├── reports/
│   └── output/
├── code/
│   ├── ingest.py               # FR‑016
│   ├── label_validation.py
│   ├── preprocess.py           # FR‑017
│   ├── augment.py              # FR‑019
│   ├── model.py
│   ├── train.py
│   ├── evaluate_external.py
│   ├── attribution.py
│   ├── mcnemar_test.py         # replaces χ²
│   ├── null_distribution.py
│   ├── permutation_test.py
│   ├── confounding_assessment.py
│   ├── ablation.py
│   ├── visualization.py
│   ├── report.py
│   ├── power_analysis.py
│   ├── create_external_validation.py
│   ├── seed.py
│   ├── utils.py
│   ├── requirements.txt
│   └── .ruff.toml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── state/
│   ├── artifact_hashes.yaml
│   ├── setup_log.txt
│   ├── ruff_check.log
│   ├── pytest.log
│   ├── power_analysis.json
│   ├── augment_check.log
│   ├── augment_error.log
│   ├── ingest_error.log
│   ├── invalid_smiles.log
│   ├── ig_summary.log
│   ├── ig_warning.log
│   ├── null_distribution.npy
│   ├── confounding_report.json
│   ├── mcnemar_results.json
│   ├── perm_test_results.json
│   ├── contract_validation.log
│   ├── smoke_test.log
│   └── augmentation_metadata.json
└── docs/
    └── reports/
        └── final_report.md
```

## Implementation Phases & FR/SC Coverage

| Phase | Task ID | Description | FR(s) addressed | SC(s) addressed |
|-------|---------|-------------|----------------|-----------------|
| **0 – Foundations** | **T001a** | Create required directory tree (`code/`, `data/raw/`, `data/processed/`, `data/augmented/`, `data/external/`, `data/reports/`, `data/output/`, `tests/`, `state/`, `state/projects/`). | **FR‑012** | — |
| | **T001b** | Generate `state/setup_log.txt` with recursive `ls -R` output and timestamp after repository initialization. | **FR‑013** | — |
| | **T002a** | Write pinned dependencies to `code/requirements.txt`. | — | — |
| | **T003a** | Add strict `.ruff.toml` (already present). | **FR‑014** | — |
| | **T003b** | Run `ruff check code/`; capture exit code 0 in `state/ruff_check.log`. | **FR‑014** | — |
| | **T008a** | Create `pytest.ini` with deterministic options (`addopts = "--random-order-seed=42"`). | **FR‑015** | — |
| | **T008b** | Create `tests/conftest.py` that pins `numpy`, `torch`, and `random` seeds to **42**. | **FR‑015** | — |
| | **T008c** | Execute `pytest`; log to `state/pytest.log`. | **FR‑015** | — |
| | **T016a** | Compute SHA‑256 checksum for `data/raw/combined.parquet` and write to `state/artifact_hashes.yaml`. | **FR‑018** | — |
| | **T016b** | Compute SHA‑256 checksums for `data/processed/records.parquet` and `data/processed/graphs/` and record in `state/artifact_hashes.yaml`. | **FR‑018** | — |
| | **T016c** | Compute SHA‑256 checksums for `data/augmented/graphs/` and record in `state/artifact_hashes.yaml`. | **FR‑018** | — |
| **1 – Data Ingestion** | **T013a** | `ingest.py` streams **Polymer Genome** dataset (`https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet`) with exponential backoff (max 3 retries). | **FR‑001**, **FR‑009**, **FR‑011**, **FR‑016** | **SC‑003** |
| | **T013b** | `ingest.py` streams **Materials Project** entries via their public API (`https://materialsproject.org/rest/v2/materials`). | **FR‑001**, **FR‑009**, **FR‑011**, **FR‑016** | **SC‑003** |
| | **T013c** | Merge both sources, de‑duplicate on canonical SMILES, write to `data/raw/combined.parquet`; compute SHA‑256 checksum (T016a). | **FR‑001** | **SC‑006** |
| | **T013d** | Verify that the merged dataset contains records from **both** sources (log to `state/ingest.log`). | **FR‑011** | — |
| | **T013e** | Log all API interactions, retries, and backoff timings to `state/ingest_error.log`. | **FR‑009** | — |
| **2 – Label Validation & Synthetic Labeling** | **T014a** | `label_validation.py` scans for `label`. Missing labels receive rule‑based synthetic labels (ester → hydrolysis, aromatic → photolysis, etc.). | **FR‑001** | **SC‑006** |
| | **T014b** | Validate that class frequencies are within 10 % of literature‑reported proportions (Bergman 2022); abort with error if not. | **FR‑001** | **SC‑006** |
| | **T014c** | Flag each record with `label_source` = `"curated"` or `"synthetic"`; synthetic records are **marked for augmentation only** and will be excluded from training. | **FR‑001**, **FR‑008** | **SC‑006** |
| | **T014d** | If **all** records lack a curated label, halt and report a fatal error (FR‑008). | **FR‑008** | — |
| | **T014e** | Create external validation set of ≥ 30 curated records, de‑duplicated against the training data, stored as `data/external/validation.parquet`; abort if fewer than 30 (FR‑010). | **FR‑010** | **SC‑010** |
| **3 – SMILES & Graph Construction** | **T015a** | `preprocess.py` parses SMILES with RDKit; invalid SMILES are **skipped** and logged in `state/invalid_smiles.log`. | **FR‑002**, **FR‑009**, **FR‑017** | **SC‑006** |
| | **T015b** | Detect ester functional group via SMARTS `C(=O)O`; retain only polyesters and output boolean `is_polyester`. | **FR‑001**, **FR‑017** | **SC‑006** |
| | **T015c** | Encode environmental features as `temp_c`, `ph`, `uv_exposure`; impute missing values (25 °C, pH 7, UV 0) and flag in metadata. | **FR‑002** | **SC‑006** |
| | **T015d** | Save validated `PolymerRecord`s to `data/processed/records.parquet` and pickled `MolecularGraph`s to `data/processed/graphs/`; record checksums (T016b). | **FR‑002** | **SC‑006** |
| **4 – Power‑Analysis & Sample‑Size Cutoff** | **T017a** | Conduct power‑analysis with `statsmodels` targeting macro‑F1 ≥ 0.70, power ≥ 0.8; store results in `state/power_analysis.json`. | **SC‑004** | — |
| | **T017b** | If *n* < 150, abort the pipeline with a clear under‑powered warning (fulfills FR‑008’s fatal‑error clause). | **FR‑008**, **SC‑004** | — |
| **5 – Data Augmentation** | **T018a** | `augment.py` reads `data/processed/graphs/` and applies **bond rotation and atom masking** (FR‑019) **only to records with `label_source='synthetic'`** to generate exactly **2×** graphs (≤ 30 min). Output to `data/augmented/graphs/`. | **FR‑004**, **FR‑019** | **SC‑009** |
| | **T018b** | Verify augmentation factor (`assert n_aug == 2 * n_pre`); log to `state/augment_check.log`. | **FR‑004** | — |
| | **T018c** | Abort on factor mismatch; log to `state/augment_error.log`. | **FR‑004** | — |
| | **T018d** | RDKit sanitization of each augmented graph; failures logged to `state/invalid_augmented.log` and removed. | **FR‑004** | — |
| | **T018e** | Write `state/augmentation_metadata.json` documenting original count, augmented count, and factor = 2. | **FR‑004**, **VII** | — |
| **6 – Model Definition & Training** | **T019a** | `model.py` defines ≤ 3‑layer GNN, hidden dim ≤ 128, softmax over three pathways. | **FR‑003** | — |
| | **T019b** | `train.py` loads **augmented** graphs **but filters to records where `label_source='curated'` only**; runs **5‑fold CV** (source 2604.10702) unless *n* < 150 (then abort). Early‑stop when `|Δloss|/loss < 0.05` over last 5 epochs. Logs macro‑F1 per fold and overall mean. | **FR‑003**, **SC‑001** | **SC‑001** |
| | **T019c** | Evaluate on the **external validation set** (≥ 30 curated records) and compute macro‑F1; log to `state/external_metrics.json`. | **FR‑010** | **SC‑001** |
| **7 – Feature Attribution** | **T020a** | `attribution.py` computes Integrated Gradients for every test sample; outputs node‑level IG maps and aggregated motif scores to `data/attribution/`. | **FR‑005** | **SC‑005** |
| | **T020b** | Verify that **≥ 10 curated hydrolysis records** in the external set have the ester bond among the top **deferred** IG scores for ≥ 90 % of cases (confidence threshold 0.6 from 2312.01650). Synthetic‑label records are **not** used for this validation. Log warnings in `state/ig_warning.log`. | **SC‑005** | — |
| | **T020c** | Summarize IG statistics (mean ester‑bond IG, proportion meeting threshold) to `state/ig_summary.log`. | **SC‑005** | — |
| **8 – McNemar’s Significance Test** | **T021a** | `mcnemar_test.py` builds a 2×2 contingency table of correct/incorrect predictions on the **external validation set**; computes McNemar’s χ² statistic and p‑value (α = 0.05). Results saved to `state/mcnemar_results.json`. | **FR‑006**, **SC‑002**, **SC‑011** | — |
| **9 – Permutation Test for Motif Significance** | **T022a** | `null_distribution.py` shuffles IG scores ≥ 1 000 times; saves `state/null_distribution.npy`. | **FR‑006**, **SC‑002**, **SC‑011** | — |
| | **T022b** | `permutation_test.py` compares observed motif‑importance against the null distribution, computes empirical p‑values (α = 0.05), stores results in `data/reports/perm_test_results.json`. | **FR‑006**, **SC‑002**, **SC‑011** | — |
| **10 – Expanded Confounding Assessment** | **T023a** | `confounding_assessment.py` regresses IG importance scores against imputed `temp_c`, `ph`, `uv_exposure` **and** polymer size (number of atoms), degree distribution statistics, and aromatic ring count; saves report to `state/confounding_report.json`. | **SC‑003**, **SC‑006** | — |
| **11 – Ablation Study (No Synthetic Labels)** | **T024a** | `ablation.py` retrains the GNN **without any synthetically labeled records** (uses only curated records), evaluates on the external set, and records macro‑F1 difference relative to the full‑training run in `state/ablation_results.json`. | **FR‑021** | **SC‑005** |
| **12 – Visualization of Top Pathways** | **T025a** | `visualization.py` builds a NetworkX graph of the top degradation pathways with associated motifs; saves PNG to `data/reports/visualizations/top5_pathways.png`. | **FR‑020** | **SC‑010** |
| **13 – Final Reporting** | **T026a** | `report.py` assembles `docs/reports/final_report.md` containing macro‑F1 ± 95 % CI (internal & external), power‑analysis warning (if applicable), McNemar’s statistic & p‑value, top 3‑5 motifs with importance scores and permutation‑test p‑values, low‑confidence flag summary (threshold 0.6), data ingestion success rate (≥ 95 %), augmentation verification, confounding assessment, and ablation‑study outcome. | **FR‑007**, **SC‑007**, **SC‑008**, **SC‑009**, **SC‑010**, **SC‑011**, **SC‑012**, **SC‑013** |
| **14 – Contract‑Validated Output Generation** | **T027a** | `output_generator.py` writes model predictions for the test set to `data/output/predictions.json` conforming to `output.schema.yaml`. | — | — |
| | **T027b** | `model_output_generator.py` writes aggregated motif importance (including permutation‑test p‑values) to `data/output/model_output.json` conforming to `motif_importance.schema.yaml`. | **FR‑007** | — |
| **15 – Contract Validation** | **T028a** | Run JSON‑Schema validation against all contracts in `contracts/`; log results to `state/contract_validation.log`. | — | — |
| **16 – Reference‑Validator Execution** | **T030a** | Run the Reference‑Validator on all citation‑containing files (`plan.md`, `research.md`, `quickstart.md`) and log outcomes to `state/reference_validator.log`. | — | — |
| **17 – End‑to‑End Smoke Test** | **T029a** | Execute full pipeline on CI runner; record total runtime and peak RAM via `psutil`. Ensure ≤ 5.5 h and ≤ 6.5 GB RAM; log to `state/smoke_test.log`. | **SC‑003** | — |

*All tasks are ordered to respect data flow: download → validation → preprocessing → augmentation → training → attribution → statistical testing → reporting → contract validation → smoke test.*


