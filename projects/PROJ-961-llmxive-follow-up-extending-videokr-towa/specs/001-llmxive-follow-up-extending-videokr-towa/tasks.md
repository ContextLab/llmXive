# Tasks: Video Reasoning Threshold Analysis

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, existing artifacts, and reviewer feedback.

The checklist follows the canonical format `- [ ] T### [P?] [USx?] description …`.  
Checked boxes (`[X]`) denote tasks that have already passed verification and are retained unchanged.  
Unchecked boxes (`[ ]`) are pending or have been revised to satisfy the specification and reviewer comments.

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Establish a reproducible pipeline on a small real input and produce the first set of processed artifacts.

- [ ] T123 [P] Fix `download_data.py` to guarantee successful execution (exit 0) and creation of required raw files.  
  - **File**: `code/ingest/download_data.py`  
  - **Verification**: Running `python code/ingest/download_data.py` exits with status 0 and creates `data/raw/videokr_sft.csv`, `metadata/video_lengths.csv`, `knowledge_graph.json`, and `checksums.json`.

- [ ] T103 [S] [US1] Download the official **VideoKR‑SFT** dataset and its ground‑truth knowledge graph.  
  - **File**: `code/ingest/download_data.py`  
  - **Behaviour**:  
    1. Use `datasets.load_dataset("llmxive/video_kr_sft", split="train", streaming=True)` to fetch the QA split and `datasets.load_dataset("llmxive/video_kr_sft", split="train", streaming=False)` for any auxiliary metadata.  
    2. Download the knowledge‑graph JSON (`knowledge_graph.json`) via `huggingface_hub.hf_hub_download` from the verified repo `llmxive/video_kr_kg`.  
    3. Abort loudly with a custom `DataUnavailableError` if any fetch fails; **no synthetic fallback**.  
    4. Compute SHA‑256 checksums for every downloaded file and write `data/raw/checksums.json`.  
  - **Verification**: Running `python code/ingest/download_data.py` creates `data/raw/` with `videokr_sft.csv`, `metadata/video_lengths.csv`, `knowledge_graph.json`, and a non‑empty `checksums.json`. The script exits with status 0 on success and non‑zero on failure.

- [ ] T124 [S] Generate ingestion log `ingest_log.json` recording the exit code of the download script.  
  - **File**: `code/ingest/ingest_log.py` (called by the orchestrator after T103).  
  - **Output**: `data/processed/ingest_log.json` with field `exit_code` (integer).  
  - **Verification**: The JSON exists and `exit_code == 0` after a successful download.

- [ ] T104 [S] [US1] Annotate the raw VideoKR‑SFT records with structural hop counts, required covariates, and a placeholder `predicted_correctness` column (default 0.0).  
  - **File**: `code/ingest/annotate_graph.py`  
  - **Steps**:  
    1. Stream the raw CSV (`data/raw/videokr_sft.csv`) using `pandas.read_csv(chunksize=10_000)`.  
    2. For each record, invoke `entity_linker.link_dataframe` to obtain node IDs for the question and answer entities.  
    3. Compute the shortest‑path hop count (`chain_length`) via BFS on the graph loaded by `code/utils/graph_utils.py`.  
    4. Extract covariates: `question_difficulty` (from `difficulty_score`), `video_length_seconds` (from `metadata/video_lengths.csv`), and `answer_type` (derived from the answer‑format field).  
    5. Set `status = "annotated"` when both entities are linked; otherwise `status = "mapping_failure"` and `chain_length = -1`.  
    6. Add columns `chain_bin` (derived from `chain_length`: `'1'`, `'2'`, `'3+'`), duplicate `hop_bin` for backward compatibility, and a placeholder `predicted_correctness` = 0.0.  
  - **Outputs** (conform to `contracts/annotated_questions.schema.yaml`):  
    - `data/processed/annotated_videokr.csv` (all required columns).  
    - `data/processed/annotation_coverage.json` (total, annotated, unresolvable counts).  
  - **Verification**: CSV validates against the schema; a sanity‑check script confirms every row with `status="annotated"` has `chain_length ≥ 1` and that `predicted_correctness` is present (0.0).

- [ ] T105 [S] Perform a pilot‑driven power analysis to determine the minimum per‑bin sample size.  
  - **File**: `code/analysis/power_analysis.py`  
  - **Method**:  
    1. Randomly sample 1 000 annotated records (seed `pilot_sampling`).  
    2. Estimate the observed accuracy difference between low‑hop (1‑2) and high‑hop (3+) bins.  
    3. Use `statsmodels.stats.power.NormalIndPower` with effect size *h* ≈ 0.12, α = 0.05 (Bonferroni‑adjusted for five candidate knots → α_adj = 0.01), and power = 0.80 to compute `min_samples_per_bin`.  
  - **Output**: `data/processed/power_analysis.json` containing `effect_size_h`, `alpha`, `adjusted_alpha`, `power`, `min_samples_per_bin`, and `rounded_n`.  
  - **Verification**: The JSON field `rounded_n` ≥ 100 and matches a unit‑test reproduction of the calculation.

- [ ] T106 [S] Validate that each hop‑bin meets the power‑analysis sample requirement; flag any insufficient bin.  
  - **File**: `code/analysis/validate_bins.py`  
  - **Steps**:  
    1. Load `annotated_videokr.csv` and compute `chain_bin` (`'1'`, `'2'`, `'3+'`).  
    2. Load `power_analysis.json` to obtain `rounded_n`.  
    3. For each bin, compare its record count to `rounded_n`.  
    4. Write a flag file `data/processed/bin_validation.json` listing bins that satisfy the requirement and those that fail.  
    5. If any bin fails, the pipeline records a warning but continues; downstream statistical tests will automatically defer for that bin (as required by FR‑003).  
  - **Verification**: A script confirms that `bin_validation.json` correctly reflects the counts and that the `limit_exceeded` flag is `false` when all bins pass.

- [ ] T107 [S] Compute stratified accuracy per hop‑bin and generate the bin‑mapping file.  
  - **File**: `code/analysis/stratify_accuracy.py`  
  - **Outputs**:  
    - `data/processed/chain_bins.csv` (`question_id`, `hop_bin`).  
    - `data/processed/accuracy_binned.csv` (`hop_bin`, `n`, `accuracy`).  
    - `data/processed/accuracy_binned.png` (bar chart).  
  - **Verification**: The CSV contains exactly three rows (bins) and the accuracies equal the mean of `correctness` within each bin.

- [ ] T108 [S] Produce a continuous scatter plot of raw correctness vs. hop count with LOESS smoothing.  
  - **File**: `code/analysis/visualize_continuous.py`  
  - **Outputs**:  
    - `data/processed/accuracy_vs_hop_raw.csv` (`chain_length`, `correctness`).  
    - `data/processed/accuracy_vs_hop_raw.png`.  
  - **Verification**: PNG is non‑empty; CSV row count matches the number of records in `annotated_videokr.csv`.

- [ ] T109 [S] Detect the “reasoning cliff” using both a permutation change‑point test and a logistic‑regression LRT.  
  - **File**: `code/analysis/detect_threshold.py`  
  - **Procedure**:  
    1. **Null model**: binomial logistic regression of `correctness` on `chain_length` plus covariates (`question_difficulty`, `video_length_seconds`, `answer_type`).  
    2. **Alternative models**: piecewise logistic with a single knot at each candidate *k* ∈ {1, 2, 3, 4, 5}.  
    3. For each knot, compute the likelihood‑ratio statistic against the null model.  
    4. Perform **10 000** label permutations (seed `permutation`) to obtain an empirical null distribution for the maximum LRT statistic.  
    5. Apply Bonferroni correction (α = 0.05 → α_adj = 0.01).  
    6. Select the knot with the smallest corrected p‑value and record significance.  
  - **Outputs**:  
    - `data/processed/threshold_results.json` (conforms to `contracts/threshold_results.schema.yaml`).  
    - `data/processed/threshold_meta.json` (contains `alpha`, `bonferroni_corrected`, `selected_knot`, human‑readable `conclusion`).  
  - **Verification**: JSON validates against the schema; a unit test confirms that the selected knot corresponds to the minimum corrected p‑value.

- [ ] T110 [S] Conduct sensitivity analysis over three explicit binning schemes and assess robustness.  
  - **File**: `code/analysis/sensitivity.py`  
  - **Schemes** (clarified – “initial” = hop count 1):  
    1. **Scheme A**: `'1', '2', '3+'` (default).  
    2. **Scheme B**: `'1', '2', '3', '4+'` (aggregate hop ≥ 4).  
    3. **Scheme C**: `'1', '2', '3', '4', '5+'` (aggregate hop ≥ 5).  
  - **For each scheme**: repeat the full permutation‑test + LRT pipeline from T109.  
  - **Outputs**:  
    - `data/processed/sensitivity_analysis.json` (per‑scheme `selected_knot`, `p_value`, `is_significant`).  
    - `data/processed/stability_metric.json` (`robustness_status` = `"PASS"` if ≥ 2 of 3 schemes yield `p < 0.05` after correction, else `"FAIL"`).  
  - **Verification**: A script recomputes the PASS/FAIL flag from the JSON and asserts consistency.

- [ ] T116 [S] Perform a covariate‑adjusted likelihood‑ratio test to verify that the identified reasoning cliff remains significant after controlling for question difficulty, video length, and answer type.  
  - **File**: `code/analysis/confound_adjusted_lrt.py`  
  - **Steps**:  
    1. Fit the null logistic model (covariates only).  
    2. Fit the piecewise logistic model (selected knot from T109) **including the same covariates**.  
    3. Compute LRT statistic and Bonferroni‑adjusted p‑value; set `is_significant`.  
  - **Output**: `data/processed/confound_adjusted_lrt.json` (matches the schema required by SC‑006).  
  - **Verification**: JSON validates against the dedicated schema; a unit test checks that `is_significant` aligns with the corrected p‑value.

- [ ] T111 [S] Train a text‑only logistic‑regression baseline and an extended model that adds `chain_length`; evaluate improvement via LRT and inject predictions.  
  - **File**: `code/analysis/model_lrt.py`  
  - **Steps**:  
    1. Vectorise `question_text` + `answer_text` with TF‑IDF.  
    2. Fit baseline logistic regression (text features only).  
    3. Fit extended model adding `chain_length` as a continuous predictor.  
    4. Perform LRT between the two models; record statistic, p‑value, and `is_significant`.  
    5. Generate predicted probabilities for every record and **atomically overwrite** `predicted_correctness` in `annotated_videokr.csv`.  
  - **Outputs**: `data/processed/model_lrt_results.json`.  
  - **Verification**: JSON contains `baseline_loglik`, `extended_loglik`, `lrt_statistic`, `p_value`, `is_significant`, `conclusion`; the updated CSV has a non‑null `predicted_correctness` in the range [0, 1] for all rows with `status="annotated"`.

- [ ] T122 [S] Validate the `predicted_correctness` column values are present and lie within [0, 1] for every annotated record.  
  - **File**: `code/analysis/predicted_correctness_check.py`  
  - **Output**: `data/processed/predicted_correctness_check.json` (`all_in_range: true/false`, `missing_count: int`).  
  - **Verification**: The script scans `annotated_videokr.csv` and asserts that every non‑null `predicted_correctness` is between 0.0 and 1.0; fails the task if any violation is found.

- [ ] T112 [S] Record total runtime and peak memory usage for the whole pipeline.  
  - **Files**: `code/utils/memory_tracker.py` (uses `psutil`), `code/main.py` (orchestrator).  
  - **Outputs**:  
    - `data/processed/runtime_log.json` (`total_seconds`, `limit_exceeded` vs 7200 s, `pipeline_success`).  
    - `data/processed/memory_log.json` (`peak_gb`, `limit_exceeded` vs 7 GB).  
  - **Verification**: Both JSON files exist and `limit_exceeded` is `false` on a successful run.

- [ ] T113 [S] Implement the orchestrator that runs all stages in the correct order and handles failures gracefully.  
  - **File**: `code/main.py`  
  - **Workflow**:  
    `fix_download → download_data → ingest_log → annotate_graph → validate_bins → stratify_accuracy → visualize_continuous → detect_threshold → sensitivity → covariate_adjusted_lrt → model_lrt → predicted_correctness_check → runtime/memory logging`.  
  - **Error handling**: Catches `DataUnavailableError`, `MemoryLimitError`, `BinPowerError`; on error writes partial artifacts with `.invalid` suffix and exits non‑zero.  
  - **Verification**: `python code/main.py` completes without error on a fresh runner and produces every artifact listed above.

## Phase 2 – Reproducible results and paper handoff  

- [ ] T114 [S] Generate a fully automated final report that draws exclusively from the JSON artifacts.  
  - **File**: `code/analysis/generate_final_report.py`  
  - **Output**: `data/processed/final_report.md` (methods, results, robustness discussion, runtime/memory compliance, and a “Paper‑Stage Handoff” section listing figure/table filenames).  
  - **Verification**: Every numeric value appearing in the markdown is a verbatim copy of a value from a source JSON file (checked by a regression test).

- [ ] T115 [S] Update the project quick‑start documentation to reflect the new end‑to‑end command and data provenance.  
  - **File**: `specs/001-llmxive-follow-up-extending-videokr-towa/quickstart.md`  
  - **Content**:  
    1. Prerequisite: Python 3.10, `pip install -r code/requirements.txt`.  
    2. Command: `python code/main.py`.  
    3. List of expected output artifacts with brief descriptions.  
    4. Instructions for reproducing the run from a clean `data/processed/` directory.  
  - **Verification**: A clean re‑run (delete `data/processed/*`) followed by the documented command reproduces identical artifact checksums (validated by a test script).

- [ ] T117 [S] (Optional) Provide a CI configuration snippet that enforces the 7200 s runtime and 7 GB memory limits, referencing `runtime_log.json` and `memory_log.json`.  
  - **File**: `.github/workflows/ci.yml` (generated by `code/utils/ci_generator.py`).  
  - **Verification**: CI run fails if either `limit_exceeded` flag is `true`.

## Phase 3 – Additional verification tasks (independent checks)

- [ ] T118 [S] Verify that the original correctness labels are used unchanged.  
  - **File**: `code/analysis/label_integrity_check.py`  
  - **Output**: `data/processed/label_integrity_check.json` (`original_labels_used: true`).  
  - **Verification**: The script cross‑checks the `correctness` column against the raw dataset before any transformation.

- [ ] T119 [S] Confirm that the official VideoKR‑SFT dataset checksum matches the known release checksum.  
  - **File**: `code/ingest/verify_dataset.py`  
  - **Output**: `data/processed/dataset_verification.json` (`checksum_match: true/false`).  
  - **Verification**: The script aborts with a non‑zero exit code if the checksum does not match.

- [ ] T120 [S] Validate that `annotated_videokr.csv` conforms to the updated schema after FR‑013 injection.  
  - **File**: `code/analysis/annotated_schema_check.py`  
  - **Output**: `data/processed/annotated_schema_validation.json` (`schema_valid: true`).  
  - **Verification**: Uses `jsonschema.validate`; the task passes only if the CSV validates against `contracts/annotated_questions.schema.yaml`.

--- 

*All tasks above are ordered to respect data dependencies. Execution of a later task assumes successful completion of its prerequisites.*  