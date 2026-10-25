# Tasks: Extending AgentDoG 1.5 with Zero‑Shot Drift Detection  

**Inputs**: `spec.md`, `plan.md`, data‑model contracts, and any existing artifacts.  
All tasks follow the canonical format `- [ ] T### [P?] [USx?] description …` with
indented continuation lines that spell out the concrete output, verification
steps, and any required scientific checks.

---

## Phase 0 – Project scaffolding & reproducibility guarantees  

- [ ] T001 [Setup] **Create project directory tree**  
  *Create the following relative paths under the repository root:*  
  `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`  
  `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/raw/`  
  `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/`  
  `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`  
  `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/docs/`  
  `specs/PROJ-924/`  
  **Verification:**  
  1. `tests/test_setup.py` is created and contains `test_directories_exist` asserting the existence of each directory.  
  2. Run `pytest` and capture full console output to `data/processed/pytest_setup_log.txt`.  
  3. The log must contain the phrase `1 passed` for `test_directories_exist`.  

- [ ] T002 [Setup] **Add package manifests**  
  *Files:* `requirements.txt` (list of runtime dependencies) and `pyproject.toml` (PEP 621 metadata) – both must include the exact dependency list from the plan (sentence‑transformers, transformers, datasets, scikit‑learn, scipy, pandas, numpy, jsonschema, statsmodels, pytest, accelerate).  
  **Verification:**  
  1. `tests/test_config_files.py` is created and contains `test_pyproject_config_exists` and `test_ruff_config_exists`.  
  2. Run `pytest` and capture console output to `data/processed/pytest_manifest_log.txt`.  
  3. The log must contain `1 passed` for each test.  

- [ ] T010d **Create lint configuration & verify with pytest**  
  *Create* a `.ruff.toml` file at the repository root containing the lint rules required by the project.  
  *Add* a test `tests/test_config_files.py::test_ruff_config_exists` that asserts the file exists and contains a `[tool.ruff]` section.  
  *Run* `pytest` and capture the full console output to `data/processed/pytest_lint_log.txt`.  
  **Verification:** The log must contain the phrase `1 passed` for `test_ruff_config_exists` (and also for `test_pyproject_config_exists` from T002). The CI step fails if the log is missing or reports a failure.  

- [ ] T011a **Create core configuration module & verify constants**  
  *File:* `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/config.py` with the exact contents:  

  ```python
  RANDOM_SEED = 42
  MAX_RAM_GB = 7
  BATCH_SIZE = 64
  DRIFT_THRESHOLD = 0.5
  ```  

  *Add* a unit test `tests/test_config.py::test_constants` that imports the module and asserts each constant has the required value.  
  *Run* `pytest` and store the console output in `data/processed/pytest_config_log.txt`.  
  **Verification:** The log must contain `1 passed` for `test_constants`. The CI aborts if the constants are missing, have different values, or the test fails.

---

## Phase 1 – Data acquisition & taxonomy preparation  

- [ ] T005 **Download raw resources & compute checksums**  
  *Implement* `code/data_loader.py` to:  
  1. Load the verified taxonomy dataset `agentdog/safety-v1` via `datasets.load_dataset`.  
  2. Stream ≥ 500 post‑2025 GitHub‑issue logs from a public repository (e.g., `mlfoundations/agent_logs`).  
  3. Save taxonomy examples to `data/raw/safety_v1/` and logs to `data/raw/novel_corpus.jsonl`.  
  4. Compute SHA‑256 checksums for every downloaded file and write `data/raw/checksums.json`.  
  **Verification:** `tests/test_data_loader.py` confirms that (a) the taxonomy folder contains ≥ 100 examples per category, (b) the novel‑corpus file has ≥ 500 entries, and (c) the checksum file matches on‑disk hashes. All tests must pass (`pytest`).  

- [ ] T006 **Build category centroids**  
  *Implement* `code/taxonomy_builder.py` to:  
  1. Read curated examples from `data/raw/safety_v1/`.  
  2. Embed each example with **all‑MiniLM‑L6‑v2** (CPU‑friendly) in batches of size `BATCH_SIZE`.  
  3. Compute L2‑normalized mean vectors for each safety category (≥ 100 samples per category, satisfying FR‑004).  
  4. Persist a list of `TaxonomyCentroid` objects to `data/processed/taxonomy_centroids.json`.  
  **Verification:** `tests/test_taxonomy.py` validates the JSON file against `specs/001-llmxive-follow-up-extending-agentdog-1-5/contracts/taxonomy_centroid.schema.yaml` using `jsonschema`. The test must succeed.

---

## Phase 2 – Zero‑shot drift scoring & stratified sampling  

- [ ] T007 **Compute drift scores for every log**  
  *Implement* `code/drift_scoring.py` to:  
  1. Stream‑embed all logs from `data/raw/novel_corpus.jsonl` with the same MiniLM model.  
  2. For each embedding, compute cosine distance to every centroid and keep the minimum as `drift_score`.  
  3. Set `review_flag = drift_score >= DRIFT_THRESHOLD` (FR‑002).  
  4. Record additional fields `log_length` (character count) and `source`.  
  5. Write a Parquet table `data/processed/drift_scores.parquet`.  
  **Verification:** `tests/test_drift_schema.py` validates each row against `specs/001-llmxive-follow-up-extending-agentdog-1-5/contracts/drift_output.schema.yaml`. The test must pass.

- [ ] T008 **Stratify logs and draw unbiased sample**  
  *Implement* `code/sampling.py` to:  
  1. Load `drift_scores.parquet`.  
  2. Define **high‑drift** as the top 20 % of `drift_score` values and **low‑drift** as the bottom 20 % (FR‑005).  
  3. Perform a seeded random draw of **≥ 100 logs** that are uniformly distributed across the full drift range (FR‑017).  
  4. Write:  
     - `data/processed/high_drift_ids.json`  
     - `data/processed/low_drift_ids.json`  
     - `data/processed/full_range_sample.json` (list of sampled `log_id`s).  
  **Verification:** `tests/test_sampling.py` checks that the quantile splits are correct and that the sample size is ≥ 100.

- [ ] T009 **Create blinded annotation batches**  
  Using the IDs from `full_range_sample.json`, generate CSV files under `data/processed/annotation_batches/` containing only `log_id`, `text`, `log_length`, `source` (no scores or bin labels).  
  **Verification:** `tests/test_annotation_batches.py` ensures each CSV has the required columns and that the number of rows matches the sample size.

---

## Phase 3 – Human‑in‑the‑loop validation & statistical analysis  

- [ ] T010 **Ingest real human annotations**  
  *File expected:* `data/human_annotations.json` (provided externally).  
  *Process:* `code/ingest_annotations.py` must:  
  1. Load the annotation batches and the human annotation file.  
  2. Verify **exactly three distinct `annotator_id`s** per `log_id`.  
  3. Compute the majority‑vote binary label (`novel` if ≥ 2 annotators chose “novel attack”, else `benign`).  
  4. Save `data/processed/gold_standard.csv` with columns `log_id`, `binary_label`.  
  **Verification:** `tests/test_gold_standard.py` raises an error if any log lacks three annotators or if the majority‑vote rule is violated; the test must pass.

- [ ] T011 **Statistical validation of drift scores**  
  *Implement* `code/validation.py` to compute, on the **full‑range sample** (using the gold‑standard from T010):  
  1. Mean pairwise Cohen’s κ across the three annotators (must be ≥ 0.6 → FR‑007).  
  2. Mann‑Whitney U test between `drift_score` for “novel” vs “benign” logs (p < 0.05, rank‑biserial ≥ 0.5 → FR‑008).  
  3. Logistic regression `novel ~ drift_score + log_length + source` (coefficient p < 0.05, report AUC‑ROC).  
  4. Chi‑squared test on the contingency table of “novel” vs “benign” across high‑drift/low‑drift bins (reject H₀ at α = 0.05 → FR‑015).  
  5. **DeLong’s test** for paired AUC comparison between drift‑based and Flan‑T5 AUCs (required by the plan).  
  6. Apply Holm‑Bonferroni correction across the family of tests.  
  *Output:* `data/processed/validation_metrics.json` containing all statistics and a boolean `validation_passed` that is true only if **all** thresholds are satisfied.  
  **Verification:** `tests/test_validation.py` asserts the presence of every required key and that `validation_passed` is true; the CI fails otherwise.

- [ ] T012 **Run zero‑shot Flan‑T5 baseline**  
  *Implement* `code/baseline_llm.py` to:  
  1. Load `google/flan-t5-small` on CPU (no CUDA fallback).  
  2. Classify the same sampled logs used in T011 (text → “novel” / “benign”).  
  3. Record per‑log inference latency (wall‑clock time).  
  4. Compute AUC‑ROC against the gold‑standard.  
  5. Verify baseline AUC ≥ 0.70 (FR‑016).  
  *Outputs:* `data/processed/flan_predictions.json`, `data/processed/flan_metrics.json` (contains `auc`, `median_latency`).  
  **Verification:** `tests/test_flant5.py` checks that the model loads within `MAX_RAM_GB`, that the AUC meets the 0.70 threshold, and that latency values are numeric.

- [ ] T013 **Efficiency & performance comparison**  
  *Implement* `code/comparison.py` to:  
  1. Load drift AUC from `validation_metrics.json` and Flan‑T5 AUC/latency from `flan_metrics.json`.  
  2. Compute `auc_diff = abs(auc_drift - auc_flant5)`.  
  3. Compute `latency_ratio = median_latency_drift / median_latency_flant5`.  
  4. Perform **DeLong’s test** for paired AUC comparison (as already computed in T011) and store its p‑value.  
  5. Flag `computationally_efficient_alternative = (auc_diff <= 0.10) and (latency_ratio <= 0.5)`.  
  6. Write `data/processed/comparison.json` with the three numbers, the DeLong p‑value, and the flag.  
  **Verification:** `tests/test_comparison.py` asserts that the flag is true; if not, the test fails, satisfying FR‑011 and FR‑013.

---

## Phase 4 – Final reporting, resource accounting & reproducibility audit  

- [ ] T014 **Generate final report**  
  *Script:* `code/report.py` reads `validation_metrics.json`, `comparison.json`, and the CI runtime log (peak RAM, total wall‑clock time).  
  *Creates:* `data/processed/final_report.md` containing:  
  - Summary tables for US‑01, US‑02, US‑03 success criteria.  
  - All p‑values, effect‑size metrics, κ, AUC‑ROC values, latency ratios.  
  - Resource usage (≤ 7 GB RAM, ≤ 6 h wall‑clock – FR‑012).  
  - Explicit statement whether the “computationally efficient alternative” flag was set.  
  **Verification:** `tests/test_report.py` parses the markdown and checks that every required metric line is present and that the resource limits are respected.

- [ ] T015 **Reproducibility audit documentation**  
  *Create* `docs/reproducibility_audit.md` that lists:  
  - All random seeds (`RANDOM_SEED = 42`).  
  - Exact dataset versions / SHA‑256 checksums (from `data/raw/checksums.json`).  
  - Model identifiers and commit hashes (`all‑MiniLM‑L6‑v2`, `google/flan‑t5‑small`).  
  - Full command to re‑run the pipeline:  

    ```bash
    python run_full_pipeline.py --seed 42
    ```  

  - Expected SHA‑256 hash of `final_report.md` for deterministic verification.  
  **Verification:** `tests/test_audit.py` runs the command in a fresh temporary environment and asserts that the resulting `final_report.md` hash matches the recorded value.  

---

### Dependency ordering (implicit)

All tasks are listed in logical execution order; a later task depends on the outputs of any earlier task that creates the referenced file. The CI runner will enforce this ordering automatically.

---  

*All scientific requirements (FR‑001 – FR‑017, SC‑001 – SC‑004) are satisfied by the tasks above.  The early end‑to‑end runnable command is provided by `run_full_pipeline.py`, which orchestrates T007 → T011 → T012 → T013 → T014.*  