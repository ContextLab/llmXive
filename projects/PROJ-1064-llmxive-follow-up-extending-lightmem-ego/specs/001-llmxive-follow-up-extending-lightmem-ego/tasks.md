# Tasks: Semantic Decay Retrieval for LightMem-Ego

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/evaluation_report.schema.yaml`, original research question.

This is a research implementation plan. All tasks satisfy the specification (FR-001–FR-015, SC-001–SC-010) and follow the three-phase structure: (1) setup and first end-to-end analysis on real inputs, (2) complete study with validation, (3) reproducible results and paper handoff.

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`.
Each task names its scientific requirement, concrete output, and observable check.
Paths are relative to the project directory. All outputs go under `data/`, `code/`, `figures/`, or `paper/`.

---

## Phase 1: Setup and First End-to-End Analysis

**Goal**: Run an executable analysis on valid, small real inputs early. Establish the existing code layout, validate input provenance, implement the primary computation, and produce real result rows under `data/results/`.

- [ ] T001 [P1] [US-1] **Establish project layout, document dependencies, and validate Ego4D data provenance.**
  - Create the project directory structure under `code/` with subdirectories: `code/src/data/`, `code/src/retrieval/`, `code/src/evaluation/`, `code/src/cli/`, `code/tests/contract/`, `code/tests/unit/`.
  - Create `specs/001-semantic-decay-retrieval/quickstart.md` documenting: (i) how to install dependencies from `requirements.txt` (numpy, pandas, scipy, scikit-learn, faiss-cpu, datasets, tqdm, psutil, matplotlib), (ii) the exact command to download Ego4D metadata and embeddings from the verified HuggingFace URL, (iii) how to run the end-to-end pipeline with a small validation set (50 queries, 60-day window).
  - Implement `code/src/data/download.py` with a function `download_ego4d_metadata(output_dir)` that fetches the Ego4D JSON manifest and video-MAE embeddings from `https://huggingface.co/datasets/` (or equivalent verified source) and stores raw files under `data/raw/`.
  - Compute SHA-256 checksums of downloaded files and log them to `data/raw/CHECKSUMS.txt` for reproducibility (FR-001, Constitution III).
  - **Output**: `code/requirements.txt`, `specs/001-semantic-decay-retrieval/quickstart.md`, `code/src/data/download.py`, `data/raw/CHECKSUMS.txt`.
  - **Verification**: Run `python code/src/data/download.py --output-dir data/raw/` and confirm that files are downloaded, checksums are recorded, and the command completes without errors.

- [ ] T002 [P1] [US-1] **Preprocess Ego4D data into memory nodes and compute semantic distinctness.**
  - Implement `code/src/data/preprocess.py` with a function `build_memory_nodes_parquet(raw_dir, output_path)` that:
    - Reads Ego4D JSON metadata and embeddings from `data/raw/`.
    - Extracts `node_id`, `timestamp` (ISO-8601), `event_label`, and `embedding` (float32, shape (768,)).
    - Computes `is_rare` (boolean): True if event_label frequency ≤ 5 in the corpus (FR-012).
    - Performs semantic clustering via k-means (k=10, random_state=42) on the embeddings to compute within-cluster cohesion for each node.
    - Computes `is_semantically_distinct` (boolean): True if the node's within-cluster cohesion exceeds the corpus median (Phase 0.4, construct validity for "semantically significant").
    - Writes output to `data/processed/memory_nodes.parquet` with all fields as per `data-model.md`.
  - Include error handling: if embeddings are malformed or timestamps are missing, raise a descriptive error (do not fall back to synthetic data).
  - **Output**: `code/src/data/preprocess.py`, `data/processed/memory_nodes.parquet`.
  - **Verification**: Run `python code/src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet` and confirm that the parquet file contains ≥100 rows with all required fields, `is_rare` and `is_semantically_distinct` are populated, and the schema matches `data-model.md`.

- [ ] T003 [P1] [US-1] **Build FAISS HNSW index and implement Fixed Hierarchy baseline retriever.**
  - Implement `code/src/data/faiss_builder.py` with a function `build_faiss_index(memory_nodes_parquet, output_path)` that:
    - Reads embeddings from `data/processed/memory_nodes.parquet`.
    - Builds a FAISS HNSW index deterministically (seed=42, M=16, ef_construction=200, ef_search=50).
    - Saves the index to `data/processed/faiss_hnsw_ego4d.index`.
    - Stores a mapping of FAISS row IDs to node IDs in `data/processed/faiss_index_mapping.json` for result reconstruction.
  - Implement `code/src/retrieval/baseline.py` with a class `FixedHierarchyRetriever` that:
    - Routes queries to "current" (≤1 day), "short-term" (1–14 days), or "long-term" (>14 days) buckets based on explicit timestamp thresholds.
    - Loads the FAISS index; if index load fails, raises a runtime exception with the message "FAISS index load failure: <details>" (FR-011).
    - Implements `retrieve(query_embedding, timestamp, k=1)` returning the top-k node IDs and their similarity scores.
  - **Output**: `code/src/data/faiss_builder.py`, `code/src/retrieval/baseline.py`, `data/processed/faiss_hnsw_ego4d.index`, `data/processed/faiss_index_mapping.json`.
  - **Verification**: Run `python code/src/data/faiss_builder.py --memory-nodes data/processed/memory_nodes.parquet --output data/processed/faiss_hnsw_ego4d.index` and confirm the index file exists and is loadable. Then instantiate `FixedHierarchyRetriever`, call `retrieve()` with a sample query, and confirm it returns valid node IDs without errors.

- [ ] T004 [P1] [US-1] **Implement Semantic Decay retriever with parameter bounds and error handling.**
  - Implement `code/src/retrieval/semantic_decay.py` with a class `SemanticDecayRetriever` that:
    - Scores memory nodes using `S = α·sim(q, m) + β·exp(-λ·t)` where `sim` is cosine similarity and `t` is time-since-event in days (FR-001).
    - Takes learnable parameters `alpha`, `beta`, `lambda` as constructor arguments.
    - Enforces bounds: `0 < α < 1`, `0 < β < 1`, `0 < λ < 10` (FR-010, FR-014); raise a validation error if any parameter is out of bounds.
    - Implements `retrieve(query_embedding, timestamp, k=1)` returning the top-k node IDs and their semantic decay scores.
    - Loads the FAISS index and handles load failures with the exact error message from FR-011.
  - Implement `code/src/retrieval/utils.py` with helper functions for cosine similarity and exponential decay calculation.
  - **Output**: `code/src/retrieval/semantic_decay.py`, `code/src/retrieval/utils.py`.
  - **Verification**: Instantiate `SemanticDecayRetriever` with valid parameters (α=0.6, β=0.3, λ=0.5), call `retrieve()` with a sample query, and confirm it returns valid results. Then attempt instantiation with out-of-bounds parameters (e.g., λ=15) and confirm that a validation error is raised with a clear message.

- [ ] T005 [P1] [US-1] **Create a small validation set and run end-to-end retrieval on both models.**
  - Implement `code/src/evaluation/grid_search.py` with a function `create_validation_set(memory_nodes_parquet, num_queries=50, random_seed=42)` that:
    - Samples 50 representative queries uniformly from the 60-day corpus (using fixed seed 42 for reproducibility).
    - For each query, selects a random memory node and uses its embedding as the query vector, recording the true node ID as the ground truth.
    - Returns a list of (query_embedding, ground_truth_node_id, query_timestamp) tuples.
    - Stores the validation set to `data/processed/validation_queries.json` for reproducibility.
  - Implement `code/src/cli/run.py` with a function `run_end_to_end_validation(memory_nodes_parquet, faiss_index, output_dir)` that:
    - Loads the validation set from `data/processed/validation_queries.json`.
    - Instantiates both `FixedHierarchyRetriever` and `SemanticDecayRetriever` (with placeholder parameters α=0.6, β=0.3, λ=0.5).
    - For each validation query, calls both retrievers and records: Top-1 hit (boolean), inference latency (ms via `time.perf_counter()`), and CPU time (via `psutil.Process().cpu_times().user`).
    - Writes per-query results to `data/results/validation_run.json` with fields: `query_id`, `ground_truth_node_id`, `baseline_top1_hit`, `semantic_decay_top1_hit`, `baseline_latency_ms`, `semantic_decay_latency_ms`, `baseline_cpu_seconds`, `semantic_decay_cpu_seconds`.
  - **Output**: `code/src/evaluation/grid_search.py`, `code/src/cli/run.py`, `data/processed/validation_queries.json`, `data/results/validation_run.json`.
  - **Verification**: Run `python code/src/cli/run.py --memory-nodes data/processed/memory_nodes.parquet --faiss-index data/processed/faiss_hnsw_ego4d.index --output-dir data/results/` and confirm that `data/results/validation_run.json` contains ≥50 query results with all required fields populated (no null values). Spot-check 3–5 results for correctness: Top-1 hits should be boolean, latencies should be positive numbers, and CPU times should be non-decreasing.

**Checkpoint**: The documented quickstart command executes successfully on a small validation set (50 queries) and produces real result rows in `data/results/validation_run.json`. Numerical outputs are populated and can be inspected.

---

## Phase 2: Complete the Study and Validate Its Evidence

**Goal**: Run the complete specified parameter and data domain, implement all required correctness and sensitivity checks, and generate validated artifacts.

- [ ] T006 [P2] [US-1] **Implement deterministic joint grid search for (α, β, λ) optimization.**
  - Extend `code/src/evaluation/grid_search.py` with a function `grid_search_optimal_parameters(memory_nodes_parquet, validation_queries, output_dir)` that:
    - Iterates over the parameter grid: α ∈ {0.5, 0.6, 0.7}, β ∈ {0.2, 0.3, 0.4}, λ ∈ {0.1, 0.2, 0.3, ..., 9.9} (27 × 99 = 2,673 combinations).
    - For each combination, instantiates `SemanticDecayRetriever` and evaluates Top-1 accuracy on the validation set (from T005).
    - Selects the first triple (α*, β*, λ*) achieving the maximal validation Top-1 accuracy (deterministic tie-breaking: ascending order by α, then β, then λ) (FR-001, FR-015).
    - Logs the grid search progress to `data/results/grid_search_log.txt` with columns: `alpha`, `beta`, `lambda`, `validation_accuracy`.
    - Stores the optimal parameters and their validation accuracy to `data/results/optimal_parameters.json` with fields: `optimal_alpha`, `optimal_beta`, `optimal_lambda`, `validation_accuracy`.
  - **Output**: Updated `code/src/evaluation/grid_search.py`, `data/results/grid_search_log.txt`, `data/results/optimal_parameters.json`.
  - **Verification**: Run `python -c "from code.src.evaluation.grid_search import grid_search_optimal_parameters; grid_search_optimal_parameters(...)"` and confirm that `data/results/optimal_parameters.json` contains three float fields in (0, 1), (0, 1), and (0, 10) respectively, and that `validation_accuracy` is between 0 and 1. Spot-check the grid search log to ensure all 2,673 combinations were evaluated and the selected parameters are indeed the first to achieve the maximum accuracy.

- [ ] T007 [P2] [US-1] [US-2] [US-3] **Run full evaluation on representative query set and compute all required metrics.**
  - Extend `code/src/evaluation/metrics.py` with functions to:
    - Load the optimal parameters from `data/results/optimal_parameters.json`.
    - Create a representative evaluation set of ≥200 queries spanning 1–30 days (stratified by age bucket: 1–3 days, 4–14 days, >14 days) using fixed seed 42.
    - Identify "rare" events: `is_rare AND is_semantically_distinct` from the memory nodes (Phase 0.4, refined definition).
    - If the rare-event subset contains <50 events, log the flag "Insufficient rare-event data (n < 50): analysis skipped" and abort long-term accuracy analysis (FR-009, revised threshold).
    - For each evaluation query, run both `FixedHierarchyRetriever` and `SemanticDecayRetriever` (with optimal parameters), recording:
      - Top-1 hit (boolean), latency (ms), CPU time (seconds).
      - Age bucket (short-term: 1–3 days, long-term: >14 days).
    - Compute aggregated metrics:
      - Long-term accuracy (Top-1) for events >14 days (SC-001).
      - Short-term accuracy (Top-1) for events 1–3 days (SC-004).
      - Overall accuracy across all queries.
      - Latency: max, mean, p95 percentile (FR-006, SC-003).
      - CPU cycles: baseline average, semantic decay average, ratio ≤1.10 (FR-013, SC-009).
      - McNemar's test statistic and p-value for long-term queries (FR-005, SC-002, SC-010).
    - Flag any short-term degradation >5% (FR-007, SC-004).
    - Write all per-query results to `data/results/evaluation_queries.json` and aggregated metrics to `data/results/evaluation_metrics.json`.
  - Extend `code/src/cli/run.py` with a function `run_full_evaluation(memory_nodes_parquet, faiss_index, optimal_parameters, output_dir)` that orchestrates the above.
  - **Output**: `code/src/evaluation/metrics.py`, updated `code/src/cli/run.py`, `data/results/evaluation_queries.json`, `data/results/evaluation_metrics.json`.
  - **Verification**: Run `python code/src/cli/run.py --mode full-evaluation --memory-nodes data/processed/memory_nodes.parquet --faiss-index data/processed/faiss_hnsw_ego4d.index --optimal-parameters data/results/optimal_parameters.json --output-dir data/results/` and confirm that:
    - `data/results/evaluation_queries.json` contains ≥200 query results with all required fields.
    - `data/results/evaluation_metrics.json` contains all required metric keys (long_term.accuracy_top1, short_term.accuracy_top1, latency.max_ms, latency.mean_ms, latency.p95_ms, cpu_cycles.baseline_avg, cpu_cycles.semantic_decay_avg, cpu_cycles.ratio, mcnemar_test.p_value, flags).
    - All latencies are ≤200 ms (FR-006, SC-003).
    - CPU cycle ratio is ≤1.10 (FR-013, SC-009).
    - If short-term degradation >5%, the flags array contains the degradation warning (FR-007, SC-004).

- [ ] T008 [P2] [US-1] **Implement statistical significance testing via McNemar's test and validate edge cases.**
  - Extend `code/src/evaluation/metrics.py` with a function `mcnemar_test_long_term(evaluation_queries, output_path)` that:
    - Filters evaluation queries to the long-term subset (>14 days).
    - Constructs a 2×2 contingency table: rows = baseline Top-1 hit (yes/no), columns = semantic decay Top-1 hit (yes/no).
    - Computes McNemar's test statistic and p-value using `scipy.stats.chi2_contingency` or equivalent.
    - Determines significance: `p_value < 0.05` (SC-002, SC-010).
    - Writes results to `data/results/mcnemar_test.json` with fields: `statistic`, `p_value`, `significant` (boolean).
  - Implement edge-case handling in `code/src/evaluation/metrics.py`:
    - If rare-event subset is empty or <50 events, set flag "Insufficient rare-event data (n < X): analysis skipped" and skip long-term analysis (FR-009, SC-006).
    - If λ is out of bounds (0, 10) during grid search or inference, raise a validation error "Lambda out of bounds: <value>" (FR-010, FR-014, SC-007).
    - If FAISS index fails to load, catch the exception and re-raise with the exact message "FAISS index load failure: <details>" (FR-011, SC-008).
  - **Output**: Updated `code/src/evaluation/metrics.py`, `data/results/mcnemar_test.json`.
  - **Verification**: Run the full evaluation and confirm that `data/results/mcnemar_test.json` contains `statistic` (float ≥0), `p_value` (float in [0, 1]), and `significant` (boolean). Manually verify the contingency table by spot-checking a few query results. If the rare-event subset is small, confirm that the "Insufficient rare-event data" flag is present in `data/results/evaluation_metrics.json`.

- [ ] T009 [P2] **Assemble evaluation report conforming to the contract schema.**
  - Implement `code/src/evaluation/report.py` with a function `assemble_evaluation_report(optimal_parameters, evaluation_metrics, mcnemar_test, output_path)` that:
    - Reads results from `data/results/optimal_parameters.json`, `data/results/evaluation_metrics.json`, and `data/results/mcnemar_test.json`.
    - Constructs a JSON object conforming to `contracts/evaluation_report.schema.yaml` with all required fields:
      - `optimal_alpha`, `optimal_beta`, `optimal_lambda` (from grid search).
      - `validation_accuracy` (from grid search).
      - `long_term` (accuracy_top1, num_queries).
      - `short_term` (accuracy_top1, num_queries).
      - `overall` (accuracy_top1).
      - `latency` (max_ms, mean_ms, p95_ms).
      - `cpu_cycles` (baseline_avg, semantic_decay_avg, ratio).
      - `mcnemar_test` (statistic, p_value, significant).
      - `flags` (array of warning strings).
    - Validates the report against the schema using `jsonschema`.
    - Writes the report to `data/results/evaluation_report.json`.
  - Implement a contract validation test in `code/tests/contract/test_evaluation_report.py` that:
    - Loads the generated `evaluation_report.json`.
    - Validates it against `contracts/evaluation_report.schema.yaml` using `jsonschema.validate()`.
    - Checks that all numeric fields are within their specified ranges (e.g., accuracy ∈ [0, 1], latency ≥0, ratio ≥0).
    - Asserts that `mcnemar_test.significant == (mcnemar_test.p_value < 0.05)`.
  - **Output**: `code/src/evaluation/report.py`, `code/tests/contract/test_evaluation_report.py`, `data/results/evaluation_report.json`.
  - **Verification**: Run `python code/src/evaluation/report.py --optimal-parameters data/results/optimal_parameters.json --evaluation-metrics data/results/evaluation_metrics.json --mcnemar-test data/results/mcnemar_test.json --output data/results/evaluation_report.json` and confirm the report is generated. Then run `pytest code/tests/contract/test_evaluation_report.py` and confirm all validation checks pass without errors.

- [ ] T010 [P2] **Implement unit tests for baseline and semantic decay retrievers.**
  - Implement `code/tests/unit/test_baseline.py` with tests for `FixedHierarchyRetriever`:
    - Test that queries are correctly routed to "current," "short-term," and "long-term" buckets based on timestamp thresholds.
    - Test that Top-1 results are valid node IDs and similarity scores are in [0, 1].
    - Test that FAISS index load failure raises the exact error message from FR-011.
    - Test that the retriever handles edge cases (empty query, out-of-range timestamp).
  - Implement `code/tests/unit/test_semantic_decay.py` with tests for `SemanticDecayRetriever`:
    - Test that parameter bounds are enforced (α, β ∈ (0, 1), λ ∈ (0, 10)); out-of-bounds parameters raise a validation error (FR-010, FR-014).
    - Test that the semantic decay score formula `S = α·sim + β·exp(-λ·t)` is computed correctly for known inputs.
    - Test that Top-1 results are valid node IDs and scores are non-negative.
    - Test that FAISS index load failure raises the exact error message from FR-011.
    - Test that the retriever handles edge cases (zero decay rate, very large time delta).
  - **Output**: `code/tests/unit/test_baseline.py`, `code/tests/unit/test_semantic_decay.py`.
  - **Verification**: Run `pytest code/tests/unit/test_baseline.py code/tests/unit/test_semantic_decay.py -v` and confirm all tests pass without errors.

---

## Phase 3: Reproducible Results and Paper Handoff

**Goal**: Write a concise methods/results account, re-run the documented workflow from declared inputs, confirm all tests and artifact checks, and prepare the paper-stage handoff.

- [ ] T011 [P3] **Write methods and results narrative linked to actual output artifacts.**
  - Create `paper/methods.md` documenting:
    - Data acquisition: Ego4D source URL, download procedure, checksum verification.
    - Preprocessing: Memory node construction, semantic clustering, rarity definition (≤5 occurrences), semantic distinctness computation.
    - FAISS index construction: HNSW parameters (M=16, ef_construction=200, ef_search=50), deterministic seed (42).
    - Fixed Hierarchy baseline: Routing logic, timestamp thresholds (current ≤1 day, short-term 1–14 days, long-term >14 days).
    - Semantic Decay model: Scoring formula `S = α·sim(q, m) + β·exp(-λ·t)`, parameter bounds (0 < α, β < 1; 0 < λ < 10).
    - Grid search: Parameter space (α ∈ {0.5, 0.6, 0.7}, β ∈ {0.2, 0.3, 0.4}, λ ∈ {0.1, ..., 9.9}), validation set size (50 queries), deterministic selection (first achieving maximum accuracy).
    - Evaluation protocol: Query stratification (1–3 days, 4–14 days, >14 days), metrics (Top-1 accuracy, latency, CPU cycles, McNemar's test).
    - Edge cases: Insufficient rare-event handling (n < 50), λ bounds enforcement, FAISS index error handling.
  - Create `paper/results.md` documenting:
    - Optimal parameters: α*, β*, λ* and validation accuracy.
    - Long-term accuracy (>14 days) for both models, improvement percentage, McNemar's test p-value and significance.
    - Short-term accuracy (1–3 days) for both models, degradation percentage (if any), flag if >5%.
    - Overall accuracy across all queries.
    - Inference latency: max, mean, p95 percentile; confirmation that all queries ≤200 ms.
    - CPU cycles: baseline average, semantic decay average, ratio; confirmation that ratio ≤1.10.
    - Flags: Any warnings (insufficient data, degradation, out-of-bounds parameters).
    - Links to actual output files: `data/results/evaluation_report.json`, `data/results/evaluation_queries.json`, `data/results/grid_search_log.txt`.
  - **Output**: `paper/methods.md`, `paper/results.md`.
  - **Verification**: Review the markdown files for completeness and accuracy. Spot-check 3–5 specific claims (e.g., "optimal λ = X") against the actual values in `data/results/evaluation_report.json`. Confirm all links to output files are correct and files exist.

- [ ] T012 [P3] **Generate summary figures and tables from validated outputs.**
  - Implement `code/src/evaluation/visualization.py` with functions to:
    - Generate a bar chart comparing long-term accuracy (>14 days) for baseline vs. semantic decay, with error bars (±1 std) and the improvement percentage labeled.
    - Generate a line plot of latency (ms) vs. time-since-event (days) for both models, showing that all queries ≤200 ms.
    - Generate a table summarizing: optimal parameters, validation accuracy, long-term accuracy, short-term accuracy, latency stats, CPU cycle ratio, McNemar's test result.
    - Save figures to `figures/long_term_accuracy.png`, `figures/latency_vs_age.png` and the table to `figures/summary_table.txt`.
  - Use `matplotlib` with consistent styling (sans-serif font, 10pt labels, high DPI for publication).
  - **Output**: `code/src/evaluation/visualization.py`, `figures/long_term_accuracy.png`, `figures/latency_vs_age.png`, `figures/summary_table.txt`.
  - **Verification**: Run `python code/src/evaluation/visualization.py --evaluation-report data/results/evaluation_report.json --output-dir figures/` and confirm that all three output files are generated, figures are readable PNG files with proper labels and legends, and the table contains all required metrics.

- [ ] T013 [P3] **Re-run the documented workflow end-to-end and verify reproducibility.**
  - Create a shell script `code/run_full_pipeline.sh` that:
    - Clones/downloads the Ego4D data from the verified URL (as documented in `specs/001-semantic-decay-retrieval/quickstart.md`).
    - Runs all preprocessing steps: `python code/src/data/download.py`, `python code/src/data/preprocess.py`, `python code/src/data/faiss_builder.py`.
    - Runs the full evaluation: `python code/src/cli/run.py --mode full-evaluation ...`.
    - Runs all tests: `pytest code/tests/contract/ code/tests/unit/ -v`.
    - Generates figures and tables: `python code/src/evaluation/visualization.py ...`.
    - Outputs a summary log to `data/results/pipeline_run.log`.
  - Execute the script on a clean directory and confirm that:
    - All intermediate artifacts are generated (parquet files, FAISS index, JSON results).
    - All tests pass without errors.
    - The final `evaluation_report.json` is generated and conforms to the schema.
    - All figures and tables are produced.
    - The pipeline completes within the CI resource limits (2 vCPU, 7 GB RAM, 6 h).
  - **Output**: `code/run_full_pipeline.sh`, `data/results/pipeline_run.log`.
  - **Verification**: Run `bash code/run_full_pipeline.sh 2>&1 | tee data/results/pipeline_run.log` and confirm that the log shows all steps completed successfully (no errors or failures). Spot-check 3–5 key outputs (parquet schema, FAISS index size, evaluation report fields) to ensure they match expectations from previous tasks.

- [ ] T014 [P3] **Document paper-stage handoff and archive final artifacts.**
  - Create `paper/HANDOFF.md` documenting:
    - **Input data**: Ego4D source, download URL, checksum verification procedure.
    - **Code location**: All source code under `code/src/`, tests under `code/tests/`, entry point `code/run_full_pipeline.sh`.
    - **Output artifacts**: `data/results/evaluation_report.json` (primary result), `data/results/evaluation_queries.json` (per-query details), `figures/` (summary visualizations).
    - **Reproducibility**: Fixed random seed (42) used throughout; all external dependencies pinned in `requirements.txt`.
    - **Verification**: Contract validation test in `code/tests/contract/test_evaluation_report.py`; unit tests in `code/tests/unit/`.
    - **Limitations and flags**: List any warnings from `evaluation_report.json.flags` (e.g., insufficient rare-event data, short-term degradation).
    - **Next steps for paper pipeline**: The evaluation report and figures are ready for inclusion in a manuscript; no additional data processing or analysis is needed. The paper pipeline should handle figure captioning, table formatting, PDF compilation, and submission workflows.
  - Archive all code, tests, and documentation under `code/`, `specs/001-semantic-decay-retrieval/`, and `paper/`.
  - **Output**: `paper/HANDOFF.md`.
  - **Verification**: Review the handoff document for completeness. Confirm that all required outputs are listed and their file paths are correct. Verify that the document clearly separates research-stage artifacts (data, code, tests) from paper-stage responsibilities (PDF, submission, peer review).

---

## Dependencies and Requirement Coverage

| Specification Requirement | Task(s) | Command/Artifact | Verification |
|---------------------------|---------|-----------------|--------------|
| **FR-001**: Semantic Decay formula `S = α·sim(q,m) + β·exp(-λ·t)` with grid search | T004, T006 | `code/src/retrieval/semantic_decay.py`, `code/src/evaluation/grid_search.py` | Instantiate retriever with optimal params; inspect `data/results/optimal_parameters.json` |
| **FR-002**: Fixed Hierarchy baseline | T003 | `code/src/retrieval/baseline.py` | Run baseline retriever; confirm routing logic by bucket |
| **FR-003**: Full evaluation on substantial query set | T007 | `code/src/cli/run.py`, `data/results/evaluation_queries.json` | ≥200 queries; all age buckets represented |
| **FR-004**: Measure latency and CPU cycles | T007 | `code/src/evaluation/metrics.py`, `data/results/evaluation_metrics.json` | Latency in ms, CPU time in seconds, both per-query and aggregated |
| **FR-005**: McNemar's test for statistical significance | T008 | `code/src/evaluation/metrics.py`, `data/results/mcnemar_test.json` | p-value < 0.05 for success; recorded in report |
| **FR-006**: Inference latency ≤ 200 ms for all queries | T007 | `data/results/evaluation_metrics.json.latency.max_ms` | max_ms ≤ 200 |
| **FR-007**: Short-term accuracy degradation ≤ 5% | T007 | `data/results/evaluation_metrics.json`, flags | Flag if degradation > 5% |
| **FR-008**: CPU-only execution, ≤ 7 GB RAM | T001, T007 | `code/requirements.txt` (no CUDA), pipeline runs on CI | No CUDA imports; memory monitoring via psutil |
| **FR-009**: Rare-event subset < 30 → abort long-term analysis | T007 | `code/src/evaluation/metrics.py`, flags | Flag "Insufficient rare-event data" if n < 50 |
| **FR-010**: λ bounds (0, 10) enforcement during grid search | T006 | `code/src/evaluation/grid_search.py` | Grid search only iterates λ ∈ {0.1, ..., 9.9}; validation error if out-of-bounds |
| **FR-011**: FAISS index load failure → exact error message | T003, T007 | `code/src/retrieval/baseline.py`, `code/src/retrieval/semantic_decay.py` | Try/catch with "FAISS index load failure: <details>" |
| **FR-012**: Rare events defined as ≤ 5 occurrences | T002 | `code/src/data/preprocess.py`, `data/processed/memory_nodes.parquet` | is_rare field computed from event_label frequency |
| **FR-013**: CPU cycles ratio ≤ 1.10 | T007 | `data/results/evaluation_metrics.json.cpu_cycles.ratio` | ratio ≤ 1.10; recorded in report |
| **FR-014**: λ bounds enforced during training and inference | T004, T006 | `code/src/retrieval/semantic_decay.py` | Constructor raises error if λ ∉ (0, 10) |
| **FR-015**: Deterministic grid search with fixed seed and ascending order | T006 | `code/src/evaluation/grid_search.py` | Seed=42; enumerate in ascending order; select first achieving max accuracy |
| **SC-001**: Improvement in long-term accuracy measured | T007, T009 | `data/results/evaluation_report.json.long_term` | accuracy_top1 for both models; improvement % computed |
| **SC-002**: McNemar's test p < 0.05 | T008, T009 | `data/results/evaluation_report.json.mcnemar_test.p_value` | p_value in [0, 1]; significant = (p_value < 0.05) |
| **SC-003**: Latency ≤ 200 ms; max and p95 recorded | T007, T009 | `data/results/evaluation_report.json.latency` | max_ms ≤ 200; mean_ms, p95_ms present |
| **SC-004**: Short-term degradation ≤ 5%; flag if exceeded | T007, T009 | `data/results/evaluation_report.json.short_term`, flags | accuracy_top1 for both models; degradation % computed; flag if > 5% |
| **SC-005**: Memory ≤ 7 GB | T001, T007 | Pipeline execution on CI | Monitor via psutil; confirm no OOM errors |
| **SC-006**: Rare-event subset < 30 → flag in report | T007, T009 | `data/results/evaluation_report.json.flags` | "Insufficient rare-event data: analysis skipped" if n < 50 |
| **SC-007**: λ bounds (0, 10) enforced; violations logged and terminate | T006, T008 | `code/src/evaluation/grid_search.py`, logs | Grid search rejects λ ∉ (0, 10); error logged and pipeline stops |
| **SC-008**: FAISS load failure → exact error message | T003, T008 | `code/src/retrieval/baseline.py`, `code/src/retrieval/semantic_decay.py` | "FAISS index load failure: <details>" on failure |
| **SC-009**: CPU cycles ratio ≤ 1.10; both averages and ratio in report | T007, T009 | `data/results/evaluation_report.json.cpu_cycles` | baseline_avg, semantic_decay_avg, ratio all present; ratio ≤ 1.10 |
| **SC-010**: McNemar's p-value reported; success if p < 0.05 | T008, T009 | `data/results/evaluation_report.json.mcnemar_test` | statistic, p_value, significant (bool) all present |

---

## Revision Behavior

Preserve working artifacts and already verified requirements. Carry forward their identities and status; do not erase completed work to make the list look shorter. Use the precise failing command or verifier diagnosis to repair affected tasks. Consolidate redundant pending tasks without dropping their acceptance criteria. A narrow implementation failure is not a reason to rebuild the project skeleton, rewrite unrelated modules, or expand the study into an application framework.

**All tasks in this plan are new and unchecked.** Completed tasks will be marked with `[x]` and their identities preserved across revision rounds.
