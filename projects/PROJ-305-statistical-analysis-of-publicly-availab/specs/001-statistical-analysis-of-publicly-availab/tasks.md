# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.

The goal is a reproducible, CPU‑only pipeline that (1) downloads real VAERS 2020–2023 data, (2) validates and cleans it, (3) computes disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) runs sensitivity and temporal analyses, (5) profiles memory, and (6) hands off a human‑readable report. This revision consolidates the prior 19-item list into 12 substantive tasks, repairs the four verifier rejections (T001 logs snapshot, T003 lint, T005 plots placeholder, T006 validator), and replaces the previously unresolved data-source claims with explicit, reachable fetch recipes that fail loudly rather than fall back to synthetic data.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] Establish the project layout, runnable commands, and the filesystem evidence artifact (repairs prior T001/T002 rejection: `logs/structure.txt` was absent).
  - Create `src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `data/results/`, `output/figures/`, `output/temporal_profiles/`, and **`logs/`**. The platform's `llmxive_toolkit.paths` creates folders on demand; use it rather than a bespoke setup script.
  - Copy the three contracts (`dataset.schema.yaml`, `signal.schema.yaml`, `soc_cluster.schema.yaml`) from the feature's `specs/` directory into the working tree only if code needs a local reference; the canonical contracts live in `specs/`.
  - **Actually produce** `logs/structure.txt` by running `tree -a -L 3` (or `find . -maxdepth 3` if `tree` is unavailable) from the project root; the file must be non-empty and contain one line per listed directory.
  - Document the runnable command (`python -m src.main`) and input provenance in the feature's `quickstart.md`.
  - **Verification**: `test -s logs/structure.txt` passes and the file lists `src/`, `data/`, `output/`, `logs/`, `tests/`.

- [ ] T002 [P] [US1] Download the real VAERS 2020–2023 data and the MedDRA→SOC mapping, with checksums and NO synthetic fallback (replaces prior T007, whose URLs were unresolved 404 claims).
  - Implement `src/data/download.py`. For each year Y in {2020, 2021, 2022, 2023}, stream-download the three real VAERS CSVs from the HHS data distribution point:
    - `https://vaers.hhs.gov/data/datasets/{Y}VAERSDATA.csv.zip` (report metadata: `VAERS_ID`, `REPT_DATE`, `AGE`, `SEX`, `OUTCOME`, `EVENT_DATE`, `VAX_DATE`)
    - `https://vaers.hhs.gov/data/datasets/{Y}VAERSVAX.csv.zip` (vaccine info: `VAERS_ID`, `VAX_TYPE`, `VAX_NAME`)
    - `https://vaers.hhs.gov/data/datasets/{Y}VAERSSYMPTOMS.csv.zip` (MedDRA-coded symptoms: `VAERS_ID`, `SYMPTOM1..5`, `SYMPTOMVERSION1..5`)
    using `requests` with `stream=True`, unzip in memory or to `data/raw/`, and write extracted CSVs to `data/raw/{Y}/`.
  - If any HTTP status is not 200 or a download otherwise fails, the script MUST `raise` and exit non-zero — **never** generate, mock, or fall back to synthetic data. If the execution feedback later injects a "VERIFIED REAL DATA SOURCE" block (e.g., a Hugging Face parquet mirror), adopt that exact package/recipe as the single source and delete the guessed URLs.
  - Fetch a real MedDRA Preferred-Term→SOC mapping. Primary candidate: the NLM's free MedDRA–SNOMED mapping / MedDRA hierarchy files (https://www.nlm.nih.gov/research/umls/mapped-projects/meddra_snomed_ct.html), or a published PT→SOC table reachable from the VAERS SYMPTOMVERSION files. If the mapping fetch fails, raise — do not fabricate a mapping table.
  - After each successful download, compute SHA-256 and append `data/checksums.txt` lines of the form `<file> <sha256> OK`.
  - **Verification**: `logs/download_checksums.txt` lists every year × file with "OK"; `data/raw/` contains 12 extracted CSVs with row counts > 0; a missing/unreachable source produces a non-zero exit and NO partial substitute files.

- [ ] T003 [P] [US1] Implement the schema validator CLI `src/data/validate.py` (repairs prior T006 rejection: script exited 2).
  - Load the contract from the feature's `specs/.../contracts/dataset.schema.yaml` (or its project-local copy) and validate that an input CSV/Parquet contains the required columns `VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE` with non-null values.
  - Accept `--input <path>`; exit 0 on success writing `logs/validate_pass.txt` containing "PASS"; on missing columns exit 1 with error code `E_SCHEMA_MISSING` and a message naming the missing column (e.g., "MISSING VAX_TYPE") in `logs/validate_fail.txt`.
  - Bundle the focused test `tests/unit/test_validate.py` covering: a known-good fixture passes; a fixture missing `VAX_TYPE` fails with the expected message. Create the malformed fixture `tests/fixtures/malformed_missing_vax_type.csv` as a 3-row real-shaped CSV.
  - **Verification**: `pytest tests/unit/test_validate.py` passes; both log files are produced with the required content.

- [ ] T004 [US1] Clean, filter, map MedDRA→SOC, and split the real VAERS data into analysis groups (FR-001; replaces prior T008).
  - Implement `src/data/clean.py`: load the raw CSVs per year (use `pandas.read_csv(..., chunksize=...)` if any file exceeds 500 MB so peak RAM stays well under 7 GB); merge DATA+VAX+SYMPTOMS on `VAERS_ID`; explode `SYMPTOM1..5` to long format; join PT→SOC via the mapping from T002; keep rows with non-null `VAX_TYPE`, parsable ISO `REPT_DATE`, and non-missing `SOC_NAME`.
  - Assign `VAX_GROUP`: "COVID-19" if `VAX_TYPE` contains "COVID" (case-insensitive); "Flu-only" if it contains "Influenza"; otherwise "Non-COVID-Non-Flu".
  - Write `data/processed/cleaned.parquet` plus group files `covid.parquet`, `non_covid.parquet`, `flu.parquet`. Log mapping coverage (must be ≥ 95% of observed PTs; unmapped codes are logged and excluded, per the data model) to `logs/clean_summary.txt` with per-group row counts.
  - Run `python -m src.data.validate --input data/processed/cleaned.parquet` as a blocking gate (T003).
  - **Verification** (`tests/unit/test_clean_filter.py`): all four Parquet files exist; `covid + non_covid` row partition is consistent with `cleaned`; no null `SOC_NAME`; `logs/clean_summary.txt` reports coverage ≥ 95%.

- [ ] T005 [P] [US1] Implement the utility modules `src/utils/config.py` and `src/utils/plots.py` with REAL, complete function bodies (repairs prior T005 rejection: file contained an "omitted for brevity" placeholder).
  - `config.py`: define `SEED = 42`, `MAX_MEMORY_GB = 7`, `BH_ALPHA = 0.05`, directory `Path` objects, and the metric thresholds (ROR > 2.0 with lower CI > 1.0; PRR > 1.5 with lower CI > 1.0; IC > 0 with lower CI > 0).
  - `plots.py`: implement (no placeholders, no omitted bodies) `save_line_plot(df, x, y, title, path)` and `save_forest_plot(df, metric, ci_low, ci_high, title, path)`, both writing non-empty PNGs via matplotlib with the Agg backend.
  - **Verification**: `python -c "import src.utils.config as cfg; assert cfg.SEED == 42; print('PASS')"` writes "PASS" to `logs/config_import.txt`; `pytest tests/unit/test_plots.py` runs against a small DataFrame built from real cleaned rows (or a 2-row slice of `data/processed/cleaned.parquet`) and produces non-empty `output/figures/line_example.png` and `output/figures/forest_example.png`.

- [ ] T006 [US2] Compute the disproportionality metrics end-to-end on the real cleaned data and produce the first result table (FR-002, FR-003, FR-005; replaces prior T010).
  - Implement `src/analysis/disproportionality.py`: for every SOC with ≥ 5 total reports across the COVID-19 and Non-COVID-Non-Flu groups, build the 2×2 contingency table; apply the +0.5 continuity correction to any zero cell; compute ROR, PRR, IC with 95% Wald CIs; obtain raw two-sided p-values via `scipy.stats.fisher_exact`; apply Benjamini‑Hochberg FDR correction (α = 0.05, e.g., `statsmodels.stats.multitest.multipletests`); flag `is_signal` when ≥ 2 of the 3 metric thresholds hold, recording which metrics passed in `signal_metrics`.
  - Write `data/results/signals.csv` conforming to `contracts/signal.schema.yaml`, with `background_rate_status = "UNKNOWN"` on every row (edge case: missing background rates), and `data/results/soc_cluster_stats.csv` conforming to `contracts/soc_cluster.schema.yaml`. Log counts of SOCs examined and signals found to `logs/disproportionality.txt`.
  - **Verification** (`tests/integration/test_disproportionality.py`, run AFTER the computation): both CSVs exist with the contract-required headers; metric columns are finite (non-NaN, non-Inf) for ≥ 95% of examined SOCs (SC-001); BH-adjusted p-values are monotonically non-decreasing when sorted by raw p-value (SC-002); every `is_signal = True` row lists ≥ 2 entries in `signal_metrics` (FR-005). Include a hand-checkable unit test on a fixed 2×2 table (e.g., a=10, b=90, c=20, d=980) asserting the closed-form ROR and PRR values.

**Checkpoint**: `python -m src.main --stage disproportionality` executes on the real downloaded data and its numerical outputs in `data/results/signals.csv` can be checked against the contingency tables. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T007 [US2] Perform the Flu-only sensitivity analysis (FR-007; replaces prior T011).
  - Implement `src/analysis/sensitivity.py`: select the top 5 signals from `data/results/signals.csv` by smallest BH-adjusted p-value; recompute ROR, PRR, IC using `data/processed/flu.parquet` as the baseline; compute `delta_ROR`, `delta_PRR`, `delta_IC` (Flu-baseline minus Non-COVID-Non-Flu-baseline values).
  - Write `data/results/sensitivity_analysis.csv` with columns `SOC_CODE, SOC_NAME, ROR_flu, PRR_flu, IC_flu, delta_ROR, delta_PRR, delta_IC, baseline` ("Flu-only"); log to `logs/sensitivity.txt`.
  - **Verification** (`tests/unit/test_sensitivity.py`, run after T006): the delta columns exist and are numeric; the file has exactly 5 rows (or fewer if fewer signals exist, with the shortfall logged).

- [ ] T008 [US3] Generate the descriptive weekly reporting profiles for the top-5 signals (FR-004, SC-003; replaces prior T012).
  - Implement `src/analysis/temporal.py`: compute the median `REPT_DATE` of the combined COVID + Non-COVID cohort; for each top-5 SOC, aggregate weekly counts relative to that median as `week_offset`; write per-SOC count CSVs to `output/temporal_profiles/<SOC_CODE>.csv` (fields per the data model) and call `src.utils.plots.save_line_plot` to produce one PNG per SOC titled "Weekly Reporting Time for {SOC_NAME}" with axis label "Weeks relative to cohort median reporting date".
  - All labels MUST say "Reporting Time", never "Post-Vaccination Time" (spec assumption; temporal limitation). If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt` instead of fabricating profiles.
  - **Verification** (`tests/integration/test_temporal_profiles.py`, run after T006): at least one non-empty PNG per selected SOC when signals exist; the warning file is absent in that case; PNG metadata/titles contain "Reporting Time".

- [ ] T009 [P] [US1] Create the pipeline orchestrator `src/main.py` with memory profiling and CPU-only enforcement (FR-006, SC-004; replaces prior T013).
  - Sequentially invoke download → validate → clean → disproportionality → sensitivity → temporal stages; record peak RSS via `psutil` throughout and write `data/results/memory_profile.json` as `{"peak_gb": <float>, "status": "OK"}` when ≤ 7 GB, else `"EXCEEDED"` with a non-zero exit.
  - Do not import or use any GPU/CUDA-dependent library; the run is pure pandas/scipy/matplotlib on CPU. If any stage raises (e.g., a data fetch failure), the orchestrator must propagate the failure, not substitute data.
  - **Verification**: `python -m src.main` completes with exit 0 on the real data, `data/results/memory_profile.json` reports `"status": "OK"`, and `logs/main_run.txt` is non-empty.

- [ ] T010 Add the independent validation suite enforcing all quantitative success criteria, and execute it against the real artifacts (replaces prior T014; runs after T006–T009).
  - Implement `src/validation/validate_outputs.py`; each check writes a PASS/FAIL line to `data/results/validation.log`:
    1. BH monotonicity (SC-002);
    2. ≥ 95% finite ROR/PRR/IC among examined SOCs (SC-001);
    3. temporal PNGs exist for the top-5 signals (SC-003);
    4. `memory_profile.json` status "OK" (SC-004);
    5. proportion of flagged signals satisfying the 2-out-of-3 rule reported (SC-005, FR-005);
    6. every `signals.csv` row has `background_rate_status == "UNKNOWN"`;
    7. `signals.csv` and `soc_cluster_stats.csv` validate against their contracts via `jsonschema` (row-wise);
    8. sparse SOCs (< 5 total reports) are excluded from the metrics table (edge case).
  - **Verification**: `python -m src.validation.validate_outputs` exits 0 and `grep -c FAIL data/results/validation.log` returns 0.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Generate the final tables and figures directly from the validated outputs (replaces prior T015 figure/report split).
  - Produce `output/figures/forest_top_signals.png` via `save_forest_plot` from the top-10 rows of `data/results/signals.csv`; reference the temporal PNGs from T008.
  - Write `output/report.md` containing: memory summary from `memory_profile.json`; the PASS lines from `validation.log`; a top-10 signal table rendered from `signals.csv`; the sensitivity Δ-table; embedded figure references; and a limitations section stating that temporal analysis is "Reporting Time" only, findings are associational (not causal), background incidence rates are unknown, and sparse SOCs were excluded.
  - The report must NOT contain the strings "Post-Vaccination Time", "Causal", or "Incidence Rate".
  - **Verification**: `grep -E "Post-Vaccination|Causal|Incidence Rate" output/report.md` returns no matches; every table row traces to a row in `data/results/signals.csv` or `sensitivity_analysis.csv`.

- [ ] T012 Re-run the documented workflow end-to-end from its declared inputs, confirm all checks, and document the paper-stage handoff (repairs prior T003 lint failure; replaces prior T016).
  - Ensure code style passes: run `ruff check .` and `black --check .` (or the platform's lint runner `code/run_lint.py`); fix any reported issues so the run exits 0, capturing output in `logs/lint.txt`.
  - Delete `data/processed/` and `data/results/`, then re-run `python -m src.main` from the raw `data/raw/` inputs and `python -m src.validation.validate_outputs`; confirm identical signal counts and metric values (fixed seed, deterministic pipeline) and that all prior verification commands (T001 structure check, T003 validator logs, T004 clean tests, T006–T010 checks) still pass.
  - Update the feature's `quickstart.md` with the exact commands (`pip install -r requirements.txt; python -m src.main; python -m src.validation.validate_outputs`) and a one-line description of each output artifact, and record the paper-stage handoff: the paper pipeline receives `output/report.md`, `data/results/signals.csv`, `data/results/sensitivity_analysis.csv`, and the figures under `output/figures/` and `output/temporal_profiles/`.
  - **Verification**: lint exits 0; the re-run reproduces the same signal set (log diff to `logs/rerun_diff.txt` showing no metric changes); `grep -q "Quickstart" quickstart.md` succeeds.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (download, filter, SOC mapping) | T002, T004 | `python -m src.main` (download+clean stages) |
| FR-002 (ROR/PRR/IC, ≥5 reports) | T006 | `pytest tests/integration/test_disproportionality.py` |
| FR-003 (BH correction) | T006, T010 | validation.log BH monotonicity check |
| FR-004 (weekly reporting profile) | T008 | temporal PNGs in `output/temporal_profiles/` |
| FR-005 (2-of-3 signal rule) | T006, T010 | `signal_metrics` column + validation check 5 |
| FR-006 (CPU-only) | T009 | `memory_profile.json` status OK; no GPU imports |
| FR-007 (Flu-only sensitivity) | T007 | `data/results/sensitivity_analysis.csv` |
| SC-001–SC-005 | T010 | `python -m src.validation.validate_outputs` |
| Schema contracts | T003, T004, T010 | validator logs + jsonschema checks |
| Report handoff | T011, T012 | `output/report.md`, `quickstart.md` |

Execution order: T001, T002, T003, T005 are independent; T004 after T002+T003; T006 after T004; T007, T008 after T006; T009 after T004; T010 after T006–T009; T011 after T010; T012 last.

## Revision behavior

Prior task identities preserved where possible (T007→T002, T008→T004, T010→T006, T011→T007, T012→T008, T013→T009, T014→T010, T015/T016→T011/T012). The four verifier rejections are folded into T001 (missing `logs/structure.txt`), T012 (lint exit 1), T005 (placeholder plots module), and T003 (validator exit 2). The fabricated/unreachable URLs from prior T007 are replaced with explicit real HHS VAERS zip URLs and a fail-loudly contract; no synthetic fallback exists anywhere in the pipeline. All tasks remain unchecked pending independent verification.
