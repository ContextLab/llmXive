# Tasks: Video Reasoning Threshold Analysis

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, prior task artifacts, reviewer feedback.  
The list below follows the canonical checklist format. Checked boxes (`[X]`) indicate tasks that have already been verified and are retained unchanged. Unchecked boxes (`[ ]`) are pending or have been reopened for correction.

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Establish a reproducible pipeline on a small real input and produce the first set of processed artifacts.

- [X] T101 [P] Establish project configuration, constants, and directory paths.  
  - **Files**: `code/utils/config.py`, `code/ingest/checksum.py`  
  - **Verification**: `python -c "import code.utils.config as cfg; assert cfg.SEEDS['pilot_sampling'] == 42"` passes; `python code/ingest/checksum.py` runs without error and creates `data/raw/checksums.json`.

- [X] T102 [P] [US1] Implement deterministic entity‑linking **without any embedding fallback**.  
  - **File**: `code/utils/entity_linker.py`  
  - **Behaviour**:  
    1. Normalise strings (lower‑case, strip punctuation).  
    2. Attempt **exact match** to a node name in the knowledge‑graph.  
    3. If no exact match, apply **Levenshtein distance ≤ 2** as the only fuzzy option.  
    4. Return `entity_node_id` and a confidence flag; **never** call embedding models.  
  - **Tests**: `tests/unit/test_entity_linker.py` covering exact‑match, Levenshtein fallback, and failure cases. All pytest tests must pass.  
  - **Output**: The function `link_dataframe(df, graph_nodes)` is importable from `code.utils.entity_linker`.

- [ ] T103 [S] [US1] Implement robust data‑download script for the open‑access TVQA dataset (substitute for the proprietary VideoKR‑SFT).   <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest/download_data.py exit=1 -->
  - **File**: `code/ingest/download_data.py`  
  - **Behaviour**:  
    1. Use `datasets.load_dataset("tvqa", split="train", streaming=True)` to fetch the QA split and `datasets.load_dataset("tvqa", split="train", streaming=False)` for the accompanying metadata.  
    2. Download the bundled knowledge‑graph JSON (`data/raw/knowledge_graph.json`) via `huggingface_hub.hf_hub_download` from the verified repo `llmxive/videoqa-kg`.  
    3. Abort loudly with a custom `DataUnavailableError` if any fetch fails; **no synthetic fallback**.  
    4. Compute SHA‑256 checksums for every downloaded file and write `data/raw/checksums.json`.  
  - **Verification**: Running `python code/ingest/download_data.py` creates the `data/raw/` directory, populates `tvqa_train.csv`, `metadata/video_lengths.csv`, and `knowledge_graph.json`, and produces a non‑empty `checksums.json`. The script exits with status 0 on success and non‑zero on failure.

- [ ] T104 [S] Annotate the raw TVQA records with structural hop counts, required covariates, **and a placeholder `predicted_correctness` column** (default 0.0).  
  - **File**: `code/ingest/annotate_graph.py`  
  - **Steps**:  
    1. Stream the raw TVQA CSV (or JSONL) using `pandas.read_csv(chunksize=10_000)` to stay within the 7 GB RAM limit.  
    2. For each record, invoke `entity_linker.link_dataframe` to obtain node IDs for the question and answer entities.  
    3. Compute the shortest‑path hop count (`chain_length`) via BFS on the graph loaded by `code/utils/graph_utils.py`.  
    4. Extract covariates `question_difficulty` (from `difficulty_score`), `video_length_seconds` (from `metadata/video_lengths.csv`), and `answer_type` (derived from the answer format field).  
    5. Assign `status` = `"valid"` when both entities are linked, otherwise `"mapping_failure"` and set `chain_length = -1`.  
    6. Add column `predicted_correctness` initialized to `0.0` for all rows (will be overwritten later).  
  - **Outputs** (conforming to `contracts/annotated_questions.schema.yaml`):  
    - `data/processed/annotated_videokr.csv` (columns exactly as required).  
    - `data/processed/annotation_coverage.json` (total, annotated, unresolvable counts).  
  - **Verification**: CSV validates against the schema; a sanity‑check script confirms that every row with `status="valid"` has `chain_length ≥ 1` and that `predicted_correctness` is non‑null.

- [ ] T105 [S] Perform a pilot‑driven power analysis to determine the minimum per‑bin sample size.  
  - **File**: `code/analysis/power_analysis.py`  
  - **Method**:  
    1. Randomly sample 1 000 annotated records (seed `pilot_sampling`).  
    2. Estimate the observed accuracy difference between low‑hop (1‑2) and high‑hop (3+) bins.  
    3. Use `statsmodels.stats.power.NormalIndPower` with effect size *h* ≈ 0.12, α = 0.01 (Bonferroni‑adjusted for five knots), and power = 0.80 to compute `min_samples_per_bin`.  
  - **Output**: `data/processed/power_analysis.json` (contains `effect_size_h`, `alpha`, `adjusted_alpha`, `power`, `min_samples_per_bin`, `rounded_n`).  
  - **Verification**: The JSON file contains the field `rounded_n` ≥ 50 and matches the calculation reproduced by a unit test.

- [ ] T106 [S] Ensure each hop‑bin meets the power‑analysis sample requirement via stratified oversampling.  
  - **File**: `code/analysis/oversample_bins.py`  
  - **Steps**:  
    1. Load `annotated_videokr.csv`.  
    2. Derive `chain_bin` (`'1'`, `'2'`, `'3+'`) from `chain_length`.  
    3. For any bin with count < `rounded_n` (from `power_analysis.json`), perform stratified oversampling with replacement (seed `oversampling`) until the threshold is reached.  
    4. Write the balanced dataset back to `data/processed/annotated_videokr.csv` (atomic write).  
    5. Emit `data/processed/sampling_log.json` documenting pilot size, bins oversampled, and random seeds used.  
  - **Verification**: After execution, a script verifies that each bin count ≥ `rounded_n` and that `sampling_log.json` records the correct numbers.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T107 [S] Compute stratified accuracy per hop‑bin and generate bin‑mapping file.  
  - **File**: `code/analysis/stratify_accuracy.py`  
  - **Outputs**:  
    - `data/processed/chain_bins.csv` (`question_id`, `hop_bin`).  
    - `data/processed/accuracy_binned.csv` (`hop_bin`, `n`, `accuracy`).  
    - `data/processed/accuracy_binned.png` (bar chart).  
  - **Verification**: The CSV has exactly three rows (bins) and the accuracies recompute to the mean of `correctness` in the annotated CSV.

- [ ] T108 [S] Produce a continuous scatter plot of raw correctness vs. hop count with LOESS smoothing.  
  - **File**: `code/analysis/visualize_continuous.py`  
  - **Outputs**:  
    - `data/processed/accuracy_vs_hop_raw.csv` (`chain_length`, `correctness`).  
    - `data/processed/accuracy_vs_hop_raw.png`.  
  - **Verification**: PNG file is non‑empty; CSV rows equal the number of records in `annotated_videokr.csv`.

- [ ] T109 [S] Detect the “reasoning cliff” using both a permutation change‑point test and a logistic‑regression LRT.  
  - **File**: `code/analysis/detect_threshold.py`  
  - **Procedure**:  
    1. Null model: binomial logistic regression of `correctness` on `chain_length` plus covariates (`question_difficulty`, `video_length_seconds`, `answer_type`).  
    2. Alternative models: piecewise logistic with a single knot at each candidate *k* ∈ {1,2,3,4,5}.  
    3. Compute likelihood‑ratio statistic for each knot; record the maximum across knots for each of **500** label permutations (seed `permutation`).  
    4. Apply Bonferroni correction (α = 0.05 → α_adj = 0.01).  
    5. Select the knot with the smallest corrected p‑value.  
  - **Outputs**:  
    - `data/processed/threshold_results.json` (conforms to `contracts/threshold_results.schema.yaml`).  
    - `data/processed/threshold_meta.json` (contains `alpha`, `bonferroni_corrected`, `selected_knot`, human‑readable `conclusion`).  
  - **Verification**: JSON validates against the schema; a unit test confirms that the selected knot matches the one with the lowest corrected p‑value.

- [ ] T110 [S] Conduct sensitivity analysis over three alternative binning schemes and assess robustness.  
  - **File**: `code/analysis/sensitivity.py`  
  - **Schemes**:  
    1. `[1,2,3+]`  
    2. `[1,2,3,4+]`  
    3. `[1,2,3,4,5+]`  
  - **For each scheme**: repeat the full permutation‑test + LRT pipeline from T109.  
  - **Outputs**:  
    - `data/processed/sensitivity_analysis.json` (per‑scheme `selected_knot`, `p_value`, `is_significant`).  
    - `data/processed/stability_metric.json` (`robustness_status` = `"PASS"` if ≥ 2 of 3 schemes yield `p < 0.05` after correction, else `"FAIL"`).  
  - **Verification**: A script recomputes the PASS/FAIL flag from the JSON and asserts consistency.

- [ ] T111 [S] Train a text‑only logistic‑regression baseline and an extended model that adds `chain_length`; evaluate improvement via LRT **and inject predictions**.  
  - **File**: `code/analysis/model_lrt.py`  
  - **Steps**:  
    1. Vectorise `question_text` + `answer_text` with TF‑IDF.  
    2. Fit baseline logistic regression (no hop information).  
    3. Fit extended model adding `chain_length` as a continuous predictor.  
    4. Perform LRT between the two models; record statistic, p‑value, and conclusion.  
    5. Generate predicted probabilities for every record and write them to the `predicted_correctness` column of `annotated_videokr.csv` (atomic overwrite).  
  - **Outputs**: `data/processed/model_lrt_results.json`.  
  - **Verification**: The JSON contains fields `baseline_loglik`, `extended_loglik`, `lrt_statistic`, `p_value`, `is_significant`, `conclusion`; the updated CSV contains a non‑null `predicted_correctness` for all rows with `status="valid"`.

- [ ] T112 [S] Record total runtime and peak memory usage for the whole pipeline.  
  - **Files**: `code/utils/memory_tracker.py` (uses `tracemalloc`/`psutil`), `code/main.py` (orchestrator).  
  - **Outputs**:  
    - `data/processed/runtime_log.json` (`total_seconds`, `limit_exceeded` vs 7200 s, `pipeline_success`).  
    - `data/processed/memory_log.json` (`peak_gb`, `limit_exceeded` vs 7 GB).  
  - **Verification**: Both JSON files exist; `limit_exceeded` is `false` on a successful run.

- [ ] T113 [S] Implement the orchestrator that runs all stages in the correct order and handles failures gracefully.  
  - **File**: `code/main.py`  
  - **Workflow**: `download_data → annotate_graph → oversample_bins → stratify_accuracy → detect_threshold → visualize_continuous → sensitivity → model_lrt → runtime/memory logging`.  
  - **Error handling**: Catches `DataUnavailableError`, `MemoryLimitError`, `BinPowerError`; on error writes partial artifacts with `.invalid` suffix and exits non‑zero.  
  - **Verification**: `python code/main.py` completes without error on a fresh runner and produces every artifact listed above.

- [ ] T116 [S] Perform a covariate‑adjusted likelihood‑ratio test to verify that the identified reasoning cliff remains significant after controlling for question difficulty, video length, and answer type, and write the result to `confound_adjusted_lrt.json`.  
  - **File**: `code/analysis/confound_adjusted_lrt.py`  
  - **Steps**:  
    1. Fit the null logistic model (as in T109) with covariates only.  
    2. Fit the piecewise logistic model (with the selected knot from T109) **including the same covariates**.  
    3. Compute the LRT statistic and p‑value, apply Bonferroni correction, and set `is_significant`.  
  - **Output**: `data/processed/confound_adjusted_lrt.json` matching the schema required by SC‑006.  
  - **Verification**: JSON validates against a dedicated schema (implicitly required) and a unit test checks that `is_significant` aligns with the corrected p‑value.

## Phase 3 – Reproducible results and paper handoff  

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
  - **Verification**: CI run fails if either limit flag is `true`.
