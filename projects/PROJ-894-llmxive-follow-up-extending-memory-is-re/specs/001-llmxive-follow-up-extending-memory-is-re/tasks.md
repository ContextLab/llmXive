# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Inputs**: Active `spec.md`, `plan.md`, and existing artifacts under `specs/001-llmxive-follow-up-extending-memory-is-re/`.
**Re-plan note**: The prior tasks.md was rejected for format (no canonical checkbox items). This revision preserves all verified work and scientific requirements while regenerating the task list in canonical `- [ ] T###` format, consolidating the many overlapping pending micro-tasks into substantive research tasks.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Run an executable analysis on valid, small real inputs early.

- [ ] T001 [P1] [US1] Download the LoCoMo benchmark subset via a strict loader with no synthetic fallback, producing `data/raw/locomo.jsonl` (FR-001).
    - Implement `code/data/download_locomo.py` calling `load_locomo_strict()` which uses `datasets.load_dataset(..., split=..., streaming=True)` (streaming to stay within RAM limits); on failure it MUST raise — never fall back to synthetic/mock data.
    - Verify presence of expected columns (`question`, `context`, `answer`); raise `ValueError("Dataset schema mismatch")` if missing.
    - Compute and log the SHA-256 of `data/raw/locomo.jsonl` in the run output (do not write to `state/`).
    - Verification: run `python code/data/download_locomo.py`; assert `data/raw/locomo.jsonl` exists, is non-empty, and `tests/integration/test_data_loader_audit.py` passes.

- [ ] T002 [P1] [US1] Construct the immutable per-task memory graphs and noisy variants (FR-001, plan Phase 1).
    - Implement `code/data/generate_graphs.py`: parse each task context into sentence nodes; select the top-K (K=50) most relevant sentences by similarity to the question using Model A (`all-MiniLM-L6-v2`); build directed edges via Model A similarity; write `data/intermediate/graphs_raw.json` keyed by `task_id`.
    - Compute edge-coherence scores and write `data/intermediate/graph_validation_scores.json`; flag tasks below the coherence threshold as `invalid_graph` and exclude them from strategy runs.
    - Implement `code/data/generate_noisy_graphs.py`: apply `inject_noise` with edge replacement at density 0.05, seed 42, output `data/processed/graphs/graph_noise_42.json`; verify the noisy graph has the same edge count as the clean graph but different targets.
    - Verification: `tests/unit/test_graph_utils.py::test_serialization` and `test_noise_reproducibility` pass (same seed → identical noisy graph); schema validation against `contracts/noisy_graphs.schema.yaml` passes.

- [ ] T003 [P1] [US1] Implement the three traversal strategies (Full, Lazy, Greedy) with degenerate-input handling (FR-002, FR-003, FR-004, US-4 edge cases).
    - Implement `code/models/graph_traversal.py`: Full (traverse all nodes of the constructed sampled graph), Lazy (expand edges only when Model B `all-mpnet-base-v2` score > evidence threshold; hard cap 50 nodes), Greedy (top-k Model B edges; hard cap 50 nodes).
    - All strategies load the SAME `data/intermediate/graphs_raw.json` instance per task ID.
    - Handle disconnected graphs (unreachable target → "UNREACHABLE" flag or full component traversal), zero-edge/single-node graphs (no division-by-zero; "DEGENERATE" flag), and self-loops.
    - Verification: `tests/unit/test_traversal.py` passes on known graph structures including degenerate cases; `tests/unit/test_degenerate_graphs.py` passes.

- [ ] T004 [P1] [US1] Implement the execution runner with per-task timeout, strict data-flow checks, and evidence-threshold logging (FR-007, FR-003 logging).
    - Implement `code/analysis/runner.py` with a `timeout_wrapper` using `signal`/`subprocess` enforcing the 30-minute per-task cap; on timeout log `TIMEOUT` status and continue to the next task.
    - Before execution, assert `data/intermediate/graphs_raw.json` exists and is non-empty; abort with a descriptive error if missing. For noisy runs, assert `data/processed/graphs/graph_noise_42.json` exists first.
    - Initialize the quantized CPU LLM (e.g., Llama-3-8B-4bit via `llama-cpp-python`) for FINAL ANSWER GENERATION ONLY; extract `token_count` from model metadata for every execution (Constitution Principle VI).
    - Log per-task records with all `contracts/execution_log.schema.yaml` required fields: `task_id`, `strategy`, `accuracy`, `nodes_visited`, `inference_time_seconds`, `token_count`, `status`, `noise_applied`, `hard_cap_applied`, `construction_model`, `scoring_model`, plus `evidence_threshold` for Lazy.
    - Add `validate_evidence_threshold(results_df)` raising `ValueError` if the threshold column is unpopulated for Lazy rows.
    - Verification: `tests/unit/test_timeout_handler.py` and `tests/integration/test_hard_timeout.py` pass (timeout strictly enforced, no crash); `tests/integration/test_pipeline_order.py` passes.

- [ ] T005 [P1] [US1] Run the Full baseline end-to-end on a small real subset, producing the first real results (US-1).
    - Implement `code/run_baseline.py` executing the Full strategy on the clean graphs for a small fixed subset (first N tasks, N stated in the output), producing `data/processed/baseline_results.csv` with exactly `task_id`, `accuracy`, `nodes_visited`, `inference_time_seconds`, `token_count` (plus `status`).
    - Support a `--streaming` flag processing tasks in batches with intermediate results written to disk.
    - Verification: `tests/unit/test_baseline_schema.py::test_baseline_columns` passes; every task row has a recorded accuracy (0.0–1.0) and latency; `tests/integration/test_e2e_pipeline.py` passes on the small subset.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [P2] [US2] Run the complete strategy comparison: Full, Lazy (with sensitivity sweep), and Greedy on the full task set, clean and noisy (FR-002–FR-004, SC-001, SC-002).
    - Run Full baseline on the full task set → `data/processed/baseline_results.csv`.
    - Run Lazy via `code/run_lazy.py` with `--thresholds 0.5,0.6,0.7,0.8` sweep → `data/processed/lazy_results.csv` and combined `data/processed/lazy_sweep_results.csv` (with `threshold_value` column); each run logs its exact `evidence_threshold`.
    - Run Greedy via `code/run_greedy.py` → `data/processed/greedy_results.csv`.
    - Run noisy variants: Full on noisy graphs → `data/processed/noisy_baseline_results.csv`; Lazy on noisy graphs → `data/processed/lazy_noisy_results.csv`.
    - Verification: `tests/unit/test_runner_schemas.py` column checks for Lazy and Greedy CSVs pass; noisy runs use the same graph instance per task; accuracy delta vs. baseline computed for the 2%-margin hypothesis test.

- [ ] T007 [P3] [US3] Perform the statistical analysis: paired tests, Point-Biserial correlation, binning/inflection, power analysis (FR-005, FR-006, SC-003, SC-004).
    - Implement `code/analysis/stats.py`: normality check (Shapiro-Wilk) selecting paired t-test vs. Wilcoxon; Bonferroni correction; `calc_point_biserial()` between `nodes_visited` and success; `bin_tasks_by_nodes(min_bin_size=3)` with `merge_bins()` enforcing n ≥ 3; `find_inflection_point()` reporting the first bin with mean accuracy < 95% of baseline only when p < 0.05, otherwise reporting the trend without asserting a threshold; post-hoc power analysis.
    - Clean analysis → `data/processed/stats_clean.json`; noisy robustness analysis (paired test of Accuracy(Lazy, Noisy) vs. Accuracy(Baseline, Noisy), explicit H0/H1) → `data/processed/stats_noisy.json`, both conforming to `contracts/statistical_result.schema.yaml` and `contracts/stats_summary.schema.yaml`.
    - Aggregate into `data/processed/stats_final.json` via `code/scripts/generate_stats_report.py` with keys `p-value`, `test_statistic`, `correlation_coefficient`, `inflection_point`.
    - Verification: `tests/unit/test_stats.py::test_statistical_outputs`, `tests/unit/test_binning_edge_cases.py`, and `tests/unit/test_bin_merging.py` pass; stats tasks run AFTER T006 results exist.

- [ ] T008 [P2] [US2] Analyze threshold sensitivity and generate figures (SC-001, methodology-panel requirement).
    - Implement `code/scripts/analyze_sensitivity.py` comparing accuracy and node counts across sweep thresholds → `data/processed/sensitivity_analysis.json`.
    - Implement `code/scripts/plot_sensitivity.py` producing Accuracy vs. Nodes Visited per threshold → `docs/plots/threshold_sensitivity.png`; additional figures for accuracy delta and node-reduction percentage per strategy vs. baseline.
    - Verification: JSON and PNG artifacts exist and are generated directly from T006/T007 outputs, not from expected values.

- [ ] T009 [P1] [US4] Run the robustness and edge-case regression suite (US-4, FR-007).
    - Use `code/scripts/generate_edge_case_dataset.py` / `generate_mixed_robustness_dataset.py` to produce datasets with disconnected graphs, zero-edge graphs, and timeout-prone tasks (these are graph-structure test fixtures derived from real graphs, not fabricated measurement data).
    - Run `tests/integration/test_end_to_end_robustness.py` and `tests/integration/test_edge_case_regression.py`: every task is processed with a status (`completed`, `unresolved`, `degenerate`, `timeout`) and the pipeline never crashes.
    - Record counts of timed-out vs. completed tasks (SC-005) in `data/processed/stats_final.json`.
    - Verification: all robustness integration tests pass; no division-by-zero or hangs.

- [ ] T010 [P1] [US1] Validate contracts and data integrity across all artifacts.
    - Implement/extend `tests/contract/test_schema_validation.py` validating every results CSV and stats JSON against the schemas in `specs/001-llmxive-follow-up-extending-memory-is-re/contracts/`.
    - Run `code/scripts/audit_no_fallbacks.py` scanning `code/data/` and `code/models/` for any try/except or conditional synthetic-data fallback; the script must raise if fallback logic is found.
    - Verify streaming vs. in-memory loader equivalence on a small fixed subset via `tests/integration/test_streaming_integrity.py`.
    - Verification: all contract tests, the audit script (exit 0), and integrity tests pass.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 [P3] [US1] Aggregate results and write the methods/results account.
    - Implement `code/scripts/aggregate_results.py` → `data/processed/report_data.json` with keys `accuracy_delta`, `node_reduction_pct`, `statistical_significance`, `inflection_point` (verified by `tests/unit/test_report_data.py::test_report_schema`).
    - Write `docs/research_report.md` describing methods, actual measured results (linked to the result files), the sensitivity sweep, the noisy-graph robustness check, negative findings, and limitations (associational framing, fixed sample size / power limits, benchmark ground-truth validity caveat, top-K sampling scope).
    - Verification: report cites actual values from `data/processed/` artifacts; `code/scripts/verify_docs.py` passes.

- [ ] T012 [P1] [US1] Re-run the documented workflow end-to-end and document the paper-stage handoff.
    - Update `code/scripts/run_pipeline.py` to orchestrate: download → graphs → noise → baseline → lazy (sweep) → greedy → noisy runs → stats → report, with explicit dependency assertions (`validate_intermediate_artifacts()` checking `graphs_raw.json`, `triples_raw.jsonl`, `graph_noise_42.json` before execution) and correct ordering (stats only after all result CSVs).
    - Re-run the full pipeline from declared inputs; confirm all expected artifacts regenerate and `code/scripts/verify_reproducibility.py` confirms deterministic outputs (fixed seeds).
    - Document the paper-stage handoff in `docs/research_report.md`: required tables (strategy comparison, statistical tests, sensitivity sweep), figures (`threshold_sensitivity.png`), and the limitations section — layout/PDF/publication remain with the paper pipeline.
    - Verification: `tests/integration/test_pipeline_order.py` and a clean re-run produce all artifacts listed above.

## Dependencies and requirement coverage

| Requirement | Task(s) | Command demonstrating completion |
|---|---|---|
| FR-001 (data download, noise injection) | T001, T002 | `python code/data/download_locomo.py`; `python code/data/generate_noisy_graphs.py` |
| FR-002 (Full baseline) | T003, T005, T006 | `python code/run_baseline.py` |
| FR-003 (Lazy + threshold logging) | T003, T004, T006 | `python code/run_lazy.py --thresholds 0.5,0.6,0.7,0.8` |
| FR-004 (Greedy) | T003, T006 | `python code/run_greedy.py` |
| FR-005/FR-006 (statistics) | T007 | `python code/scripts/generate_stats_report.py` |
| FR-007 (timeout, robustness) | T004, T009 | `pytest tests/integration/test_hard_timeout.py` |
| SC-001–SC-005 | T006, T007, T008, T009 | artifacts under `data/processed/` |

Execution order: T001 → T002 → (T003, T004) → T005 → T006 → T007 → T008/T009/T010 → T011 → T012. Statistical analysis (T007) strictly follows result generation (T006). All previously verified unit/integration tests are retained as verification steps within the consolidated tasks above; completed checked work is preserved and not re-tasked.
