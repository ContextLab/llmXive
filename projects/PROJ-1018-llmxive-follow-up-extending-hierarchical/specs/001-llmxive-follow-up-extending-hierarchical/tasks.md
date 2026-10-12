# Tasks: llmXive follow‑up: extending “Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode”

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts (`*.schema.yaml`)  

**Goal**: Implement the full end‑to‑end pipeline required by the specification and produce the canonical artifacts that will be validated by the verifier.

---

## Phase 1 – Project scaffolding (already completed)

- [ ] T001 Create project directory structure (`projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/`) – `src/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/`.
- [ ] T001b Create `requirements.txt` at `projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/requirements.txt` with the pinned dependencies listed in the plan.
- [ ] T001c Create `pyproject.toml` at the same root containing project metadata and build‑system config.
- [ ] T003 Configure linting/formatting tools (ruff/black/isort) in `pyproject.toml`.
- [ ] T007b Load/initialize the pre‑trained HiLS checkpoint (`src/model_loader.py`) – verifies checkpoint compatibility and raises a clear error on version mismatch.
- [ ] T009 [P] [US1] Contract test for extraction output schema (`tests/test_extraction.py::test_extraction_output_schema`).
- [ ] T010 [P] [US1] Integration test for end‑to‑end extraction on a tiny sample (`tests/test_extraction.py::test_end_to_end_extraction`).
- [ ] T011 [P] [US1] Define `RelevanceProfile` dataclass in `src/models.py` (fields match `RelevanceProfile` contract).
- [ ] T013 [US1] Implement `chunk_document` in `src/extraction.py` – handles short‑doc skipping/padding per `config.skip_short_documents`.
- [ ] T012 [US1] Implement `DynamicHiLSWrapper` in `src/extraction.py` with `extract_scores` and robust error handling.
- [ ] T012b [US1] Implement `run_dynamic_inference` in `src/extraction.py` – writes raw per‑chunk score tensors to `data/interim/raw_extraction_results.json`.
- [ ] T017 [P] [US2] Contract test for static index JSON structure (`tests/test_clustering.py::test_static_index_schema`).
- [ ] T018 [P] [US2] Integration test for K‑Means convergence and retry logic (`tests/test_clustering.py::test_kmeans_retry`).
- [ ] T024 [P] [US3] Contract test for `EvaluationReport` schema (`tests/test_evaluation.py::test_report_schema`).
- [ ] T025 [P] [US3] Integration test that the paired‑t‑test returns a float p‑value in \[0, 1\] (`tests/test_evaluation.py::test_pvalue_range`).

---

## Phase 2 – Foundational infrastructure (must be completed before any user story)

- [ ] T004 Implement a robust streaming data loader for the PG‑19 test split.  
  *File*: `src/data_loader.py` – class `StreamingDataLoader` with `__iter__` yielding `{text, id, source}`.  
  *Verification*: Running `python -c "from src.data_loader import StreamingDataLoader; list(itertools.islice(StreamingDataLoader(),1))"` prints one record without error; network failures raise `RuntimeError`.  

- [ ] T005b [P] Load/define the **validation** split.  
  *File*: `src/data_loader.py` – function `load_validation_split()` returning a `StreamingDataLoader` that streams the `validation` split of `lmsys/pg-19-test`.  
  *Verification*: `len(list(itertools.islice(load_validation_split(),5))) == 5`.  

- [ ] T005 Implement document‑length filtering and write the split definition.  
  *File*: `src/data_loader.py` – function `filter_documents(loader, min_tokens=32000) -> List[Dict]`.  
  *Output*: `data/interim/filtered_pg19.json` (JSON list of `{document_id, text, token_count}`) conforming to the `SplitDefinition` contract.  
  *Verification*: The file exists, validates against the schema, and the log contains `WARNING: Skipping document …` for every short document.  

- [ ] T006 [P] Add explicit error handling for real‑data fetch failures.  
  *File*: `src/data_loader.py` – any failure in `datasets.load_dataset` raises `RuntimeError` with a descriptive message; no synthetic fallback is present.  

- [ ] T007 Implement a central configuration object.  
  *File*: `src/config.py` – dataclass `Config` with fields `seed`, `chunk_size`, `model_path`, `k_clusters`, `skip_short_documents` (default True).  
  *Verification*: `from src.config import Config; assert Config().skip_short_documents is True`.  

- [ ] T008 [P] Set up structured JSON‑line logging.  
  *File*: `src/logging_utils.py` – function `get_logger(name: str)` returning a logger that emits JSON lines with `timestamp`, `level`, `message`, `version_hash`.  
  *Verification*: Running a script that logs a test message produces a single line parsable by `json.loads`.  

---

## Phase 3 – User Story 1: Dynamic baseline extraction (Priority P1)

- [ ] T014 [US1] Implement aggregation of raw scores into canonical relevance profiles.  
  *File*: `src/extraction.py` – function `aggregate_profiles(raw_results_path, chunk_metadata_path) -> List[RelevanceProfile]`.  
  *Output*: `data/interim/relevance_profiles.json` (matches `RelevanceProfile` contract).  

- [ ] T016 [US1] Add validation of aggregated profiles.  
  *File*: `src/extraction.py` – function `validate_profiles(profiles)` that checks for NaN/Inf and correct dimensionality.  
  *Verification*: The function returns without exception on the produced `relevance_profiles.json`; a failing case raises `ValueError`.  

- [ ] T015 [US1] Serialize relevance profiles to disk.  
  *File*: `src/extraction.py` – function `save_profiles(profiles, path)` writing to `data/interim/relevance_profiles.json`.  

---

## Phase 4 – User Story 2: Static index construction (Priority P2)

- [ ] T019 [US2] Implement PCA dimensionality reduction on relevance profiles.  
  *File*: `src/clustering.py` – function `apply_pca(profiles, n_components=64) -> np.ndarray`.  
  *Verification*: The returned array has shape `(n_profiles, 64)` and the function writes the PCA‑transformed data to a temporary file for debugging.  

- [ ] T020 [US2] Implement CPU‑optimized K‑Means with retry logic for empty clusters.  
  *File*: `src/clustering.py` – function `run_kmeans(data, k, retry_count=3)` using scikit‑learn’s `KMeans` with `n_init=10`.  
  *Verification*: On failure (empty cluster) the function retries with a new random seed up to three times; if still failing it raises `RuntimeError`.  

- [ ] T021 [US2] Define the `StaticIndex` class.  
  *File*: `src/clustering.py` – dataclass `StaticIndex` with fields `k`, `centroids`, `chunk_to_cluster_map`, `validation_checksum`, `created_at`, `seed`, `pca_components`, `distance_metric`.  

- [ ] T022 [US2] Serialize the static index.  
  *File*: `src/clustering.py` – function `save_static_index(index, path)` writing JSON to `data/processed/static_index_k{K}.json` (e.g., `static_index_k100.json`).  
  *Verification*: The file validates against the `StaticIndex` schema and contains exactly `K` centroids.  

- [ ] T023 [US2] Benchmark static‑lookup latency.  
  *File*: `src/clustering.py` – function `benchmark_lookup(index, token_count)` that times a single lookup on a 2‑core CPU; returns `True` iff latency < 50 ms.  
  *Verification*: The CI test asserts the function returns `True` for the generated index with `K=100`.  

---

## Phase 5 – User Story 3: Comparative evaluation & statistical significance (Priority P3)

- [ ] T026 [US3] Implement static‑HiLS inference that uses the static index instead of dynamic retrieval.  
  *File*: `src/inference.py` – function `static_inference(model, static_index, input_ids)` that replaces the dynamic retrieval step with a lookup into `static_index.chunk_to_cluster_map` to construct the sparsity mask.  
  *Verification*: Running the function on a sample 32 k‑token document returns logits without raising errors.  

- [ ] T027 [US3] Implement perplexity calculation for both dynamic and static models.  
  *File*: `src/evaluation.py` – function `calculate_perplexity(model, dataset)` returning a float log‑perplexity.  

- [ ] T028 [US3] Implement downstream long‑context QA evaluation.  
  *File*: `src/evaluation.py` – function `evaluate_qa(model, qa_dataset)` that computes exact‑match accuracy on the `llamaindex/long-qa` dataset (fallback to `narrativeqa` if unavailable).  
  *Verification*: Returns a float in \[0, 1\]; raises `RuntimeError` if neither dataset can be loaded.  

- [ ] T029 [US3] Perform the required paired t‑test on per‑document perplexities.  
  *File*: `src/evaluation.py` – function `run_paired_ttest(dynamic_scores, static_scores)` using `scipy.stats.ttest_rel`. Returns a dict with `method`, `p_value`, `significance`, `confidence_interval`.  

- [ ] T030 [P] [US3] Measure inference latency following the protocol (32 k tokens, 10 runs, 2 warm‑ups) on a 2‑core CPU.  
  *File*: `src/evaluation.py` – function `measure_latency(model, dataset)` writing `latency_ms` to `data/processed/latency_metrics.json`.  

- [ ] T030b [US3] Measure the memory footprint of the retrieval module with `tracemalloc`.  
  *File*: `src/evaluation.py` – function `measure_retrieval_memory(dynamic_wrapper)` that isolates the memory used by `DynamicHiLSWrapper.extract_scores`. Writes `memory_footprint_bytes` to `data/processed/memory_metrics.json`.  

- [ ] T031a [US3] Sensitivity sweep over K ∈ {50, 100, 200}.  
  *File*: `src/evaluation.py` – function `sweep_k_values(k_values=[50,100,200])` that re‑runs clustering (T019/T020) for each K, saves each static index, and records the corresponding metrics.  

- [ ] T031b [US3] Generate a consolidated sweep report.  
  *File*: `src/evaluation.py` – function `generate_sensitivity_report(index_paths)` producing `data/processed/sweep_report.json` with per‑K perplexity, QA accuracy, latency, and memory.  

- [ ] T033a [US3] Orchestrate full test‑set evaluation for both dynamic and static variants.  
  *File*: `src/evaluation.py` – function `run_test_evaluation(dynamic_model, static_model, test_dataset, static_index)` that calls `calculate_perplexity`, `evaluate_qa`, `measure_latency`, `measure_retrieval_memory`, and `run_paired_ttest`.  

- [ ] T032 [US3] Serialize the final `EvaluationReport`.  
  *File*: `src/evaluation.py` – function `generate_report(metrics, sensitivity_report, k_value)` writing `data/processed/evaluation_report.json` that conforms to the `EvaluationReport` schema.  

---

## Phase 6 – Polish & hand‑off (no scientific content, but required for reproducibility)

- [ ] T029b [P] Update `plan.md` to replace any mention of a “Wilcoxon test” with “paired t‑test” so that the plan aligns with FR‑005.  
  *Verification*: `grep -r "Wilcoxon" plan.md` returns no matches.  

- [ ] T033 [P] Refresh documentation (`docs/quickstart.md`, `docs/research.md`) to reflect the final file paths and command‑line entry points introduced in the implementation.  

- [ ] T034 Add comprehensive docstrings and type hints to all newly created functions (data loader, extraction, clustering, inference, evaluation).  

- [ ] T035 Optimize streaming processing (e.g., batch tokenization) to stay within the 7 GB RAM limit on the GitHub Actions runner.  

- [ ] T036 [P] Add edge‑case unit tests for short‑document handling, K‑Means empty‑cluster retries, and memory‑measurement isolation (`tests/test_edge_cases.py`).  

- [ ] T037 Run the `run_pipeline.sh` script end‑to‑end and verify that the following files are produced and pass schema validation:  
  * `data/interim/filtered_pg19.json`  
  * `data/interim/relevance_profiles.json`  
  * `data/processed/static_index_k100.json` (and K = 50, 200)  
  * `data/processed/evaluation_report.json`  
  * `data/processed/sweep_report.json`  

---

### Dependency & execution order summary

1. **Phase 2** (T004 → T008) must finish before any user‑story tasks.  
2. **US 1** (T014 → T016 → T015) depends on Phase 2 outputs (`filtered_pg19.json`).  
3. **US 2** (T019 → T020 → T021 → T022 → T023) depends on `relevance_profiles.json`.  
4. **US 3** (T026 → T027 → T028 → T029 → T030/T030b → T031a/T031b → T033a → T032) depends on the static index (any K) and the test split generated by Phase 2.  
5. **Polish** tasks run after the core pipeline succeeds.

--- 

*All tasks are written as unchecked boxes except those already verified (✓).  The pending tasks directly address the reviewer‑rejected items and ensure that every artifact required by the spec is produced from real data, validated against the corresponding JSON‑schema contracts, and measurable on the prescribed hardware.*
