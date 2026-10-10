# Tasks: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and reviewer feedback from prior verification rounds.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T101 [US1] **Acquire a real WCST dataset**  
  Implement `fetch_data()` in `code/ingestion.py`.  
  - Probe public sources in deterministic order: (a) OpenML datasets filtered by keywords `["WCST","card‑sorting","executive function"]`; select the dataset with the **largest row count**, breaking ties by the **lowest OpenML ID**. (b) If none, attempt `datasets.load_dataset("<huggingface‑repo>", name="wcst", split="train", streaming=False)`.  
  - Write raw CSV to `data/raw/raw_dataset.csv`.  
  - Write `data/raw/metadata.json` containing: `dataset_source`, full fetch recipe, `simulation_mode: false`, **`has_condition_labels`** (true if the source includes a column that can be mapped to `stimulus_type`, false otherwise), and the SHA‑256 checksum of the raw file.  
  - Record column‑mapping table in the same metadata (e.g., `{ "participant_id": "subj_id", "age": "age_years", "stimulus_type": "condition", "perseverative_errors": "perseverative_err", "categories_completed": "cat_completed", "mmse_score": "MMSE" }`).  
  - On failure of **all** real sources, raise `RealDataFetchFailed`. No synthetic fallback.

- [ ] T102 [US1] **Clean and validate the real dataset**  
  Implement `clean_data()` in `code/ingestion.py`, invoked via `code/main.py`. Steps:  
  1. Load `data/raw/raw_dataset.csv`.  
  2. Apply column mapping from T101 metadata, **renaming the MMSE column to `mmse_score` (cast to integer)** and ensuring the condition column is named `stimulus_type` (enum `"nostalgia"` | `"control"`).  
  3. Cast `age` to integer and filter `age >= 65`; log `ERR_MISSING_AGE_FIELD` and drop rows with missing/invalid age → `data/processed/cleaned_age_filtered.csv`.  
  4. Drop rows missing `perseverative_errors` or `categories_completed`; log `ERR_MISSING_SCORE` → `data/processed/cleaned_score_filtered.csv`.  
  5. Detect presence of `mmse_score`: if present and at least one non‑null value, set `has_mmse: true` in `data/processed/mmse_flag.json` and filter `mmse_score >= 24`; otherwise set `has_mmse: false` and skip this filter (log `ERR_MMSE_MISSING`).  
  6. Write **`data/processed/final_cleaned_dataset.csv`** (MMSE‑filtered when applicable) and **`data/processed/cleaned_dataset_no_mmse.csv`** (score‑filtered only).  
  7. Produce `data/processed/exclusion_log.json` (counts per exclusion reason) and `data/processed/validity_metrics.json` (percent retained).  
  8. Raise `DataNotFoundError` if any output file would be empty.  
  Verification: unit tests `test_cleaning_filters_age` and `test_cleaning_filters_mmse` must pass.

- [ ] T106 [US1] **Stimulus integrity and citation validation**  
  - Validate each file in `data/stimuli/` against SHA‑256 checksums recorded in `data/stimuli_checksums.json`. On mismatch raise `ERR_STIMULUS_CORRUPT`. If the directory is empty, write `{"status":"absent"}` to `data/stimuli_checksums.json` and add `WARN_STIMULI_ABSENT` to `data/raw/metadata.json`.  
  - Run `code/reference_validator.py` on the dataset source recorded in `data/raw/metadata.json`. Write `data/citation_status.json` with fields `doi`, `verification_status` (`verified` or `skipped`).  
  - **Do not modify** `statistical_report.json` here; downstream tasks will read `citation_status.json` to set `validity_status`.  
  Verification: both JSON files exist with the documented schema.

- [ ] T103 [US2] **Welch’s t‑test analysis on the real cleaned data**  
  Implement in `code/analysis.py`:  
  1. Load `data/processed/final_cleaned_dataset.csv`.  
  2. If `has_condition_labels` (from T101 metadata) is **false**, write `data/processed/grouped_data.json` with `{ "status": "NO_CONDITION_LABELS" }` and **skip** hypothesis testing, logging `WARN_NO_CONDITION_LABELS`.  
  3. Otherwise, split by `stimulus_type` into nostalgia/control groups; write group sizes and descriptive stats to `data/processed/grouped_data.json`.  
  4. For each outcome (`perseverative_errors`, `categories_completed`):  
     - Perform assumption checks (Shapiro‑Wilk, Levene) → `data/results/assumption_checks.json`. Log any violations as `WARN_ASSUMPTION_VIOLATION`.  
     - If a group has `n < 10` or zero variance, log `ERR_SMALL_SAMPLE` / `ERR_ZERO_VARIANCE` and **skip** that comparison.  
     - Run Welch’s independent‑samples t‑test (`scipy.stats.ttest_ind(..., equal_var=False)`).  
     - Compute Cohen’s d with 95 % CI, statistical power, and Minimum Detectable Effect Size (MDES).  
  5. Apply Bonferroni correction across the two outcomes (`statsmodels.stats.multitest.multipletests`).  
  6. Produce **`data/results/statistical_report.json`** as a **list of objects**, each conforming to `contracts/output.schema.yaml` with required keys: `comparison_name`, `p_value`, `p_value_corrected`, `effect_size`, `effect_size_ci_lower`, `effect_size_ci_upper`, `significance_status` (`significant`/`non‑significant`/`sensitive`), `mdes`, `adjustment_status` (`adjusted`), and `validity_status` (read from `data/citation_status.json`).  

  Verification: `python code/main.py --stage analysis` creates the JSON file; unit test `test_welch_ttest` validates against a hand‑computed example.

- [ ] T104 [US3] **Sensitivity sweep over significance thresholds**  
  Using the **Bonferroni‑corrected** p‑values from T103, evaluate significance at thresholds **0.01, 0.04, 0.05, 0.06, 0.10**. Flag `is_sensitive_to_threshold: true` when a corrected p‑value falls within **0.04 – 0.06** (per clarified FR‑005). Write `data/results/sensitivity_report.json` with an array of objects per outcome, each containing `threshold`, `significance_status`, and the sensitivity flag.  

- [ ] T105 [US3] **MMSE robustness re‑analysis**  
  - Re‑run the analysis pipeline on `data/processed/cleaned_dataset_no_mmse.csv`.  
  - If `has_mmse: false` (from `mmse_flag.json`), write `data/results/robustness_report.json` with `{ "status": "SKIPPED", "reason": "MMSE_MISSING" }`.  
  - Otherwise, produce the same structure as `statistical_report.json` (but based on the no‑MMSE‑exclusion dataset) and write to `data/results/robustness_report.json`.  
  - Generate `data/results/sensitivity_comparison.json` comparing primary vs robustness results (differences in `significance_status` and `effect_size`).  
  - Also write `data/results/primary_analysis_report.json` derived from the primary `statistical_report.json` and **including** the `validity_status` read from `citation_status.json`.  

- [ ] T107 [US2/US3] **Runtime monitoring and integration test**  
  - Wrap the full pipeline (`code/main.py`) in a timer; if runtime > 21 600 s, log `WARN_TIMEOUT` and append to `data/results/runtime_log.json` but continue.  
  - Add `tests/integration/test_full_pipeline.py` that runs the entire pipeline on the real dataset and asserts existence and non‑null required fields in all contracted JSON artifacts.  

- [ ] T108 [US3] **Results tables and figures**  
  - Generate `data/results/results_table.md` containing per‑outcome group means ± SD, t‑statistics, raw and corrected p‑values, Cohen’s d with 95 % CI, power, and MDES.  
  - Generate `data/results/robustness_summary.md` summarizing primary vs no‑MMSE results and the threshold‑sweep, explicitly noting any limitations (e.g., missing condition labels, sample size).  
  - All numbers must be pulled directly from the corresponding JSON files.  

## Phase 2: Complete the study and validate its evidence

- [ ] T109 [US1/US2/US3] **Methods/results quickstart and documentation**  
  - Update `specs/001-nostalgia-cognitive-flexibility/quickstart.md` and `README.md` with exact commands (`pip install -r requirements.txt`, `python code/main.py`).  
  - Write `paper/001_results.md` detailing methods (real data source, cleaning rules, Welch’s t‑test rationale, citation validation, stimulus integrity), linking each reported number to its JSON source, and stating any honest limitations (e.g., no nostalgia labels, small sample).  

- [ ] T110 [US1/US2/US3] **State versioning and final re‑run**  
  - Update `state/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle.yaml` with SHA‑256 hashes and `updated_at` timestamps for **all** artifacts under `data/`.  
  - Re‑run the full workflow from a clean slate and confirm that `pytest` passes and all artifact hashes match the recorded values.  
  - Document the handoff in `paper/001_results.md` (paper‑stage handoff, not duplicated here).  

## Phase 3: Reproducible results and paper handoff

- [ ] T111 [US1/US2/US3] **Final artifact verification**  
  - Run the reference validator one last time on all citations and stimuli.  
  - Ensure `data/citation_status.json` reports `verified` and that `data/stimuli_checksums.json` status is consistent.  
  - Archive a copy of the full `state/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle.yaml` as `state/archive/<timestamp>.yaml` for provenance.  

### New tasks addressing coverage concerns

- [ ] T112 [US1] **Validate cleaned dataset against contract schema**  
  - Use `jsonschema.validate` to check `data/processed/final_cleaned_dataset.csv` (converted to JSON records) against `contracts/dataset.schema.yaml`.  
  - On validation failure, raise `DatasetSchemaValidationError` with details; on success, write `data/processed/schema_validation_log.json` indicating pass.  
  - Verification: unit test `test_dataset_schema_validation` must succeed on the cleaned dataset.

- [ ] T113 [US2] **Detect repeated‑measure records and optional mixed‑effects analysis**  
  - Scan the cleaned dataset for multiple rows sharing the same `participant_id` with differing `stimulus_type`.  
  - If such repeated‑measure cases exist, log `WARN_REPEATED_MEASURES` and run a mixed‑effects model (`statsmodels.formula.api.mixedlm`) with `stimulus_type` as a fixed effect and `participant_id` as a random intercept, producing `data/results/mixed_effects_report.json` (same schema fields as `statistical_report.json`).  
  - If no repeated measures are found, log `INFO_NO_REPEATED_MEASURES` and skip the mixed‑effects step.  
  - Verification: unit test `test_mixed_effects_path` ensures the report is created only when repeated measures are present.

## Dependencies and requirement coverage

- **FR‑001**: Enforced in T102 (age filter).  
- **FR‑002**: Implemented in T103 (Welch’s t‑test on both outcomes).  
- **FR‑003**: Bonferroni correction in T103.  
- **FR‑004**: Cohen’s d & 95 % CI in T103.  
- **FR‑005**: Sensitivity flag on corrected p‑values in T104 (clarified).  
- **FR‑006**: MMSE exclusion in T102; robustness check in T105.  
- **FR‑007**: Runtime warning in T107.  
- **US1**: T101, T102, T106.  
- **US2**: T103, T107.  
- **US3**: T104, T105, T108.  

# Execution order

T101 → T102 → T106 → T103 → T104 → T105 → T107 → T108 → T109 → T110 → T112 → T113 → T111