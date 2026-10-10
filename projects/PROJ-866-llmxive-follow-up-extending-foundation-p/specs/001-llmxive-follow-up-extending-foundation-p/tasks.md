# Tasks: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Input**: Design documents from `/specs/001-policy-compression-tradeoff/`
**Prerequisites**: plan.md, spec.md

## Status summary

The simulation pipeline (generation, Oracle, full/compressed execution, GLMM analysis, integrity checks) is implemented and verified. Remaining work repairs four rejected verification items: the final state-registry update (duplicate T051 entries consolidated into one task), invalid-workflow exclusion verification (T067), README documentation (T071), and the final reproducibility re-run and paper handoff (T072 split). Additional tasks address earlier coverage and consistency concerns.

## Completed work (verified — preserved)

- Project scaffolding, contracts (`contracts/workflow.schema.yaml`, `execution_log.schema.yaml`, `analysis_results.schema.yaml`), tokenizer wrapper (`code/utils/token_counter.py`, cl100k_base, FR-009), checksum utilities (T054), CLI orchestrator (`code/main.py`), and benchmark logging (FR-007/SC-005).
- Synthetic workflow generation with deterministic seeding, uniform depth distribution, invalid-workflow flagging (FR-001, US-1).
- Independent Oracle Policy Engine (FR-008), Full Context engine with ground-truth logs (FR-002), Compressed Context engine with constrained BFS/DFS and edge-case `[deferred]` handling (FR-003, US-2).
- Token counting via tiktoken and context-reduction calculation (FR-004, FR-009).
- Filtering/binning, GLMM with random intercepts, monotonicity check, multiple-comparison correction, threshold detection with bootstrapping rounded to 2 decimals (FR-005, FR-006, US-3).
- Oracle independence checks (AST static analysis, runtime isolation), data consistency check (T062), edge-case audit (T066), reproducibility report (T047/T065), full pytest suite, schema validation, and hygiene audits.

## Remaining tasks

### Phase 1: Core result regeneration
- [ ] T070 [US3] **Regenerate and verify core result artifacts**: Run the analysis pipeline (`python code/main.py --analyze`) to produce `data/results/tradeoff_curve.csv` **and** `data/results/threshold_report.json`. The JSON file must contain keys `threshold_pct`, `ci_lower`, `ci_upper` and respect the spec‑mandated error bound (≤1 % policy‑violation rate). **Dependency**: existing analysis implementation (complete). <!-- FAILED-IN-EXECUTION: code/main.py exit=2 -->

### Phase 2: Validation and state update
- [ ] T067 [US1] **Verify invalid workflow exclusion**: Execute `code/utils/verify_invalid_exclusion.py` which cross‑references workflow IDs marked `is_valid=false` in `data/raw/workflows.json` against the per‑run records underlying `data/results/tradeoff_curve.csv`. The script must ensure no invalid workflow contributes to any row in the CSV and write `data/results/invalid_exclusion_report.json` with keys `invalid_workflow_count`, `excluded_count`, `status`. **Dependency**: T070.

- [ ] T051 [P] **Final state registry update (consolidated)**: After T072c completes, compute the SHA‑256 reproducibility hash of the entire `data/` directory (using `code/utils/checksum_utils.py`) and record it as `reproducibility_hash` together with `final_verification_timestamp` (ISO 8601) in `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`. **Dependency**: T072c. Clarified that this task runs **in parallel** with T071 only.

### Phase 3: Documentation
- [ ] T071 [P] **README reproducibility section**: Add a "Reproducibility and Verification" section to `README.md` describing the full pipeline command, checksum verification, interpretation of `data/results/reproducibility_report.json`, and how to run the invalid‑exclusion check (T067). **Dependency**: T067.

### Phase 4: End‑to‑end verification and handoff (split)
- [ ] T072a **End‑to‑end pipeline verification run**: Re‑run the full workflow (`python code/main.py --generate --compress --analyze`) on a fresh runner, ensure all pytest and schema validation pass, and record wall‑clock metrics in `data/results/run_metrics.json`. Verify that runtime does not exceed the spec‑stated **6 hours** on the CI runner. **Dependency**: T051. <!-- ATOMIZE: requested -->

- [ ] T072b **Results documentation**: Write `specs/001-policy-compression-tradeoff/results.md` summarizing methods, outcomes, edge‑case handling, and the safe‑operating‑zone threshold (≤1 % error). All figures and tables must be generated directly from `data/results/tradeoff_curve.csv`. **Dependency**: T072a.

- [ ] T072c **Paper‑stage handoff note**: Produce a handoff markdown `specs/001-policy-compression-tradeoff/paper_handoff.md` linking to the generated figures, tables, and the reproducibility hash from T051, confirming compliance with Constitution Principles IV and V. **Dependency**: T072b.

### Phase 5: Additional coverage tasks
- [ ] T077 **Adaptive sampling in workflow generator**: Extend `services/generator.py` to implement adaptive sampling that densifies workflow depth distribution near the 1 % error‑rate threshold identified by analysis. Document the approach in `docs/adaptive_sampling.md`. **Dependency**: T070 (uses threshold info).

- [ ] T078 **Provide tradeoff‑curve schema**: Add `contracts/tradeoff_curve.schema.yaml` defining columns `reduction_pct`, `error_rate`, `depth`, `ci_lower`, `ci_upper`. Update `code/main.py` to validate `data/results/tradeoff_curve.csv` against this schema. **Dependency**: T070.

- [ ] T079 **Migrate source to match plan**: Create a `src/` mirror of the current `code/` package (including `models/`, `services/`, `cli/`, `lib/`) and add a compatibility shim (`code/__init__.py` importing from `src/`). Update the plan documentation (outside this repo) to reflect the `src/` layout, satisfying the plan’s Project Structure while preserving the constitution‑mandated `code/` entry point. **Dependency**: none.

- [ ] T080 **Tokenizer name consistency**: Ensure all code and documentation reference the correct tokenizer model `cl100k_base`. Update `code/lib/utils.py` docstring and any README mentions. **Dependency**: none.

- [ ] T081 **Integrate pm4py for log verification**: Add a usage of `pm4py` in `services/executor.py` to generate and validate execution logs against the Oracle Policy Engine, satisfying the plan’s listed dependency. Include a unit test `tests/unit/test_pm4py_integration.py`. **Dependency**: none.

- [ ] T082 **Threshold bound enforcement**: Add a verification step in `services/analyzer.py` that asserts the identified safe‑operating‑zone threshold yields a policy‑violation error rate ≤ 1 % as required by SC‑004. Fail the pipeline if the bound is exceeded. **Dependency**: T070.
