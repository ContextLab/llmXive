# Tasks: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

**Input**: Design documents from `/specs/001-leptophilic-dm-g2/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by phase and user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Research & Data Strategy

**Purpose**: Verify dataset availability and define physics constants.

**Independent Test**: Run Reference-Validator Agent on all citations; verify Yukawa solver strategy.

- [ ] T001 [P] Run Reference-Validator Agent on all citations in `idea/`, `technical-design/`, `implementation-plan/`, and `paper/` (Constitution II). <!-- ATOMIZE: requested -->
- [ ] T002 [P] Implement numerical Yukawa potential solver for validation (Plan 0.2).
- [ ] T003 [P] Define Adaptive Mesh Refinement (AMR) strategy for grid convergence (Plan 0.3).
- [ ] T004 [P] Verify dataset availability for Planck, Xenon1T, and LEP; document fallback strategies.

**Checkpoint**: Research strategy validated; data sources confirmed.

---

## Phase 1: Data Model & Contracts

**Purpose**: Define schemas for inputs/outputs.

**Independent Test**: Generate and validate `LEP_Exclusion_Data` schema; define `RelicLookupTable` schema.

- [ ] T005 [P] Generate and validate `LEP_Exclusion_Data` schema (Plan 1.1).
- [ ] T006 [P] Define `RelicLookupTable` schema (Plan 1.2).
- [ ] T007 [P] Define `ParameterPoint` schema (FR-001, FR-005).

**Checkpoint**: Data models defined and validated.

---

## Phase 2: Core Physics Implementation (User Story 4 - Relic Density Validation)

**Purpose**: Implement analytic and numeric functions, specifically for relic density validation and pre-computation.

**Independent Test**: Run `validate_relic_density.py` with resonance points; verify error ≤ 5%.

### Implementation for User Story 4

- [ ] T008 [US4] Implement `code/physics/delta_a_mu.py` for analytic one-loop calculation (FR-001, US-2 benchmark).
- [X] T009 [US4] Implement `code/physics/cross_section.py` for σ_SI calculation including convolution method for Xenon1T limits (FR-003, FR-015).
- [X] T010 [US4] Implement `code/physics/relic_density.py` with manual RK4 integration (FR-010) and Sommerfeld enhancement via Hulthen potential (FR-002). **SCOPE: Pre-computation and Validation ONLY.**
- [ ] T011 [US4] Implement thermal averaging of Sommerfeld factor <σv> over Maxwell-Boltzmann distribution (FR-002).
- [ ] T012 [US4] Implement `code/physics/relic_reference.py`: A high-precision numerical solver (manual RK4) to generate benchmark data for validation. **Output: `data/relic_reference_benchmarks.csv`.**
- [ ] T013 [US4] Implement `code/validation/validate_relic_density.py` to compare RK4 results against high-precision reference solver benchmarks for resonance points.
- [ ] T014 [US4] Generate `relic_lookup.csv` pre-computed tables using Hulthen approximation (FR-011, FR-014).
- [ ] T015 [US4] Validate lookup table generation process against the high-precision reference solver (T012) to ensure < 10% error (FR-014, SC-008).
- [ ] T016 [US4] Add logic to flag "approximation uncertainty high" if error > 10% in resonance region (FR-014).
- [ ] T017 [US4] Implement logic to flag "physically undefined" points if hadronic matrix element conversion is invalid (FR-013).

**Checkpoint**: Relic density calculation is validated and tables are ready for the main scan.

---

## Phase 3: User Story 5 - Validate Methodological Rigor and Search Space Definition (Priority: P5)

**Goal**: Ensure grid density is sufficient to capture narrow viable bands and no multiplicity corrections are applied.

**Independent Test**: Run grid convergence study and verify ≥ 95% confidence in capturing viable regions; confirm no Bonferroni corrections in code.

### Implementation for User Story 5

- [ ] T018 [US5] Define coarse and fine grid parameters in `code/config.py` (FR-012, SC-006).
- [ ] T019 [US5] Implement `code/scan/grid_generator.py` to create grid with Adaptive Mesh Refinement (AMR) strategy (FR-012, Plan 3.2).
- [ ] T020 [US5] Implement logic to execute the convergence study: run the scan pipeline at multiple grid densities (coarse, medium, fine), compare viable region overlap, and determine the minimum density required to capture ≥ 95% of the fine-grid viable region. **Output: `data/convergence_study_results.json`.**
- [ ] T021 [US5] Generate convergence report confirming ≥ 95% confidence in grid density (US-5, SC-006) and output the final grid parameters to be used by the main scan.
- [ ] T022 [US5] Audit `run_scan.py` and `constraints.py` to ensure NO multiplicity corrections (e.g., Bonferroni) are applied to results (FR-008, US-5). **Output: `audit_report.md`.**

**Checkpoint**: Grid strategy is validated and scientifically rigorous. Final grid parameters are defined for US1.

---

## Phase 4: User Story 1 - Perform a Complete Parameter Scan (Priority: P1) 🎯 MVP

**Goal**: Execute the full grid scan and output viable points and contour plots within 30 minutes on 2-core CPU.

**Independent Test**: Execute `python run_scan.py` on a fresh runner; verify `viable_points.csv` exists and `viable_region.png` is generated within 30 mins.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US1] Unit test for constraint application logic (Planck, Xenon1T, LEP) in `tests/unit/test_constraints.py`.
- [ ] T024 [P] [US1] Unit test for `delta_a_mu` calculation against hardcoded benchmark values in `tests/unit/test_delta_a.py`.

### Implementation for User Story 1

- [ ] T025 [US1] Fetch and verify checksum of raw LEP source data (Ref [2014]) (FR-004, Constitution II).
- [ ] T026 [US1] Parse/convert raw LEP source to `data/raw/lep_limits.parquet` (FR-004).
- [ ] T027 [US1] Load `lep_limits.parquet` into `ConstraintDataset` model (depends on T007).
- [ ] T028 [US1] Implement `code/scan/grid_generator.py` to create the parameter grid using the FINAL grid parameters determined by T021 (FR-012, US-5).
- [ ] T029 [US1] Implement `code/scan/interpolate.py` for linear interpolation of pre-computed relic density tables (FR-011).
- [ ] T030 [US1] Implement `code/physics/constraints.py` to apply Planck, Xenon1T (hardcoded curve fallback), and LEP limits (FR-004, FR-005).
- [ ] T031 [US1] Implement `code/scan/run_scan.py` main entry point: generate grid, interpolate, apply constraints, filter viable points, save `viable_points.csv`.
- [ ] T032 [US1] Implement `code/reporting/plot_utils.py` to generate `viable_region.png` (m_V vs g contour) with high-resolution imaging, labels, and legend (FR-006, SC-004).
- [ ] T033 [US1] Add error handling for "no viable region" case and logging of grid configuration (FR-007).
- [ ] T034 [US1] Integration test for scan pipeline execution and output file generation in `tests/integration/test_scan_pipeline.py`. **Test function: `test_run_scan_generates_viable_points`. Asserts `viable_points.csv` exists and has >0 rows after running `run_scan.py`.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 5: User Story 2 - Validate Analytic Δaₘᵤ Implementation (Priority: P2)

**Goal**: Cross-check the computed one-loop contribution against benchmark values from Ref [2014].

**Independent Test**: Run `validate_delta_a.py` with benchmark point (m_χ=10 MeV, m_V=100 MeV, g=10⁻³) and verify Δa_μ error ≤ 2%.

### Implementation for User Story 2

- [ ] T035 [US2] Implement `code/validation/validate_delta_a.py` script to load benchmark parameters, compute Δa_μ, and compare to Ref [2014] value.
- [ ] T036 [US2] Add logging of relative error and pass/fail status to `validation.log` (SC-002).

**Checkpoint**: At this point, User Story 2 is validated independently.

---

## Phase 6: User Story 3 - Generate a Reproducible Report (Priority: P3)

**Goal**: Produce a PDF report summarizing scan outcomes, constraints, and reproducibility metadata.

**Independent Test**: Run `make_report.py` and verify `g2_dm_report.pdf` contains required sections and matches latest scan outputs.

### Implementation for User Story 3

- [ ] T037 [US3] Implement `code/reporting/make_report.py` to aggregate scan results, plots, and configuration into `g2_dm_report.pdf`.
- [ ] T038 [US3] Ensure report includes: viable point count, contour plot, citations for Planck/Xenon1T/LEP/SM g-2, scan config, and Xenon1T fallback mechanism (US-3).
- [ ] T039 [US3] Implement reproducibility section in report: data-source DOIs, script SHA-256, exact grid specs (SC-005, FR-007).
- [ ] T040 [US3] Run Reference-Validator Agent on final report citations (Plan 4.3).
- [ ] T041 [US3] Log configuration and data checksums (FR-007).
- [ ] T042 [US3] Verify report generation handles "no viable region" case gracefully with justification (US-3 edge case).

**Checkpoint**: User Story 3 delivers the final documentation artifact.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Add unit tests for `cross_section.py` (Helm form factor) and `constraints.py` (Xenon1T fallback).
- [ ] T044 [P] Performance optimization: verify `run_scan.py` completes in ≤ 30 mins on 2-core CPU (SC-001).
- [ ] T045 [P] Documentation: Update `README.md` with quickstart instructions and data directory structure.
- [ ] T046 [P] Final integration test: Run full pipeline from scratch (clean data dir) to `viable_points.csv` and `g2_dm_report.pdf`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately.
- **Phase 1 (Data Models)**: Depends on Phase 0 completion.
- **Phase 2 (Relic Density)**: Depends on Phase 1. Generates tables for Phase 4.
- **Phase 3 (Grid Strategy)**: Depends on Phase 1. Defines grid for Phase 4.
- **Phase 4 (Scan)**: Depends on Phase 2 (tables) and Phase 3 (grid).
- **Phase 5 (Delta a_mu)**: Independent, can run in parallel with Phase 2/3.
- **Phase 6 (Reporting)**: Depends on Phase 4 (scan results).
- **Phase 7 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 5 (P5)**: **CRITICAL**. Must be completed first to define the grid parameters (T021) used by US1.
- **User Story 4 (P4)**: Must be completed to generate `relic_lookup.csv` required by US1.
- **User Story 1 (P1)**: Depends on US5 (grid definition) and US4 (tables).
- **User Story 2 (P2)**: Independent physics validation.
- **User Story 3 (P3)**: Depends on US1 (scan results) and US4 (tables).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2 (US4) & Phase 3 (US5)**: Can be worked on in parallel by different developers (Tables vs Grid Strategy).
- **Phase 4 (US1)**: Can only start once T021 (Grid Definition) and T014 (Lookup Tables) are complete.
- **Phase 5 (US2)**: Independent, can run in parallel with US4/US5/US1.
- **Phase 6 (US3)**: Can run in parallel once US1 is complete.

---

## Parallel Example: Physics Implementation

```bash
# Developer A: Relic Density (US4)
Task: "Implement code/physics/relic_density.py with manual RK4 integration (FR-010)"
Task: "Implement code/physics/relic_reference.py (high-precision solver for validation)"

# Developer B: Grid Strategy (US5)
Task: "Implement code/scan/grid_generator.py with AMR logic (FR-012)"
Task: "Generate convergence report (US-5)"

# Developer C: Analytic Calculation (US2)
Task: "Implement code/physics/delta_a_mu.py (FR-001)"
Task: "Implement code/validation/validate_delta_a.py (US-2)"
```

---

## Implementation Strategy

### MVP First (User Story 5 + 4 + 1)

1. Complete Phase 0: Research
2. Complete Phase 1: Data Models
3. **Parallel**: Complete Phase 2 (US4 - Tables) and Phase 3 (US5 - Grid)
4. Complete Phase 4 (US1 - Scan) using the tables and grid from above
5. **STOP and VALIDATE**: Run `run_scan.py` and verify `viable_points.csv`
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Phase 1 → Foundation ready
2. Add Phase 2 (Relic Tables) + Phase 3 (Grid Strategy) → Physics engine ready
3. Add Phase 4 (Scan) → Core deliverable (MVP!)
4. Add Phase 5 (Validation) → Confidence in physics
5. Add Phase 6 (Report) → Final documentation
6. Add Phase 7 (Polish) → Hardening

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Phase 1 together
2. Once Phase 1 is done:
 - Developer A: Phase 2 (Relic Density & Tables)
 - Developer B: Phase 3 (Grid Convergence & Strategy)
 - Developer C: Phase 5 (Delta a_mu Validation)
3. Once A and B are done:
 - Developer C (or new dev): Phase 4 (Main Scan Pipeline)
4. Once Phase 4 is done:
 - Developer D: Phase 6 (Reporting)
5. All stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All tasks involving heavy computation (RK integration) must be optimized for CPU-only, limited-core, constrained RAM environment. Use pre-computed tables (FR-011) to avoid re-integrating during the scan.
- **Data Sources**: LEP data must be fetched from verified URL or generated from paper tables (T025-T026). Xenon1T uses hardcoded curve (FR-003) with optional live fetch fallback. Planck uses standard constants. No fabricated data.
- **Validation**: The "non-perturbative solver" requirement is satisfied by the high-precision reference solver (T012) implemented for validation purposes only.