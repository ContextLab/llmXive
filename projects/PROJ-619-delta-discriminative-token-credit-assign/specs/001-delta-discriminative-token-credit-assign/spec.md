# Feature Specification: DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

**Feature Branch**: `619-delta-discriminative-token-credit-assign`
**Created**: 2026-05-25
**Status**: Draft
**Input**: User description: "Reproduce & validate: DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards"

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Code Verification (Priority: P1)

The researcher MUST successfully initialize the project environment, clone the vendored `dlbook_notation` submodule, and verify that the codebase structure matches the paper's description before attempting any execution.

**Why this priority**: This is the foundational step. Without a verified environment and correct codebase, no reproduction is possible. It isolates infrastructure failures from algorithmic failures.

**Independent Test**: A researcher can run a single validation command to confirm the presence of all required files (`make.sh`, `notation.tex`, `README.md`) and that the git submodule points to the correct commit hash of `goodfeli/dlbook_notation`.

**Acceptance Scenarios**:

1. **Given** the project directory is empty, **When** the user executes the initialization script, **Then** the `external/dlbook_notation` directory is populated with the exact file tree described in the idea markdown (including `venn.pdf`, `make.sh`, etc.).
2. **Given** the environment is initialized, **When** the user inspects the `git submodule` status, **Then** the output confirms the remote URL is ` and the commit hash matches the one referenced in the project's `.gitmodules`.
3. **Given** the files are present, **When** the user attempts to run the `make.sh` script with no arguments, **Then** the script either executes successfully or exits with a clear, non-fatal error message (e.g., "Missing LaTeX dependencies") rather than a silent crash.

---

### User Story 2 - End-to-End Execution and Artifact Generation (Priority: P2)

The researcher MUST execute the primary entry point (`make.sh` or equivalent) to generate the paper's core artifacts (PDFs, figures, or LaTeX compilation outputs) without requiring GPU hardware.

**Why this priority**: The core value of a reproduction project is demonstrating that the original work's code actually runs. Since the paper focuses on a method (DelTA) and the code is vendored, "running" implies successful compilation or execution of the provided scripts to produce the documented outputs.

**Independent Test**: A researcher can run the build script and verify the existence of generated artifacts (e.g., `notation_example.pdf`, `venn.pdf`) within a defined directory structure, confirming the code is executable on CPU-only infrastructure.

**Acceptance Scenarios**:

1. **Given** the environment is initialized and dependencies (e.g., TeX Live) are installed, **When** the user executes `./make.sh`, **Then** the process completes within 6 hours on a CPU-only runner (2 cores, 7GB RAM) without CUDA errors.
2. **Given** the build process completes, **When** the user lists the output directory, **Then** at least one PDF artifact (e.g., `notation_example.pdf`) is generated with a file size > 50KB, indicating successful content rendering.
3. **Given** the build process encounters a missing dependency, **When** the script fails, **Then** it outputs a specific error message identifying the missing component (e.g., "Error: `pdflatex` not found") rather than a generic "Build failed."

---

### User Story 3 - Reproduction Report and Validation Summary (Priority: P3)

The researcher MUST generate a summary report that explicitly maps the execution results to the paper's claims, noting any deviations or confirmations of the DelTA method's behavior as described in the vendored code.

**Why this priority**: Execution alone is insufficient; the project must produce a "reproduction report" that serves as the validation evidence. This connects the mechanical run to the scientific claims.

**Independent Test**: A researcher can inspect the generated `reproduction_report.md` and verify it contains a section confirming whether the code executed as expected and a section addressing the "verifiable rewards" claim based on the code's logic.

**Acceptance Scenarios**:

1. **Given** the build artifacts exist, **When** the validation script runs, **Then** it generates a `reproduction_report.md` containing a "Status" field set to either "Success," "Partial," or "Failed."
2. **Given** the code executed successfully, **When** the report is generated, **Then** it explicitly states whether the codebase implements the "Discriminative Token Credit Assignment" logic described in the abstract (based on file content analysis or successful execution of specific logic paths).
3. **Given** The paper claims performance on multiple benchmarks., **When** the report is generated, **Then** it notes that these specific benchmarks were not re-run (due to scope constraints of validating the *vendored code structure* vs. *training* a new model) but confirms the *mechanism* for such benchmarks is present in the code.

---

### Edge Cases

- **Missing LaTeX Dependencies**: If the CI runner lacks a full TeX Live installation, the `make.sh` script must fail gracefully with a specific error code (e.g., exit 1) and a message directing the user to install `texlive-full`, rather than hanging or crashing with a segmentation fault.
- **Submodule Corruption**: If the git submodule is corrupted or points to a commit that no longer exists, the initialization step must detect this and abort with a clear message: "Submodule commit not found," preventing partial execution.
- **Resource Constraints**: If the build process attempts to load a file larger than 7GB (unlikely for LaTeX but possible with data files), the system must terminate with an "Out of Memory" error rather than swapping to disk and hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST successfully clone the `dlbook_notation` repository into `external/dlbook_notation` and verify the presence of `make.sh`, `notation.tex`, and `venn.pdf`. (See US-1)
- **FR-002**: The system MUST execute the `make.sh` script on a CPU-only environment (2 cores, 7GB RAM) and complete the build process within 6 hours without GPU acceleration. (See US-2)
- **FR-003**: The system MUST generate at least one PDF artifact (e.g., `notation_example.pdf` or `venn.pdf`) with a file size greater than 50KB as proof of successful rendering. (See US-2)
- **FR-004**: The system MUST produce a `reproduction_report.md` that explicitly categorizes the execution status (Success/Partial/Failed) and lists the generated artifacts. (See US-3)
- **FR-005**: The system MUST detect and report missing dependencies (e.g., `pdflatex`, `bibtex`) with a specific error code and message, rather than failing silently. (See US-1)
- **FR-006**: The system MUST verify that the vendored code does not contain hardcoded GPU/CUDA device assignments that would cause immediate failure on CPU-only runners. (See US-2)

### Key Entities

- **Vendored Codebase**: The git submodule `external/dlbook_notation` containing the LaTeX source and build scripts for the DelTA paper.
- **Build Artifacts**: The generated PDF files (e.g., `notation_example.pdf`) produced by the `make.sh` script.
- **Reproduction Report**: The `reproduction_report.md` file summarizing the validation results and mapping them to the paper's claims.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The time elapsed from script start to the generation of the first PDF artifact is measured against the established limit for CPU-only CI jobs. (See FR-002)
- **SC-002**: The file size of the generated `notation_example.pdf` is measured against a threshold of 50KB to confirm non-empty content. (See FR-003)
- **SC-003**: The presence of the `reproduction_report.md` file is measured against the requirement that it contains a "Status" field with a value of "Success," "Partial," or "Failed." (See FR-004)
- **SC-004**: The error message output for missing dependencies is measured against the requirement that it explicitly names the missing tool (e.g., "pdflatex") rather than a generic "build failed" string. (See FR-005)
- **SC-005**: The code scan result is measured against the requirement that zero instances of `device="cuda"` or `load_in_8bit` are found in the Python/LaTeX configuration files. (See FR-006)

## Assumptions

- The `dlbook_notation` repository contains a self-contained LaTeX build system that does not require external data downloads or network access during the `make.sh` execution.
- The CI runner environment has `texlive-full` (or equivalent) installed by default, or the project's workflow file explicitly installs it before running `make.sh`.
- The paper's claims regarding "seven mathematical benchmarks" refer to training experiments that are out of scope for this specific reproduction project, which focuses on validating the *vendored code structure* and *build process* rather than re-training the DelTA model from scratch.
- The `venn.pdf` and `notation_example.pdf` are static artifacts generated by the LaTeX engine and do not require dynamic data input.
- The git submodule URL ` is publicly accessible and does not require authentication tokens.
