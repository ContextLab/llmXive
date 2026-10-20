# Tasks: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Inputs**: `spec.md`, `plan.md`, active contracts in `specs/001-the-effect-of-simulated-social-rejection/contracts/`, existing project skeleton (`code/`, `data/`, `results/`, `paper/`, `tests/`).

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Build a runnable pipeline that can be executed on a small real input and produce a complete set of result artifacts.

- [X] T001 [US‑1] **Create project layout and dependency file**  
  *Create the directories `code/`, `code/utils/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/` with placeholder `__init__.py` files; write `requirements.txt` (pandas ≥ 2.0, numpy, scipy, statsmodels, pyarrow, pyyaml, requests); generate `quickstart.md` documenting the single‑command pipeline `python -m code.pipeline`.  
  **Verification**: `quickstart.md` exists, lists the command, and `python -c "import pandas"` runs without error; directory tree matches the plan.

- [ ] T002 [US‑1] **Ingest Cyberball dataset (ds000208)**   <!-- FAILED-IN-EXECUTION: code/ingest.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
  *Download the verified OpenNeuro parquet file `ds000208.parquet` to `data/raw/ds000208.parquet` via streaming HTTP; abort with exit 1 if file size > 7 GB or download fails. Compute SHA‑256 checksum and write `data/raw/metadata_ds000208.json`; create a human‑readable citation file `data/raw/CITATION.md`. Add a `task` column with value `"cyberball"` to each record.*  
  **Verification**: `code/ingest.py --dataset ds000208` exits 0; parquet file present; checksum matches the recorded value; `CITATION.md` contains a valid OpenNeuro citation; `task` column exists.

- [ ] T003 [US‑1] **Ingest reward‑feedback dataset (ds003392) – optional fallback**  
  *Attempt to download `ds003392.parquet` to `data/raw/ds003392.parquet` using the same logic as T002. If the dataset is not publicly available, record the absence in `data/interim/reward_unavailable.json` and continue with a Between‑Subjects design.*  
  **Verification**: Successful download yields `metadata_ds003392.json` and `CITATION.md`; if unavailable, `reward_unavailable.json` exists with `"available": false`.

- [ ] T004 [US‑1] **Validate raw datasets against schemas**   <!-- FAILED-IN-EXECUTION: code/validate.py exit=1 -->
  *Run `code/validate.py` on each parquet file, checking required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`), value ranges, and that both `rejection` and `control` conditions appear. Write validation reports `data/interim/ingest_validation_ds000208.json` and, when present, `data/interim/ingest_validation_ds003392.json`. Abort with exit 1 on any failure.*  
  **Verification**: Validation scripts return exit 0; JSON reports contain `"status": "pass"`; missing columns or size violations cause a non‑zero exit.

- [ ] T005 [US‑1] **Determine statistical design and record overlap**  
  *Compare `participant_id` sets across the two datasets (if both are present). Produce `data/interim/overlap_report.json` with counts of matching IDs and a boolean `ids_match`. Based on the result, write `data/interim/design_branch.json` containing `"design_type": "Between-Subjects"` and a `"reason"` field explaining the decision. Also write `data/processed/metadata.json` summarising the chosen design.*  
  **Verification**: `design_branch.json` exists, `design_type` equals `"Between-Subjects"`, and `reason` is a non‑empty string; `overlap_report.json` lists numeric counts.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T006 [US‑2] **Preprocess each raw dataset (outlier flagging & normalization)**  
  *For every raw parquet (`ds000208`, `ds003392` if present): stream‑load with memory‑mapping, apply the IQR rule (1.5 × IQR) **per condition** to set `is_outlier`; compute per‑condition Z‑score of `reaction_time` → `rt_normalized`. Write the cleaned file to `data/interim/preprocessed_<dataset_id>.csv` and append the per‑condition thresholds and flagged counts to `data/interim/outlier_log.json` (list of objects `{ "condition": "...", "iqr_lower": ..., "iqr_upper": ..., "flagged_count": ... }`).*  
  **Verification**: Each `preprocessed_*.csv` contains the new columns; `outlier_log.json` is a non‑empty list with one entry per condition; memory usage stays ≤ 7 GB (checked via logger).

- [ ] T007 [US‑2] **Aggregate preprocessed data to participant‑level features**  
  *Read all `preprocessed_*.csv` files, concatenate them, and group by `participant_id` × `condition`. Compute `rt_mean` (mean of `rt_normalized`) and `mood_mean` (mean of `mood_rating`), propagate optional `age`/`gender`. Write the result to `data/processed/analysis_ready_combined.csv`.*  
  **Verification**: The CSV has exactly one row per participant‑condition pair; columns include `participant_id`, `condition`, `rt_mean`, `mood_mean`, `age`, `gender`, `is_outlier` (aggregated flag).

- [ ] T008 [US‑3] **Statistical analysis & assumption handling**  
  *Load `analysis_ready_combined.csv` and the design metadata. For each outcome (RT, mood) run a One‑Way ANOVA (`statsmodels.stats.anova.anova_lm`) under the Between‑Subjects design. Perform Shapiro‑Wilk normality and Levene homogeneity checks; if assumptions fail, automatically (i) log‑transform RT, (ii) switch to Welch’s ANOVA, or (iii) fall back to Kruskal‑Wallis, logging the chosen path. Record F‑statistic, raw p‑value, effect size (eta‑squared), and any convergence warnings in `results/analysis_raw.json`.*  
  **Verification**: `analysis_raw.json` conforms to a loose internal schema, contains keys `test_type`, `f_value`, `p_raw`, `effect_size`, and an `"assumption_notes"` field.

- [ ] T009 [US‑3] **Multiple‑testing correction & α‑sensitivity sweep**  
  *Apply Benjamini‑Hochberg FDR correction to all raw p‑values from T008. For each outcome, create the boolean flags for significance at α = 0.01, 0.05, 0.1. Write the final structured output to `results/analysis_output.json` that **must** validate against `contracts/analysis_output.schema.yaml` (including `p_fdr ≥ p_raw`).*  
  **Verification**: JSON schema validation passes; each `alpha_sensitivity` entry is present and boolean; `p_fdr` values are ≥ corresponding `p_raw`.

- [ ] T010 [US‑3] **Outlier‑sensitivity re‑analysis**  
  *Re‑run the analysis of T008 twice: once with outliers retained and once with outliers removed (using the flags from `outlier_log.json`). Summarise the before/after differences in F‑values, p‑values, and effect sizes in `results/outlier_sensitivity.json`. Include a flag `conclusion_changed` indicating whether statistical significance altered.*  
  **Verification**: JSON contains `with_outliers` and `without_outliers` sub‑objects and `conclusion_changed` boolean.

- [ ] T011 [US‑3] **A‑priori power analysis & reporting**  
  *Using `statsmodels.stats.power.FTestAnovaPower`, compute required total N for a medium effect size (Cohen d = 0.5) at α = 0.05, power = 0.80; write the number to `results/power_analysis.txt`. Then calculate achieved power for each α in the sensitivity set and store in `results/power_by_alpha.json` (array of `{ "alpha": ..., "power_at_alpha": ... }`).*  
  **Verification**: Text file contains a numeric N; JSON array has three entries with values between 0 and 1.

- [ ] T012 [US‑3] **Assemble full results package**  
  *Combine `analysis_output.json`, `design_branch.json`, `outlier_sensitivity.json`, `power_by_alpha.json`, and the phrasing‑check flags into `results/analysis_results.json` that conforms to `contracts/analysis_results.schema.yaml`. The `limitations` object must have `contains_associational: true` and `modulation_claim_valid: false` (because only Between‑Subjects).*  
  **Verification**: Schema validation succeeds; required boolean flags are present and correctly set.

- [ ] T013 [US‑3] **Render final markdown report**  
  *Generate `paper/report.md` from `analysis_results.json`. The report must (a) display the design type “Between‑Subjects”, (b) include ANOVA (or fallback) tables with raw and FDR‑corrected p‑values, (c) show the α‑sensitivity table with power numbers, (d) contain the exact word **“associational”** in the Limitations section, (e) contain **no** occurrence of the word “causal” in the Results section, and (f) state “Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed.” Abort with non‑zero exit if any phrasing constraint fails.*  
  **Verification**: A post‑generation script scans the markdown; it returns exit 0 only when all phrasing checks pass.

- [ ] T014 [US‑3] **Runtime accounting and resource guard**  
  *After the full pipeline finishes, query the GitHub Actions run API (or use the CI‑provided environment variables) to sum `duration_ms` of all steps, write `results/runtime_report.json` with fields `total_seconds`, `peak_ram_gb`, and `runtime_ok` (true iff `total_seconds ≤ 21600` and `peak_ram_gb ≤ 7`).*  
  **Verification**: JSON reports `runtime_ok: true`; CI step fails if the condition is violated.

- [ ] T015 [US‑3] **Comprehensive testing suite**  
  *Add unit and integration tests under `tests/` covering: (i) column‑presence validation, (ii) IQR outlier flagging, (iii) Z‑score normalization, (iv) BH correction monotonicity (`p_fdr ≥ p_raw`), (v) α‑sensitivity coverage, (vi) phrasing constraints on the rendered report, (vii) end‑to‑end pipeline execution producing all expected artifacts. Run with `pytest`; the CI must exit 0.*  
  **Verification**: `pytest -q` returns exit 0; coverage report shows > 90 % of pipeline modules exercised.

---  

### Dependency mapping (summary)

| FR / SC | Satisfied by |
|---------|--------------|
| FR‑000, FR‑001 | T002, T003, T004 |
| FR‑002 | T006 |
| FR‑003, FR‑009 | T013 |
| FR‑004 | T009 |
| FR‑005 | T001, T014 |
| FR‑006 | T009 |
| FR‑007, FR‑008 | T005 |
| SC‑001 | T004, T013 |
| SC‑002 | T014 |
| SC‑003 | T009 |
| SC‑004 | T009 |

All tasks are ordered to respect data flow: ingestion → validation → design determination → preprocessing → aggregation → analysis → corrections → sensitivity → reporting → runtime check → testing.
