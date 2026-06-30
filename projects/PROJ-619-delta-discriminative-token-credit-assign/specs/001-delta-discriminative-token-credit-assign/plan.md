# Implementation Plan: DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

**Branch**: `619-delta-discriminative-token-credit-assign` | **Date**: 2026-05-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/619-delta-discriminative-token-credit-assign/spec.md`

## Summary

This project validates the build infrastructure and code structure of the "DelTA" (Discriminative Token Credit Assignment) paper reproduction. The primary requirement is to verify that the vendored `dlbook_notation` submodule initializes correctly, compiles on a CPU-only CI environment without GPU dependencies, and produces the expected LaTeX artifacts (PDFs). The technical approach involves a shell-script-driven build pipeline (`make.sh`) that clones the submodule, checks for system dependencies (TeX Live), and generates static documentation artifacts. No machine learning training or dynamic model inference is performed in this phase; the scope is strictly limited to the verification of the codebase structure and build process as described in the specification.

## Technical Context

**Language/Version**: Bash (5.0+), LaTeX (TeX Live 2023+), Git (2.30+)  
**Primary Dependencies**: `texlive-full` (system package), `git`, `make`  
**Storage**: Local filesystem (for artifacts and submodule)  
**Testing**: Shell unit tests (`bats` or `shunit2`), file existence assertions, regex scanning for GPU keywords  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Build/Verification Script  
**Performance Goals**: Build completes < 10 minutes; RAM usage < 1GB (LaTeX compilation is lightweight); No GPU usage.  
**Constraints**: Must run on CPU-only CI (cores, sufficient RAM); No external network downloads during build (except git submodule); Must fail gracefully with specific error codes if dependencies are missing.  
**Scale/Scope**: Single repository validation; Small output artifacts.

## Constitution Check

*Gates determined based on constitution file*

*Note: The project constitution file (`constitution.md`) was not provided in the input. Per the SSoT protocol, this constitutes a gap. In the absence of a formal constitution, this plan adheres to standard scientific reproducibility principles: Transparency, Verifiability, and Resource Efficiency. A formal `constitution.md` is required for future SSoT compliance.*

1.  **Transparency**: The plan explicitly maps every Functional Requirement (FR-001 to FR-006) to a specific build step or validation check. No "black box" steps are introduced.
2.  **Verifiability**: Success is defined by the generation of specific file artifacts (`notation_example.pdf`, `venn.pdf`) with measurable properties (size > 50KB) and the existence of a `reproduction_report.md` with a defined status field.
3.  **Resource Efficiency**: The plan strictly adheres to the CPU-only constraint. It explicitly forbids GPU/CUDA calls and ensures the LaTeX build process (which is the heaviest operation) fits within the RAM / 6-hour limit.
4.  **Scope Adherence**: The plan does not attempt to re-train the DelTA model or run the 7 benchmarks mentioned in the paper's abstract. It focuses solely on the *mechanism* and *build process* as scoped in the User Stories.

## Project Structure

### Documentation (this feature)

```text
specs/619-delta-discriminative-token-credit-assign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── build-artifacts.schema.yaml
│   └── reproduction-report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── dlbook_notation/     # Vendored submodule (populated by setup-plan.sh)

scripts/
├── setup-plan.sh        # Mechanical entry point
├── validate-build.sh    # Validates artifacts and dependencies
└── generate-report.sh   # Generates reproduction_report.md

Makefile                 # Wrapper for make.sh if needed
reproduction_report.md   # Generated output
```

**Structure Decision**: A flat structure with a dedicated `external/` directory for the submodule is chosen to isolate vendored code. The `scripts/` directory contains the validation logic to separate build orchestration from verification logic. This aligns with the requirement for a clear separation between the "build" (make.sh) and the "validation" (reproduction report generation).

## Complexity Tracking

*No complexity violations detected. The scope is limited to a build verification task.*

## Phase Breakdown

### Phase 0: Environment Initialization & Dependency Check
- **Goal**: Ensure the CI runner has `texlive-full` and `git` configured.
- **Steps**:
  1. Check for `pdflatex`, `bibtex`, `make`.
  2. If missing, exit with specific error code (FR-005) and message (e.g., "Error: pdflatex not found. Install texlive-full").
  3. Initialize `external/dlbook_notation` submodule.
  4. Verify submodule commit hash matches `.gitmodules` (FR-001). This step must validate that the hash is a 40-character hex string as defined in the `SubmoduleMetadata` entity in `data-model.md`.
- **FR/SC Mapping**: FR-001, FR-005, SC-004.

### Phase 1: Build Execution
- **Goal**: Execute `make.sh` to generate PDFs.
- **Steps**:
  1. Run `./make.sh` in `external/dlbook_notation`.
  2. Monitor for GPU/CUDA errors (FR-006).
  3. Verify execution time < 6 hours (SC-001).
  4. Check for generation of `notation_example.pdf` and `venn.pdf`.
- **FR/SC Mapping**: FR-002, FR-003, SC-001, SC-002, SC-005.

### Phase 2: Artifact Validation & Report Generation
- **Goal**: Generate `reproduction_report.md` confirming success status.
- **Steps**:
  1. Scan generated PDFs for size > 50KB (FR-003, SC-002). This step validates the `BuildArtifact` entity defined in `data-model.md`, ensuring `size_bytes` > 50,000.
  2. Scan source code for `device="cuda"` or `load_in_8bit` (FR-006, SC-005).
  3. Compile findings into `reproduction_report.md` with "Status: Success/Partial/Failed" (FR-004, SC-003).
  4. Explicitly note that the benchmarks were not re-run. but the mechanism exists (US-3).
- **FR/SC Mapping**: FR-004, SC-003, US-3.

## Risks & Mitigations

- **Risk**: Missing LaTeX dependencies on CI.
  - *Mitigation*: Explicit check in Phase 0 with clear error messaging (FR-005).
- **Risk**: Submodule commit hash mismatch.
  - *Mitigation*: Verification step in Phase 0 aborts if hash does not match (FR-001).
- **Risk**: Build hanging or exceeding RAM.
  - *Mitigation*: Timeout wrapper (6h) and memory monitoring; LaTeX is generally low-memory, but a hard limit is enforced.