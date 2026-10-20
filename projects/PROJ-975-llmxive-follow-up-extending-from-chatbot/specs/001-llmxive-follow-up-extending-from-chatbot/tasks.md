# Tasks: llmXive follow-up – extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Inputs**: `spec.md`, `plan.md`, data-model and contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, verifier feedback on rejected tasks, and the reviewer's pruning-heuristic objection.

**Corrections applied in this revision**:
- Tasks no longer write to `state/...` (platform-owned; the earlier plan asked scripts to write artifact hashes into the state YAML — that produced stale shadows and is removed). Checksums are written to `data/raw/checksums.json` instead.
- The four verifier-rejected tasks (logger truncation, contract tests that never load real data files, missing schemas, missing data-generation serialization) are folded into consolidated tasks below with explicit "must load the real file" verification.
- Reviewer concern (freeman-dyson-simulated): FR-004 as specified prunes *dissimilar* unused skills, which inverts the curation intent. The spec remains authoritative, so FR-004 is implemented exactly as written, and a **redundancy-pruning variant** (remove unused skill whose *max* cosine similarity to a retained neighbor ≥ 0.70) is added as a comparison arm so the study empirically tests both directions of the heuristic.
- Scaffold-only tasks (directories, requirements, config, utils, placeholder docs) are dropped; the platform supplies common packages and `llmxive_toolkit` (`paths`, `get_logger`).

---

## Phase 1: Contracts, data generation, and first end-to-end run

- [ ] T001 [P] [US1] Create root-level contract schemas `contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/execution_log.schema.yaml`, and `contracts/metrics.schema.yaml` exactly matching the read-only schemas in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.
  *Verification*: `jsonschema.validate` succeeds on one minimal valid instance per schema; a pytest presence-test imports each file from `contracts/`.

- [ ] T002 [US1] Implement `code/generate_data.py` producing the real dataset: exactly 500 tasks in `data/raw/tasks.json` (unique `task_id`, `description`, `complexity` 3–5, `ground_truth_skills` 3–5, deterministic `solution_path` independent of any retrieval logic) and exactly 100 skills in `data/raw/skills.json` (unique `skill_id`, executable Python `code`, 768-dim `embedding` from the CPU-only sentence-transformers model, `usage_count=0`, ISO-8601 `last_used`). Enforce the configured overlap level (low: mean pairwise cosine < 0.30; medium: mean > 0.50 and ≥30% of pairs > 0.50; high: mean > 0.80 and ≥30% of pairs > 0.80) by iterative embedding adjustment, with pinned seeds. Include the memory-pressure guard: before embedding, estimate required RAM and raise `MemoryError("Memory Limit Exceeded")` if it would exceed the budget (never crash silently, never substitute synthetic stand-ins). Write SHA-256 checksums of both JSON files to `data/raw/checksums.json` (NOT to `state/`).
  *Verification*: script runs end-to-end; record counts are exactly 500 and 100; both files validate against `contracts/task.schema.yaml` and `contracts/skill.schema.yaml`; printed overlap statistics satisfy FR-002 for the requested level; checksums match recomputed digests.

- [ ] T003 [US1] Implement contract tests `tests/contract/test_schemas.py` that load the REAL generated files (not hard-coded samples): validate every object in `data/raw/tasks.json` against `contracts/task.schema.yaml` and every object in `data/raw/skills.json` against `contracts/skill.schema.yaml`; additionally assert the mean-pairwise-cosine overlap statistics for the active `OVERLAP_LEVEL` per FR-002.
  *Verification*: `pytest tests/contract/` fails when data files are absent or malformed and passes after T002 runs.

- [ ] T004 [US2] Implement `code/logging_config.py` with a complete `get_logger(name)` returning a CSV logger writing to `data/results/experiment_log.csv`, whose header contains ALL columns required by `contracts/experiment_log.schema.yaml` including `edge_case`, flushing after each record. No truncated function bodies.
  *Verification*: a small script logs one entry; the CSV header matches the schema exactly; `tests/contract/test_logging_schema.py` validates the written row.

- [ ] T005 [US2] Implement `code/agent.py`: load `data/raw/tasks.json` and `data/raw/skills.json`; for each task retrieve top-k=5 skills by cosine similarity; execute the retrieved skills in order and compare against `solution_path` to record success/failure; log `latency_ms`, deterministic `tokens_used`, `retrieval_precision` (Jaccard@5 vs ground-truth set), `retrieval_diversity` (inverse variance of top-5 cosine similarities), and `edge_case` tags (`missing_skill`, `maximal_overlap`, `memory_limit`, `null`). Handle the edge cases: maximal overlap (mean pairwise cosine ≥ 0.95) must not crash and reports retrieval precision 0 when no ground-truth skills are retrieved; a task requiring an absent skill must fail gracefully with a logged `missing_skill` reason and no hallucinated solution. Also write per-task execution logs to `data/results/execution_logs/*.jsonl` conforming to `contracts/execution_log.schema.yaml`.
  *Verification*: `python -m code.agent --library-size 50 --pruning false --task-sample 100` produces 100 schema-compliant CSV rows and JSONL entries; a printed per-run summary matches manual recomputation on a small subset.

## Phase 2: Complete experimental sweep and validation

- [ ] T006 [US2] Implement `code/pruning.py` exposing `prune_library(library) -> (pruned_library, false_prune_count)` implementing FR-004 exactly: remove a skill if `usage_count == 0` AND `min_cosine_similarity_to_any_other_skill_in_library < 0.70`, triggered after every 10 tasks; `false_prune_count` counts removed skills with similarity > 0.70 to any ground-truth skill of pending tasks. ALSO implement a `redundancy` variant (remove unused skill whose MAX similarity to a retained neighbor ≥ 0.70) to address the reviewer's objection that FR-004 deletes unique rather than redundant skills; both variants are selectable via a flag.
  *Verification*: `tests/unit/test_pruning.py` builds a synthetic library and asserts, for each variant, exactly the eligible skills are removed and `false_prune_count` matches manual expectation.

- [ ] T007 [US2] Add pruning-enabled mode to the agent: after every 10 tasks invoke the selected pruning variant; `library_size` in logs reflects the post-pruning active count; pruning events and variant are recorded. Run the full factorial sweep — library sizes {10, 30, 50, 100} × pruning {off, FR-004, redundancy-variant} × overlap {low, medium, high} — writing all runs to `data/results/experiment_log.csv` (append-only).
  *Verification*: the CSV contains all configuration blocks; with pruning on, `library_size` decreases at 10-task intervals; `false_prune_count ≥ 0`; every row validates against `contracts/experiment_log.schema.yaml`.

- [ ] T008 [US3] Implement `code/analysis.py` reading `data/results/experiment_log*.csv`: (1) fit piecewise linear regression with a single breakpoint on task-level binary success vs. library size for the PRIMARY configuration (high overlap, pruning disabled, sizes 10/30/50/100), with 1 000 bootstrap resamples for a confidence interval on x₀; (2) compute VIF for predictors "library size" and "total redundancy" (sum of pairwise cosine similarities in the active library); (3) paired pruning-efficacy test (baseline vs. each pruning variant at the same library size) with p-value; (4) write `data/results/analysis_report.json` (sole source for all tables/figures) containing `breakpoint`, `breakpoint_ci`, `vif`, `pruning_pvalue` per variant, and `performance_recovery_delta`; (5) run the granularity-validation sweep (denser 10-unit library-size grid on a task subset) reported as supplemental, not replacing the primary breakpoint.
  *Verification*: `python -m code.analysis` succeeds; `breakpoint` ∈ [10, 100]; VIF values reported and interpretable (SC-006 flags VIF < 5.0); p-values ∈ [0, 1]; `tests/contract/test_analysis_output.py` validates the JSON structure.

- [ ] T009 [US3] Add the sensitivity sweep to `code/analysis.py`: pruning intervals {5, 10, 15} tasks, recompute the breakpoint each time, record VIFs in `data/results/sensitivity_report.json`; the primary breakpoint in `analysis_report.json` remains the baseline-configuration value per plan.md, with sweep estimates reported as supplemental.
  *Verification*: `sensitivity_report.json` contains entries with `interval`, `breakpoint`, `vif`; the selection/reporting logic matches the plan's primary-vs-supplemental rule.

- [ ] T010 [US2] Execute the complete pipeline end-to-end on the full 500-task set and all configurations, and run independent correctness/sensitivity/runtime checks: verify aggregate metrics (success rate, mean latency, precision@5, false_prune_count per `contracts/metrics.schema.yaml`) computed from the raw logs, and record actual runtime and peak memory alongside the results.
  *Verification*: aggregated metrics file validates against `contracts/metrics.schema.yaml`; recomputed aggregates match the analysis inputs; runtime fits the CI budget (SC-005).

- [ ] T011 [P] [US2] Generate the study's tables and figures directly from `data/results/analysis_report.json` and the raw logs: success-rate vs. library-size curve with fitted breakpoint and bootstrap CI, pruning-variant comparison, retrieval precision/diversity trends, and VIF table. Save under `data/results/` and `figures/`.
  *Verification*: every figure/table is generated by script from the actual result files (no hand-entered values); scripts re-run cleanly.

## Phase 3: Reproducible results and paper handoff

- [ ] T012 [US3] Write the methods/results account in `specs/001-llmxive-follow-up-extending-from-chatbot/research.md` (or a results section linked from it), referencing actual output cells and figure files. Report honestly: the primary breakpoint estimate with CI, pruning efficacy per variant (including whether FR-004's dissimilarity-based rule underperforms the redundancy variant, per the reviewer's concern), VIF diagnostics, negative findings, and the synthetic-environment limitation (causal within simulation, associative beyond).
  *Verification*: every numeric claim in the account traces to a field in `analysis_report.json` or `sensitivity_report.json`.

- [ ] T013 [P] Update `specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md` with the exact runnable command sequence (`python -m code.generate_data`, `python -m code.agent ...`, `python -m code.analysis`), environment variables (`OVERLAP_LEVEL`), expected output locations, and pinned seeds. Document the paper-stage handoff: figures/tables derive solely from `data/results/analysis_report.json`; layout, PDF compilation and publication belong to the paper pipeline.
  *Verification*: on a fresh checkout the documented commands run from scratch and produce all referenced artifacts; `pytest tests/` passes.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (500 tasks, ground truth) | T002, T003 | `python -m code.generate_data && pytest tests/contract/` |
| FR-002 (100 skills, overlap levels) | T002, T003 | same; overlap stats printed and asserted |
| FR-003 (sizes 10/30/50/100, metrics) | T005, T007, T010 | `python -m code.agent ...` full sweep |
| FR-004 (pruning heuristic) + reviewer variant | T006, T007 | `pytest tests/unit/test_pruning.py` |
| FR-005 (PLR breakpoint / tipping point) | T008, T009 | `python -m code.analysis` |
| FR-006 (precision, diversity) | T005, T010 | CSV columns validated by contract tests |
| FR-007 (VIF) | T008 | `analysis_report.json` `vif` field |
| Edge cases (maximal overlap, missing skill, memory guard) | T002, T005 | edge-case tags in logs; `MemoryError` test |
| SC-001–SC-006 | T005, T007–T010 | aggregated metrics + analysis report |

Execution order: T001 → T002 → T003/T004 (parallel) → T005 → T006 → T007 → T008 → T009 → T010 → T011/T012/T013 (T011–T013 partially parallel). No task writes to `state/` or `.github/`; the platform owns project state, artifact hashes, and CI.

## Revision behavior

Previously verified scaffolding (directories, requirements, config, utils) is subsumed by the platform and existing code and is not re-tasked. The four verifier-rejected items are consolidated into T001–T005 with load-the-real-file verification requirements. FR-004 is preserved verbatim per the specification; the reviewer's objection is answered empirically via the redundancy-variant comparison arm rather than by weakening the specified heuristic.
