# Implementation Plan: ArcANE

## Phases

1. **Phase 1: Setup** - Project initialization, directory structure, and basic tooling.
2. **Phase 2: Foundational** - Core infrastructure, data contracts, logging, and state tracking.
3. **Phase 3: User Story 1** - Axis definition and validation.
4. **Phase 4: User Story 2** - Probe generation and validation.
5. **Phase 5: User Story 3** - Experiment execution, judge calibration, and statistical analysis.
6. **Phase 6: Polish** - Documentation, performance, and cross-cutting concerns.
7. **Phase 7: Resolution** - Addressing specific feedback and CPU feasibility.

## Task Dependencies

- T001 (Structure) must be completed before any code is written.
- T002 (Dependencies) must be completed before running scripts.
- T004 (Data Dirs) is a prerequisite for data loading tasks.
- T009 (Gold Standard) is a prerequisite for Judge Calibration (T029).

## Execution Order

1. Run `setup_project_structure.py`
2. Run `setup_data_dirs.py`
3. Install dependencies (`requirements.txt`)
4. Run `download_gold_standard.py` (or `generate_gold_standard.py` if fetch fails)
5. Run `run_experiment.py`
