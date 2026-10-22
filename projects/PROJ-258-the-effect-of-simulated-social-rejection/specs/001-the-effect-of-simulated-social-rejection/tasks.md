# Tasks: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Inputs**: `spec.md`, `plan.md`, active contracts in `specs/001-the-effect-of-simulated-social-rejection/contracts/`, existing project skeleton (`code/`, `data/`, `results/`, `paper/`, `tests/`).

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Build a runnable pipeline that can be executed on a small real input and produce a complete set of result artifacts.

- [ ] T001 **Create project layout and dependency file**  
  *Create the directories `code/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/` (each with an empty `__init__.py`). Write `code/requirements.txt` with the exact pinned versions listed in the plan and add the runnable command to `quickstart.md`.*  
  *Verification*: `quickstart.md` exists and contains the full pipeline command; `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.

- [ ] T002 [US-1] **Ingest the Cyberball dataset (ds000208)**   <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
  *Download the verified OpenNeuro parquet file for ds000208 from the HuggingFace mirror to `data/raw/ds000208.parquet` using streaming HTTP. Compute a SHA‑256 checksum and write `data/raw/metadata.json`. Create a human‑readable citation file `data/raw/CITATION.md`. Abort with exit 1 if (a) required columns are missing, (b) file size > 7 GB, or (c) the `condition` column does not contain both “rejection” and “control”.*  
  *Verification*: Running `python code/ingest.py --url <verified‑url> --out-dir data/raw --dataset-id ds000208` exits 0, the parquet file and both metadata files exist, and a log entry confirms column validation passed.

- [ ] T003 [US-1] **Validate raw dataset against schemas**  
  *Run `code/validate.py` on `data/raw/ds000208.parquet` using `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml`. The validator must check for the required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`), enforce numeric constraints, and confirm that both “rejection” and “control” appear in `condition`. Write a JSON validation report to `data/interim/ingest_validation_report.json`. Abort with exit 1 on any failure.*  
  *Verification*: `python code/validate.py --raw data/raw/ds000208.parquet --schema contracts/dataset.schema.yaml --output data/interim/ingest_validation_report.json` exits 0 and the JSON report contains `"status": "pass"`.

- [ ] T003b [US-1] **Detect participant ID overlap**  
  *Inspect `data/raw/ds000208.parquet` to determine whether the same `participant_id` appears in both `rejection` and `control` conditions. Write `data/interim/id_match_report.json` with a boolean field `ids_match`. This report drives design selection.*  
  *Verification*: JSON file exists with `"ids_match": true` or `false`.

- [ ] T004 [US-1] **Record reward‑feedback dataset unavailability**  
  *Because no open‑access reward dataset exists, the script must create `data/interim/reward_unavailable.json` with the exact content:*  
  ```json
  {
    "reward_dataset_available": false,
    "reason": "No open-access reward dataset with verified URL."
  }
  ```  
  *The script exits 0 after writing the file.*  
  *Verification*: `data/interim/reward_unavailable.json` exists and matches the JSON above; no `data/raw/ds003392.parquet` is created.

- [ ] T005 [US-1] **Determine statistical design and record it**  
  *Using the `ids_match` flag from `data/interim/id_match_report.json` (and noting reward‑dataset unavailability), write `data/interim/design_branch.json`.*  
  *If `ids_match` is true, set `"design_type": "Between-Subjects"` and include a note that IDs matched but a Between‑Subjects analysis is still required. If false, also set `"design_type": "Between-Subjects"` with a reason indicating mismatch.*  
  *Verification*: The file exists and `design_type` is `"Between-Subjects"`; a `reason` field explains the situation.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T006 [US-2] **Preprocess raw dataset (outlier flagging & Z‑score normalization)**  
  *Memory‑map `data/raw/ds000208.parquet`, apply the IQR rule (1.5 × IQR) **per condition** to set a boolean `is_outlier`. Compute Z‑score normalized reaction times within each condition (`rt_normalized`). Write the cleaned table to `data/interim/preprocessed_ds000208.csv` and append per‑condition thresholds and flagged counts to `data/interim/outlier_log.json` (one object per condition). Ensure peak RAM ≤ 7 GB.*  
  *Verification*: The CSV contains the new columns `is_outlier` and `rt_normalized`; `outlier_log.json` lists both conditions with numeric `iqr_lower`, `iqr_upper`, and `flagged_count`; a runtime log shows memory ≤ 7 GB.

- [ ] T007 [US-2] **Aggregate preprocessed data to participant‑level features**  
  *Group `data/interim/preprocessed_ds000208.csv` by `participant_id` × `condition` and compute:*  
  - `rt_mean` = mean of `rt_normalized` per participant‑condition  
  - `mood_mean` = mean of `mood_rating` per participant‑condition  
  Propagate optional `age`/`gender`. Write the result to `data/processed/analysis_ready_ds000208.csv`.  
  *Verification*: The CSV has exactly one row per participant‑condition pair and includes the columns `participant_id`, `condition`, `rt_mean`, `mood_mean`, `age`, `gender`, and an aggregated `is_outlier` flag (true if any row for that participant‑condition was flagged).

- [ ] T008 [US-3] **Between‑Subjects statistical analysis and assumption handling**  
  *Load `data/processed/analysis_ready_ds000208.csv` and the design metadata (`design_branch.json`). Because the specification mandates a Between‑Subjects analysis, run a One‑Way ANOVA for each outcome (RT and mood) using `statsmodels`. Perform Shapiro‑Wilk normality and Levene homogeneity checks; if assumptions fail, automatically (i) log‑transform RT, (ii) switch to Welch’s ANOVA, or (iii) fall back to Kruskal‑Wallis, logging the chosen path and noting the `ids_match` status from the design file. Record for each outcome:*  
  - `test_type` (`One_Way_ANOVA`, `Welch_ANOVA`, or `Kruskal_Wallis`)  
  - `f_value` (or equivalent statistic)  
  - `p_raw`  
  - `effect_size` (eta‑squared)  
  - `assumption_notes` (if any)  
  *Write the intermediate results to `results/analysis_raw.json`.*  
  *Verification*: `results/analysis_raw.json` contains required keys for both outcomes and includes `assumption_notes` when fallbacks occur.

- [ ] T009 [US-3] **Benjamini‑Hochberg FDR correction & α‑sensitivity sweep**  
  *Apply BH FDR correction to the raw p‑values from T008. For each outcome, create boolean flags for significance at α = 0.01, 0.05, 0.1. Write the final structured output to `results/analysis_output.json` that validates against `contracts/analysis_output.schema.yaml` (including the required `p_fdr ≥ p_raw` inequality).*  
  *Verification*: JSON schema validation passes; each `alpha_sensitivity` entry (`"0.01"`, `"0.05"`, `"0.1"`) is present and boolean; every `p_fdr` ≥ corresponding `p_raw`.

- [ ] T009b [US-3] **Validate analysis_output.json against schema**  
  *Run JSON‑schema validation of `results/analysis_output.json` using `contracts/analysis_output.schema.yaml`. Abort with exit 1 if validation fails.*  
  *Verification*: Validation script exits 0.

- [ ] T010 [US-3] **Outlier‑sensitivity re‑analysis**  
  *Re‑run the analysis of T008 twice:*  
  1. **With outliers retained** (use the original preprocessed file).  
  2. **With outliers removed** (filter rows where `is_outlier` = true before aggregation).  
  *Summarise differences in F‑values, p‑values, and effect sizes in `results/outlier_sensitivity.json`. Include a boolean `conclusion_changed` indicating whether statistical significance (after FDR correction) differs between the two runs.*  
  *Verification*: The JSON contains `with_outliers` and `without_outliers` sub‑objects and a `conclusion_changed` flag.

- [ ] T011 [US-3] **Power analysis & α‑sensitivity reporting**  
  *Using `statsmodels.stats.power.FTestAnovaPower`, compute the required total N for a medium effect size (Cohen d ≈ 0.5) at α = 0.05, power = 0.80; write the integer to `results/power_analysis.txt`. Then calculate achieved power for each α in {0.01, 0.05, 0.1} based on the observed effect size and write an array of objects (`alpha`, `power_at_alpha`) to `results/power_by_alpha.json`.*  
  *Verification*: The text file contains a single integer; the JSON array has three entries with values between 0 and 1.

- [ ] T011a [US-3] **Generate phrasing‑check flags**  
  *Scan the upcoming `paper/report.md` template (or placeholder) to confirm that the Limitations section contains the word “associational” and that the Results section contains no occurrence of “causal”. Write `data/interim/phrasing_flags.json` with:*  
  ```json
  {
    "contains_associational": true,
    "no_causal_in_results": true
  }
  ```  
  *Verification*: JSON file exists with both booleans true.

- [ ] T012 [US-3] **Assemble full results package**  
  *Combine `results/analysis_output.json`, `data/interim/design_branch.json`, `results/outlier_sensitivity.json`, `results/power_by_alpha.json`, and the phrasing‑check flags from `data/interim/phrasing_flags.json` into `results/analysis_results.json` that conforms to `contracts/analysis_results.schema.yaml`. The `limitations` object must contain:*  
  ```json
  {
    "contains_associational": true,
    "modulation_claim_valid": false
  }
  ```  
  *Verification*: Schema validation succeeds; the two booleans are present and set as required.

- [ ] T013 [US-3] **Render final markdown report**  
  *Generate `paper/report.md` from `results/analysis_results.json`. The report must:*  
  1. State the design type (“Between‑Subjects”).  
  2. Include ANOVA (or fallback) tables with raw and FDR‑corrected p‑values, and 95 % confidence intervals for effect sizes.  
  3. Show an α‑sensitivity table with the power numbers from T011.  
  4. Contain the exact word **“associational”** in the Limitations section.  
  5. Contain **no** occurrence of the word **“causal”** in the Results section.  
  6. State: “Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed.”  
  *Abort with non‑zero exit if any phrasing constraint fails.*  
  *Verification*: A post‑generation script scans the markdown; it returns exit 0 only when all six conditions are satisfied.

- [ ] T014 [US-3] **Runtime accounting and resource guard**  
  *After the full pipeline finishes, query the GitHub Actions run (or use CI‑provided environment variables) to sum `duration_ms` of all steps. Write `results/runtime_report.json` with fields:*  
  - `total_seconds` (float)  
  - `peak_ram_gb` (float)  
  - `runtime_ok` (true iff `total_seconds ≤ 21600` and `peak_ram_gb ≤ 7`).  
  *The CI step fails if `runtime_ok` is false.*  
  *Verification*: The JSON reports `runtime_ok: true`; CI aborts otherwise.

- [ ] T015 [US-3] **Comprehensive testing suite**  
  *Add unit and integration tests under `tests/` covering:*  
  1. Column‑presence validation (T003).  
  2. IQR outlier flagging and Z‑score normalization (T006).  
  3. Correctness of BH correction monotonicity (`p_fdr ≥ p_raw`).  
  4. Presence of required phrasing in the final report (T013).  
  5. α‑sensitivity coverage (T009).  
  6. End‑to‑end pipeline execution producing all expected artifacts.  
  *Run with `pytest -q`; CI must exit 0.*  
  *Verification*: `pytest -q` returns exit 0 and coverage > 90 % for pipeline modules.

## Phase 3 – Reproducible results and paper handoff  

- [ ] T016 [US-3] **Document methods & results handoff**  
  *Write `paper/methods_results.md` that concisely describes the methods and links every reported number (F‑values, p‑values, effect sizes, power estimates) to the exact fields in `results/analysis_results.json`. Include a Limitations paragraph containing the required “associational” phrasing and confirming that no causal language is used.*  
  *Verification*: Manual review confirms traceability of all numbers and required phrasing.

- [ ] T017 [US-3] **Re‑run full workflow from scratch for reproducibility**  
  *Delete `data/`, `results/`, and `paper/` directories, then execute the pipeline exactly as described in `quickstart.md`. Verify that all artifacts (`data/raw/ds000208.parquet`, `results/analysis_results.json`, `paper/report.md`, etc.) are regenerated and pass their respective verification steps (T003–T015).*  
  *Verification*: After the clean run, every verification script from the previous tasks succeeds, demonstrating full reproducibility.