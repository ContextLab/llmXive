# Tasks: Static‑Dynamic Gap Analysis for LLM‑Generated Code Patches  

**Inputs**: `spec.md`, `plan.md`, existing repository layout, and reviewer feedback.  

The following checklist implements the full research pipeline required by the specification. Each task is a concrete, verifiable unit; unchecked boxes indicate work that still needs to be performed. All artifact paths are relative to the project root.

---  

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run an executable analysis on a small real subset early, producing real result rows under `data/results/`. |
|------|----------------------------------------------------------------------------------------------|

- [ ] T001 [P] Create project‑wide directories, pin random seeds, and document a runnable command in `quickstart.md`.  
  *Creates*: `data/`, `interim/`, `features/`, `models/`, `reports/`, `src/pipeline/`, `src/cli/`.  
  *Verification*: `quickstart.md` contains a single command (`python -m src.cli.run_pipeline --dry-run`) that finishes without error and prints the path of a tiny result file `data/results/sample_run.csv` (≤ 10 rows).

- [ ] T002 [P] Implement **Data Ingestion** (`src/pipeline/ingest.py`).   <!-- FAILED-IN-EXECUTION: src/pipeline/ingest.py exit=1 -->
  *Produces*: `data/raw_swe_gym.parquet`, `data/raw_multi_swe_rl.jsonl`, `data/patches.csv` (columns: `patch_id,language,source_code,label`), **and** `data/execution_logs/` containing the ground‑truth test execution logs for every patch (e.g., `patch_id.log`).  
  *Verification*: SHA‑256 checksums of the two raw downloads match the values listed in `plan.md`; `patches.csv` contains ≥ 3 500 rows and a printed label‑distribution summary matching the spec; each `patch_id` has a corresponding log file in `data/execution_logs/` (checked by a contract test).

- [ ] T014 [P] Implement **Memory‑Aware Sampling Fallback** (`src/pipeline/ingest.py` extension).  
  *Logic*: Before full ingestion, estimate memory usage; if estimated peak RAM > 6 GB, automatically switch to a stratified random sample of patches (10 % of each language/dataset combination, seed = 42).  
  *Produces*: `data/patches_sample.csv` and sampled log files when fallback is triggered.  
  *Verification*: Log `reports/ingestion_mode.yaml` records whether full or sampled ingestion was used; downstream tasks read from the appropriate CSV.

- [ ] T004 [P] Implement **Static Graph Extraction** (`src/pipeline/graph_extractor.py`).  
  *Produces*: for every parseable patch, two JSON files under `interim/graphs/`  
  - `interim/graphs/{patch_id}_cfg.json` (CFG)  
  - `interim/graphs/{patch_id}_cg.json` (CG)  
  *Verification*: ≥ 99 % of parseable patches yield both JSON files; a log `reports/graph_extraction.yaml` records `total_patches`, `parsed_success`, `skipped_unparseable`. The schema `specs/001-llmxive-follow-up-extending-dockerless-e/contracts/static_graph.schema.yaml` is validated for a random sample of 10 files. **Alignment verification is performed in the subsequent task T017.**

- [ ] T017 [P] **Static‑Dynamic Alignment Verification** (`src/pipeline/alignment_checker.py`).  
  *Purpose*: Cross‑check that each static graph file (`*_cfg.json`, `*_cg.json`) is generated from the exact source code version whose execution log (`data/execution_logs/{patch_id}.log`) was used for the ground‑truth label.  
  *Produces*: `reports/alignment_check.yaml` summarizing mismatches (should be none).  
  *Verification*: A contract test asserts that the number of mismatches is zero; any violation aborts the pipeline.

- [ ] T005 [P] Implement **Feature Engineering** (`src/pipeline/feature_engineer.py`).  
  *Produces*: `features/static_features.csv` (one row per successfully extracted graph, adhering to `feature_vector.schema.yaml`).  
  *Verification*: Row count equals `parsed_success` from T004; a checksum file `features/static_features.sha256` is generated; a contract test confirms every row validates against the schema.

- [ ] T006 [P] Implement **Model Training & Evaluation** (`src/pipeline/model_trainer.py`).  
  *Produces*:  
  - `models/rf.pkl` (Random Forest)  
  - `models/lr.pkl` (Logistic Regression)  
  - `reports/evaluation.csv` (columns: `metric,rf_value,lr_value`) containing AUC, Precision, Recall, and a confusion matrix.  
  - `reports/roc_curve.png`.  
  *Verification*: `evaluation.csv` contains AUC ≥ 0.5 for both models (baseline check); a pytest `test_model_trainer.py` asserts that the confusion matrix entries sum to the test‑set size.

- [ ] T007 [P] Implement **Statistical Significance (Wald) Test** (integrated in `model_trainer.py` or separate `src/pipeline/wald_test.py`).  
  *Produces*: `reports/wald_test.csv` (columns: `feature,coefficient,z_stat,p_value,bonferroni_adj`).  
  *Verification*: At least one feature has `p_value < 0.05` after Bonferroni adjustment, confirming a statistically significant association; contract test validates CSV header integrity.

- [ ] T008 [P] Implement **Error‑Case Mining & Taxonomy Tagging** (`src/pipeline/error_miner.py`).  
  *Produces*:  
  - `reports/error_cases.csv` (rows: `patch_id,true_label,predicted_label,category`).  
  - `reports/error_category_distribution.png`.  
  *Verification*: All false‑positive and false‑negative patches are present; a validation run on a hand‑crafted set of 50 known failure modes yields ≥ 90 % correct category tags (checked by `tests/unit/test_error_miner.py`).

- [ ] T015 [P] **Validate Taxonomy Coverage** (`src/pipeline/taxonomy_validator.py`).  
  *Purpose*: Ensure that the dataset contains at least one real instance for every error‑category defined in the taxonomy (`dynamic_dispatch`, `external_api`, `concurrency_race`, `mocked_io`, `other`).  
  *Produces*: `reports/taxonomy_coverage.yaml` reporting presence/absence per category.  
  *Verification*: CI fails if any category reports zero instances; the report is referenced in the final research report.

- [ ] T009 [P] Implement **Performance Monitoring** (`src/pipeline/utils.py` helpers used by all phases).  
  *Produces*: `reports/performance.yaml` containing `total_runtime_seconds`, `peak_ram_gb`, and per‑phase timings.  
  *Verification*: Values are ≤ 21600 s (6 h) and ≤ 7 GB RAM; the file is parsed by a unit test that fails if limits are exceeded.

- [ ] T010 [P] Generate the **Final Research Report** (`src/cli/generate_report.py`).  
  *Produces*: `reports/final_report.md` that includes:  
  1. Dataset statistics & skip‑rate bias discussion.  
  2. Feature‑importance bar plot.  
  3. Evaluation metrics vs. random baseline.  
  4. Wald‑test summary.  
  5. Divergence rate (FP + FN / total parsable patches).  
  6. Error‑category frequency distribution.  
  7. Runtime & memory summary.  
  *Verification*: The markdown contains the required section headings (SC‑001 … SC‑005) and embeds the PNG figures produced earlier; a smoke‑test script checks that each referenced file exists.

- [ ] T003 [P] Run a **dry‑run end‑to‑end** on the first 20 patches **after** core components are implemented to ensure the full pipeline works.  
  *Command*: `python -m src.cli.run_pipeline --max-patches 20 --output data/results/sample_run.csv`.  
  *Verification*: `data/results/sample_run.csv` exists, has 20 rows, and includes columns `patch_id, true_label, predicted_label, predicted_prob`. No uncaught exceptions appear in the log.

---  

## Phase 2 – Complete the study and validate its evidence  

| Goal | Execute the full pipeline, generate all analyses, and record performance metrics. |
|------|-----------------------------------------------------------------------------------|

- [ ] T011 [P] Write **Contract Tests** (`tests/contract/test_contracts.py`) that validate every output artifact against its JSON/YAML schema (static graphs, feature vectors, model outputs).  
  *Verification*: `pytest -q tests/contract` exits with 0 failures.

- [ ] T012 [P] Add **End‑to‑End CI Script** (`src/cli/run_pipeline.py`) that orchestrates all phases in the correct order, aborting on any error and printing a summary of generated artifacts.  
  *Verification*: Running `python -m src.cli.run_pipeline` on a fresh clone (no `data/` or `interim/` contents) completes successfully, reproducing all files listed above; the CI log contains the phrase “Pipeline completed successfully”.

- [ ] T013 [P] Document the **Paper‑Stage Handoff** in `paper/handoff.md`.  
  *Contents*: location of the final report, all model files, the feature CSV, and a reproducibility checklist (seed values, command‑line flags, hardware specs).  
  *Verification*: The handoff file is present and a unit test confirms that every path referenced in it exists.

---  

### Dependency & Requirement Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, Edge‑case skip handling | T002, T004 |
| FR‑002 (CFG/CG generation) | T004 |
| FR‑003 (Feature vector) | T005 |
| FR‑004 (Classifier) | T006 |
| FR‑005 (Error categorisation) | T008 |
| FR‑006 (Wald test) | T007 |
| FR‑007 (Performance limits) | T009 |
| SC‑001 (AUC vs. baseline) | T006 |
| SC‑002 (Divergence rate) | T008 |
| SC‑003 (Error‑category distribution) | T008 |
| SC‑004 (Runtime & memory) | T009 |
| SC‑005 (Statistical significance) | T007 |
| Contract validation | T011 |
| Reproducibility & handoff | T012, T013 |
| Alignment verification (Constitution VI) | T017 |
| Taxonomy coverage check (Constitution VII) | T015 |
| Sampling fallback (Plan Phase 2) | T014 |

---  

*All tasks are pending (unchecked) until implementation and verification succeed.  The pipeline can be executed incrementally; each task’s verification step guarantees that the corresponding scientific requirement is met before proceeding to the next.*  