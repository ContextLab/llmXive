# Tasks: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

**Inputs**: Active `spec.md`, `plan.md`, `research.md`, `data-model.md`, JSON-schema contracts, verifier rejection feedback for T004–T028.

**Goal**: Implement the smallest complete static-distillation study: stream real PG-19 data, extract dynamic HiLS relevance profiles, build a K-Means static index, and compare static vs. dynamic inference (perplexity, QA accuracy, latency, memory) with a paired statistical test — all on real data, all artifacts schema-validated.

**Revision note**: All previously rejected tasks (T004–T028) are addressed by the regrouped tasks below; none had verified artifacts, so no checked boxes are retained. Paths are relative to `projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/`.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Implement the streaming PG-19 data loader with length filtering, split creation, and central configuration. <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=-1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=-1 --> <!-- FAILED-IN-EXECUTION: code/src/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=-1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data_loader.py exit=1 -->
  *Files*: `src/data_loader.py`, `src/config.py`, `src/logging_utils.py`, `contracts/split_definition.schema.yaml`.
  *Requirements*: FR-001 prerequisite; spec Assumptions (dataset variable fit, CPU feasibility).
  - Use the canonical dataset `lmsys/pg-19-test` (as per spec) via `datasets.load_dataset("lmsys/pg-19-test", split="train", streaming=True)`.
  - `src/config.py`: dataclass `Config` with `seed=42`, `chunk_size`, `model_path`, `k_clusters=100`, `min_tokens=32000`, `skip_short_documents=True`, `PAD_SHORT_DOCS=False`; assert `skip_short_documents`.
  - `src/data_loader.py`: `load_streaming_pg19(split, min_tokens)` streams the dataset, filters documents below `min_tokens` (or pads when `PAD_SHORT_DOCS=True`), logs exclusions, creates deterministic validation/test splits (seed = 42), writes `data/interim/filtered_pg19.json` conforming to `SplitDefinition` schema (`validation_ids`, `test_ids`, `checksum`).
  - No synthetic fallback: any failure in `datasets.load_dataset` raises `RuntimeError` with a descriptive message; if filtered set < 30 docs, abort with a power‑warning.
  - Verification: `python -c "import itertools; from src.data_loader import load_streaming_pg19; print(len(list(itertools.islice(load_streaming_pg19('train'), 5))))"` prints 5; `data/interim/filtered_pg19.json` exists, validates against the split schema, and logs the exclusion count for short documents.

- [ ] T002 [US1] Implement dynamic HiLS baseline extraction and relevance‑profile aggregation with focused tests.
  *Files*: `src/extraction.py`, `src/aggregation.py`, `tests/test_extraction.py`.
  *Requirements*: FR-001, US‑1 acceptance scenarios, edge cases (short docs, checkpoint incompatibility).
  - `DynamicHiLSWrapper` loads the pre‑trained HiLS checkpoint (`llmxive/hils-base`). Initialization detects checkpoint/environment incompatibility and halts with a clear error. If CUDA is required, the real computation runs on a Kaggle GPU escape hatch (`device="cuda"`), never a fabricated CPU stand‑in.
  - `src/extraction.py` runs dynamic inference over the **validation** split, writing per‑document raw score tensors (`N_chunks × N_tokens`) to `data/interim/raw_scores/`.
  - `src/aggregation.py` reads those tensors, computes the mean‑across‑tokens canonical relevance profile per chunk, validates dimensions (no NaN/Inf), and writes `data/interim/relevance_profiles.json` conforming to the `RelevanceProfile` contract (including `checksum`).
  - `tests/test_extraction.py` validates the schema of the profile JSON and runs an end‑to‑end test on a small real sample (≈ 3 documents) asserting non‑empty score matrices with expected chunk counts.
  - Verification: running extraction on the validation split produces `data/interim/relevance_profiles.json` with no null/NaN scores and chunk counts matching `token_count / chunk_size`.

- [ ] T003 [US2] Build the static index (PCA + spherical K‑Means) and run a first small end‑to‑end static inference, producing a real result row. <!-- FAILED-IN-EXECUTION: code/run_static_inference.py exit=1 -->
  *Files*: `src/clustering.py`, `src/inference.py`, `tests/test_clustering.py`.
  *Requirements*: FR-002, FR-003 (initial), US‑2 acceptance scenarios.
  - Apply PCA (`n_components=64`) to L2‑normalized relevance profiles, then run `sklearn.cluster.KMeans` (Euclidean distance) on the normalized vectors (spherical K‑Means). `run_kmeans` retries up to 3 random seeds on empty‑cluster failures and aborts with a clear error after the third attempt (no fallback to a lower K).
  - `StaticIndex` dataclass is populated and saved as `data/processed/static_index_k100.json` conforming to the `StaticIndex` schema (exactly K centroids, complete `chunk_to_cluster_map`, `validation_checksum`, `created_at`, `seed`, `pca_components`, `distance_metric`).
  - `src/inference.py` provides `static_inference(model, static_index, input_ids)` which replaces dynamic retrieval with a lookup into `chunk_to_cluster_map` to construct the attention sparsity mask; tokenization matches the dynamic baseline.
  - `benchmark_lookup(index)` verifies a cluster assignment returns within 50 ms on a 2‑core CPU.
  - `tests/test_clustering.py` checks the static‑index schema and the empty‑cluster retry logic.
  - Verification: `data/processed/static_index_k100.json` validates; a sample static‑inference call on a real ≥ 32k‑token test document returns logits without error; a per‑document log‑perplexity row is written under `data/results/`.

- [ ] T004 [US3] Implement diagnostic evaluation on the **validation split**: perplexity, QA accuracy (HotpotQA long‑context subset), latency, and memory for both dynamic and static variants.
  *Files*: `src/evaluation.py`, `tests/test_evaluation.py`.
  *Requirements*: FR-003‑FR‑007, SC‑001‑SC‑005 (diagnostic).
  - Load a verified HotpotQA long‑context subset (`datasets.load_dataset("hotpotqa", "full")`) and filter contexts to ≥ 32 k tokens.
  - Compute per‑document log‑perplexity for both models on the **validation** split.
  - Compute exact‑match QA accuracy on the HotpotQA subset.
  - Measure latency following the fixed protocol: 32 k‑token input, 10 timed runs, 2 warm‑up iterations, using `time.perf_counter()` on the target 2‑core CPU; report `latency_dynamic_ms` and `latency_static_ms`.
  - Measure dynamic retrieval memory via `tracemalloc` inside `DynamicHiLSWrapper.extract_scores` and static index memory via `sys.getsizeof` of the deserialized index object.
  - Produce `data/reports/diagnostic_report.json` conforming to the **extended** `EvaluationReport` schema (includes `static_memory_footprint_bytes`, `effect_size`, `bonferroni_corrected_p_value`, `power_analysis_flag`).
  - Verification: all metrics are real measured values; schema validation passes.

- [ ] T005 [US3] Perform the paired statistical test with normality check, effect sizes, Bonferroni correction, and power‑analysis flags.
  *File*: `src/evaluation.py`.
  *Requirements*: FR-005; SC‑003; plan Statistical Rigor items 1, 2, 4.
  - Run Shapiro‑Wilk on the paired log‑perplexity differences; if normal (`p ≥ 0.05`) use paired t‑test (`scipy.stats.ttest_rel`), else use Wilcoxon signed‑rank (`scipy.stats.wilcoxon`).
  - Record `method`, `p_value`, `significance` (p < 0.05), `confidence_interval` (95 %), `effect_size` (Cohen’s d or Wilcoxon r), `bonferroni_corrected_p_value` (α / 4 for the four secondary metrics), and `power_analysis_flag` (true if N meets the pre‑computed thresholds, false otherwise).
  - Store the full result object inside `diagnostic_report.json` under `statistical_test`.

- [ ] T006 [US3] Run the K‑sensitivity sweep, generate per‑K reports, and validate against sweep schema.
  *Files*: `src/sensitivity.py`, `src/report_sweep.py`, `contracts/sweep_report.schema.yaml`.
  *Requirements*: FR‑008; SC‑006.
  - For each K ∈ {50, 100, 200}:
    * Re‑run clustering (as in T003) on the relevance profiles.
    * Run the full diagnostic evaluation (as in T004) on the **validation** split, producing `data/reports/evaluation_k{K}.json`.
    * Save the static index as `data/processed/static_index_k{K}.json`.
  - `src/report_sweep.py` aggregates per‑K metrics (Δlog‑PPL, ΔQA accuracy, latency, memory) into `data/reports/sweep_report.json` conforming to the newly created `sweep_report.schema.yaml`.
  - Verification: `sweep_report.json` validates against its schema.

- [ ] T007 Add independent correctness, edge‑case, and runtime checks and record their outcomes.
  *File*: `tests/test_edge_cases.py` plus `data/results/checks.json`.
  *Requirements*: spec Edge Cases; plan Risks & Mitigations.
  - Unit tests for short‑document skip/pad handling, K‑Means empty‑cluster retry (all 3 seeds), memory‑measurement isolation, and loader failure raising (assert no synthetic fallback symbols).
  - Runtime check that streaming + batch processing keeps peak RSS ≤ 7 GB; record actual peak memory in `checks.json`.
  - Verification: `pytest tests/` passes; `checks.json` contains recorded outcomes.

- [ ] T008 Generate the study's tables and figures directly from the validated outputs.
  *Files*: `figures/` outputs generated from `data/reports/evaluation_report.json` and `data/reports/sweep_report.json`.
  *Requirements*: SC‑001‑SC‑006 presentation; plan Principle IV.
  - Table of dynamic vs. static metrics (Δlog‑PPL, QA accuracy, latency reduction factor, memory bytes, p‑value, effect size) and K‑sweep trade‑off figure (K vs. perplexity degradation & QA accuracy) are produced programmatically from the JSON reports; no manual transcription.

- [ ] T009 Write a concise methods/results account linked to the actual output cells and figure files.
  *File*: `specs/001-llmxive-follow-up-extending-hierarchical/results.md` (or `paper/notes.md`).
  - Describe the extraction → clustering → evaluation pipeline, the measured degradation and latency reduction, the statistical conclusion (significant / not significant at p < 0.05), and the K‑sweep trade‑off. Link each claim to the exact JSON cell or figure file it originates from. Include power‑analysis flags and limitations.

- [ ] T010 Re‑run the documented workflow end‑to‑end and document the paper‑stage handoff.
  *Files*: `run_pipeline.sh`, `specs/001-llmxive-follow-up-extending-hierarchical/quickstart.md`.
  - `run_pipeline.sh` chains: data loading → extraction → aggregation → clustering → diagnostic evaluation → K‑sweep → final evaluation (T016) with default K = 100. Quickstart lists the exact commands (matching the manual steps) and the verification checklist: `filtered_pg19.json`, `relevance_profiles.json`, `static_index_k{50,100,200}.json`, `diagnostic_report.json`, `sweep_report.json`, `evaluation_report.json` all exist and pass schema validation; `evaluation_report.json` includes a p‑value with a significance flag and a measured `latency_reduction_factor`.
  - Document the paper‑stage handoff: paper layout, PDF compilation, and publication requirements (tables/figures sourced from the JSON reports) are listed as named handoff items, not duplicated as research tasks.

## Phase 2: Complete the study and validate its evidence

- [ ] T011 Create `contracts/split_definition.schema.yaml` defining the SplitDefinition JSON schema.
  *File*: `contracts/split_definition.schema.yaml`.
  - Schema includes `validation_ids` (array of strings), `test_ids` (array of strings), and `checksum` (string). `additionalProperties: false`.

- [ ] T012 Extend `contracts/evaluation_report.schema.yaml` to include:
  *Fields*: `effect_size` (number), `bonferroni_corrected_p_value` (number), `power_analysis_flag` (boolean), `static_memory_footprint_bytes` (integer).
  - Keep `additionalProperties: false` and retain all existing fields.

- [ ] T013 Create `contracts/sweep_report.schema.yaml` describing the structure of `sweep_report.json` (per‑K metrics: `k`, `log_perplexity_delta`, `qa_accuracy_delta`, `latency_ms`, `memory_bytes`, plus optional confidence intervals).

- [ ] T014 Add HotpotQA long‑context subset handling: script `src/qa_loader.py` that fetches `datasets.load_dataset("hotpotqa", "full")`, filters contexts ≥ 32 k tokens, and provides a verified citation entry.

- [ ] T015 Document justification for substituting HotpotQA for the FR‑007 example, adding a brief amendment note to `specs/001-llmxive-follow-up-extending-hierarchical/spec.md` (recorded as a comment in the spec repository).

- [ ] T016 Perform the final evaluation on the held‑out test split using the best‑K index (selected from the sweep), producing `data/reports/evaluation_report.json` that conforms to the **extended** EvaluationReport schema and includes both dynamic and static memory footprints, all statistical fields, and the latency reduction factor.

## Phase 3: Reproducible results and paper handoff

- [ ] T017 Write the concise methods/results account (see T009) and ensure all claims trace to JSON cells or figure files.

- [ ] T018 Execute `run_pipeline.sh` from a fresh environment, verify that all artifacts are regenerated identically, and record the handoff to the paper pipeline.
