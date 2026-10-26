# Tasks: Semantic Decay Retrieval for LightMem‑Ego

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/evaluation_report.schema.yaml`, original research question.

This research‑implementation plan follows the three‑phase structure required by the platform and satisfies every functional requirement (FR‑001 – FR‑015) and success‑criteria (SC‑001 – SC‑010). All artifacts are written under the project‑owned directories `src/`, `data/`, `figures/`, `paper/`, or `scripts/`.  

---  

## Phase 1 – Setup and First End‑to‑End Analysis  

| Goal | Run a minimal, fully‑real pipeline on a small validation set and produce real result rows under `data/results/`. |
|------|------------------------------------------------------------|

- [ ] **T001** **[US‑1]** Establish project layout, document dependencies, and download the Ego4D dataset (real data, no synthetic fallback).   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1; src/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1; src/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1; src/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1; src/data/preprocess.py exit=1 -->
  - Create the directory tree `src/data/`, `src/retrieval/`, `src/evaluation/`, `src/cli/`, `tests/contract/`, `tests/unit/`.  
  - Add `requirements.txt` with exact versions (e.g., `faiss-cpu==1.7.4`, `datasets>=2.18`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.13`, `scikit-learn>=1.5`, `tqdm>=4.66`, `psutil>=5.9`, `matplotlib>=3.8`).  
  - Write `specs/001-semantic-decay-retrieval/quickstart.md` that documents:  
    1. `pip install -r requirements.txt`  
    2. Download of Ego4D metadata and video‑MAE embeddings from the **verified** HF URL `https://huggingface.co/datasets/ego4d/ego4d`.  
    3. SHA‑256 checksum verification.  
    4. Execution of a small validation run (`python src/cli/run.py --mode validation`).  
  - Implement `src/data/download.py` with a function `download_ego4d(output_dir: Path) -> None` that uses `datasets.load_dataset("ego4d/ego4d", split="train", streaming=False)`, streams each file to `data/raw/`, writes a `CHECKSUMS.txt` file, and **raises** an exception on any failure (no silent fallback).  
  - **Output**: `requirements.txt`, `specs/001-semantic-decay-retrieval/quickstart.md`, `src/data/download.py`, `data/raw/CHECKSUMS.txt`.  
  - **Verification**: Run `python src/data/download.py --output-dir data/raw/` and confirm (a) the expected files appear under `data/raw/`, (b) `CHECKSUMS.txt` contains matching SHA‑256 hashes, and (c) the command exits with status 0.

- [ ] **T002** **[US‑1]** Preprocess the raw Ego4D data into a parquet table of memory nodes and compute the `is_rare` flag.   <!-- FAILED-IN-EXECUTION: src/data/preprocess.py exit=1 -->
  - Implement `src/data/preprocess.py` with `build_memory_nodes_parquet(raw_dir: Path, output_path: Path) -> None`.  
  - The script must:  
    * Load the JSON manifest and embedding files from `data/raw/`.  
    * Extract `node_id`, `timestamp` (ISO‑8601), `event_label`, and the 768‑dimensional `embedding` (float32).  
    * Count occurrences of each `event_label`; set `is_rare = True` when the count ≤ 5 (FR‑012).  
    * Write a parquet file `data/processed/memory_nodes.parquet` matching the schema in `data-model.md`.  
    * Raise a descriptive error if any required field is missing or if an embedding cannot be parsed.  
  - **Output**: `src/data/preprocess.py`, `data/processed/memory_nodes.parquet`.  
  - **Verification**: Execute `python src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet` and check that the parquet contains ≥ 100 rows, all columns are present, and the `is_rare` column contains a mix of `True`/`False`.

- [ ] **T003** **[US‑1]** Build a deterministic FAISS HNSW index and implement the Fixed‑Hierarchy baseline retriever.  
  - Implement `src/data/faiss_builder.py` with `build_faiss_index(parquet_path: Path, output_path: Path) -> None` that:  
    * Loads embeddings from `memory_nodes.parquet`.  
    * Constructs a CPU‑only HNSW index (`faiss.IndexHNSWFlat`) with deterministic parameters (`seed=42`, `M=16`, `ef_construction=200`, `ef_search=50`).  
    * Saves the index to `data/processed/faiss_hnsw_ego4d.index`.  
    * Writes a mapping JSON `faiss_index_mapping.json` (FAISS row → `node_id`).  
  - Implement `src/retrieval/baseline.py` containing class `FixedHierarchyRetriever` that:  
    * Loads the index; on failure raises `RuntimeError("FAISS index load failure: <details>")` (FR‑011).  
    * Routes a query to one of three temporal buckets based on `t` (days since node timestamp): current (≤ 1 day), short‑term (1 < t ≤ 14), long‑term (t > 14).  
    * Provides `retrieve(query_embedding: np.ndarray, query_timestamp: datetime, k: int = 1) -> List[Tuple[node_id, score]]`.  
  - **Output**: `src/data/faiss_builder.py`, `src/retrieval/baseline.py`, `data/processed/faiss_hnsw_ego4d.index`, `data/processed/faiss_index_mapping.json`.  
  - **Verification**: Run the builder script, then instantiate `FixedHierarchyRetriever` and retrieve a sample query; confirm a non‑empty list of node IDs and that a simulated missing index triggers the exact error message.

- [ ] **T004** **[US‑1]** Implement the Semantic‑Decay retriever with strict parameter bounds and error handling.  
  - Implement `src/retrieval/semantic_decay.py` containing class `SemanticDecayRetriever` that:  
    * Accepts `alpha: float = 1.0`, `beta: float = 1.0`, `lam: float` in its constructor (α and β are fixed at 1.0 per the spec).  
    * Enforces `0 < lam < 10`; violations raise `ValueError("Lambda out of bounds: <value>")` (FR‑010, FR‑014).  
    * Loads the same FAISS index as the baseline; on failure raises `RuntimeError("FAISS index load failure: <details>")`.  
    * Computes cosine similarity `sim` between the query and each candidate embedding, computes decay `decay = exp(-lam * t)` where `t` is days since the candidate’s timestamp, and scores `S = alpha * sim + beta * decay`.  
    * Returns the top‑k node IDs and scores via `retrieve`.  
  - Add helper utilities (`cosine_similarity`, `days_since`) in `src/retrieval/utils.py`.  
  - **Output**: `src/retrieval/semantic_decay.py`, `src/retrieval/utils.py`.  
  - **Verification**:  
    * Instantiate with valid params (e.g., `lam=0.5`) and retrieve a sample query – ensure a non‑empty result.  
    * Attempt construction with `lam=15` and confirm the expected `ValueError` is raised with the exact message.

- [ ] **T005** **[US‑1]** Create a small validation set and run an end‑to‑end benchmark on both retrievers.  
  - Implement `src/evaluation/validation.py` with `create_validation_set(parquet_path: Path, num_queries: int = 50, seed: int = 42) -> List[Dict]` that randomly selects `num_queries` memory nodes (fixed seed) and writes them to `data/processed/validation_queries.json`. Each entry contains `query_id`, `query_embedding`, `query_timestamp`, and the ground‑truth `node_id`.  
  - Extend `src/cli/run.py` with a `--mode validation` branch that:  
    * Loads the validation set.  
    * Instantiates `FixedHierarchyRetriever` and `SemanticDecayRetriever` using **fixed** α = 1.0, β = 1.0 and a **placeholder** λ (e.g., `0.5`).  
    * For every query records: Top‑1 hit (bool) for each model, inference latency (ms via `time.perf_counter()`), and CPU user time (`psutil.Process().cpu_times().user`).  
    * Writes per‑query records to `data/results/validation_run.json`.  
  - **Output**: `src/evaluation/validation.py`, updated `src/cli/run.py`, `data/processed/validation_queries.json`, `data/results/validation_run.json`.  
  - **Verification**: Run `python src/cli/run.py --mode validation` and confirm the JSON contains 50 entries, each with the required fields, and that latency values are positive numbers.

---  

## Phase 2 – Complete Study, Optimisation, and Evidence Generation  

| Goal | Run the full benchmark, optimise λ (and α, β remain fixed), compute all metrics, and produce a contract‑compliant report. |
|------|------------------------------------------------------------|

- [ ] **T006** **[US‑1]** Deterministic λ‑only grid‑search for the optimal decay rate (FR‑001, FR‑015).  
  - Extend `src/evaluation/validation.py` with `grid_search_optimal_lambda(parquet_path: Path, validation_set_path: Path, output_dir: Path) -> None`.  
  - Search over `λ ∈ {0.1, 0.2, …, 9.9}` **only** (α and β stay at 1.0).  
  - For each λ, instantiate `SemanticDecayRetriever(alpha=1.0, beta=1.0, lam=λ)`, evaluate Top‑1 accuracy on the **distinct** validation set (the set created by T005, separate from any training data, satisfying Constitution Principle VII), and log `lambda,validation_accuracy` to `data/results/grid_search_log.txt`.  
  - Deterministic tie‑breaker: **select the first λ (in ascending order) that attains the maximal validation accuracy**.  
  - Write the selected λ and its validation accuracy to `data/results/optimal_parameters.json` with keys `optimal_lambda` and `validation_accuracy`.  
  - **Output**: Updated `src/evaluation/validation.py`, `data/results/grid_search_log.txt`, `data/results/optimal_parameters.json`.  
  - **Verification**: After execution, confirm the log has exactly 99 lines, the JSON values respect `0 < optimal_lambda < 10`, and `validation_accuracy` lies in `[0,1]`.

- [ ] **T007** **[US‑1 · US‑2 · US‑3]** Full evaluation on a stratified query set, metric aggregation, and RAM‑usage validation (FR‑003 – FR‑009, FR‑013, FR‑014, FR‑015).  
  - Extend `src/evaluation/metrics.py` with `run_full_evaluation(parquet_path: Path, index_path: Path, optimal_params_path: Path, output_dir: Path) -> None`.  
  - Steps:  
    1. Load `optimal_lambda` from `optimal_parameters.json`.  
    2. Generate a stratified evaluation set of **≥ 200** queries covering three age buckets (1‑3 days, 4‑14 days, > 14 days) using seed 42.  
    3. Identify “rare” events (`is_rare == True`).  
    4. **Power check** – if the rare‑event subset contains < 30 items, abort long‑term accuracy computation, add flag `"Insufficient rare-event data (n < 30): analysis skipped"` to the final report, and continue with short‑term/overall metrics (FR‑009).  
    5. For each query, run both retrievers, recording Top‑1 hit, latency (ms), CPU user time, and peak RSS memory (`psutil.Process().memory_info().rss`).  
    6. Aggregate:  
       * Long‑term Top‑1 accuracy and query count.  
       * Short‑term Top‑1 accuracy and query count.  
       * Overall Top‑1 accuracy.  
       * Latency statistics: `max_ms`, `mean_ms`, `p95_ms` (must satisfy FR‑006).  
       * CPU‑cycle statistics: baseline average, semantic‑decay average, and ratio (must satisfy FR‑013).  
       * Max RAM usage (must be ≤ 7 GB, FR‑008).  
       * Flag short‑term degradation > 5 % (FR‑007).  
    7. Write per‑query details to `data/results/evaluation_queries.json` and aggregated metrics to `data/results/evaluation_metrics.json`.  
  - Update `src/cli/run.py` with a `--mode full-evaluation` option that calls the above function.  
  - **Output**: `src/evaluation/metrics.py`, updated `src/cli/run.py`, `data/results/evaluation_queries.json`, `data/results/evaluation_metrics.json`.  
  - **Verification**: Run `python src/cli/run.py --mode full-evaluation` and confirm:  
    * ≥ 200 query entries exist.  
    * All latency values ≤ 200 ms, RAM ≤ 7 GB, CPU‑cycle ratio ≤ 1.10.  
    * If rare‑event count < 30, the appropriate flag appears.  
    * If short‑term degradation > 5 %, the flag appears.

- [ ] **T008** **[US‑1]** Compute statistical significance with McNemar’s test (FR‑005).  
  - Extend `src/evaluation/metrics.py` with `compute_mcnemar_test(evaluation_queries_path: Path, output_path: Path) -> None`.  
  - Build the 2 × 2 contingency table for baseline vs. semantic‑decay Top‑1 outcomes on the **long‑term** subset (> 14 days).  
  - Use `scipy.stats.chi2_contingency` (Yates’ correction) to obtain `statistic` and `p_value`.  
  - Write `statistic`, `p_value`, and `significant` (`p_value < 0.05`) to `data/results/mcnemar_test.json`.  
  - If the long‑term subset is empty (e.g., due to the power abort), write a flag `"Insufficient long-term data for McNemar test"` and skip the test.  
  - **Output**: Updated `src/evaluation/metrics.py`, `data/results/mcnemar_test.json`.  
  - **Verification**: After a full evaluation, confirm the JSON contains numeric fields within valid ranges, and that `significant` correctly reflects the p‑value; if skipped, the flag is present.

- [ ] **T009** **[US‑1]** Assemble a contract‑compliant evaluation report (FR‑001 – FR‑015, SC‑001 – SC‑010).  
  - Implement `src/evaluation/report.py` with `assemble_report(optimal_params_path: Path, metrics_path: Path, mcnemar_path: Path, output_path: Path) -> None`.  
  - The function must:  
    * Load `optimal_parameters.json`, `evaluation_metrics.json`, and `mcnemar_test.json`.  
    * Construct a JSON object that **exactly matches** `contracts/evaluation_report.schema.yaml`.  
    * Add two supplemental, non‑schema fields:  
      - `baseline_long_term_accuracy` (float) – long‑term Top‑1 accuracy of the Fixed‑Hierarchy baseline.  
      - `improvement_percent` (float) – percentage improvement of the Semantic‑Decay model over the baseline.  
    * Validate the base object with `jsonschema.validate`.  
    * Write the final report to `data/results/evaluation_report.json`.  
  - Add a contract test `tests/contract/test_evaluation_report.py` that loads the generated report, validates it against the schema, and asserts that the supplemental fields are present and correctly computed.  
  - **Output**: `src/evaluation/report.py`, `tests/contract/test_evaluation_report.py`, `data/results/evaluation_report.json`.  
  - **Verification**: Run the report assembly script, then `pytest tests/contract/test_evaluation_report.py`; both must pass.

- [ ] **T010** **[US‑1]** Unit‑test suite for both retrievers (FR‑002, FR‑001).  
  - `tests/unit/test_baseline.py` must verify:  
    * Correct bucket routing based on timestamps.  
    * Successful Top‑1 retrieval with realistic scores in `[0,1]`.  
    * Proper raising of `RuntimeError("FAISS index load failure: <details>")` when the index file is missing or corrupted.  
    * Behaviour with an empty query vector.  
  - `tests/unit/test_semantic_decay.py` must verify:  
    * Enforcement of **λ** bounds (`0 < lam < 10`).  
    * Correct computation of the decay score for a known example (`sim=0.8`, `t=5`, `lam=0.5`, α=1.0, β=1.0).  
    * Proper handling of FAISS load failures with the exact error message.  
    * Score dominance by similarity when `t` is very large.  
    * **New** test that the pipeline aborts with a clear error and logs the message when λ is out of bounds (covers SC‑007).  
  - **Output**: `tests/unit/test_baseline.py`, `tests/unit/test_semantic_decay.py`.  
  - **Verification**: Execute `pytest -q tests/unit/` and ensure all tests pass.

- [ ] **T011** **[US‑2]** Measure and verify peak RAM usage during the full evaluation (FR‑008).  
  - In `src/evaluation/metrics.py`, add a lightweight wrapper that records the peak RSS memory (`psutil.Process().memory_info().rss`) for each query and stores the maximum observed value (in GB) as `max_ram_gb` inside `evaluation_metrics.json`.  
  - Include a verification step that asserts `max_ram_gb <= 7.0`.  
  - **Output**: Updated `src/evaluation/metrics.py`, updated `data/results/evaluation_metrics.json` with `max_ram_gb`.  
  - **Verification**: After `full-evaluation`, inspect the JSON field; the pipeline must abort with an error if the limit is exceeded.

- [ ] **T012** **[US‑1]** Compute and embed the improvement percentage for reporting (FR‑001).  
  - Implement `src/evaluation/improvement.py` that reads baseline and semantic‑decay long‑term accuracies from `evaluation_metrics.json`, computes `baseline_long_term_accuracy` and `improvement_percent = (semantic - baseline) / baseline * 100`, and writes these two fields into `evaluation_report.json` (called from T009).  
  - **Output**: `src/evaluation/improvement.py`.  
  - **Verification**: After report assembly, open `evaluation_report.json` and confirm the two new fields exist and contain plausible numbers (e.g., improvement between –100 % and +100 %).

---  

## Phase 3 – Reproducibility, Visualization, and Paper‑Stage Handoff  

| Goal | Produce narrative, figures, a fully automated pipeline, and a clean hand‑off package for the downstream paper stage. |
|------|------------------------------------------------------------|

- [ ] **T013** **[US‑3]** Write methods and results narratives linked to actual artifacts.  
  - `paper/methods.md` must detail: data acquisition (Ego4D URL, checksum), preprocessing steps, rarity definition, FAISS construction, baseline logic, Semantic‑Decay formula, parameter bounds, deterministic λ‑only grid‑search configuration, evaluation protocol, and edge‑case handling (rare‑event abort, λ bounds, FAISS failures).  
  - `paper/results.md` must summarize: optimal λ and validation accuracy, long‑term Top‑1 accuracies (baseline & Semantic‑Decay), percentage improvement, McNemar p‑value, short‑term accuracy and any degradation flag, overall accuracy, latency statistics (max, mean, p95), CPU‑cycle ratio, max RAM usage, and all flags from the report.  
  - Both files should include direct hyperlinks to the JSON artifacts (`evaluation_report.json`, `evaluation_queries.json`, `grid_search_log.txt`).  
  - **Verification**: Run `scripts/verify_methods_consistency.py` (see T017) to ensure the numeric values in `methods.md` match those in `evaluation_report.json`.

- [ ] **T014** **[US‑2]** Generate summary figures and tables from validated outputs.  
  - Implement `src/evaluation/visualization.py` with functions that:  
    * Plot a side‑by‑side bar chart of long‑term Top‑1 accuracy (baseline vs. Semantic‑Decay) with error bars (±1 std) and annotate the percentage improvement.  
    * Plot latency (ms) versus query age (days) for both models, showing the 200 ms ceiling.  
    * Produce a concise markdown table summarising optimal parameters, validation accuracy, long‑term/short‑term/overall accuracies, latency stats, CPU‑cycle ratio, max RAM, and McNemar significance.  
  - Save PNGs to `figures/long_term_accuracy.png`, `figures/latency_vs_age.png` and the table to `figures/summary_table.txt`. Use `matplotlib` with a clean style (sans‑serif, 10 pt, 300 dpi).  
  - **Verification**: A post‑generation script checks that each PNG exists, has non‑zero size, and width ≥ 400 px; the text table must be non‑empty and contain the required column headers.

- [ ] **T015** **[US‑3]** Automate the full research pipeline in a reproducible shell script.  
  - Create `run_full_pipeline.sh` that sequentially executes:  
    1. `python src/data/download.py --output-dir data/raw/`  
    2. `python src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet`  
    3. `python src/data/faiss_builder.py --memory-nodes data/processed/memory_nodes.parquet --output data/processed/faiss_hnsw_ego4d.index`  
    4. `python src/cli/run.py --mode validation`  
    5. `python src/evaluation/validation.py --grid-search` (runs T006)  
    6. `python src/cli/run.py --mode full-evaluation`  
    7. `python src/evaluation/report.py --optimal-parameters data/results/optimal_parameters.json --evaluation-metrics data/results/evaluation_metrics.json --mcnemar-test data/results/mcnemar_test.json --output data/results/evaluation_report.json`  
    8. `pytest tests/contract/ tests/unit/ -q`  
    9. `python src/evaluation/visualization.py --report data/results/evaluation_report.json --output-dir figures/`  
    10. `echo "Pipeline completed successfully – report at data/results/evaluation_report.json"`  
  - Log all stdout/stderr to `data/results/pipeline_run.log`.  
  - **Verification**: On a clean CI runner, execute `bash run_full_pipeline.sh 2>&1 | tee data/results/pipeline_run.log`; the log must end with the success message and all intermediate artifacts listed above must exist.

- [ ] **T016** **[US‑3]** Document the paper‑stage handoff and archive final artifacts.  
  - Create `paper/HANDOFF.md` that enumerates:  
    * Input data (Ego4D URL, checksum steps).  
    * Code location (`src/`, `scripts/`, entry point `run_full_pipeline.sh`).  
    * Output artifacts (`data/results/evaluation_report.json`, `evaluation_queries.json`, all figures, methods/results narratives).  
    * Reproducibility guarantees (fixed seed 42, exact dependency versions).  
    * Verification artefacts (contract test, unit tests).  
    * Any flags from `evaluation_report.json.flags` (e.g., insufficient rare events, short‑term degradation).  
    * Next steps for the downstream paper pipeline (figure captioning, PDF generation, submission).  
  - Archive the complete research tree (`src/`, `specs/001-semantic-decay-retrieval/`, `paper/`, `data/`, `figures/`, `scripts/`) as part of the handoff.  
  - **Verification**: Manual review of `HANDOFF.md` to ensure all paths are correct and responsibilities are cleanly separated between research and paper stages.

---  

## Dependency Mapping (summary)

| Specification | Satisfied by Task(s) |
|---------------|----------------------|
| FR‑001 – FR‑015 | T001‑T010, T012 |
| SC‑001 – SC‑010 | T007, T008, T009, T011, T014 |
| US‑1 | T001‑T010, T012, T013, T015, T016 |
| US‑2 | T004, T007, T011, T014 |
| US‑3 | T010, T013, T015, T016 |

---  

**Checkpoint**: After completing **T001** through **T016** and confirming all verification steps pass, the pipeline can be rerun via `run_full_pipeline.sh` to produce a validated `evaluation_report.json` and accompanying figures, ready for paper‑stage handoff.  