# Tasks: Semantic Decay Retrieval for LightMem‑Ego

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/evaluation_report.schema.yaml`, original research question.

This is a research implementation plan. All tasks satisfy the specification (FR‑001 – FR‑015, SC‑001 – SC‑010) and follow the three‑phase structure: (1) setup and first end‑to‑end analysis, (2) complete study with validation, (3) reproducible results and paper handoff.

## Task format and paths

Use `- [ ] T### [USx?] description with exact artifact paths`.  
Each task names its scientific requirement, concrete output, and observable check.  
Paths are relative to the project directory. All outputs go under `data/`, `src/`, `figures/`, or `paper/`.

---

## Phase 1: Setup and First End‑to‑End Analysis

**Goal**: Run an executable analysis on valid, small real inputs early. Establish the existing code layout, validate input provenance, implement the primary computation, and produce real result rows under `data/results/`.

- [ ] T001 [US-1] **Establish project layout, document dependencies, and validate Ego4D data provenance.**   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - Create the project directory structure under `src/` with sub‑directories: `src/data/`, `src/retrieval/`, `src/evaluation/`, `src/cli/`, `tests/contract/`, `tests/unit/`.  
  - Add a top‑level `requirements.txt` listing the exact versions needed (e.g., `faiss-cpu==1.7.4`, `datasets>=2.18`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.13`, `scikit-learn>=1.5`, `tqdm>=4.66`, `psutil>=5.9`, `matplotlib>=3.8`).  
  - Create `specs/001-semantic-decay-retrieval/quickstart.md` documenting:  
    1. Installation via `pip install -r requirements.txt`.  
    2. Download of the Ego4D metadata and video‑MAE embeddings from the verified HF hub URL `https://huggingface.co/datasets/ego4d/ego4d`.  
    3. Checksum verification (SHA‑256) of the downloaded files.  
    4. Execution of the small validation pipeline (`python src/cli/run.py --mode validation`).  
  - Implement `src/data/download.py` with a function `download_ego4d(output_dir: Path) -> None` that:  
    * Uses `datasets.load_dataset("ego4d/ego4d", split="train", streaming=False)` to fetch the JSON manifest and embeddings.  
    * Saves raw files under `data/raw/`.  
    * Writes SHA‑256 checksums to `data/raw/CHECKSUMS.txt`.  
    * Raises an exception if the download fails (no silent fallback).  
  - **Output**: `requirements.txt`, `specs/001-semantic-decay-retrieval/quickstart.md`, `src/data/download.py`, `data/raw/CHECKSUMS.txt`.  
  - **Verification**: Run `python src/data/download.py --output-dir data/raw/` and confirm that (a) the expected files appear, (b) the checksum file contains matching hashes, and (c) the command exits with status 0.

- [ ] T002 [US-1] **Preprocess Ego4D data into memory‑node parquet and compute rarity flag.**  
  - Implement `src/data/preprocess.py` with a function `build_memory_nodes_parquet(raw_dir: Path, output_path: Path) -> None` that:  
    * Reads the Ego4D JSON manifest and embedding files from `data/raw/`.  
    * Extracts `node_id`, `timestamp` (ISO‑8601), `event_label`, and `embedding` (float32, shape (768,)).  
    * Computes `is_rare` = True if the frequency of `event_label` ≤ 5 (FR‑012).  
    * Writes a parquet file `data/processed/memory_nodes.parquet` with the schema defined in `data-model.md`.  
    * Raises a descriptive error if any required field is missing or embeddings are malformed (no synthetic fallback).  
  - **Output**: `src/data/preprocess.py`, `data/processed/memory_nodes.parquet`.  
  - **Verification**: Execute `python src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet` and check that the parquet contains ≥ 100 rows, all columns are present, and the `is_rare` flag is populated correctly.

- [ ] T003 [US-1] **Build FAISS HNSW index and implement Fixed‑Hierarchy baseline retriever.**  
  - Implement `src/data/faiss_builder.py` with `build_faiss_index(memory_nodes_parquet: Path, output_path: Path) -> None` that:  
    * Loads embeddings from `data/processed/memory_nodes.parquet`.  
    * Constructs a FAISS HNSW index on CPU with deterministic parameters (`seed=42`, `M=16`, `ef_construction=200`, `ef_search=50`).  
    * Saves the index to `data/processed/faiss_hnsw_ego4d.index`.  
    * Writes a JSON mapping `faiss_index_mapping.json` (FAISS row → `node_id`).  
  - Implement `src/retrieval/baseline.py` containing class `FixedHierarchyRetriever` that:  
    * Loads the FAISS index; if loading fails, raises `RuntimeError("FAISS index load failure: <details>")` (FR‑011).  
    * Routes queries to buckets based on timestamp `t` (days since event):  
      - **current**: `t ≤ 1` day,  
      - **short‑term**: `1 < t ≤ 14` days,  
      - **long‑term**: `t > 14` days.  
    * Provides `retrieve(query_embedding: np.ndarray, query_timestamp: datetime, k: int = 1) -> List[Tuple[node_id, score]]`.  
  - **Output**: `src/data/faiss_builder.py`, `src/retrieval/baseline.py`, `data/processed/faiss_hnsw_ego4d.index`, `data/processed/faiss_index_mapping.json`.  
  - **Verification**: Run the builder script and then instantiate `FixedHierarchyRetriever` to retrieve a sample query; ensure a valid node ID list is returned and that a simulated load failure produces the exact error message.

- [ ] T004 [US-1] **Implement Semantic‑Decay retriever with strict parameter bounds and error handling.**  
  - Implement `src/retrieval/semantic_decay.py` with class `SemanticDecayRetriever` that:  
    * Accepts `alpha: float`, `beta: float`, `lam: float` in the constructor.  
    * Enforces `0 < alpha < 1`, `0 < beta < 1`, and `0 < lam < 10`; violation raises `ValueError("Lambda out of bounds: <value>")` (FR‑010, FR‑014).  
    * Loads the same FAISS index as the baseline; on failure raises `RuntimeError("FAISS index load failure: <details>")`.  
    * Computes similarity `sim = cosine(query, node_embedding)` and decay `decay = np.exp(-lam * t)` where `t` is days since the node’s timestamp.  
    * Scores each candidate with `S = alpha * sim + beta * decay`.  
    * Returns the top‑k node IDs and scores via `retrieve`.  
  - Add helper functions in `src/retrieval/utils.py` for cosine similarity and exponential decay.  
  - **Output**: `src/retrieval/semantic_decay.py`, `src/retrieval/utils.py`.  
  - **Verification**: Instantiate with valid parameters (e.g., `alpha=0.6, beta=0.3, lam=0.5`) and retrieve a sample query – confirm non‑empty results. Attempt construction with `lam=15` and verify that the expected `ValueError` is raised with the correct message.

- [ ] T005 [US-1] **Create a small validation set and run an end‑to‑end benchmark on both models.**  
  - Implement `src/evaluation/validation.py` with `create_validation_set(memory_nodes_parquet: Path, num_queries: int = 50, seed: int = 42) -> List[Dict]` that:  
    * Randomly selects `num_queries` memory nodes (fixed seed 42) and uses each node’s embedding as a query vector.  
    * Records the ground‑truth `node_id` and the query timestamp (the node’s own timestamp).  
    * Saves the set to `data/processed/validation_queries.json`.  
  - Extend `src/cli/run.py` with a `run_validation` mode that:  
    * Loads the validation set.  
    * Instantiates `FixedHierarchyRetriever` and `SemanticDecayRetriever` with placeholder parameters (`alpha=0.6, beta=0.3, lam=0.5`).  
    * For each query, records: Top‑1 hit (bool) for each model, inference latency (`time.perf_counter()`), and CPU time (`psutil.Process().cpu_times().user`).  
    * Writes per‑query records to `data/results/validation_run.json`.  
  - **Output**: `src/evaluation/validation.py`, updated `src/cli/run.py`, `data/processed/validation_queries.json`, `data/results/validation_run.json`.  
  - **Verification**: Execute `python src/cli/run.py --mode validation` and confirm that `validation_run.json` contains 50 entries with all required fields populated and that latencies are positive numbers.

**Checkpoint**: The quick‑start command documented in `quickstart.md` runs successfully on the 50‑query validation set and produces real rows in `data/results/validation_run.json`.

---

## Phase 2: Complete the Study and Validate Its Evidence

**Goal**: Run the full evaluation on the complete query set, optimise hyper‑parameters, compute all required metrics, and generate a contract‑compliant report.

- [ ] T006 [US-1] **Deterministic joint grid‑search for (α, β, λ) optimisation.**  
  - Extend `src/evaluation/validation.py` with `grid_search_optimal_parameters(memory_nodes_parquet: Path, validation_set_path: Path, output_dir: Path) -> None` that:  
    * Iterates over the grid `α ∈ {0.5,0.6,0.7}`, `β ∈ {0.2,0.3,0.4}`, `λ ∈ {0.1,0.2,…,9.9}` (27 × 99 = 2 673 combos).  
    * For each combo, builds a `SemanticDecayRetriever`, evaluates Top‑1 accuracy on the validation set, and logs `alpha,beta,lambda,validation_accuracy` to `data/results/grid_search_log.txt`.  
    * Uses the deterministic tie‑breaker: **first** triple (ascending α, then β, then λ) that attains the maximal validation accuracy (FR‑015).  
    * Writes the selected triple and its accuracy to `data/results/optimal_parameters.json` with fields `optimal_alpha`, `optimal_beta`, `optimal_lambda`, `validation_accuracy`.  
  - **Output**: Updated `src/evaluation/validation.py`, `data/results/grid_search_log.txt`, `data/results/optimal_parameters.json`.  
  - **Verification**: Run the grid‑search script and confirm that the log contains exactly 2 673 lines, that the JSON file contains numbers respecting the bounds (`alpha,beta ∈ (0,1)`, `lambda ∈ (0,10)`), and that `validation_accuracy` lies in `[0,1]`.

- [ ] T007 [US-1] [US-2] [US-3] **Full evaluation on a representative query set and computation of all metrics, including RAM usage.**  
  - Extend `src/evaluation/metrics.py` with a function `run_full_evaluation(memory_nodes_parquet: Path, faiss_index_path: Path, optimal_params_path: Path, output_dir: Path) -> None` that:  
    1. Loads the optimal `(α,β,λ)` from `optimal_parameters.json`.  
    2. Generates a stratified evaluation set of **≥ 200** queries covering three age buckets (1‑3 days, 4‑14 days, > 14 days) using fixed seed 42.  
    3. Identifies **rare** events as `is_rare` **only** (FR‑012).  
    4. **If the rare‑event subset contains fewer than 30 events**, abort long‑term accuracy computation, add the flag `"Insufficient rare-event data (n < 30): analysis skipped"` to the final report, and continue with short‑term/overall metrics (FR‑009).  
    5. For each query, runs both retrievers, recording Top‑1 hit, latency (ms), CPU time (seconds), and RAM usage (peak RSS via `psutil`).  
    6. Aggregates:  
       - Long‑term Top‑1 accuracy (> 14 days) and query count.  
       - Short‑term Top‑1 accuracy (1‑3 days) and query count.  
       - Overall Top‑1 accuracy.  
       - Latency statistics: max, mean, 95th‑percentile (must satisfy FR‑006).  
       - CPU‑cycle statistics: baseline average, semantic‑decay average, and ratio (must satisfy FR‑013).  
       - Max RAM usage (must satisfy FR‑008).  
       - Flag short‑term degradation > 5 % (FR‑007).  
    7. Stores per‑query results to `data/results/evaluation_queries.json` and aggregated metrics to `data/results/evaluation_metrics.json`.  
  - Update `src/cli/run.py` with a `--mode full-evaluation` entry that calls the above function.  
  - **Output**: `src/evaluation/metrics.py`, updated `src/cli/run.py`, `data/results/evaluation_queries.json`, `data/results/evaluation_metrics.json`.  
  - **Verification**: Execute `python src/cli/run.py --mode full-evaluation` and confirm:  
    * ≥ 200 query entries exist.  
    * All latency values ≤ 200 ms.  
    * CPU‑cycle ratio ≤ 1.10.  
    * Max RAM usage ≤ 7 GB.  
    * If short‑term degradation > 5 % a corresponding warning appears in `evaluation_metrics.json["flags"]`.  
    * If rare‑event count < 30, the flag `"Insufficient rare-event data (n < 30): analysis skipped"` is present.

- [ ] T008 [US-1] **Statistical significance testing via McNemar’s test and edge‑case handling.**  
  - Extend `src/evaluation/metrics.py` with `compute_mcnemar_test(evaluation_queries_path: Path, output_path: Path) -> None` that:  
    * Filters the long‑term subset (> 14 days).  
    * Builds the 2 × 2 contingency table of baseline vs. semantic‑decay Top‑1 outcomes.  
    * Uses `scipy.stats.chi2_contingency` (with Yates’ correction) to compute the chi‑square statistic and p‑value.  
    * Writes `statistic`, `p_value`, and `significant` (`p_value < 0.05`) to `data/results/mcnemar_test.json`.  
  - Ensure that if the long‑term subset is empty (e.g., because of the < 30 rare‑event abort) the function writes a flag `"Insufficient long-term data for McNemar test"` and skips the test.  
  - **Output**: Updated `src/evaluation/metrics.py`, `data/results/mcnemar_test.json`.  
  - **Verification**: After a full evaluation, run the McNemar utility (invoked automatically by the full‑evaluation pipeline) and check that `mcnemar_test.json` contains numeric `statistic` and `p_value` in `[0,1]`, and that `significant` correctly reflects `p_value < 0.05`. If the test is skipped, confirm the appropriate flag appears.

- [ ] T009 [US-1] **Assemble a contract‑compliant evaluation report including baseline accuracy and improvement.**  
  - Implement `src/evaluation/report.py` with `assemble_report(optimal_params_path, metrics_path, mcnemar_path, output_path) -> None` that:  
    * Reads `optimal_parameters.json`, `evaluation_metrics.json`, and `mcnemar_test.json`.  
    * Constructs a JSON object matching `contracts/evaluation_report.schema.yaml` **and** adds two supplemental fields:  
      - `baseline_long_term_accuracy` (float) – the long‑term accuracy of the Fixed Hierarchy baseline.  
      - `improvement_percent` (float) – `(semantic_decay_accuracy - baseline_accuracy) / baseline_accuracy * 100`.  
    * Validates the base object with `jsonschema.validate`.  
    * Writes the report to `data/results/evaluation_report.json`.  
  - Add a contract test `tests/contract/test_evaluation_report.py` that loads the generated report and validates it against the schema, asserting that numeric ranges are respected, that the supplemental fields are present and correctly computed, and that `mcnemar_test.significant` matches the p‑value condition.  
  - **Output**: `src/evaluation/report.py`, `tests/contract/test_evaluation_report.py`, `data/results/evaluation_report.json`.  
  - **Verification**: Run the report assembly script and then `pytest tests/contract/test_evaluation_report.py`; both must succeed without errors.

- [ ] T010 [US-1] **Unit tests for both retrievers.**  
  - Create `tests/unit/test_baseline.py` covering:  
    * Correct bucket routing based on timestamps.  
    * Valid Top‑1 results and similarity scores in `[0,1]`.  
    * Proper raising of `RuntimeError("FAISS index load failure: <details>")` when the index file is missing or corrupted.  
    * Edge cases such as an empty query vector.  
  - Create `tests/unit/test_semantic_decay.py` covering:  
    * Enforcement of parameter bounds (α, β ∈ (0,1); λ ∈ (0,10)).  
    * Correct computation of the decay score for a known input (e.g., `sim=0.8`, `t=5`, `α=0.6`, `β=0.3`, `λ=0.5`).  
    * Proper handling of FAISS load failures with the exact error message.  
    * Behaviour when `t` is very large (score should be dominated by the similarity term).  
  - **Output**: `tests/unit/test_baseline.py`, `tests/unit/test_semantic_decay.py`.  
  - **Verification**: Execute `pytest tests/unit/test_baseline.py tests/unit/test_semantic_decay.py -q`; all tests must pass.

- [ ] T015 [US-2] **Measure and verify RAM usage during full evaluation.**  
  - Implement a lightweight wrapper in `src/evaluation/metrics.py` that records peak RSS memory (via `psutil.Process().memory_info().rss`) for each query and stores the maximum observed value in `evaluation_metrics.json` under the key `max_ram_gb`.  
  - Add verification that `max_ram_gb <= 7.0`.  
  - **Output**: Updated `src/evaluation/metrics.py`, updated `data/results/evaluation_metrics.json` with `max_ram_gb`.  
  - **Verification**: After running full evaluation, inspect `evaluation_metrics.json["max_ram_gb"]` and ensure it does not exceed 7.0.

- [ ] T016 [US-1] **Compute improvement percentage for reporting.**  
  - Add a small utility `src/evaluation/improvement.py` that reads baseline and semantic‑decay long‑term accuracies from `evaluation_metrics.json` and writes `baseline_long_term_accuracy` and `improvement_percent` into `evaluation_report.json` (called from T009).  
  - **Output**: `src/evaluation/improvement.py`.  
  - **Verification**: After report assembly, confirm the two new fields are present and correctly calculated.

- [ ] T017 [US-3] **Automated verification of methods narrative consistency.**  
  - Add script `scripts/verify_methods_consistency.py` that parses `paper/methods.md`, extracts the reported optimal α, β, λ values, and compares them against `evaluation_report.json`. It exits with status 0 on match, non‑zero otherwise.  
  - Update T011 verification to invoke this script.  
  - **Output**: `scripts/verify_methods_consistency.py`.  
  - **Verification**: Run the script; it must succeed when the numbers agree.

---

## Phase 3: Reproducible Results and Paper Handoff

**Goal**: Write a concise methods/results narrative linked to actual artifacts, generate figures/tables, re‑run the entire pipeline for reproducibility, and hand off the final artifacts to the paper‑stage pipeline.

- [ ] T011 [US-3] **Write methods and results narrative linked to actual output artifacts.**  
  - Create `paper/methods.md` that details:  
    * Data acquisition (Ego4D URL, download steps, checksum verification).  
    * Preprocessing (memory‑node construction, rarity definition).  
    * FAISS index construction (deterministic HNSW parameters).  
    * Fixed‑Hierarchy baseline logic.  
    * Semantic‑Decay model formula and parameter bounds.  
    * Grid‑search configuration (parameter grid, deterministic tie‑breaker).  
    * Evaluation protocol (query stratification, metrics, statistical test).  
    * Edge‑case handling (rare‑event abort, λ bounds, FAISS failures).  
  - Create `paper/results.md` summarising:  
    * Optimal `(α*, β*, λ*)` and validation accuracy.  
    * Long‑term Top‑1 accuracy for both models, % improvement, and McNemar p‑value.  
    * Short‑term accuracy and any degradation flag.  
    * Overall accuracy, latency statistics (max, mean, p95), CPU‑cycle ratio, and max RAM usage.  
    * All flags recorded in the report.  
    * Direct links to `data/results/evaluation_report.json`, `evaluation_queries.json`, and `grid_search_log.txt`.  
  - **Output**: `paper/methods.md`, `paper/results.md`.  
  - **Verification**: Run `scripts/verify_methods_consistency.py` to ensure numeric statements match the JSON report; manually cross‑check at least three quantitative statements.

- [ ] T012 [US-2] **Generate summary figures and tables from validated outputs.**  
  - Implement `src/evaluation/visualization.py` with functions to:  
    * Plot a side‑by‑side bar chart of long‑term Top‑1 accuracy (baseline vs. semantic‑decay) with error bars (±1 std) and annotate the % improvement.  
    * Plot latency (ms) versus age (days) for both models, showing the 200 ms ceiling.  
    * Produce a concise text table summarising optimal parameters, validation accuracy, long‑term/short‑term/overall accuracies, latency stats, CPU‑cycle ratio, RAM usage, and McNemar significance.  
    * Save PNGs to `figures/long_term_accuracy.png`, `figures/latency_vs_age.png` and the table to `figures/summary_table.txt`.  
  - Use `matplotlib` with a clean style (sans‑serif, 10 pt fonts, 300 dpi).  
  - **Verification**: After generation, a script checks that each PNG exists, has size > 0 bytes, and dimensions ≥ 400 px in width; the text table must be non‑empty and contain the required column headers.  
  - **Output**: `src/evaluation/visualization.py`, `figures/long_term_accuracy.png`, `figures/latency_vs_age.png`, `figures/summary_table.txt`.

- [ ] T013 [US-3] **Re‑run the documented full pipeline end‑to‑end and verify reproducibility.**  
  - Write a shell script `run_full_pipeline.sh` that performs, in order:  
    1. `python src/data/download.py --output-dir data/raw/`  
    2. `python src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet`  
    3. `python src/data/faiss_builder.py --memory-nodes data/processed/memory_nodes.parquet --output data/processed/faiss_hnsw_ego4d.index`  
    4. `python src/cli/run.py --mode validation`  
    5. `python src/evaluation/validation.py --grid-search`  
    6. `python src/cli/run.py --mode full-evaluation`  
    7. `python src/evaluation/report.py --optimal-parameters data/results/optimal_parameters.json --evaluation-metrics data/results/evaluation_metrics.json --mcnemar-test data/results/mcnemar_test.json --output data/results/evaluation_report.json`  
    8. `pytest tests/contract/ tests/unit/ -q`  
    9. `python src/evaluation/visualization.py --report data/results/evaluation_report.json --output-dir figures/`  
    10. Echo a summary line with the path to `evaluation_report.json`.  
  - The script logs progress and any errors to `data/results/pipeline_run.log`.  
  - **Verification**: On a clean CI runner, execute `bash run_full_pipeline.sh 2>&1 | tee data/results/pipeline_run.log`. The log must end with “Pipeline completed successfully” and all intermediate artifacts must exist. Spot‑check that `evaluation_report.json` validates and that the figures are present.

- [ ] T014 [US-3] **Document paper‑stage handoff and archive final artifacts.**  
  - Create `paper/HANDOFF.md` that lists:  
    * **Input data**: Ego4D source URL, checksum verification steps.  
    * **Code location**: All source under `src/`, tests under `tests/`, entry point `run_full_pipeline.sh`.  
    * **Output artifacts**: `data/results/evaluation_report.json` (primary result), `data/results/evaluation_queries.json` (per‑query details), `figures/` (visualisations), `paper/methods.md` & `paper/results.md`.  
    * **Reproducibility**: Fixed random seed 42 throughout; exact dependency versions in `requirements.txt`.  
    * **Verification**: Contract test (`test_evaluation_report.py`) and unit tests (`test_baseline.py`, `test_semantic_decay.py`).  
    * **Limitations & flags**: Any warnings from `evaluation_report.json.flags` (e.g., insufficient rare events, short‑term degradation, RAM usage).  
    * **Next steps for the paper pipeline**: The report and figures are ready for inclusion in a manuscript; the paper‑stage will handle captioning, table formatting, PDF generation, and submission.  
  - Archive the entire research artefact tree (`src/`, `specs/001-semantic-decay-retrieval/`, `paper/`, `data/`, `figures/`) as part of the handoff.  
  - **Output**: `paper/HANDOFF.md`.  
  - **Verification**: Review the handoff document to ensure all paths are correct and that it clearly separates research‑stage artefacts from paper‑stage responsibilities.
