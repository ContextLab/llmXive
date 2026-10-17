# Tasks: Predicting Plant Root Architecture from Soil Nutrient Availability

**Input**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contract schemas, and reviewer feedback.  
All tasks write only to project‑owned paths (`code/`, `data/`, `artifacts/`, `tests/`, `README.md`, `quickstart.md`).  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

- [X] T001 Create the project directory skeleton (`code/`, `tests/`, `data/raw/`, `data/processed/`, `artifacts/`, `artifacts/logs/`) and verify its existence by committing a `directory_structure.txt` file that lists the created directories.  
  *Path*: `directory_structure.txt` (project root)  
  *Verification*: `cat directory_structure.txt` must contain all six directories; CI test `tests/test_directory_structure.py` asserts their presence.

- [X] T002 Write `code/requirements.txt` with exact pinned versions for all dependencies required by the specification.  
  *Path*: `code/requirements.txt`  
  *Verification*: `ls code/requirements.txt` must return the file; `pip install -r code/requirements.txt` must exit with code 0.

- [ ] T003 Add linting configuration (`pyproject.toml` with Black & Flake8 settings) and a wrapper script `code/run_lint.py` that exits with code 0 only when lint passes. <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=123 --> <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=123 -->
  *Path*: `pyproject.toml`, `code/run_lint.py`  
  *Verification*: CI step `python code/run_lint.py` must return exit 0; failing lint will cause the task to remain unchecked.

- [ ] T004 Implement a configuration loader, logging setup, and the base data‑model classes `RootPhenotypeRecord` and `SoilNutrientRecord`. Also create a template config file.  
  *Paths*: `code/config.py` (loader & `setup_logging()`), `code/models.py` (dataclasses for the two records), `config.yaml.template` (empty template).  
  *Verification*:  
    1. `python -c "import code.config; code.config.setup_logging()"` creates a log file in `artifacts/logs/`.  
    2. Importing `code.models` yields the two dataclasses without error.  
    3. `config.yaml.template` exists and is listed by `ls`.

- [X] T005 Initialise the project state file with an ISRIC‑verification flag and log any deviation.  
  *Path*: `artifacts/state.json` (JSON with at least `"is_isric_verified": false`) and `artifacts/logs/fallback.log` (must contain the line `ISRIC source not verified – proceeding without soil interpolation`).  
  *Verification*: `jq .is_isric_verified artifacts/state.json` returns `false`; the log file contains the required message.

- [ ] T006 Write the data-ingestion and merging script: download root phenotype data from **RootReader** and **PlantPheno**, download soil nutrient data from **ISRIC**, merge using geographic matching with nearest-neighbor interpolation (≤ 10km), and compute `merge_success_rate` (SC-001). Fail loudly if any required source cannot be fetched.   <!-- FAILED-IN-EXECUTION: code/ingestion.py exit=1 -->
  *Path*: `code/ingestion.py` → output `data/raw/merged_dataset.parquet`  
  *Verification*:  
    1. Running `python code/ingestion.py` creates `data/raw/merged_dataset.parquet`.  
    2. `artifacts/reports/metrics.json` contains `merge_success_rate`.  
    3. `tests/test_ingestion.py` asserts that the output contains both phenotype and nutrient columns.

- [ ] T007 Build the preprocessing pipeline: filter for `data_source_type == "observational"` (FR-012), exclude species with **< 20 observations** (SC-005) and record the exclusion ratio, apply the FR‑025 missing‑nutrient policy (species‑level mean imputation when ≤30 % missing, exclusion otherwise), log all exclusions/imputations, log‑transform root metrics, z‑score nutrients, perform k‑NN (k=5) imputation with mean fallback, and write the cleaned dataset.  
  *Path*: `code/preprocessing.py` → output `data/processed/merged_dataset.parquet`  
  *Verification*:  
    1. The parquet file loads without error and contains the columns required by `contracts/dataset.schema.yaml`.  
    2. `tests/test_preprocessing.py` checks that every species has ≥20 rows, that no `data_source_type` equals `"experimental"`, and that the proportion of imputed values matches the logged decisions.

- [ ] T008 Compute `merge_success_rate` (proportion of root records successfully merged with soil nutrients) and other early success‑criteria; write them to `artifacts/reports/metrics.json` and a companion status file `artifacts/reports/success_criteria_status.json`.  
  *Path*: `code/metrics.py` → `artifacts/reports/metrics.json`, `artifacts/reports/success_criteria_status.json`  
  *Verification*: Both JSON files contain the keys `merge_success_rate` (float ≥ 0.0) and `species_excluded_ratio` (float ≤ 0.10). Unit test `tests/test_metrics.py` asserts the values meet SC‑001 and SC‑005 thresholds.

- [ ] T009 Create the three contract schemas (`contracts/dataset.schema.yaml`, `contracts/model_results.schema.yaml`, `contracts/output.schema.yaml`) and implement a pytest suite `tests/contract/test_schemas.py` that validates:  
    1. The cleaned dataset against `dataset.schema.yaml`.  
    2. The model‑results JSON against `model_results.schema.yaml`.  
    3. The final report JSON against `output.schema.yaml`.  
  *Verification*: Running `pytest tests/contract/test_schemas.py` must exit with all tests passing.

- [ ] T010 Implement the full modelling and analysis pipeline: retrieve peer‑reviewed literature effect sizes (FR-021), fit Linear Mixed‑Effects Model (LMM) and Random Forest baseline, perform 5‑fold species‑stratified CV, apply Benjamini‑Hochberg correction, calculate VIF, perform an F‑test for overall significance (FR-008), and conduct a leave‑one‑species‑out (LOSO) bias assessment (FR-027). All results are written to `artifacts/reports/model_metrics.json`.  
  *Path*: `code/modeling.py` → `artifacts/reports/model_metrics.json`  
  *Verification*: The JSON file contains the fields required by `model_results.schema.yaml` **and** the following SC flags: `sc_002_met`, `sc_003_met`, `sc_006_met`, `power_achieved`, `vif_warning`, `loso_max_coeff_change` (must be ≤ 0.05 per SC-008), and `imputation_bias`. Unit test `tests/test_modeling.py` checks these thresholds.

- [ ] T011 Generate partial‑dependence plots for each nutrient–trait pair (six plots total) using the 5th–95th percentile range of nutrient values, save them as PNGs under `artifacts/reports/plots/`, and verify total size ≤ 100 MB (SC-004). Assemble a markdown report (`artifacts/reports/final_report.md`) that includes:  
    * the mandatory associational statement *“All findings are presented as associational relationships; no causal inference is claimed.”*  
    * tables of model performance and SC flags,  
    * all generated plots.  
  Then run a causal‑language lint (word‑boundary regex for `cause|leads to|effect of|driven by`) to verify SC-007 and write `artifacts/reports/report_verification.json` with fields `associational_statement_present` (bool), `causal_violations` (list), `sc007_met` (bool), and `sc011_met` (bool). Finally convert the markdown to PDF (`final_report.pdf`).  
  *Paths*: `code/visualization.py`, `code/reporting.py`, `artifacts/reports/final_report.md`, `artifacts/reports/final_report.pdf`, `artifacts/reports/report_verification.json`  
  *Verification*:  
    1. `du -m artifacts/reports/plots/` reports ≤ 100 MB total.  
    2. `grep -q "associational relationships" artifacts/reports/final_report.md`.  
    3. `python -c "import json; print(json.load(open('artifacts/reports/report_verification.json'))['sc007_met'])"` returns `true`.  
    4. `pytest tests/test_report.py` confirms all checks.

- [ ] T012 Ensure full reproducibility and hand‑off: compute SHA‑256 checksums for every raw file (`data/checksums.json`), record the checksum of `artifacts/reports/model_metrics.json` as the Single Source of Truth in `artifacts/state.json`, update `README.md` and `quickstart.md` with the exact end‑to‑end command sequence, then run the complete workflow (`python code/ingestion.py && python code/preprocessing.py && python code/modeling.py && python code/visualization.py && python code/reporting.py`) followed by `pytest -q`. The final CI run must finish with exit code 0 and all contract tests passing.  
  *Paths*: `data/checksums.json`, `artifacts/state.json`, `README.md`, `quickstart.md`  
  *Verification*:  
    1. `jq .model_metrics_sha256 artifacts/state.json` returns a non‑empty SHA‑256 string.  
    2. The CI log shows “All tasks completed successfully”.  
    3. `pytest` exits with “0 passed, 0 failed”.  

---

**Dependency summary**

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T001 |
| T004 | T001 |
| T005 | T001 |
| T006 | T001 |
| T007 | T006 |
| T008 | T007 |
| T009 | – (schemas are independent) |
| T010 | T007, T008, T009 |
| T011 | T010, T008 |
| T012 | T011, T009 |

All scientific requirements (FR‑001 … FR‑028) and success criteria (SC‑001 … SC‑011) are covered by the tasks above. The pipeline can be executed on the free‑tier CPU runner (≤ 4 GB RAM, ≤ 6 h).