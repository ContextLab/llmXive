# Tasks: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-dream-state-learning-implementing-rem-li/contracts/`

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the environment and execute a thin, end-to-end training and evaluation run on real GLUE subsets to verify the Wake/Dream cycle.

- [ ] T001 Establish the project layout, pinned dependencies in `code/requirements.txt`, and `code/config.py` with CPU-only enforcement and memory limits (6.3 GB). <!-- FAILED-IN-EXECUTION: code/train.py exit=1 -->
    - Verification: `pip install -r code/requirements.txt` completes and `code/config.py` is importable without errors.
- [ ] T002a [US1] Implement core Wake/Dream logic: 20-step warm-up, BERT-style random token masking, DAE reconstruction loss combined with knowledge-distillation loss (Teacher-Student distribution matching), entropy-based batch retries, and perplexity-based dream phase skipping (skip if perplexity > 50 against held-out corpus). `code/models/trainer.py`, `code/data/augment.py`. <!-- FAILED-IN-EXECUTION: code/train.py exit=-1 (TIMEOUT) -->
    - Verification: Unit tests in `tests/unit/test_trainer.py` confirm warm-up duration, that low-entropy batches trigger retries, and that high-perplexity batches trigger a phase skip.
- [ ] T002b [US1] Implement the training CLI entry point `code/train.py` and integrate the `memory_monitor` to abort and checkpoint on OOM. `code/train.py`, `code/utils/memory_monitor.py`. <!-- FAILED-IN-EXECUTION: code/train.py exit=1 -->
    - Verification: Execute `python code/train.py` on a small GLUE subset; verify a model checkpoint is saved to `data/checkpoints/` and structured JSON logs are written to `data/logs/`.
- [ ] T003 [US2] Implement the few-shot evaluation pipeline and result logging for the QNLI validation set. `code/eval.py`, `code/eval/metrics.py`.
    - Verification: Run `python code/eval.py` on a saved checkpoint; verify `data/results/evaluation_result.json` is produced and conforms to `evaluation_result.schema.yaml`.

**Checkpoint**: The documented command in `quickstart.md` executes a full train-eval cycle and produces a numerical accuracy result in `data/results/`.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement the continuous-training baseline mode and a multi-run orchestrator to ensure identical real token exposure between regimes. `code/models/trainer.py`, `code/main.py`.
    - Verification: Integration test asserts that for a fixed seed, the baseline and experimental runs consume the exact same number of real training tokens.
- [ ] T005 [US2] Execute the full 5-seed experiment and compute the paired t-test, Cohen's d, and statistical power estimate, explicitly flagging results as 'insufficient power' if the held-out evaluation set contains fewer than 5 samples per seed. `code/main.py`, `data/results/statistical_report.json`.
    - Verification: Validate `statistical_report.json` against `statistical_report_schema.schema.yaml` and confirm the presence of `p_value`, `effect_size`, and the 'insufficient power' flag where applicable.
- [ ] T006 [FR-006] Conduct the temperature sweep across $[0.5, 1.0, 1.5, 2.0]$ and report the variance in final accuracy to isolate the consolidation effect. `code/main.py`, `data/results/variance_report.json`.
    - Verification: Check `variance_report.json` for numeric variance and mean accuracy across the four temperature settings.
- [ ] T007 [US3] Implement and run the resource audit to verify peak RSS $\le 6.3$ GB and total wall-clock time $\le 5$ hours. `code/utils/memory_monitor.py`, `code/scripts/verify_feasibility.sh`.
    - Verification: Run `verify_feasibility.sh` and assert a zero exit code; check `data/results/resource_audit.json` for peak memory and duration.
- [ ] T008 [P] Implement full contract validation for all 10 schemas and comprehensive unit tests for entropy and masking logic. `tests/contract/`, `tests/unit/`.
    - Verification: `pytest` passes with $\ge 90\%$ coverage for `code/models/` and `code/utils/` and all schema tests in `tests/contract/` pass.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 Finalize the `docs/architecture.md` defining the logical depth of consolidation, perform a PII scan of `data/`, and conduct a fresh-runner reproducibility check. `docs/architecture.md`, `quickstart.md`.
    - Verification: Run the workflow from `quickstart.md` on a clean environment; confirm all required result JSONs and checkpoints are generated.
- [ ] T010 [P] Modularize logging and data loading to separate concerns and improve maintainability. `code/utils/logging.py`, `code/data/data_loader.py`.
    - Verification: Code review confirms separation of I/O and training logic; `pytest` passes.
- [ ] T011 [P] Optimize batching and data loading to ensure maximum CPU efficiency and minimize I/O overhead. `code/data/data_loader.py`.
    - Verification: Compare training step time before and after optimization; verify no increase in memory usage.
- [ ] T012 [P] Implement security hardening, including strict input validation and PII scanning of data artifacts. `code/utils/security.py`.
    - Verification: Run PII scan script on `data/` and assert zero findings; test input validator with malformed JSON.

## Dependencies and requirement coverage

| Requirement | Task | Verification Command |
|-------------|------|---------------------|
| FR-001 (Wake/Dream Loop) | T002a, T002b | `python code/train.py` |
| FR-002 (DAE/Masking/KD) | T002a | `pytest tests/unit/test_trainer.py` |
| FR-003 (Baseline) | T004 | `python code/main.py --mode baseline` |
| FR-004 (Evaluation) | T003 | `python code/eval.py` |
| FR-005 (Memory Limit) | T002b, T007 | `bash code/scripts/verify_feasibility.sh` |
| FR-006 (Temp Sweep) | T006 | `python code/main.py --sweep` |
| FR-007 (Warm-up) | T002a | `pytest tests/unit/test_trainer.py` |
| SC-002 (T-Test/Power) | T005 | `pytest tests/unit/test_stats.py` |