# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-10-21 | **Spec**: `specs/001-polymer-degradation/spec.md`  
**Input**: Feature specification from `/specs/001-polymer-degradation/spec.md`

## Summary
We will build a fully reproducible, CPU‑only research pipeline that (1) streams polymer degradation records from the open **WebBook** CSV on Hugging Face **and** the **Materials Project** API, (2) validates and enriches records (imputes missing temperature/pH/UV, generates rule‑based synthetic degradation labels **only for augmentation**), (3) converts valid SMILES to RDKit molecular graphs and filters for polyesters, (4) doubles the dataset via edge‑dropout + subgraph‑sampling augmentation, (5) trains a ≤3‑layer GNN (hidden dim ≤128) with 5‑fold CV (or leave‑one‑out if *n* < 150) **using only curated labels**, (6) evaluates on a mandatory external validation set of ≥ 30 experimentally verified records, (7) computes Integrated Gradients attributions, (8) runs a **permutation test** (≥1 000 permutations) on IG scores to assess motif significance, (9) performs a confounding‑assessment of imputed environmental variables, (10) assembles a JSON‑backed markdown report satisfying all functional requirements (FR‑001 – FR‑019) and success criteria (SC‑001 – SC‑012). All steps respect the free‑tier GitHub Actions compute budget (≤6 h, ~7 GB RAM) and run on CPU only (no GPU escape hatch).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.3.0` (CPU‑only), `torch_geometric`, `pandas`, `numpy`, `scikit-learn`, `datasets`, `scipy`, `statsmodels`, `click`, `tqdm`, `ruff`, `pytest`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw CSV, processed Parquet, augmented graphs, **output** JSON) and `state/` for logs, checksums, and intermediate artifacts.  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: End‑to‑end runtime ≤ 5.5 h; peak RAM ≤ 6.5 GB; augmentation ≤ 30 min; training ≤ 2 h.  
- **Constraints**: CPU‑only GNN (no GPU escape hatch); data limited to **NIST Chemistry WebBook** and **Materials Project** records; synthetic labels are generated **only for augmentation**, never for supervised training (FR‑001, FR‑008).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | Random seeds pinned in `code/seed.py`; `requirements.txt` pins exact versions; `state/setup_log.txt` records recursive `ls -R` output with timestamp after directory creation (T001b). |
| **II. Verified Accuracy** | All citations verified by Reference‑Validator; title‑token overlap ≥ 0.7. |
| **III. Data Hygiene** | Raw CSV SHA‑256 checksummed; each transformation writes a new file with its own checksum recorded in `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | `docs/reports/final_report.md` is designated as the SSoT for every figure, statistic, and interpretation. |
| **V. Versioning Discipline** | All artifacts content‑hashed; `state/projects/PROJ-078-...yaml` stores `artifact_hashes` and timestamps. |
| **VI. Computational Chemistry Validation** | Integrated Gradients for attribution; permutation test (≥1 000 permutations) for motif significance (α = 0.05); 5‑fold CV (or LOO) as mandated. |
| **VII. Small Dataset Robustness** | Bond‑rotation + atom‑masking doubles the dataset; confidence intervals derived from CV folds are reported. |

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
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-078-predicting-polymer-degradation-pathways-/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── augmented/
│   ├── reports/
│   └── output/            # <--- added to match T024a/T025a
├── code/
│   ├── ingest.py
│   ├── label_validation.py
│   ├── preprocess.py
│   ├── augment.py
│   ├── model.py
│   ├── train.py
│   ├── attribution.py
│   ├── null_distribution.py
│   ├── permutation_test.py
│   ├── confounding_assessment.py
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
│   └── contract_validation.log
└── docs/
    └── reports/
        └── final_report.md
```

## Implementation Phases & FR/SC Coverage

| Phase | Task ID | Description | FR(s) addressed | SC(s) addressed |
|-------|---------|-------------|----------------|-----------------|
| **0 – Foundations** | **T001a** | Create required directory tree (`code/`, `data/raw/`, `data/processed/`, `data/augmented/`, `data/reports/`, `data/output/`, `tests/`, `state/`, `state/projects/`). | **FR-012** | — |
| | **T001b** | Generate `state/setup_log.txt` with recursive `ls -R` output and timestamp after directory creation. | **FR-013** | — |
| | **T002a** | Write pinned dependencies to `code/requirements.txt`. | — | — |
| | **T003a** | Add strict `.ruff.toml` (already present). | **FR-014** | — |
| | **T003b** | Run `ruff check code/`; capture exit code 0 in `state/ruff_check.log`. | **FR-014** | — |
| | **T008a** | Create `pytest.ini` with deterministic options (random‑seed = 42). | **FR-015** | — |
| | **T008b** | Create `tests/conftest.py` that pins `numpy`, `torch`, and `random` seeds to **42**. | **FR-015** | — |
| | **T008c** | Execute `pytest`; log to `state/pytest.log`. | **FR-015** | — |
| **1 – Data Ingestion** | **T013a** | `ingest.py` streams **WebBook CSV** (`https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt`) with exponential backoff (max 3 retries). | FR‑001, FR‑009 | SC‑003 |
| | **T013b** | `ingest.py` also streams **Materials Project** entries via their public API (`https://materialsproject.org/rest/v2/materials`). | FR‑001, FR‑009, **FR-011** | SC‑003 |
| | **T013c** | Merge both sources, de‑duplicate on SMILES, and write to `data/raw/combined.csv`; compute SHA‑256 checksum. | FR‑001 | SC‑006 |
| | **T013d** | Explicitly verify that the merged dataset contains records from **both** NIST WebBook and Materials Project, satisfying FR‑011’s source restriction. | **FR-011** | — |
| **2 – Label Validation & Synthetic Labeling** | **T014a** | `label_validation.py` scans for `degradation_pathway`. Records with missing labels are **synthetically** assigned using rule‑based mapping (ester → hydrolysis, aromatic → photolysis, etc.). | FR‑001 | SC‑006 |
| | **T014b** | Verify that resulting class frequencies are within 10 % of literature‑reported proportions; abort with clear error if not. | FR‑001 | SC‑006 |
| | **T014c** | Flag each record with `label_source` = `"curated"` or `"synthetic"` and store in `data/processed/records.parquet`. Synthetic records are marked for augmentation only. | FR‑001, FR‑008 | SC‑006 |
| | **T014d** | If **all** records lack a curated label, the pipeline aborts (fatal as per FR‑008). | FR‑008 | — |
| **3 – SMILES & Graph Construction** | **T015a** | `preprocess.py` parses SMILES; invalid SMILES are **skipped** and logged in `state/invalid_smiles.log`. | FR‑002, FR‑009 | SC‑006 |
| | **T015b** | Detect ester functional group via SMARTS `C(=O)O`; retain only polyesters. | FR‑001 | SC‑006 |
| | **T015c** | Encode environmental features (temperature, pH, UV) as global graph attributes; impute missing values (25 °C, pH 7, UV 0) and flag in metadata. | FR‑002 | SC‑006 |
| | **T015d** | Save validated `PolymerRecord`s to `data/processed/records.parquet` and pickled `MolecularGraph`s to `data/processed/graphs/`. Record checksums in `state/artifact_hashes.yaml`. | FR‑002 | SC‑006 |
| **4 – Power‑Analysis & Minimum Sample‑Size Cutoff** | **T017a** | Conduct power‑analysis with `statsmodels` to estimate required *n* for macro‑F1 ≥ 0.70, power ≥ 0.8; store results in `state/power_analysis.json`. | SC‑004 | — |
| | **T017b** | If *n* < 150, abort the pipeline with a clear under‑powered warning (fulfills FR‑008’s fatal‑error clause). | FR‑008, SC‑004 | — |
| **5 – Data Augmentation** | **T018a** | `augment.py` reads `data/processed/graphs/` and applies **bond rotation** + **atom masking** to generate exactly **2×** graphs (≤ 30 min). Output to `data/augmented/graphs/`. | FR‑004 | SC‑009 |
| | **T018b** | Verify augmentation factor (`assert n_aug == 2 * n_pre`); log to `state/augment_check.log`. | FR‑004 | — |
| | **T018c** | Abort on factor mismatch; log to `state/augment_error.log`. | FR‑004 | — |
| | **T018d** | RDKit sanitization of each augmented graph; failures logged to `state/invalid_augmented.log` and removed. | FR‑004 | — |
| **6 – Model Definition & Training** | **T019a** | `model.py` defines ≤ 3‑layer GNN, hidden dim ≤ 128, softmax over three pathways. | FR‑003 | — |
| | **T019b** | `train.py` loads **augmented** graphs **with curated labels only** (synthetic labels are used **only for augmentation**). Runs **5‑fold CV** (source 2604.10702) unless *n* < 150 → **Leave‑One‑Out** (per T017b). Early‑stop when `|Δloss|/loss < 0.05` over the last 5 epochs. Logs macro‑F1 per fold and overall mean. | FR‑003, SC‑001 | SC‑001 |
| | **T019c** | Evaluate on the **external validation set** (≥ 30 curated records) required by FR‑010 and compute macro‑F1; log to `state/external_metrics.json`. | FR‑010 | SC‑001 |
| **7 – Feature Attribution** | **T020a** | `attribution.py` computes Integrated Gradients for every test sample; outputs node‑level IG maps and aggregated motif scores to `data/attribution/`. | FR‑005 | SC‑005 |
| | **T020b** | Requires ≥ 10 **curated** hydrolysis records in the external validation set; verifies that the ester bond ranks in the top *deferred* of IG scores for ≥ 90 % of these cases; logs warnings in `state/ig_warning.log`. | SC‑005 | — |
| | **T020c** | Summarize IG statistics (mean ester‑bond IG, proportion meeting threshold) to `state/ig_summary.log`. | SC‑005 | — |
| **8 – Permutation Test for Motif Significance** | **T021a** | `null_distribution.py` shuffles IG scores ≥ 1 000 times; saves `state/null_distribution.npy`. | FR‑006, SC‑002, SC‑011 | — |
| | **T021b** | `permutation_test.py` compares observed motif‑importance against the null distribution, computes empirical p‑values (α = 0.05), and stores results in `data/reports/perm_test_results.json`. | FR‑006, SC‑002, SC‑011 | — |
| **9 – Confounding Assessment of Imputed Variables** | **T022a** | `confounding_assessment.py` regresses IG importance scores against imputed environmental features to detect spurious correlations; results saved to `state/confounding_report.json`. | SC‑003, SC‑006 | — |
| | **T022b** | Reports any significant associations (p < 0.05) between imputed variables and motif importance. | SC‑003 | — |
| **10 – Final Reporting** | **T023a** | `report.py` assembles `docs/reports/final_report.md` containing macro‑F1 ± 95 % CI (internal & external), power‑analysis warning (if *n* < 150), top 3‑5 motifs with importance scores and permutation‑test p‑values, low‑confidence flag summary (threshold 0.6), data ingestion success rate (≥ 95 %), augmentation verification, confounding assessment, and sensitivity outcomes. | FR‑007, SC‑007, SC‑008, SC‑009, SC‑010, SC‑011, SC‑012 |
| **11 – Contract‑Validated Output Generation** | **T024a** | `output_generator.py` writes model predictions for the test set to `data/output/predictions.json` conforming to `output.schema.yaml`. | — | — |
| | **T025a** | `model_output_generator.py` writes aggregated motif importance (including permutation‑test p‑values) to `data/output/model_output.json` conforming to `model_output.schema.yaml`. | **FR-007** | — |
| **12 – Contract Validation** | **T026a** | Run JSON‑Schema validation against all contracts in `contracts/`; log results to `state/contract_validation.log`. | — | — |
| **13 – End‑to‑End Smoke Test** | **T027a** | Execute full pipeline on CI runner; record total runtime and peak RAM via `psutil`. Ensure ≤ 5.5 h and ≤ 6.5 GB RAM; log to `state/smoke_test.log`. | SC‑003 | — |

*All tasks are ordered to respect data flow: download → validation → preprocessing → augmentation → training → attribution → statistical testing → reporting → contract validation → smoke test.*

---


