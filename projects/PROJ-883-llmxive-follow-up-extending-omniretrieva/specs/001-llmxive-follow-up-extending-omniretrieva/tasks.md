# Tasks: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Input**: Design documents from `specs/001-structural-mismatch-cost/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Research scripts write ONLY to project-owned paths (`data/`, `code/`, `specs/`); never to `state/` or `.github/` — the platform owns those.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 Establish the project skeleton with real, non‑empty directories and placeholder files (`code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `specs/001-structural-mismatch-cost/contracts/`). Do **not** create any schema files here; schema creation is handled by T004. Document the runnable pipeline command (`python -m code.main`) in `specs/001-structural-mismatch-cost/quickstart.md`. Include a minimal `requirements.txt` and lint config (`.ruff.toml`, `pyproject.toml`). `ruff check code/` must run successfully. <!-- FAILED-IN-EXECUTION: code/ground_truth_engine.py exit=1; code/visualize.py exit=1; code/main.py exit=1 -->

- [ ] T004 Create/repair the data schemas in `specs/001-structural-mismatch-cost/contracts/`: `query_instance.schema.yaml`, `execution_log.schema.yaml`, `execution_metric.schema.yaml`, `statistics-result.schema.yaml`. Validate a sample row against each schema with `pyyaml` + `jsonschema`. **Do not** create `analysis_result.schema.yaml` or `gam_results.schema.yaml` – they are deprecated.

- [ ] T005 Implement `code/config.py` (seeds, paths, throttling config) and `code/utils/data_fetcher.py` for real dataset fetching: MS MARCO via `datasets.load_dataset("microsoft/ms_marco", "v1.1")`, Spider via `datasets.load_dataset("xlangai/spider")`, and a reachable DBpedia/Wikidata subset. Stream large datasets with `datasets.load_dataset(..., streaming=True)` and chunked processing. Real fetch failures **must raise**; no synthetic fallback unless an explicit `--allow-synthetic` flag is passed, in which case a synthetic graph is generated with `synthetic_flag=1` and logged.

- [X] T007 Implement `code/generators/reference_engine.py` (FR‑008): deterministic, rule‑based greedy ground‑truth plan generator that selects the next step with the lowest estimated cost and shortest depth.

- [ ] T006 Implement `code/generators/synthetic_query.py` generating queries with exact integer plan depths (1, 2, 3, 4+) persisted as integers (FR‑002). Calls T007 to attach `ground_truth_plan` to each query and writes the definitions to `data/processed/generation_log.json` conforming to `query_instance.schema.yaml`. Caps depth with a logged warning if the requested depth exceeds the generator maximum.

- [X] T022 Implement a lightweight unified router (`code/router/sut_router.py`) that, given a query definition, produces a **system‑generated execution plan** (`sut_plan`) using a limited‑lookahead heuristic (e.g., depth‑1 cost estimate). The router writes the `sut_plan` back into each entry of `generation_log.json`. This satisfies FR‑004’s requirement for a system‑generated plan.

- [X] T016 Implement CPU throttling in `code/utils/cpu_throttle.py` enforcing the strict 2‑core, 7 GB RAM limits via cgroups. If cgroups cannot be applied (e.g., insufficient permissions), the process aborts with `EXIT_CODE_THROTTLING_FAILURE = 1` and a clear error message. No RLIMIT fallback is permitted. The throttling mode (`cgroups`) and the configured core/RAM limits are recorded in the logs.

- [ ] T008 Implement `code/executors/` with `base.py` (abstract executor with 60‑second timeout handling) and three concrete wrappers: `text_executor.py` (sampled MS MARCO), `relational_executor.py` (in‑memory SQLite from Spider), `graph_executor.py` (NetworkX/RDFLib over DBpedia/Wikidata). **Dependency:** T016, T005, T006.

- [ ] T021 Implement `code/main.py` orchestration: load config, generate queries (T006), enrich with `sut_plan` (T022), route to executors (T008), enforce throttling (T016), compute **translation_error** (`sut_plan` ≠ `ground_truth_plan`), record **timeout_flag** (true if executor hit 60 s), and persist raw metrics to `data/processed/execution_logs.csv` with columns matching `execution_log.schema.yaml` **plus** an additional `timeout_flag` column (now part of the CSV). Also write a complementary `data/processed/execution_metrics.jsonl` conforming to `execution_metric.schema.yaml` (produced by T023). Run the pipeline on a small real sample (≥ 30 queries across all source types and depths 1‑4) and commit the CSV and JSONL. <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->

- [ ] T023 Transform the CSV produced by T021 into `data/processed/execution_metrics.jsonl` matching `execution_metric.schema.yaml`. Fields populated:
  * `query_id` (from CSV)
  * `latency_ms` (from CSV)
  * `mismatch_flag` (boolean version of `translation_error`)
  * `delta_latency` (latency – ground‑truth latency, retrieved via `ground_truth_engine`)
  * `engine_version` (static string, e.g., `"sqlite-3.41"` or `"rdflib-6.2"`)
  * `throttle_config` (string describing cgroups limits, e.g., `"2 cores, 7 GB"`).

- [ ] T018 [US1] Implement `code/analysis/stats.py` two‑way ANOVA/ANCOVA (`latency_ms ~ complexity_level * source_type`) reading `execution_logs.csv` (excluding rows where `synthetic_flag=1`). **Output** conforms to `analysis_result.schema.yaml`: for each `source_type` × `complexity_category` (low/high) produce `mean_delta_latency`, `std_delta_latency`, `n_samples`, plus global `anova_f_statistic`, `anova_p_value`, `interaction_significant`, `segmented_regression_knee_point`, `segmented_regression_p_value`. Write to `data/results/anova_results.json`.

- [ ] T020 [US1] Implement the FR‑007 sensitivity sweep in `code/analysis/stats.py`: loop over cutoffs `[2, 3, 4]`, compute `spike_point` and `slope_change` as defined, and write the list to `data/results/sensitivity_analysis.json` conforming to `statistics-result.schema.yaml`.

- [ ] T025 [US2] Implement translation‑error analysis in `code/analysis/metrics.py` and `code/analysis/stats.py`: compare `sut_plan` vs. `ground_truth_plan` for **all** queries, then aggregate error rates for **low** (≤ 2) vs. **high** (≥ 3) complexity groups **and** specifically for the **100 high‑complexity graph queries** required by US‑2 Scenario 2. Output the absolute difference and write a summary to `data/results/translation_error_summary.json`.

- [ ] T030 [US3] Implement `code/analysis/viz.py` generating interaction plots (latency vs. complexity per source type) from `execution_logs.csv`. Highlight the graph‑source slope and the identified spike/threshold region. Save `data/results/interaction_plot.png` and `data/results/interaction_plot.pdf`. **Verification:** a unit test asserts that the PNG file exists and is non‑empty.

- [ ] T033 Generate `data/results/research_summary.md` summarising ANOVA interaction statistics, slope ratios, translation‑error differences, sensitivity sweep results, and links to the plots. Include a candid limitations paragraph (associational framing, throttling mode used, any synthetic_flag exclusions).

- [ ] T037 Run the full documented workflow from `specs/001-structural-mismatch-cost/quickstart.md` on the complete 500‑query set (including the 100 high‑complexity graph queries) within the CPU‑only budget. Verify that all unit, integration, and contract tests pass, and record the final outcomes in `data/results/research_summary.md`. This constitutes the reproducibility hand‑off.

## Removed / corrected tasks

- **T039** (state.yaml generator) – removed.
- **T042** (secondary synthetic fallback) – folded into T005 with explicit flag.
- **T040/T041** – satisfied inside T005.
- **T043** – folded into T008/T006.
- **T044** – satisfied by T025.
- **T002/T003** – folded into T001.
- **T013/T014/T014b/T022** – folded into T021, T016, T025.
- **T015/T017/T024/T026/T027** – consolidated into T021, T006, T025.
- **T028–T032** – consolidated into T030 and T033.