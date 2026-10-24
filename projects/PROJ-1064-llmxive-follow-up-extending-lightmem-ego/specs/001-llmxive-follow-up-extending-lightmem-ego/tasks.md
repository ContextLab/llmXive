# Tasks: Semantic Decay Retrieval for LightMem‑Ego

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/evaluation_report.schema.yaml`, original research question.

This is a research implementation plan. All tasks satisfy the specification (FR‑001 – FR‑015, SC‑001 – SC‑010) and follow the three‑phase structure: (1) setup and first end‑to‑end analysis, (2) complete study with validation, (3) reproducible results and paper handoff.

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`.  
Each task names its scientific requirement, concrete output, and observable check.  
Paths are relative to the project directory. All outputs go under `data/`, `code/`, `figures/`, or `paper/`.

---

## Phase 1: Setup and First End‑to‑End Analysis

**Goal**: Run an executable analysis on valid, small real inputs early. Establish the existing code layout, validate input provenance, implement the primary computation, and produce real result rows under `data/results/`.

- [ ] T001 [P1] [US-1] **Establish project layout, document dependencies, and validate Ego4D data provenance.**  
  - Create the project directory structure under `code/` with subdirectories: `code/src/data/`, `code/src/retrieval/`, `code/src/evaluation/`, `code/src/cli/`, `code/tests/contract/`, `code/tests/unit/`.  
  - Add `code/requirements.txt` listing the exact versions needed (e.g., `faiss-cpu==1.7.4`, `datasets>=2.18`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.13`, `scikit-learn>=1.5`, `tqdm>=4.66`, `psutil>=5.9`, `matplotlib>=3.8`).  
  - Create `specs/001-semantic-decay-retrieval/quickstart.md` documenting:  
    1. Installation via `pip install -r code/requirements.txt`.  
    2. Download of the Ego4D metadata and video‑MAE embeddings from the verified HF hub URL `https://huggingface.co/datasets/ego4d/ego4d`.  
    3. Checksum verification (SHA‑256) of the downloaded files.  
    4. Execution of the small validation pipeline (`python code/src/cli/run.py --mode validation`).  
  - Implement `code/src/data/download.py` with a function `download_ego4d(output_dir: Path) -> None` that:  
    * Uses `datasets.load_dataset("ego4d/ego4d", split="train", streaming=False)` to fetch the JSON manifest and embeddings.  
    * Saves raw files under `data/raw/`.  
    * Writes SHA‑256 checksums to `data/raw/CHECKSUMS.txt`.  
    * Raises an exception if the download fails (no silent fallback).  
  - **Output**: `code/requirements.txt`, `specs/001-semantic-decay-retrieval/quickstart.md`, `code/src/data/download.py`, `data/raw/CHECKSUMS.txt`.  
  - **Verification**: Run `python code/src/data/download.py --output-dir data/raw/` and confirm that (a) the expected files appear, (b) the checksum file contains matching hashes, and (c) the command exits with status 0.

- [ ] T002 [P1] [US-1] **Preprocess Ego4D data into memory‑node parquet and compute semantic distinctness.**  
  - Implement `code/src/data/preprocess.py` with a function `build_memory_nodes_parquet(raw_dir: Path, output_path: Path) -> None` that:  
    * Reads the Ego4D JSON manifest and embedding files from `data/raw/`.  
    * Extracts `node_id`, `timestamp` (ISO‑8601), `event_label`, and `embedding` (float32, shape (768,)).  
    * Computes `is_rare` = True if the frequency of `event_label` ≤ 5 (FR‑012).  
    * Performs k‑means clustering (`k=10`, `random_state=42`) on all embeddings, computes each node’s within‑cluster cohesion, and sets `is_semantically_distinct` = True if the cohesion exceeds the corpus median (Phase 0.4).  
    * Writes a parquet file `data/processed/memory_nodes.parquet` with the schema defined in `data-model.md`.  
    * Raises a descriptive error if any required field is missing or embeddings are malformed (no synthetic fallback).  
  - **Output**: `code/src/data/preprocess.py`, `data/processed/memory_nodes.parquet`.  
  - **Verification**: Execute `python code/src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet` and check that the parquet contains ≥ 100 rows, all columns are present, and both boolean flags are populated.

- [ ] T003 [P1] [US-1] **Build FAISS HNSW index and implement Fixed‑Hierarchy baseline retriever.**  
  - Implement `code/src/data/faiss_builder.py` with `build_faiss_index(memory_nodes_parquet: Path, output_path: Path) -> None` that:  
    * Loads embeddings from `data/processed/memory_nodes.parquet`.  
    * Constructs a FAISS HNSW index on CPU with deterministic parameters (`seed=42`, `M=16`, `ef_construction=200`, `ef_search=50`).  
    * Saves the index to `data/processed/faiss_hnsw_ego4d.index`.  
    * Writes a JSON mapping `faiss_index_mapping.json` (FAISS row → `node_id`).  
  - Implement `code/src/retrieval/baseline.py` containing class `FixedHierarchyRetriever` that:  
    * Loads the FAISS index; if loading fails, raises `RuntimeError("FAISS index load failure: <details>")` (FR‑011).  
    * Routes queries to buckets based on timestamp `t` (days since event):  
      - **current**: `t ≤ 1` day,  
      - **short‑term**: `1 < t ≤ 14` days,  
      - **long‑term**: `t > 14` days.  
    * Provides `retrieve(query_embedding: np.ndarray, query_timestamp: datetime, k: int = 1) -> List[Tuple[node_id, score]]`.  
  - **Output**: `code/src/data/faiss_builder.py`, `code/src/retrieval/baseline.py`, `data/processed/faiss_hnsw_ego4d.index`, `data/processed/faiss_index_mapping.json`.  
  - **Verification**: Run the builder script and then instantiate `FixedHierarchyRetriever` to retrieve a sample query; ensure a valid node ID list is returned and that a simulated load failure produces the exact error message.

- [ ] T004 [P1] [US-1] **Implement Semantic‑Decay retriever with strict parameter bounds and error handling.**  
  - Implement `code/src/retrieval/semantic_decay.py` with class `SemanticDecayRetriever` that:  
    * Accepts `alpha: float`, `beta: float`, `lam: float` in the constructor.  
    * Enforces `0 < alpha < 1`, `0 < beta < 1`, and `0 < lam < 10`; violation raises `ValueError("Lambda out of bounds: <value>")` (FR‑010, FR‑014).  
    * Loads the same FAISS index as the baseline; on failure raises `RuntimeError("FAISS index load failure: <details>")`.  
    * Computes similarity `sim = cosine(query, node_embedding)` and decay `decay = np.exp(-lam * t)` where `t` is days since the node’s timestamp.  
    * Scores each candidate with `S = alpha * sim + beta * decay`.  
    * Returns the top‑k node IDs and scores via `retrieve`.  
  - Add helper functions in `code/src/retrieval/utils.py` for cosine similarity and exponential decay.  
  - **Output**: `code/src/retrieval/semantic_decay.py`, `code/src/retrieval/utils.py`.  
  - **Verification**: Instantiate with valid parameters (e.g., `alpha=0.6, beta=0.3, lam=0.5`) and retrieve a sample query – confirm non‑empty results. Attempt construction with `lam=15` and verify that the expected `ValueError` is raised with the correct message.

- [ ] T005 [P1] [US-1] **Create a small validation set and run an end‑to‑end benchmark on both models.**  
  - Implement `code/src/evaluation/validation.py` with `create_validation_set(memory_nodes_parquet: Path, num_queries: int = 50, seed: int = 42) -> List[Dict]` that:  
    * Randomly selects `num_queries` memory nodes (fixed seed 42) and uses each node’s embedding as a query vector.  
    * Records the ground‑truth `node_id` and the query timestamp (the node’s own timestamp).  
    * Saves the set to `data/processed/validation_queries.json`.  
  - Extend `code/src/cli/run.py` with a `run_validation` mode that:  
    * Loads the validation set.  
    * Instantiates `FixedHierarchyRetriever` and `SemanticDecayRetriever` with placeholder parameters (`alpha=0.6, beta=0.3, lam=0.5`).  
    * For each query, records: Top‑1 hit (bool) for each model, inference latency (`time.perf_counter()`), and CPU time (`psutil.Process().cpu_times().user`).  
    * Writes per‑query records to `data/results/validation_run.json`.  
  - **Output**: `code/src/evaluation/validation.py`, updated `code/src/cli/run.py`, `data/processed/validation_queries.json`, `data/results/validation_run.json`.  
  - **Verification**: Execute `python code/src/cli/run.py --mode validation` and confirm that `validation_run.json` contains 50 entries with all required fields populated and that latencies are positive numbers.

**Checkpoint**: The quick‑start command documented in `quickstart.md` runs successfully on the 50‑query validation set and produces real rows in `data/results/validation_run.json`.

---

## Phase 2: Complete the Study and Validate Its Evidence

**Goal**: Run the full evaluation on the complete query set, optimise hyper‑parameters, compute all required metrics, and generate a contract‑compliant report.

- [ ] T006 [P2] [US-1] **Deterministic joint grid‑search for (α, β, λ) optimisation.**  
  - Extend `code/src/evaluation/validation.py` with `grid_search_optimal_parameters(memory_nodes_parquet: Path, validation_set_path: Path, output_dir: Path) -> None` that:  
    * Iterates over the grid `α ∈ {0.5,0.6,0.7}`, `β ∈ {0.2,0.3,0.4}`, `λ ∈ {0.1,0.2,…,9.9}` (27 × 99 = 2 673 combos).  
    * For each combo, builds a `SemanticDecayRetriever`, evaluates Top‑1 accuracy on the validation set, and logs `alpha,beta,lambda,validation_accuracy` to `data/results/grid_search_log.txt`.  
    * Uses the deterministic tie‑breaker: **first** triple (ascending α, then β, then λ) that attains the maximal validation accuracy (FR‑015).  
    * Writes the selected triple and its accuracy to `data/results/optimal_parameters.json` with fields `optimal_alpha`, `optimal_beta`, `optimal_lambda`, `validation_accuracy`.  
  - **Output**: Updated `code/src/evaluation/validation.py`, `data/results/grid_search_log.txt`, `data/results/optimal_parameters.json`.  
  - **Verification**: Run the grid‑search script and confirm that the log contains exactly 2 673 lines, that the JSON file contains numbers respecting the bounds (`alpha,beta ∈ (0,1)`, `lambda ∈ (0,10)`), and that `validation_accuracy` lies in `[0,1]`.

- [ ] T007 [P2] [US-1] [US-2] [US-3] **Full evaluation on a representative query set and computation of all metrics.**  
  - Extend `code/src/evaluation/metrics.py` with a function `run_full_evaluation(memory_nodes_parquet: Path, faiss_index_path: Path, optimal_params_path: Path, output_dir: Path) -> None` that:  
    1. Loads the optimal `(α,β,λ)` from `optimal_parameters.json`.  
    2. Generates a stratified evaluation set of **≥ 200** queries covering three age buckets (1‑3 days, 4‑14 days, > 14 days) using fixed seed 42.  
    3. Identifies **rare** events as `is_rare AND is_semantically_distinct`.  
    4. **If the rare‑event subset contains fewer than 30 events**, abort long‑term accuracy computation, add the flag `"Insufficient rare-event data (n < 30): analysis skipped"` to the final report, and continue with short‑term/overall metrics (FR‑009).  
    5. For each query, runs both retrievers, recording Top‑1 hit, latency (ms), and CPU time (seconds), as well as the age bucket.  
    6. Aggregates:  
       - Long‑term Top‑1 accuracy (> 14 days) and query count.  
       - Short‑term Top‑1 accuracy (1‑3 days) and query count.  
       - Overall Top‑1 accuracy.  
       - Latency statistics: max, mean, 95th‑percentile (must satisfy FR‑006).  
       - CPU‑cycle statistics: baseline average, semantic‑decay average, and ratio (must satisfy FR‑013).  
       - Flag short‑term degradation > 5 % (FR‑007).  
    7. Stores per‑query results to `data/results/evaluation_queries.json` and aggregated metrics to `data/results/evaluation_metrics.json`.  
  - Update `code/src/cli/run.py` with a `--mode full-evaluation` entry that calls the above function.  
  - **Output**: `code/src/evaluation/metrics.py`, updated `code/src/cli/run.py`, `data/results/evaluation_queries.json`, `data/results/evaluation_metrics.json`.  
  - **Verification**: Execute `python code/src/cli/run.py --mode full-evaluation …` and confirm:  
    * ≥ 200 query entries exist.  
    * All latency values ≤ 200 ms.  
    * CPU‑cycle ratio ≤ 1.10.  
    * If short‑term degradation > 5 % a corresponding warning appears in `evaluation_metrics.json["flags"]`.  
    * If rare‑event count < 30, the flag `"Insufficient rare-event data (n < 30): analysis skipped"` is present.

- [ ] T008 [P2] **Statistical significance testing via McNemar’s test and edge‑case handling.**  
  - Extend `code/src/evaluation/metrics.py` with `compute_mcnemar_test(evaluation_queries_path: Path, output_path: Path) -> None` that:  
    * Filters the long‑term subset (> 14 days).  
    * Builds the 2 × 2 contingency table of baseline vs. semantic‑decay Top‑1 outcomes.  
    * Uses `scipy.stats.chi2_contingency` (with Yates’ correction) to compute the chi‑square statistic and p‑value.  
    * Writes `statistic`, `p_value`, and `significant` (`p_value < 0.05`) to `data/results/mcnemar_test.json`.  
  - Ensure that if the long‑term subset is empty (e.g., because of the < 30 rare‑event abort) the function writes a flag `"Insufficient long-term data for McNemar test"` and skips the test.  
  - **Output**: Updated `code/src/evaluation/metrics.py`, `data/results/mcnemar_test.json`.  
  - **Verification**: After a full evaluation, run the McNemar utility (it is invoked automatically by the full‑evaluation pipeline) and check that `mcnemar_test.json` contains numeric `statistic` and `p_value` in `[0,1]`, and that `significant` correctly reflects `p_value < 0.05`. If the test is skipped, confirm the appropriate flag appears.

- [ ] T009 [P2] **Assemble a contract‑compliant evaluation report.**  
  - Implement `code/src/evaluation/report.py` with `assemble_report(optimal_params_path, metrics_path, mcnemar_path, output_path) -> None` that:  
    * Reads `optimal_parameters.json`, `evaluation_metrics.json`, and `mcnemar_test.json`.  
    * Constructs a JSON object matching `contracts/evaluation_report.schema.yaml`, populating all required fields (`optimal_alpha`, `optimal_beta`, `optimal_lambda`, `validation_accuracy`, `long_term`, `short_term`, `overall`, `latency`, `cpu_cycles`, `mcnemar_test`, `flags`).  
    * Validates the object with `jsonschema.validate`.  
    * Writes the report to `data/results/evaluation_report.json`.  
  - Add a contract test `code/tests/contract/test_evaluation_report.py` that loads the generated report and validates it against the schema, asserting that numeric ranges are respected and that `mcnemar_test.significant` matches the p‑value condition.  
  - **Output**: `code/src/evaluation/report.py`, `code/tests/contract/test_evaluation_report.py`, `data/results/evaluation_report.json`.  
  - **Verification**: Run the report assembly script and then `pytest code/tests/contract/test_evaluation_report.py`; both must succeed without errors.

- [ ] T010 [P2] **Unit tests for both retrievers.**  
  - Create `code/tests/unit/test_baseline.py` covering:  
    * Correct bucket routing based on timestamps.  
    * Valid Top‑1 results and similarity scores in `[0,1]`.  
    * Proper raising of `RuntimeError("FAISS index load failure: <details>")` when the index file is missing or corrupted.  
    * Edge cases such as an empty query vector.  
  - Create `code/tests/unit/test_semantic_decay.py` covering:  
    * Enforcement of parameter bounds (α, β ∈ (0,1); λ ∈ (0,10)).  
    * Correct computation of the decay score for a known input (e.g., `sim=0.8`, `t=5`, `α=0.6`, `β=0.3`, `λ=0.5`).  
    * Proper handling of FAISS load failures with the exact error message.  
    * Behaviour when `t` is very large (score should be dominated by the similarity term).  
  - **Output**: `code/tests/unit/test_baseline.py`, `code/tests/unit/test_semantic_decay.py`.  
  - **Verification**: Execute `pytest code/tests/unit/test_baseline.py code/tests/unit/test_semantic_decay.py -q`; all tests must pass.

---

## Phase 3: Reproducible Results and Paper Handoff

**Goal**: Write a concise methods/results narrative linked to actual artifacts, generate figures/tables, re‑run the entire pipeline for reproducibility, and hand off the final artifacts to the paper‑stage pipeline.

- [ ] T011 [P3] **Write methods and results narrative linked to actual output artifacts.**  
  - Create `paper/methods.md` that details:  
    * Data acquisition (Ego4D URL, download steps, checksum verification).  
    * Preprocessing (memory‑node construction, rarity & semantic‑distinctness definitions).  
    * FAISS index construction (deterministic HNSW parameters).  
    * Fixed‑Hierarchy baseline logic.  
    * Semantic‑Decay model formula and parameter bounds.  
    * Grid‑search configuration (parameter grid, deterministic tie‑breaker).  
    * Evaluation protocol (query stratification, metrics, statistical test).  
    * Edge‑case handling (rare‑event abort, λ bounds, FAISS failures).  
  - Create `paper/results.md` summarising:  
    * Optimal `(α*, β*, λ*)` and validation accuracy.  
    * Long‑term accuracy for both models, % improvement, and McNemar p‑value.  
    * Short‑term accuracy and any degradation flag.  
    * Overall accuracy, latency statistics (max, mean, p95), CPU‑cycle ratio.  
    * All flags recorded in the report.  
    * Direct links to `data/results/evaluation_report.json`, `evaluation_queries.json`, and `grid_search_log.txt`.  
  - **Output**: `paper/methods.md`, `paper/results.md`.  
  - **Verification**: Manually cross‑check at least three quantitative statements (e.g., “optimal λ = 0.7”) against the values in `evaluation_report.json`.

- [ ] T012 [P3] **Generate summary figures and tables from validated outputs.**  
  - Implement `code/src/evaluation/visualization.py` with functions to:  
    * Plot a side‑by‑side bar chart of long‑term Top‑1 accuracy (baseline vs. semantic‑decay) with error bars (±1 std) and annotate the % improvement.  
    * Plot latency (ms) versus age (days) for both models, showing the 200 ms ceiling.  
    * Produce a concise text table summarising optimal parameters, validation accuracy, long‑term/short‑term/overall accuracies, latency stats, CPU‑cycle ratio, and McNemar significance.  
    * Save PNGs to `figures/long_term_accuracy.png`, `figures/latency_vs_age.png` and the table to `figures/summary_table.txt`.  
  - Use `matplotlib` with a clean style (sans‑serif, 10 pt fonts, 300 dpi).  
  - **Output**: `code/src/evaluation/visualization.py`, `figures/long_term_accuracy.png`, `figures/latency_vs_age.png`, `figures/summary_table.txt`.  
  - **Verification**: Run `python code/src/evaluation/visualization.py --report data/results/evaluation_report.json --output-dir figures/` and confirm that the three files appear and are visually sensible.

- [ ] T013 [P3] **Re‑run the documented full pipeline end‑to‑end and verify reproducibility.**  
  - Write a shell script `code/run_full_pipeline.sh` that performs, in order:  
    1. `python code/src/data/download.py --output-dir data/raw/`  
    2. `python code/src/data/preprocess.py --raw-dir data/raw/ --output data/processed/memory_nodes.parquet`  
    3. `python code/src/data/faiss_builder.py --memory-nodes data/processed/memory_nodes.parquet --output data/processed/faiss_hnsw_ego4d.index`  
    4. `python code/src/cli/run.py --mode validation` (creates validation set and runs the small benchmark)  
    5. `python code/src/evaluation/validation.py --grid-search` (optimises α, β, λ)  
    6. `python code/src/cli/run.py --mode full-evaluation` (full metrics)  
    7. `python code/src/evaluation/report.py --optimal-parameters data/results/optimal_parameters.json --evaluation-metrics data/results/evaluation_metrics.json --mcnemar-test data/results/mcnemar_test.json --output data/results/evaluation_report.json`  
    8. `pytest code/tests/contract/ code/tests/unit/ -q` (run all tests)  
    9. `python code/src/evaluation/visualization.py --report data/results/evaluation_report.json --output-dir figures/`  
    10. Echo a summary line with the path to `evaluation_report.json`.  
  - The script logs progress and any errors to `data/results/pipeline_run.log`.  
  - **Output**: `code/run_full_pipeline.sh`, `data/results/pipeline_run.log`.  
  - **Verification**: On a clean CI runner, execute `bash code/run_full_pipeline.sh 2>&1 | tee data/results/pipeline_run.log`. The log must end with “Pipeline completed successfully” and all intermediate artifacts must exist. Spot‑check that `evaluation_report.json` validates and that the figures are present.

- [ ] T014 [P3] **Document paper‑stage handoff and archive final artifacts.**  
  - Create `paper/HANDOFF.md` that lists:  
    * **Input data**: Ego4D source URL, checksum verification steps.  
    * **Code location**: All source under `code/src/`, tests under `code/tests/`, entry point `code/run_full_pipeline.sh`.  
    * **Output artifacts**: `data/results/evaluation_report.json` (primary result), `data/results/evaluation_queries.json` (per‑query details), `figures/` (visualisations), `paper/methods.md` & `paper/results.md`.  
    * **Reproducibility**: Fixed random seed 42 throughout; exact dependency versions in `requirements.txt`.  
    * **Verification**: Contract test (`test_evaluation_report.py`) and unit tests (`test_baseline.py`, `test_semantic_decay.py`).  
    * **Limitations & flags**: Any warnings from `evaluation_report.json.flags` (e.g., insufficient rare events, short‑term degradation).  
    * **Next steps for the paper pipeline**: The report and figures are ready for inclusion in a manuscript; the paper‑stage will handle captioning, table formatting, PDF generation, and submission.  
  - Archive the entire research artefact tree (`code/`, `specs/001-semantic-decay-retrieval/`, `paper/`, `data/`) as part of the handoff.  
  - **Output**: `paper/HANDOFF.md`.  
  - **Verification**: Review the handoff document to ensure all paths are correct and that it clearly separates research‑stage artefacts from paper‑stage responsibilities.

---

## Dependencies and Requirement Coverage

| Specification Requirement | Task(s) | Artifact / Command | Verification |
|---------------------------|---------|--------------------|--------------|
| **FR‑001** Semantic‑Decay formula & grid‑search | T004, T006 | `semantic_decay.py`, `validation.py` | Inspect code & optimal parameters JSON |
| **FR‑002** Fixed‑Hierarchy baseline | T003 | `baseline.py` | Run baseline retrieval and check bucket routing |
| **FR‑003** Full evaluation on substantial query set | T007 | `run_full_evaluation` → `evaluation_queries.json` | ≥ 200 queries spanning all age buckets |
| **FR‑004** Measure latency & CPU cycles | T007 | `evaluation_metrics.json` latency & cpu_cycles fields | All latencies ≤ 200 ms; ratio ≤ 1.10 |
| **FR‑005** McNemar’s test | T008 | `mcnemar_test.json` | p‑value < 0.05 reported as `significant` |
| **FR‑006** Latency ≤ 200 ms | T007 | `latency.max_ms` | ≤ 200 |
| **FR‑007** Short‑term degradation ≤ 5 % | T007 | `short_term.accuracy_top1` & flags | Flag present only if > 5 % |
| **FR‑008** CPU‑only execution, ≤ 7 GB RAM | T001, T007 | No CUDA imports; monitor via psutil | No OOM, no CUDA errors |
| **FR‑009** Rare‑event abort if < 30 | T007 | Flag in `evaluation_metrics.json` | Correct threshold (30) enforced |
| **FR‑010** λ bounds enforcement | T004, T006 | Constructor validation & grid‑search filter | Errors raised for out‑of‑bounds λ |
| **FR‑011** FAISS load failure message | T003, T004 | RuntimeError with exact message | Simulate missing index → correct error |
| **FR‑012** Rare‑event definition ≤ 5 | T002 | `is_rare` column in parquet | Verify counts ≤ 5 |
| **FR‑013** CPU‑cycle ratio ≤ 1.10 | T007 | `cpu_cycles.ratio` ≤ 1.10 | Check in metrics JSON |
| **FR‑014** λ bounds during training & inference | T004, T006 | Same as FR‑010 | Consistent enforcement |
| **FR‑015** Deterministic grid‑search | T006 | Log order & tie‑breaker | Ascending enumeration, first max selected |
| **SC‑001** Long‑term accuracy improvement | T007, T009 | `long_term.accuracy_top1` & report | Compute % improvement |
| **SC‑002** McNemar significance | T008, T009 | `mcnemar_test.p_value` | < 0.05 |
| **SC‑003** Latency stats | T007, T009 | `latency` object | max, mean, p95 present |
| **SC‑04** Short‑term degradation flag | T007, T009 | `flags` array | Present only if > 5 % |
| **SC‑005** Memory ≤ 7 GB | T001, T007 | CI monitor (psutil) | No OOM |
| **SC‑006** Insufficient rare‑event flag | T007, T009 | `flags` array | Correct wording with n < 30 |
| **SC‑007** λ bounds violation termination | T006, T008 | Logs / exceptions | Confirm abort on violation |
| **SC‑008** FAISS load failure exact message | T003, T008 | Exception message | Verified |
| **SC‑009** CPU‑cycle ratio ≤ 1.10 | T007, T009 | Ratio field | ≤ 1.10 |
| **SC‑010** McNemar p‑value reported | T008, T009 | `mcnemar_test` object | Present and accurate |

All scientific requirements are mapped to concrete tasks, and each task includes an observable verification step.
