# Tasks: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Inputs**: `spec.md`, `plan.md`, active contracts in `specs/001-the-effect-of-simulated-social-rejection/contracts/`, existing project skeleton (`code/`, `data/`, `results/`, `paper/`, `tests/`).

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Build a runnable pipeline that can be executed on a small real input and produce a complete set of result artifacts.

- [ ] T001 [P] **Create project layout and dependency file**  
  *Create the directories `code/`, `code/utils/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/` with placeholder `__init__.py` files; write `code/requirements.txt` with the exact pinned versions (pandas 2.2.2, numpy 1.26.4, scipy 1.13.0, statsmodels 0.14.2, pyarrow, pyyaml, requests); add the command to run the full pipeline in `quickstart.md`.*  
  **Verification**: `quickstart.md` exists, lists the command, and `python -c "import pandas"` runs without error; directory tree matches the plan.

- [ ] T002 [US‑1] **Ingest Cyberball dataset (ds000208)**  
  *Download the verified OpenNeuro parquet file `ds000208.parquet` from the HuggingFace mirror to `data/raw/ds000208.parquet` using streaming HTTP; abort with exit 1 if the file size > 7 GB or the download fails. Compute SHA‑256 checksum and write `data/raw/metadata.json`; create a human‑readable citation file `data/raw/CITATION.md`. Add a `task` column with value `"cyberball"` to each record.*  
  **Verification**: Running `python code/ingest.py --url <verified‑url> --out-dir data/raw --dataset-id ds000208` exits 0; `data/raw/ds000208.parquet` is present; `metadata.json` contains the correct checksum; `CITATION.md` contains a valid OpenNeuro citation; the parquet includes a `task` column equal to `"cyberball"`.

- [ ] T003 [US‑1] **Record reward‑feedback dataset unavailability**  
  *Attempt to download a reward‑feedback dataset (e.g., `ds003392.parquet`). Because no open‑access reward dataset exists, the script must create `data/interim/reward_unavailable.json` with the content `{ "reward_dataset_available": false, "reason": "No open‑access reward dataset with verified URL." }` and exit 0.*  
  **Verification**: Running `python code/ingest_reward.py` (or the same ingest script with `--reward`) creates `data/interim/reward_unavailable.json` exactly as specified; no `data/raw/ds003392.parquet` is created.

- [ ] T004 [US‑1] **Validate raw dataset against schemas**  
  *Run `code/validate.py` on `data/raw/ds000208.parquet` using `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml`. The validator must check for the required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`), enforce the numeric constraints, and confirm that both “rejection” and “control” appear in the `condition` column. Output a JSON validation report to `data/interim/ingest_validation_report.json`. Abort with exit 1 on any failure.*  
  **Verification**: `python code/validate.py --raw data/raw/ds000208.parquet --schema contracts/dataset.schema.yaml --output data/interim/ingest_validation_report.json` exits 0 and the JSON report contains `"status": "pass"`; if a required column is missing the script exits 1.

- [ ] T005 [US‑1] **Determine statistical design and record overlap**  
  *Because the reward dataset is unavailable, the pipeline automatically selects a Between‑Subjects design. Write `data/interim/design_branch.json` with `{ "design_type": "Between-Subjects", "reason": "Reward dataset unavailable; analysis limited to Between‑Subjects comparison of rejection vs. control." }`. Also write a brief `data/interim/overlap_report.json` indicating that no participant‑ID matching across studies is possible (counts set to zero).*
  **Verification**: `design_branch.json` exists and contains `"design_type": "Between-Subjects"`; `overlap_report.json` lists numeric counts and `"ids_match": false`.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T006 [US‑2] **Preprocess raw dataset (outlier flagging & normalization)**  
  *Stream‑load `data/raw/ds000208.parquet` with memory‑mapping, apply the IQR rule (1.5 × IQR) **per condition** to set `is_outlier`; compute per‑condition Z‑score of `reaction_time` → `rt_normalized`. Write the cleaned file to `data/interim/preprocessed_ds000208.csv` and append per‑condition thresholds and flagged counts to `data/interim/outlier_log.json` (list of objects `{ "condition": "...", "iqr_lower": ..., "iqr_upper": ..., "flagged_count": ... }`).*  
  **Verification**: The CSV contains the new columns `is_outlier` and `rt_normalized`; `outlier_log.json` is non‑empty with one entry per condition; peak RAM during execution ≤ 7 GB (logged).

- [ ] T007 [US‑2] **Aggregate preprocessed data to participant‑level features**  
  *Read `data/interim/preprocessed_ds000208.csv`, group by `participant_id` × `condition`, and compute `rt_mean` (mean of `rt_normalized`) and `mood_mean` (mean of `mood_rating`). Propagate optional `age`/`gender`. Write the result to `data/processed/analysis_ready_ds000208.csv`.*  
  **Verification**: The CSV has exactly one row per participant‑condition pair and includes columns `participant_id`, `condition`, `rt_mean`, `mood_mean`, `age`, `gender`, `is_outlier` (aggregated flag).

- [ ] T008 [US‑3] **Statistical analysis & assumption handling**  
  *Load `data/processed/analysis_ready_ds000208.csv` and the design metadata. Because the design is Between‑Subjects, run a One‑Way ANOVA for each outcome (RT and mood) using `statsmodels.stats.anova.anova_lm`. Perform Shapiro‑Wilk normality and Levene homogeneity checks; if assumptions fail, automatically (i) log‑transform RT, (ii) switch to Welch’s ANOVA, or (iii) fall back to Kruskal‑Wallis, logging the chosen path. Record F‑statistic, raw p‑value, effect size (eta‑squared), and any convergence warnings in `results/analysis_raw.json`.*  
  **Verification**: `analysis_raw.json` contains keys `test_type`, `f_value`, `p_raw`, `effect_size`, and an `assumption_notes` field describing any fallback.

- [ ] T009 [US‑3] **Benjamini‑Hochberg FDR correction & α‑sensitivity sweep**  
  *Apply BH FDR correction to the raw p‑values from T008. For each outcome, create boolean flags for significance at α = 0.01, 0.05, 0.1. Write the final structured output to `results/analysis_output.json` that validates against `contracts/analysis_output.schema.yaml` (including the required `p_fdr ≥ p_raw` inequality).*  
  **Verification**: JSON schema validation passes; each `alpha_sensitivity` entry is present and boolean; every `p_fdr` value is ≥ the corresponding `p_raw`.

- [ ] T010 [US‑3] **Outlier‑sensitivity re‑analysis**  
  *Re‑run the analysis of T008 twice: once with outliers retained and once with outliers removed (using the flags from `outlier_log.json`). Summarise the before/after differences in F‑values, p‑values, and effect sizes in `results/outlier_sensitivity.json`. Include a flag `conclusion_changed` indicating whether statistical significance altered between the two runs.*  
  **Verification**: `outlier_sensitivity.json` contains `with_outliers` and `without_outliers` sub‑objects and a boolean `conclusion_changed`.

- [ ] T011 [US‑3] **Power analysis & sensitivity reporting**  
  *Using `statsmodels.stats.power.FTestAnovaPower`, compute the required total N for a medium effect size (Cohen d = 0.5) at α = 0.05, power = 0.80; write the number to `results/power_analysis.txt`. Then calculate achieved power for each α in the set {0.01, 0.05, 0.1} and store in `results/power_by_alpha.json` (array of `{ "alpha": ..., "power_at_alpha": ... }`).*  
  **Verification**: Text file contains a single integer; JSON array has three entries with values between 0 and 1.

- [ ] T012 [US‑3] **Assemble full results package**  
  *Combine `results/analysis_output.json`, `data/interim/design_branch.json`, `results/outlier_sensitivity.json`, `results/power_by_alpha.json`, and phrasing‑check flags into `results/analysis_results.json` that conforms to `contracts/analysis_results.schema.yaml`. The `limitations` object must have `contains_associational: true` and `modulation_claim_valid: false` (because the design is Between‑Subjects and no modulation can be directly tested).*  
  **Verification**: Schema validation succeeds; required booleans are present and correctly set.

- [ ] T013 [US‑3] **Render final markdown report**  
  *Generate `paper/report.md` from `results/analysis_results.json`. The report must (a) display the design type “Between‑Subjects”, (b) include ANOVA (or fallback) tables with raw and FDR‑corrected p‑values, (c) show the α‑sensitivity table with power numbers, (d) contain the exact word **“associational”** in the Limitations section, (e) contain **no** occurrence of the word “causal” in the Results section, and (f) state “Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed.” Abort with non‑zero exit if any phrasing constraint fails.*  
  **Verification**: A post‑generation script scans the markdown; it returns exit 0 only when all phrasing checks pass.

- [ ] T014 [US‑3] **Runtime accounting and resource guard**  
  *After the full pipeline finishes, query the GitHub Actions run API (or use CI‑provided environment variables) to sum `duration_ms` of all steps, write `results/runtime_report.json` with fields `total_seconds`, `peak_ram_gb`, and `runtime_ok` (true iff `total_seconds ≤ 21600` and `peak_ram_gb ≤ 7`). The CI step fails if the condition is violated.*  
  **Verification**: `runtime_report.json` reports `runtime_ok: true`; CI aborts otherwise.

- [ ] T015 [US‑3] **Comprehensive testing suite**  
  *Add unit and integration tests under `tests/` covering: (i) column‑presence validation, (ii) IQR outlier flagging, (iii) Z‑score normalization, (iv) BH correction monotonicity (`p_fdr ≥ p_raw`), (v) α‑sensitivity coverage, (vi) phrasing constraints on the rendered report, (vii) end‑to‑end pipeline execution producing all expected artifacts. Run with `pytest -q`; the CI must exit 0.*  
  **Verification**: `pytest -q` returns exit 0; coverage report shows > 90 % of pipeline modules exercised.

## Phase 3 – Reproducible results and paper handoff  

- [ ] T016 [US‑3] **Document methods & results handoff**  
  *Write a concise methods and results summary in `paper/methods_results.md` that explicitly links every reported number (e.g., F‑values, p‑values, effect sizes, power estimates) to the exact cells in `results/analysis_results.json`. Include a “Limitations” paragraph that contains the required “associational” phrasing and confirms that no causal language is used.*  
  **Verification**: Manual review confirms all numbers are traceable to JSON fields; required phrasing is present.

- [ ] T017 [US‑3] **Re‑run full workflow from scratch for reproducibility**  
  *Delete the `data/`, `results/`, and `paper/` directories, then execute the pipeline exactly as described in `quickstart.md`. Verify that all artifacts (`data/raw/ds000208.parquet`, `results/analysis_results.json`, `paper/report.md`, etc.) are regenerated and pass their respective verification steps.*  
  **Verification**: After re‑run, the same verification scripts from T004–T015 all succeed, demonstrating full reproducibility.

---  

### Dependency mapping (summary)

| FR / SC | Satisfied by |
|---------|--------------|
| FR‑000, FR‑001 | T002, T003, T004 |
| FR‑002 | T006 |
| FR‑003, FR‑009 | T013, T016 |
| FR‑004 | T009 |
| FR‑005 | T001, T014 |
| FR‑006 | T009 |
| FR‑007, FR‑008 | T005 |
| SC‑001 | T004, T013 |
| SC‑002 | T014 |
| SC‑003 | T009 |
| SC‑004 | T009 |

All functional requirements (FR‑000 – FR‑009) and success criteria (SC‑001 – SC‑004) are explicitly addressed by the tasks above.
