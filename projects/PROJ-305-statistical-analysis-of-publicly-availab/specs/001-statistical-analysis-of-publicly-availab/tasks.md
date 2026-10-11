# Tasks: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Input**: Design documents from `/specs/001-statistical-analysis-covid-vaers/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`

---

## Phase 0 – Project scaffolding & tooling  

- [ ] **T001** [ P ] Create the full project directory tree and verify its existence.  
  - **Paths**: `src/`, `src/data/`, `src/analysis/`, `src/utils/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `contracts/`, `logs/`, `README.md`, `.gitignore`  
  - **Verification**: Run `tree -a -L 3` (or equivalent) and store the output in `logs/structure.txt`; confirm that each listed directory exists and is non‑empty.

- [ ] **T002** [ P ] Create project‑level `.gitignore` and a minimal `README.md` containing the project title, short description, and a “Quickstart” section.  
  - **Paths**: `.gitignore`, `README.md` (root)  
  - **Verification**: Grep the files for the project title “Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports”.

- [ ] **T003** [ P ] Configure linting and formatting tools (ruff, flake8, black) via a `pyproject.toml` (or separate config files).  
  - **Paths**: `pyproject.toml`, `.ruff.toml`, `.flake8` (if separate)  
  - **Verification**: Run `ruff check .` and `black --check .`; both commands must exit with status 0.

---

## Phase 1 – Foundational contracts & utilities  

- [ ] **T004** [ P ] Add the contract schema files required by the specification.  
  - **Paths**: `contracts/dataset.schema.yaml` (as defined in *specs/.../contracts/dataset.schema.yaml*), `contracts/signal.schema.yaml` (as defined in *specs/.../contracts/signal.schema.yaml*)  
  - **Verification**: Validate each YAML file with `jsonschema` (`jsonschema -i dummy.json contracts/dataset.schema.yaml`) to ensure they are syntactically correct.

- [ ] **T005** [ P ] Create `src/utils/config.py` with paths, random seeds, and metric thresholds.  
  - **Path**: `src/utils/config.py`  

- [ ] **T006** [ P ] Verify absence of GPU‑dependent libraries in `requirements.txt`.  
  - **Path**: `requirements.txt` (log written to `logs/gpu_check.log`)  

- [ ] **T007** [ P ] Implement `src/data/validate.py` – a CLI that loads `contracts/dataset.schema.yaml` and validates a CSV/Parquet file, exiting with error code `E_SCHEMA_MISSING` when required columns are absent.  
  - **Path**: `src/data/validate.py`  
  - **Verification**: Run the script on a deliberately malformed CSV and confirm it exits with the expected error code.

- [ ] **T008** [ P ] Implement `src/utils/plots.py` with helper functions for: (a) line/point plots of weekly counts, (b) forest‑plot style ROR/PRR/IC tables, and (c) saving figures to `output/figures/`.  
  - **Path**: `src/utils/plots.py`  
  - **Verification**: Unit test `tests/unit/test_plots.py` must pass, checking that a PNG file is created.

- [ ] **T009** [ P ] Implement `src/data/download_meddra.py` that fetches a verified MedDRA‑to‑SOC mapping (e.g., from the `meddra` PyPI package or a trusted public CSV) and writes `data/meddra_soc_mapping.csv`.  
  - **Paths**: `src/data/download_meddra.py`, `data/meddra_soc_mapping.csv`  
  - **Verification**: After execution, `data/meddra_soc_mapping.csv` must contain at least the columns `SOC_CODE` and `SOC_NAME`; checksum stored in `logs/meddra_checksum.txt`.

- [ ] **T010** [ P ] Initialize the Python‑3.11 environment with pinned dependencies (`pandas`, `numpy`, `scipy`, `requests`, `pyarrow`, `matplotlib`, `pytest`, `pytest‑cov`).  
  - **Path**: `requirements.txt`  

- [ ] **T011** [ P ] Create `src/main.py` – the pipeline orchestrator that (a) runs the memory‑check hooks, (b) calls each stage in order, and (c) writes a high‑level log to `logs/pipeline.log`.  

- [ ] **T012** [ P ] Integrate memory‑limit logic for the **data‑cleaning** stage (halt if RAM > 7 GB, log to `logs/memory.log`, exit with `E_MEMORY_LIMIT`).  

- [ ] **T013** [ P ] Integrate memory‑limit logic for the **disproportionality** stage (same behaviour as above).  

---

## Phase 2 – User Story 1: Data acquisition & preprocessing  

- [ ] **T014** [ P ] Implement `src/data/download.py` to fetch the VAERS 2020‑2023 CSV files from a verified CDC mirror, verify SHA‑256 checksums, and store them under `data/raw/`.  

- [ ] **T015** [ P ] Implement **filtering** part of `src/data/clean.py`:  
  - Load raw CSVs (chunked if > 5 GB).  
  - Create four groups: `COVID‑19`, `Full Non‑COVID (including Flu)`, `Flu‑only`, `Non‑COVID & Non‑Flu`.  
  - Drop records with missing `VAX_TYPE` or `REPT_DATE`.  
  - Write intermediate parquet files to `data/processed/` (e.g., `covid.parquet`, `non_covid.parquet`, `flu.parquet`).  
  - **Verification**: Unit test `tests/unit/test_clean_filter.py` checks row‑counts per group.

- [ ] **T016** [ P ] Extend `src/data/clean.py` (mapping & final output):  
  - Load `data/meddra_soc_mapping.csv`.  
  - Map MedDRA codes to SOC; abort with `E_MAPPINGS_INVALID` on missing/ malformed mapping.  
  - Merge the four groups into a single cleaned dataset and write:  
    1. `data/processed/cleaned_vaers_full_non_covid.parquet` (COVID + Full Non‑COVID) – **input for disproportionality**.  
    2. `data/processed/cleaned_vaers.parquet` (all groups).  
    3. Human‑readable CSV `data/processed/cleaned_vaers.csv`.  
  - Add logging of row counts and memory usage (writes to `logs/clean.log`).  
  - **Verification**: Integration test `tests/integration/test_pipeline.py` must succeed and produce the three files.

---

## Phase 3 – User Story 2: Disproportionality signal detection  

- [ ] **T017** [ P ] Unit test for `src/analysis/disproportionality.py` verifying ROR/PRR/IC logic with continuity correction (`0.5`).  

- [ ] **T018** [ P ] Unit test for Benjamini‑Hochberg correction monotonicity.  

- [ ] **T019** [ P ] Integration test confirming that the full signal‑detection pipeline creates `output/signals.csv`.  

- [ ] **T020** [ P ] Implement the full **disproportionality** pipeline (`src/analysis/disproportionality.py`):  
  - Read `data/processed/cleaned_vaers_full_non_covid.parquet`.  
  - For each SOC with ≥ 5 total reports, build a 2×2 contingency table (COVID vs. Full Non‑COVID).  
  - Apply continuity correction, compute ROR, PRR, IC with 95 % CIs, and raw p‑values (Fisher’s exact test).  
  - Apply Benjamini‑Hochberg correction (store `p_value_adj`).  
  - Apply the **2‑out‑of‑3** rule (FR‑005) and set `is_signal` and `signal_metrics`.  
  - Write `output/signals.csv` conforming to `contracts/signal.schema.yaml`; add column `background_rate_status` set to `"UNKNOWN"` for all rows.  
  - Log summary statistics to `logs/disproportionality.log`.  
  - **Verification**: Re‑run the integration test (T019) and manually inspect the first few rows of `output/signals.csv`.

---

## Phase 4 – User Story 3: Temporal profiling & sensitivity analysis  

- [ ] **T021** [ P ] Implement `src/analysis/sensitivity.py`:  
  - Load `output/signals.csv` and the cleaned dataset.  
  - For the top 5 signals (by smallest adjusted p‑value), recompute ROR/PRR/IC using the **Flu‑only** baseline instead of the Full Non‑COVID baseline.  
  - Calculate deltas (`ror_delta`, `prr_delta`, `ic_delta`) and write `output/sensitivity_analysis.csv`.  
  - Log to `logs/sensitivity.log`.  
  - **Verification**: Unit test `tests/unit/test_sensitivity.py` checks delta calculation on a tiny synthetic parquet file.

- [ ] **T022** [ P ] Implement `src/analysis/temporal.py`:  
  - Identify the top 5 candidate SOCs from `output/signals.csv` (fallback to all signals if fewer than 5).  
  - For each SOC, compute weekly report counts relative to the median `REPT_DATE` of the entire cohort (COVID + Non‑COVID).  
  - Generate line plots labelled **“Reporting Time”** (no mention of vaccination date) and store PNGs under `output/temporal_profiles/`.  
  - Add a placeholder warning file `output/temporal_profiles/empty_signal_warning.txt` if no signals exist.  
  - **Verification**: Integration test `tests/integration/test_temporal_profiles.py` asserts that at least one PNG is created when signals are present.

- [ ] **T023** [ P ] Unit test for weekly aggregation logic in `src/analysis/temporal.py`.  
  - **Path**: `tests/unit/test_temporal.py`  

- [ ] **T024** [ P ] Add disclaimer text to `output/report.md` stating that the temporal analysis is purely descriptive (“Reporting Time”) and does **not** imply causality.  

---

## Phase 5 – Validation, profiling & final reporting  

- [ ] **T025** [ P ] Add memory‑profiling hooks to `src/main.py` (using `psutil` or `tracemalloc`) that record peak RAM usage for the whole pipeline and write `output/memory_profile.json` (fields: `peak_gb`, `status`).  

- [ ] **T026** [ P ] Create validation script `src/validation/validate_outputs.py` that:  
  1. Checks BH monotonicity in `output/signals.csv` → log `BH_MONOTONICITY: PASSED/FAILED`.  
  2. Calculates proportion of SOCs with finite ROR/PRR/IC (SC‑001) → log `VALID_SOC_PROPORTION`.  
  3. Calculates proportion of signals satisfying the 2‑out‑of‑3 rule (SC‑005) → log `SIGNAL_RULE_COMPLIANCE`.  
  4. Writes all messages to `output/validation.log`.  

- [ ] **T027** [ P ] Generate the final human‑readable report `output/report.md` that:  
  - Summarizes memory usage, validation metrics, and key findings.  
  - Includes tables/figures from `output/signals.csv`, `output/sensitivity_analysis.csv`, and `output/temporal_profiles/`.  
  - Contains a **Limitations** section explicitly flagging `background_rate_status = "UNKNOWN"` and reiterating that only reporting disproportionality (not incidence) was assessed.  
  - Guarantees the strings “Post‑Vaccination Time”, “Causal”, or “Incidence Rate” do **not** appear.  

- [ ] **T028** [ P ] Final validation task that runs `src/validation/validate_outputs.py` and asserts that `output/report.md` exists, is non‑empty, and that all required output files (`signals.csv`, `sensitivity_analysis.csv`, at least one temporal PNG) are present.  
  - **Verification**: CI step `pytest -m validation` must exit with status 0.

---

## Phase 6 – Polish & cross‑cutting improvements  

- [ ] **T029** [ P ] Update `README.md` with a “Quickstart” section showing:  
  ```bash
  pip install -r requirements.txt
  python -m src.main
  ```  
  and brief explanations of each output artifact.

- [ ] **T030** [ P ] Perform code cleanup: remove dead imports, enforce type hints, and run `ruff --fix .`.  

- [ ] **T031** [ P ] Add additional edge‑case unit tests (zero‑count cells, sparse SOCs) under `tests/unit/` and ensure they pass (`pytest`).  

- [ ] **T032** [ P ] Validate the quick‑start documentation by executing the commands in a fresh CI run and confirming successful pipeline completion.

---

### Dependency & execution order  

| Phase | Must finish before |
|-------|--------------------|
| Phase 0 | – |
| Phase 1 | Phase 0 |
| Phase 2 | Phase 1 |
| Phase 3 | Phase 2 |
| Phase 4 | Phase 3 |
| Phase 5 | Phases 2‑4 |
| Phase 6 | Phase 5 (optional, for polishing) |

All `[P]` tasks can run in parallel **provided** their prerequisite files exist. Tasks without `[P]` are sequentially ordered as shown.  

---  

*All tasks are unchecked except those already verified (marked `[X]`).  Re‑opening of previously unchecked tasks ensures that the required artifacts will be produced and can be deterministically verified by the platform.*
