# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: `spec.md`, `plan.md`, existing artifacts in the repository.  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories).  

> **⚠️ GOVERNANCE NOTE** – The pipeline first attempts to download the original datasets (FlavorDB, Counterfactual Recipe Generation). If any of those fail, a **Ratified Amendment** must be recorded in `docs/amendment_record.md` before any downstream work proceeds. The amendment switches the methodology to a **Correlational Analysis** that uses Recipe1M embeddings / ratings as proxies.

---

## Phase 1 – Setup & Governance (must complete before any data work)

- [X] **T001a** Create project directory structure  
  *Creates* `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `data/`, `tests/`.  
  **Verification**: `data/setup_log.json` contains `{"status":"SUCCESS","paths_verified":[...],"timestamp":"ISO8601"}`.

- [X] **T001b** Create empty package init files  
  *Creates* `code/__init__.py`, `tests/__init__.py`, `code/data/__init__.py`.  
  **Verification**: Files exist and are non‑empty (contain a docstring).

- [ ] **T001c** Create placeholder `requirements.txt` and `tests/conftest.py`  
  **Verification**: Both files exist; `requirements.txt` lists at least `pandas`.

- [ ] **T001d_quickstart** Generate `quickstart.md` guide  
  *Creates* a minimal usage guide for running the pipeline.  
  **Verification**: `quickstart.md` exists and contains a code block with `python -m code.run_full_pipeline`.

- [ ] **T001e_data_model** Author `data-model.md` documenting the data model  
  *Creates* `specs/001-statistical-analysis-of-publicly-availab/data-model.md`.  
  **Verification**: File exists and includes sections for `IngredientPair` and `ModelResult` matching the schema contracts.

- [ ] **T012a_recipe1m** Download Recipe1M (streaming)  
  *Action*: `datasets.load_dataset("recipe1m/recipe1m", streaming=True)`.  
  **Output**: `data/raw/recipe1m_raw.parquet` (on success) or `data/download_status_recipe1m.json` (on failure).  
  **Verification**: Presence of one of the two JSON files; failure file must contain an `error_code`.

- [ ] **T012a_flavordb** Download FlavorDB chemical matrix (verified URL)  
  *Action*: Attempt download; always produce a status JSON (`data/download_status_flavordb.json`) with fields `status` (`SUCCESS`/`FAILURE`) and optional `error_code`. Pipeline must **not abort** on failure.  
  **Verification**: Status JSON exists; if `status` is `FAILURE`, downstream tasks treat dataset as unavailable.

- [ ] **T012a_counterfactual** Download Counterfactual Recipe Generation dataset (verified URL)  
  *Action*: Attempt download; always produce a status JSON (`data/download_status_counterfactual.json`).  
  **Verification**: Status JSON exists; pipeline proceeds regardless of success.

- [ ] **T012b_agg** Aggregate individual download‑status files into `data/download_status.json`.  
  **Verification**: JSON contains keys `recipe1m`, `flavordb`, `counterfactual` with status values.

- [ ] **T012c_schema_validate** Validate Counterfactual schema (presence of `rating`/`independent_sensory_compatibility`).  
  **Output**: Updated `data/download_status.json` with possible `INVALID_SCHEMA` flag.  
  **Verification**: Flag present only if required columns missing.

- [ ] **T012b_prepare_amendment_log** Generate `data/amendment_log.json` reflecting download results and whether a ratified amendment is required.  
  **Verification**: JSON fields `status`, `methodology`, `proxy_source`, `timestamp` exist.

- [ ] **T012d_ratification_gate** Halt pipeline until `data/amendment_log.json.status=="RATIFIED"` (human‑reviewed amendment).  
  **Verification**: If status is not `RATIFIED`, the task raises a `RuntimeError` with message `"Ratification required before proceeding"` and aborts further execution.

---

## Phase 2 – Core Infrastructure & Data Pipeline (depends on **T012d_ratification_gate**)

- [ ] **T002** Initialize Python project (pin dependencies in `code/requirements.txt`).  
  **Verification**: `pip install -r code/requirements.txt` succeeds in a clean environment.

- [ ] **T033a** Configure linting (`ruff.toml`).  
  **Verification**: `ruff .` reports no errors.

- [ ] **T033b** Configure formatting (`pyproject.toml` for Black).  
  **Verification**: `black --check .` reports zero changes.

- [ ] **T004** Create `data/` sub‑folders (`raw/`, `processed/`, `final/`) and `code/` module layout.  
  **Verification**: All directories exist; a sentinel file `data/.gitkeep` is present.

- [ ] **T005** Global random‑seed pinning (`code/__init__.py` sets `np.random.seed(42)`, `random.seed(42)`; `tests/conftest.py` applies fixture).  
  **Verification**: Running a test that prints `np.random.rand()` yields repeatable values.

- [ ] **T006** Memory‑monitor utility (`code/utils/memory_monitor.py`).  
  **Verification**: Running `check_limit(7168)` logs a JSON file `data/memory_profile.json` with `peak_ram_mb`.

- [ ] **T007a_schema_dataset** Create `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` defining the `IngredientPair` fields (including `flavor_similarity` placeholder).  
  **Verification**: YAML file loads without error.

- [ ] **T007a_schema_model** Create `specs/001-statistical-analysis-of-publicly-availab/contracts/model_output.schema.yaml` defining `ModelResult`.  
  **Verification**: YAML file loads without error.

- [ ] **T007a_validator** Implement `code/utils/validate_schema.py` that validates CSV/JSON artifacts against the two schemas above.  
  **Verification**: Running the validator on a sample file returns exit code 0.

- [ ] **T007b_Update Schema for Ratified Path** After amendment ratification, modify `dataset.schema.yaml` so `flavor_similarity` description reflects either “FlavorDB chemical vectors” or “Recipe1M embedding cosine similarity”.  
  **Verification**: The schema file contains the correct description matching `data/amendment_log.json.methodology`.

- [ ] **T038** Robust download verification (`code/data/verify.py`) – no silent fall‑backs; failures raise.  
  **Verification**: Simulated bad URL triggers an exception and logs to `data/download_errors.log`.

- [ ] **T013b** Pilot download & power‑analysis  
  *Action*: Sample ≈ 10 k recipes, compute variance of `log_co_occurrence`, run `statsmodels.stats.power.GofChisquarePower` to estimate required sample size for effect size 0.1, α = 0.05, power = 0.8.  
  **Output**: `data/pilot_stats.json` with `sample_size_required`.  
  **Verification**: JSON contains an integer > 0.

- [ ] **T013a** Stream & validate full (or down‑sampled) Recipe1M corpus  
  *Uses* `sample_size_required` from T013b to limit streaming via `itertools.islice`.  
  **Output**: `data/raw/recipe1m_processed.parquet`.  
  **Verification**: Parquet file exists; schema includes `recipe_id`, `ingredients`, `rating`.

- [ ] **T042** Schema validation for Recipe1M ratings  
  *Action*: Verify that the processed Recipe1M file contains a `rating` column of numeric type.  
  **Verification**: If the column is missing or wrong type, task fails with clear error; otherwise succeeds.

- [ ] **T014a** Normalize ingredient names & map to canonical IDs  
  *Action*: Load `data/raw/recipe1m_processed.parquet`, apply Levenshtein distance ≤ 2 against the canonical list (FlavorDB if causal, otherwise Recipe1M ingredient list). Resolve ties by marginal frequency.  
  **Output**: `data/processed/normalized_ingredients.csv` (`raw_name`, `canonical_id`, `canonical_name`).  
  **Verification**: CSV has no duplicate `canonical_id` rows; checksum file `data/processed/normalized_ingredients.sha256` is created.

- [ ] **T014b** Derive functional roles (primary/secondary/garnish) from ingredient position & marginal frequency.  
  **Output**: `data/processed/functional_roles.csv` (`canonical_id`, `functional_role`).  
  **Verification**: Role distribution sums to total ingredient count; no missing values.

- [ ] **T015** Construct global log‑transformed co‑occurrence matrix `C`.  
  *Action*: Pairwise count over streamed recipes, epsilon = 1e‑6, then `log(1 + count)`.  
  **Output**: `data/processed/co_occurrence_matrix.parquet`.  
  **Verification**: Parquet file contains columns `ingredient_a`, `ingredient_b`, `log_co_occurrence`.

- [ ] **T014c** Circularity warning (correlation between marginal frequency and co‑occurrence).  
  **Output**: `data/logs/circularity_warning.json` with fields `r` (numeric correlation) and `flag` (boolean true when `r` > 0.1).  
  **Verification**: JSON schema validated; `r` is a number; `flag` correctly reflects the threshold.

- [ ] **T016a** Chemical similarity (FlavorDB) – only executed when methodology = "Causal Independence".  
  **Output**: `data/processed/similarity_scores_chemical.parquet`.  

- [ ] **T016b** Embedding similarity (Recipe1M) – only when methodology = "Correlational Analysis".  
  *Action*: Load `sentence-transformers/all-MiniLM-L6-v2`, compute cosine similarity for each canonical ingredient pair.  
  **Output**: `data/processed/similarity_scores_embedding.parquet`.  
  **Verification**: File exists; similarity values lie in [‑1, 1].

- [ ] **T017** Functional‑role validation (ensure role not collinear with `log_co_occurrence`).  
  **Output**: `data/processed/functional_roles_validated.parquet` (same schema as `functional_roles.csv` plus a `validated` flag).  

- [ ] **T017c_role_independence_audit** Role‑independence audit (Pearson r > 0.1 warning).  
  **Output**: `data/logs/role_independence_audit.json`.  

- [ ] **T018** Imputation & bias check  
  *Select* similarity source based on methodology, fill missing similarity scores with 0, log exclusion counts.  
  **Output**: `data/processed/ingredient_pairs.csv` (final modeling dataset, matching `IngredientPair` schema).  
  **Verification**: Row count > 0; file validates against `dataset.schema.yaml`.

- [ ] **T019a** Compatibility labels – independent source (Counterfactual)  
  *Precondition*: `proxy_source` = null (i.e., original datasets succeeded).  
  **Output**: `data/processed/ingredient_pairs_with_labels.csv` (adds `compatibility_label`).  
  **Verification**: CSV contains a `compatibility_label` column with only 0 or 1 values.

- [ ] **T019b** Compatibility labels – proxy source (Recipe1M ratings)  
  *Precondition*: `proxy_source` = "Recipe1M".  
  *Action*: Compute median rating; label = 1 if rating ≥ median else 0.  
  **Output**: Same file as T019a (overwrites with proxy labels).  
  **Verification**: Binary label column present; distribution reported in `data/logs/label_distribution.json`.

- [ ] **T023** Compute Variance Inflation Factors (VIF) for `log_co_occurrence`, `flavor_similarity`, `functional_role`.  
  **Output**: `data/logs/vif_scores.json` (mapping predictor → VIF).  
  **Verification**: All VIF < 5; if any ≥ 5 the task fails the pipeline.

- [ ] **T024_methodology_decision** Read `data/amendment_log.json` and write `data/logs/methodology_flag.json` indicating which statistical route to follow (`use_lrt` vs `use_partial_corr`).  
  **Verification**: JSON contains boolean flags **and** they match the `methodology` field in `data/amendment_log.json`.

- [ ] **T024b_LRT_Execution** If `use_lrt` = true, fit full logistic regression + null (frequency‑only) model, perform likelihood‑ratio test, write `data/logs/lrt_results.json`.  
  **Verification**: JSON includes `lr_stat`, `p_value`.

- [ ] **T024b_partial** If `use_partial_corr` = true, compute partial correlation between `compatibility_label` and each predictor controlling for the others (using `pingouin.partial_corr`). Write `data/logs/partial_corr.json`.  
  **Verification**: JSON contains `r` and `p-val` per predictor.

- [ ] **T024d_metric** Extract the key metric (LRT p‑value or partial‑corr coefficient) for later reporting.  
  **Output**: `data/logs/model_metric.json`.  
  **Verification**: JSON contains the expected metric key (e.g., `"metric_value"`) with a numeric value.

- [ ] **T304** Refine Bayesian priors for proxy data (wider priors).  
  **Modification**: Update `code/models/bayesian.py` and write `data/logs/prior_config.json`.  
  **Verification**: `prior_config.json` includes the new prior parameters such as `"mean"` and `"sd"`.

- [ ] **T025** Hierarchical Bayesian model fit (PyMC ≥ 5, NUTS) on stratified subset (as defined in T013b).  
  **Output**: `data/logs/bayesian_results.json` (posterior summaries).  
  **Verification**: R̂ ≈ 1.0 for all parameters; effective sample size > 500.

---

## Phase 4 – Evaluation, Hypothesis Testing & Reporting

- [ ] **T029** Calculate evaluation metrics on held‑out test set (AUC, precision, recall, calibration error).  
  **Output**: `data/logs/evaluation_metrics.csv`.  

- [ ] **T030b_hypothesis_test** Statistical test for AUC improvement (DeLong’s test or bootstrap).  
  **Output**: `data/logs/hypothesis_test.json` (`delta_auc`, `p_value`, `significant`).  

- [ ] **T030** Generate calibration plot (predicted probability vs. observed).  
  **Output**: `docs/calibration_plot.png`.  

- [ ] **T031** Assemble final report (`docs/final_report.md`) – includes model comparison metric, hypothesis‑test outcome, VIF summary, leakage quantification (if correlational), and discussion of limitations.  
  **Verification**: Report contains sections “Methods”, “Results”, “Limitations”, and references the JSON artifacts.

- [ ] **T032** Sensitivity analysis – vary down‑sampling ratio and prior widths, re‑run evaluation, summarize in `docs/sensitivity_analysis.md`.  

- [ ] **T032b** Circularity quantification (only for correlational path) – report shared variance between embeddings and ratings, add to final report.  
  **Output**: `data/logs/circularity_quantification.json` with numeric `shared_variance`.  
  **Verification**: JSON exists and contains a numeric `shared_variance` field.

---

## Phase 5 – Orchestration & Execution

- [ ] **T099a_graph** Define the logical execution graph (YAML) linking all tasks and their dependencies.  
  **Output**: `docs/pipeline_graph.yaml`.  

- [ ] **T099a_impl** Implement `code/run_full_pipeline.py` – reads the graph, executes tasks in order, aborts on failure, logs progress to `data/logs/pipeline_execution_log.json`.  
  **Verification**: Running the script with `--dry-run` exits with status 0 and logs the intended execution order.

- [ ] **T099b** Execute the full pipeline (via `python -m code.run_full_pipeline`).  
  **Verification**: `pipeline_execution_log.json` records each task with status `"SUCCESS"`; all downstream artifacts listed in prior tasks exist and pass their individual verification steps.

---

## Phase 6 – Governance & Review Resolution (post‑analysis)

- [ ] **T301** Document data‑source provenance (`docs/data_provenance.md`) – explains any fallback to proxies, cites amendment record, and lists URLs with checksums.  
  **Verification**: File exists and contains a non‑empty list of URLs each paired with its SHA‑256 checksum.

- [ ] **T302** Add “Limitations: Corpus Circularity” section to `docs/final_report.md`.  
  **Verification**: `final_report.md` contains a heading `## Limitations` and includes the phrase “Corpus Circularity”.

- [ ] **T303** Validate proxy assumptions – correlate embedding‑derived `flavor_similarity` with compatibility labels against a random baseline; write `data/logs/proxy_validation.json`.  
  **Verification**: JSON includes a numeric `correlation_coefficient` field.

- [ ] **T305** Update hypothesis statement in `docs/final_report.md` to reflect the actual methodology (causal vs. correlational).  
  **Verification**: `final_report.md` contains the updated hypothesis text matching the `methodology` recorded in `data/amendment_log.json`.
