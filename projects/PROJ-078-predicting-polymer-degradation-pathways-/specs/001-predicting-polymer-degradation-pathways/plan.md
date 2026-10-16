# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-10-15 | **Spec**: `specs/001-polymer-degradation/spec.md`  
**Input**: Feature specification from `/specs/001-polymer-degradation/spec.md`

## Summary
We will build a fully reproducible CPU‑only pipeline that (1) **downloads a verified open polymer degradation dataset** (when one becomes available), (2) filters for polyesters, (3) **flags records missing a curated `degradation_pathway` label** and **excludes them from supervised training** (FR‑008), (4) **does not generate synthetic SMILES**; records without valid SMILES are skipped and logged (FR‑002, FR‑009), (5) converts SMILES to RDKit molecular graphs, (6) augments the graph set using **bond rotation** and **atom masking** (Constitution VII) to obtain exactly a 2× expansion, (7) trains a ≤3‑layer GNN (hidden ≤128) with 5‑fold CV (or LOO if n < 150) on **only real‑labelled data** (FR‑003, SC‑001), (8) computes Integrated Gradients attributions, (9) generates a null distribution for all identified motifs (≥1000 iterations) and performs a χ² test, (10) conducts a **sensitivity analysis** for imputed environmental variables, and (11) produces a markdown report listing the top 3‑5 motifs, confidence flags, and statistical significance. All steps respect the project constitution, the free‑tier CI compute budget, and the verified‑dataset constraint.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.3.0` (CPU‑only), `torch_geometric`, `pandas`, `numpy`, `scikit-learn`, `datasets`, `scipy`, `statsmodels`, `click`, `tqdm`  
- **Storage**: Local filesystem under `data/` (raw CSV, processed Parquet, pickled graphs) and `state/` for checksums and logs.  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Performance Goals**: End‑to‑end runtime ≤ 5.5 h, peak RAM ≤ 6.5 GB, augmentation ≤ 30 min, training ≤ 2 h.  
- **Constraints**: CPU‑only; no GPU‑only libraries; all external data must be fetched from a **verified open source** (currently pending; placeholder will be replaced once an appropriate dataset is identified).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds are pinned in `code/seed.py` and imported by every script; `requirements.txt` pins exact versions; `state/setup_log.txt` records the directory tree and timestamps. |
| **II. Verified Accuracy** | Citations (e.g., confidence threshold 0.6, 5‑fold CV) are drawn from verified sources (see `research.md`). |
| **III. Data Hygiene** | Raw CSV is checksummed (`sha256`) and stored under `data/raw/`; every transformation writes a new file with a documented checksum in `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | Every figure/table in the final report references a single row in `data/processed/records.parquet` and a specific line in a script. |
| **V. Versioning Discipline** | All artifacts are hashed; the `state/projects/...yaml` timestamp is updated on each commit. |
| **VI. Computational Chemistry Validation** | χ² test (α = 0.05) on motif importance; Integrated Gradients for attribution; 5‑fold CV (or LOO) as prescribed. |
| **VII. Small Dataset Robustness** | **Bond rotation** and **atom masking** double the dataset size; confidence intervals are reported from CV folds. |

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
│   ├── seed.py
│   ├── utils.py
│   └── requirements.txt
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── state/
│   ├── artifact_hashes.yaml
│   ├── setup_log.txt
│   ├── power_analysis.json
│   └── amendments.yaml
└── docs/
    └── reports/
        └── final_report.md
```

## Implementation Phases & Task Mapping (FR / SC coverage)

| Phase | Task ID | Description | FR(s) addressed | SC(s) addressed |
|-------|---------|-------------|----------------|-----------------|
| **0 – Foundations** | T001a | Create required directory tree (`code/`, `data/raw/`, `data/processed/`, `data/augmented/`, `tests/`, `state/`). | — | — |
| | **T001b** | **Generate reproducible setup log**: <br>`find . -type f | sort > state/file_list.txt`<br>`date > state/setup_timestamp.txt`<br>`cat state/file_list.txt state/setup_timestamp.txt > state/setup_log.txt`<br>Logs are version‑checked. | — | — |
| | T002a | Generate `code/requirements.txt` with exact version pins. | — | — |
| | T002b | Verify installability in a fresh venv (`pip install -r requirements.txt`). | — | — |
| | T003a | Add `.ruff.toml` with reasonable linting rules. | — | — |
| | T003b | Run `ruff check code/` and capture exit code 0 in `state/ruff_check.log`. | — | — |
| | **T008a** | Create `pytest.ini` with `addopts = -q` and `testpaths = tests`. | — | — |
| | **T008b** | Create `tests/conftest.py` that imports `code/seed.py` and pins `numpy`, `torch`, and `random` seeds (`seed = 42`). | — | — |
| | **T008c** | Run `pytest --maxfail=1` and log results to `state/pytest.log`. | — | — |
| **1 – Data Ingestion** | T010a | `ingest.py` **downloads the verified open polymer degradation CSV** (placeholder URL for now) using `datasets.load_dataset(..., streaming=True)`. Implements exponential backoff (max 3 retries). | FR‑001, FR‑009 | SC‑003 |
| | T010b | Save raw CSV to `data/raw/polymer_records.csv`; compute SHA‑256 and record in `state/artifact_hashes.yaml`. | FR‑001 | SC‑006 |
| **2 – Label Validation & Flagging** | T011a | `label_validation.py` scans `data/raw/polymer_records.csv` for a `degradation_pathway` column. Records missing labels → `label_source = "synthetic"` flag, `flagged_for_curation = true`. Generates `data/processed/label_flags.json`. | FR‑001, FR‑008 | SC‑010 |
| | T011b | If **all** records lack a label, abort with a clear error logged to `state/ingest_error.log` and exit status 1 (halt condition). | FR‑008 | — |
| | T011c | If **some** records lack a label, **exclude** those records from the supervised training set; retain them only for potential unsupervised analysis. No synthetic labels are generated. | FR‑001, FR‑008 | SC‑010 |
| **3 – SMILES & Graph Construction** | T012a | `preprocess.py` attempts to read SMILES from the source CSV. **If SMILES column is missing or invalid**, the record is **skipped** and the SMILES string is logged to `state/invalid_smiles.log`. No synthetic SMILES are created. | FR‑002, FR‑009 | SC‑006 |
| | T012b | Convert each valid SMILES to an RDKit `Mol`; on failure, log SMILES to `state/invalid_smiles.log` and skip the record (FR‑009). | FR‑002, FR‑009 | SC‑006 |
| | T012c | Detect ester functional group using SMARTS `C(=O)O`; retain only polyesters. | FR‑001 | SC‑006 |
| | T012d | Encode environmental features (temperature, pH, UV) as node/graph globals; impute missing values with defaults (25 °C, pH 7, UV 0) and flag imputation in `metadata`. | FR‑002 | SC‑006 |
| | T012e | Save validated `PolymerRecord`s to `data/processed/records.parquet` and pickled `MolecularGraph`s to `data/processed/graphs/`. Record checksums. | FR‑002 | SC‑006 |
| **4 – Power‑Analysis Ratification** | T013a | **Ratify** the proxy power‑analysis amendment: write `state/amendments.yaml` documenting the deviation from the original G*Power requirement, include citation to `statsmodels` documentation, and set `ratified: true`. | SC‑004 | — |
| | T013b | Run a **G\*Power‑style** simulation via `statsmodels` (proxy) to estimate required sample size for macro‑F1 ≥ 0.7 with power 0.8. Store results in `state/power_analysis.json`. | SC‑004 | — |
| **5 – Data Augmentation** | **T014a** | `augment.py` reads `data/processed/graphs/` and performs **bond rotation** (random dihedral angle perturbation) **and** **atom masking** (randomly zero‑out atom feature vectors) to create exactly **2×** the number of graphs. Command: <br>`python code/augment.py --graph-dir data/processed/graphs/ --output data/augmented/graphs/ --method bond_rotation_atom_masking --factor 2`<br>Outputs to `data/augmented/graphs/`. | FR‑004 | SC‑009 |
| | **T014b** | **Verification**: after augmentation run the exact command: <br>`python -c "import pandas as pd, pyarrow.parquet as pq; n_pre = len(pq.read_table('data/processed/records.parquet')); n_aug = len(pq.read_table('data/augmented/records.parquet')); assert n_aug == 2 * n_pre"`<br>Log success/failure to `state/augmentation_check.log`. | FR‑004 | — |
| | T014c | Abort if the final row count is not exactly 2× the pre‑augmentation count; error logged to `state/augmentation_error.log`. | FR‑004 | — |
| | T014d | **Explicit verification** that both bond rotation **and** atom masking were applied by checking log entries for each method (`state/augmentation_method.log`). | FR‑004 | — |
| | T014e | **Chemical validity check**: run RDKit sanitization on each augmented graph; any graph that fails is logged (`state/invalid_augmented.log`) and removed. | FR‑004 | — |
| **6 – Model Definition & Training** | T015a | `model.py` defines a GNN with ≤ 3 message‑passing layers, hidden dim ≤ 128, and a final softmax over three classes. | FR‑003 | — |
| | T015b | `train.py` loads the **augmented** dataset **restricted to records with curated labels**. Performs **5‑fold CV** (source 2604.10702) unless *n* < 150 → **Leave‑One‑Out**. Early‑stop when `|Δloss|/loss < 0.05` over last 5 epochs. Logs macro‑F1 per fold and overall mean. | FR‑003, SC‑001 | SC‑001 |
| **7 – Feature Attribution** | **T016a** | `attribution.py` computes Integrated Gradients for every test sample using the trained model checkpoint (`code/models/model.pt`). Command: <br>`python code/attribution.py --model code/models/model.pt --graph-dir data/augmented/graphs/ --output data/attribution/`<br>Results stored per `contracts/motif_importance.schema.yaml`. | FR‑005 | SC‑005 |
| | **T016b** | **Validation**: requires at least **10 real hydrolysis records** (checked via `pandas.read_parquet`). If available, IG must rank the ester bond among the top **[deferred]** of attribution scores; otherwise, log a warning (`state/attribution_warning.log`) and skip IG validation. | SC‑005 | — |
| | **T016c** | Log summary statistics (mean IG score for ester bond, proportion of hydrolysis cases where ester bond is in top‑[deferred]) to `state/ig_summary.log`. | SC‑005 | — |
| **8 – Null Distribution & χ² Test** | T017a | `null_distribution.py` extracts **all** subgraph patterns identified across the augmented graph set and shuffles their importance scores to build a null distribution (≥ 1000 iterations). Saves `state/null_distribution.npy`. | FR‑006, SC‑002 | — |
| | T017b | `chi2_test.py` compares observed motif‑importance frequencies against the null distribution using `scipy.stats.chi2`. Emits p‑values for each motif; records in `data/reports/chi2_results.json`. | FR‑006, SC‑002, SC‑011 | — |
| **9 – Sensitivity Analysis** | T017c | `sensitivity.py` trains the GNN on three variants of the dataset: (i) with all imputed defaults, (ii) with imputed values replaced by random draws from observed distributions, (iii) with imputed values removed. Reports macro‑F1 differences to assess confounding impact. | SC‑003, SC‑006 | — |
| **10 – Final Reporting** | T018a | `report.py` assembles a markdown report (`docs/reports/final_report.md`) containing: <br>• Macro‑F1 mean ± 95 % CI (SC‑001) <br>• Power‑analysis warning if applicable (SC‑004) <br>• Top 3‑5 motifs with importance scores and χ² p‑values (SC‑007, SC‑011) <br>• Low‑confidence flag summary (threshold 0.6) (SC‑008) <br>• Data ingestion success rate (≥ 95 %) (SC‑006) <br>• Augmentation method verification summary (SC‑009) <br>• Sensitivity‑analysis outcomes (SC‑003) | FR‑007, SC‑007, SC‑008, SC‑009, SC‑010, SC‑011, SC‑012 |
| **11 – Final Checks** | T019a | Verify that all contract schemas in `contracts/` validate against generated artifacts (using `jsonschema`). Log to `state/contract_validation.log`. | — | — |
| | T019b | Run the full pipeline on the CI runner as a smoke test; ensure total runtime ≤ 5.5 h and peak RAM ≤ 6.5 GB (recorded via `psutil`). | SC‑003 | — |

*All tasks are ordered so that data is downloaded before any consumption, models are trained before evaluation, and reports are generated last.*

---

