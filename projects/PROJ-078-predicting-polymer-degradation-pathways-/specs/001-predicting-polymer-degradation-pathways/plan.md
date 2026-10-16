# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-10-15 | **Spec**: `specs/001-polymer-degradation/spec.md`  
**Input**: Feature specification from `/specs/001-polymer-degradation/spec.md`

## Summary
We will construct a fully reproducible, CPU‑only pipeline that (1) downloads polymer degradation records from the NIST Chemistry WebBook and Materials Project APIs, (2) filters for polyesters, (3) flags and excludes records missing curated degradation‑pathway labels (no synthetic labels are generated), (4) converts valid SMILES to RDKit molecular graphs enriched with environmental features, (5) augments the graph set by exactly 2× using bond‑rotation and atom‑masking, (6) trains a ≤3‑layer GNN (hidden dim ≤128) with 5‑fold cross‑validation (or leave‑one‑out if *n* < 150), (7) evaluates on both an internal held‑out split and an external validation set of ≥30 experimentally verified records, (8) computes Integrated Gradients attributions, (9) performs a permutation‑based χ² significance test (≥1 000 permutations), (10) runs a sensitivity analysis on imputed environmental variables, and (11) assembles a final JSON‑backed markdown report containing macro‑F1 (≥ 0.70 on both test sets), motif rankings, p‑values (≤ 0.05), low‑confidence flags, and all required provenance metadata. All steps respect the free‑tier CI compute budget and the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.3.0` (CPU‑only), `torch_geometric`, `pandas`, `numpy`, `scikit-learn`, `datasets`, `scipy`, `statsmodels`, `click`, `tqdm`, `ruff`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw CSV, processed Parquet, augmented graphs) and `state/` for checksums and logs.  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: End‑to‑end runtime ≤ 5.5 h, peak RAM ≤ 6.5 GB, augmentation ≤ 30 min, training ≤ 2 h.  
- **Constraints**: CPU‑only (no GPU escape hatch), only open data from NIST Chemistry WebBook and Materials Project (no other datasets).  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | Random seeds are pinned in `code/seed.py` and imported everywhere; `requirements.txt` pins exact versions; `state/setup_log.txt` records a recursive directory listing with timestamp. |
| **II. Verified Accuracy** | All citations (e.g., 5‑fold CV source 2604.10702, confidence threshold 0.6 source 2312.01650) are drawn from verified literature. |
| **III. Data Hygiene** | Raw CSV is SHA‑256 checksummed; each transformation writes a new file with its own checksum recorded in `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | Every figure/table in the final report references a single row in `data/processed/records.parquet` and a specific line in a script. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; `state/projects/PROJ-078-...yaml` stores `artifact_hashes` and timestamps. |
| **VI. Computational Chemistry Validation** | Integrated Gradients for attribution; χ² test (α = 0.05) for motif significance; 5‑fold CV (or LOO) as mandated. |
| **VII. Small Dataset Robustness** | Bond‑rotation + atom‑masking double the dataset; confidence intervals derived from CV folds are reported. |

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
│   └── augmented/
├── code/
│   ├── ingest.py
│   ├── label_validation.py
│   ├── preprocess.py
│   ├── augment.py
│   ├── model.py
│   ├── train.py
│   ├── attribution.py
│   ├── null_distribution.py
│   ├── chi2_test.py
│   ├── sensitivity.py
│   ├── report.py
│   ├── power_analysis.py
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
│   └── amendments.yaml
└── docs/
    └── reports/
        └── final_report.md
```

## Implementation Phases & Task Mapping (FR / SC coverage)

| Phase | Task ID | Description | FR(s) addressed | SC(s) addressed |
|-------|---------|-------------|----------------|-----------------|
| **0 – Foundations** | T001a | **Create required directory tree** (`code/`, `data/raw/`, `data/processed/`, `data/augmented/`, `data/reports/`, `tests/`, `state/`). | — | — |
| | T001b | **Generate reproducible setup log** (`state/setup_log.txt`) containing `ls -R` output and a timestamp. | — | — |
| | T002a | Write exact dependency pins to `code/requirements.txt`. | — | — |
| | T002b | Verify installability in a fresh venv (`pip install -r requirements.txt`). | — | — |
| | T003a | Add `.ruff.toml` with strict linting rules. | — | — |
| | T003b | Run `ruff check code/`; capture exit code 0 in `state/ruff_check.log`. | — | — |
| | T008a | Create `pytest.ini` with deterministic options (`addopts = -q`, `testpaths = tests`). | — | — |
| | T008b | Create `tests/conftest.py` that imports `code/seed.py` and pins `numpy`, `torch`, and `random` seeds to **42**. | — | — |
| | T008c | Execute `pytest --maxfail=1`; log results to `state/pytest.log`. | — | — |
| **1 – Data Ingestion** | T010a | `ingest.py` **downloads polymer degradation CSVs** from the NIST Chemistry WebBook and Materials Project APIs using `datasets.load_dataset(..., streaming=True)`. Implements exponential backoff (max 3 retries). | FR‑001, FR‑009 | SC‑003 |
| | T010b | Save raw CSV to `data/raw/polymer_records.csv`; compute SHA‑256 and record in `state/artifact_hashes.yaml`. | FR‑001 | SC‑006 |
| **2 – Label Validation & Flagging** | T011a | `label_validation.py` scans for a `degradation_pathway` column. Records missing labels → `label_source="curated"` vs `"synthetic"` flag; writes `data/processed/label_flags.json`. | FR‑001, FR‑008 | SC‑010 |
| | T011b | If **all** records lack a label, abort with error logged to `state/ingest_error.log` and exit 1 (fatal as required). | FR‑008 | — |
| | T011c | If only some records lack a label, **exclude** those from supervised training; retain for unsupervised analysis only. | FR‑001, FR‑008 | SC‑010 |
| **3 – SMILES & Graph Construction** | T012a | `preprocess.py` attempts to read SMILES. Invalid or missing SMILES are **skipped**; each such SMILES is logged to `state/invalid_smiles.log`. No synthetic SMILES are generated. | FR‑002, FR‑009 | SC‑006 |
| | T012b | Convert valid SMILES to RDKit `Mol`; on failure, log and skip (FR‑009). | FR‑002, FR‑009 | SC‑006 |
| | T012c | Detect ester functional group via SMARTS `C(=O)O`; retain only polyesters. | FR‑001 | SC‑006 |
| | T012d | Encode environmental features (temperature, pH, UV) as global graph attributes; impute missing values (25 °C, pH 7, UV 0) and flag imputation in metadata. | FR‑002 | SC‑006 |
| | T012e | Save validated `PolymerRecord`s to `data/processed/records.parquet` and pickled `MolecularGraph`s to `data/processed/graphs/`. Record checksums. | FR‑002 | SC‑006 |
| **4 – Power‑Analysis (Ratified Amendment)** | T013a | Write `state/amendments.yaml` documenting the proxy power‑analysis amendment (ratified). | SC‑004 | — |
| | T013b | Run a G*Power‑style simulation via `statsmodels` to estimate required *n* for macro‑F1 ≥ 0.70 with power ≥ 0.8; store results in `state/power_analysis.json`. | SC‑004 | — |
| **5 – Data Augmentation** | T014a | `augment.py` reads `data/processed/graphs/` and performs **bond rotation** + **atom masking** to create exactly **2×** the number of graphs (≤ 30 min). Output to `data/augmented/graphs/`. | FR‑004 | SC‑009 |
| | T014b | Verify augmentation factor: `assert n_aug == 2 * n_pre`; log to `state/augment_check.log`. | FR‑004 | — |
| | T014c | Abort if factor mismatch; log to `state/augment_error.log`. | FR‑004 | — |
| | T014d | Log method usage (`bond_rotation`, `atom_masking`) to `state/augment_method.log`. | FR‑004 | — |
| | T014e | RDKit sanitization of each augmented graph; any failures logged to `state/invalid_augmented.log` and removed. | FR‑004 | — |
| **6 – Model Definition & Training** | T015a | `model.py` defines a GNN with ≤ 3 message‑passing layers, hidden dim ≤ 128, and a softmax over three degradation classes. | FR‑003 | — |
| | T015b | `train.py` loads **augmented** graphs **restricted to records with curated labels**. Performs **5‑fold CV** (source 2604.10702) unless *n* < 150 → **Leave‑One‑Out**. Early‑stop when `|Δloss|/loss < 0.05` over last 5 epochs. Logs macro‑F1 per fold and overall mean. | FR‑003, SC‑001 | SC‑001 |
| | T015c | After CV, evaluate on an **external validation set** of ≥ 30 experimentally verified polymer degradation records (downloaded via `datasets.load_dataset` from a verified open source if available). Compute macro‑F1 and log to `state/external_metrics.json`. | FR‑010 | SC‑001 |
| **7 – Feature Attribution** | T016a | `attribution.py` computes Integrated Gradients for every test sample using the best checkpoint (`code/models/model.pt`). Outputs per‑sample IG maps and aggregated motif scores to `data/attribution/`. | FR‑005 | SC‑005 |
| | T016b | Validation: requires ≥ 10 real hydrolysis records (checked via `pandas.read_parquet`). If available, IG must rank the ester bond among the top **[deferred]** of attribution scores for ≥ 90 % of hydrolysis cases; otherwise log warning `state/ig_warning.log`. | SC‑005 | — |
| | T016c | Summarize IG statistics (mean ester‑bond IG, proportion meeting threshold) to `state/ig_summary.log`. | SC‑005 | — |
| **8 – Null Distribution & χ² Test** | T017a | `null_distribution.py` extracts all subgraph motifs, shuffles importance scores ≥ 1 000 times, saves `state/null_distribution.npy`. | FR‑006, SC‑002 | — |
| | T017b | `chi2_test.py` compares observed motif‑importance frequencies against the null distribution using `scipy.stats.chi2`. Emits p‑values (α = 0.05) in `data/reports/chi2_results.json`. | FR‑006, SC‑002, SC‑011 | — |
| **9 – Sensitivity Analysis** | T018a | `sensitivity.py` trains the GNN on three dataset variants: (i) full imputation, (ii) random imputation, (iii) imputation‑removed. Reports macro‑F1 differences to `data/sensitivity/summary.json`. | SC‑003, SC‑006 | — |
| **10 – Final Reporting** | T019a | `report.py` assembles `docs/reports/final_report.md` containing: macro‑F1 ± 95 % CI (both internal and external), power‑analysis warning (if *n* < 150), top 3‑5 motifs with importance scores and χ² p‑values, low‑confidence flag summary (threshold 0.6), data ingestion success rate (≥ 95 %), augmentation verification, sensitivity analysis outcomes, and checksum provenance. | FR‑007, SC‑007, SC‑008, SC‑009, SC‑010, SC‑011, SC‑012 |
| **11 – Contract Validation** | T020a | Run JSON‑Schema validation against all contracts in `contracts/`; log results to `state/contract_validation.log`. | — | — |
| **12 – End‑to‑End Smoke Test** | T021a | Execute the full pipeline on the CI runner; record total runtime and peak RAM via `psutil`. Ensure ≤ 5.5 h and ≤ 6.5 GB RAM. Log to `state/smoke_test.log`. | SC‑003 | — |

*All tasks are ordered to respect data flow: download → validation → preprocessing → augmentation → training → attribution → statistical testing → reporting.*

---
