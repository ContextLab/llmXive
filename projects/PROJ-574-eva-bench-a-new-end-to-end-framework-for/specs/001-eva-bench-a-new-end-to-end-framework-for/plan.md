# Implementation Plan: EVA-Bench Reproduction & Validation

**Branch**: `574-eva-bench-reproduction` | **Date**: 2024-05-22 | **Spec**: `specs/574-eva-bench-reproduction/spec.md`
**Input**: Feature specification for reproducing the `dlbook_notation` codebase and validating EVA-Bench artifacts.

## Summary

This project reproduces the core execution flow of the `dlbook_notation` vendored codebase (a LaTeX-based notation generator) to validate the "EVA-Bench" framework's documentation artifacts. The technical approach involves executing the `./make.sh` script on a CPU-only GitHub Actions runner, capturing build logs, verifying output artifacts (PDFs, logs) against size and content constraints, and generating a `reproduction_report.md` that documents success/failure and any discrepancies.

## Technical Context

**Language/Version**: Bash (scripting), LaTeX (document generation), Python (validation logic).  
**Primary Dependencies**: `texlive-full` (or equivalent TeX Live distribution), `git` (for submodules), `ghostscript` (PDF validation).  
**Storage**: File system (local build artifacts in `external/dlbook_notation/`).  
**Testing**: Shell script assertions, file size checks, text pattern matching (grep), PDF metadata inspection.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier).  
**Project Type**: Reproduction/Validation Script.  
**Performance Goals**: Execution time < 300 seconds (SC-001), zero GPU errors (SC-005).  
**Constraints**: No GPU/CUDA usage; strict CPU-only environment; max reasonable runtime.  
**Scale/Scope**: Single repository build; ~ output PDFs; < 10MB artifact size.

> The `dlbook_notation` codebase is assumed to be a LaTeX project. The "EVA-A" and "EVA-X" metrics are validated via text extraction from the generated PDF. This extraction logic is explicitly designed to populate the `metrics_present` object defined in `contracts/build_artifacts.schema.yaml`, ensuring alignment with the validation contract.

## Constitution Check

*Gates determined based on the project's constitution:*

**Status**: No `constitution.md` was provided for this project.
**Action**: In the absence of project-specific principles, the plan adheres to the default project integrity standards required for all reproduction efforts:

1.  **Reproducibility**: The build is deterministic by pinning the TeX Live version in the CI environment and running `make.sh` in a clean state.
2.  **Transparency**: The `reproduction_report.md` explicitly logs all warnings, exit codes, and discrepancies, fulfilling the requirement to document deviations.
3.  **Feasibility**: The plan strictly adheres to CPU-only constraints, avoiding any GPU-dependent libraries or heavy model training, ensuring it runs within the RAM / h limits.
4.  **Validity**: Artifact validation (SC-002, SC-004) is performed programmatically (file size, text presence) rather than relying on subjective visual inspection.

## Project Structure

### Documentation (this feature)

```text
specs/574-eva-bench-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── build_artifacts.schema.yaml    # Defines PDF/log constraints
│   └── reproduction_report.schema.yaml # Defines report structure
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── dlbook_notation/     # Vendored LaTeX codebase (submodule)
    ├── make.sh          # Entry script
    ├── *.tex            # Source files
    └── *.cls            # Class files

scripts/
└── validate_build.py    # Validation logic (checks artifacts against contracts)

reports/
└── reproduction_report.md # Generated output
```

**Structure Decision**: Single project structure. The `external/` directory holds the vendored code, `scripts/` contains the validation logic (Python/Bash) which consumes `contracts/build_artifacts.schema.yaml` and `contracts/reproduction_report.schema.yaml`, and `reports/` stores the generated summary. This isolates the reproduction artifacts from the main project logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly limited to running a build script and validating output files. | N/A |