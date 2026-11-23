# Tasks: [Research question]

**Inputs**: The active `spec.md`, `plan.md`, original research idea, existing
artifacts, and concrete verification/reviewer feedback.

This is a research implementation plan. Replace the examples below with the
smallest complete study that satisfies the specification. Target 8–15 substantive
tasks by grouping related changes; fewer are appropriate when little work remains.
Do not omit scientific requirements to meet a task count. If more tasks are
necessary, explain the scientific dependency that prevents grouping them.

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`.
Use story labels only for requirements already in the specification. `[P]` means
different files and no dependencies; tasks editing one file are sequential.
Paths are relative to the project directory, not the llmXive repository. Reuse
existing source locations; for a new study prefer `code/`, `code/tests/`, and
`data/results/`. Do not create a second `src/` tree beside working `code/src/`.

Each task names its scientific requirement, concrete output and observable check.
Bundle setup and focused tests with the implementation they support. Do not create
standalone tasks for empty directories, generic API scaffolding, logging,
packaging, release automation or linting unless the study requires those artifacts.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Run an executable analysis on valid, small real inputs early. An
explicitly authorized mathematical or simulation study uses its specified inputs.

- [ ] T001 Establish the existing code layout and dependencies, document a runnable command in the active feature's `quickstart.md`, and validate input provenance or the specified mathematical domain.
- [ ] T002 Implement the primary computation and its focused correctness tests in the source/test files named by the plan. Include invalid-input handling required by the specification.
- [ ] T003 Connect the entry point to the computation and run a small valid case, producing real result rows under `data/results/` with required fields and units.

**Checkpoint**: The documented command executes and its numerical outputs can be
checked. Do not start report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 Run the complete specified parameter/data domain and required comparisons, preserving every population, baseline and scientific constraint from the specification.
- [ ] T005 Add the necessary independent correctness, sensitivity and runtime checks; execute them and record actual outcomes alongside the result artifacts.
- [ ] T006 Generate the specified tables and figures directly from the validated outputs, including uncertainty or limitations where required.

**Checkpoint**: All required runs complete and the artifacts match the actual
computations. Put checks after their prerequisites; avoid separate overlapping
tasks that repeatedly replace the same analysis driver.

## Phase 3: Reproducible results and paper handoff

- [ ] T007 Write a concise methods/results account linked to the actual output cells and figure files. Describe negative findings, failures and limitations honestly.
- [ ] T008 Re-run the documented workflow from its declared inputs, confirm the required tests and artifact checks, and document the paper-stage handoff.

Paper layout, PDF compilation, peer review and publication are subsequent pipeline
stages. Keep their requirements in the handoff; do not duplicate those tasks here.
The platform manages its own state, artifact tracking and CI. Research scripts
must not rewrite the platform's project-state schema.

## Dependencies and requirement coverage

Replace this section with a short mapping of specification requirements to the
tasks that satisfy them, the commands that demonstrate completion, and any
necessary execution order. Do not add requirements absent from the study.

## Revision behavior

Preserve working artifacts and already verified requirements. Carry forward their
identities and status; do not erase completed work to make the list look shorter.
Use the precise failing command or verifier diagnosis to repair affected tasks.
Consolidate redundant pending tasks without dropping their acceptance criteria.
A narrow implementation failure is not a reason to rebuild the project skeleton,
rewrite unrelated modules, or expand the study into an application framework.
