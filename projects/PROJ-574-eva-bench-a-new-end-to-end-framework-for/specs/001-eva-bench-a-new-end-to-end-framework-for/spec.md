# Feature Specification: EVA-Bench Reproduction & Validation

**Feature Branch**: `574-eva-bench-reproduction`
**Created**: 2024-05-22
**Status**: Draft
**Input**: User description: "Reproduce & validate: EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

## User Scenarios & Testing

### User Story 1 - Reproduce Core Execution Flow (Priority: P1)

As a researcher, I want to execute the vendored `dlbook_notation` codebase end-to-end on a standard CPU-only CI runner so that I can confirm the implementation runs without errors and produces the expected output artifacts (PDFs, logs) as claimed in the paper.

**Why this priority**: This is the foundational requirement for a reproduction project. If the code does not execute, no validation of the paper's claims can occur. It establishes the "run" baseline.

**Independent Test**: Can be fully tested by running the entry script (e.g., `./make.sh`) on a fresh GitHub Actions runner and verifying the existence of specific output files (e.g., `notation_example.pdf`) without manual intervention.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner (2 CPU, 7GB RAM), **When** the `./make.sh` script is executed, **Then** the process exits with code 0 and produces `notation_example.pdf` within 300 seconds.
2. **Given** the `make.sh` script runs, **When** the execution completes, **Then** no "CUDA" or "GPU" related errors appear in the standard error stream.
3. **Given** the execution finishes, **When** the output directory is inspected, **Then** at least 3 distinct artifact files (PDFs or logs) matching the paper's description are present.

---

### User Story 2 - Validate Artifact Fidelity (Priority: P2)

As a reviewer, I want to verify that the generated artifacts (PDFs/figures) from the vendored code match the visual and structural descriptions in the EVA-Bench paper so that I can confirm the reproduction is faithful to the original work.

**Why this priority**: Execution alone is insufficient; the output must be semantically correct. This validates that the code actually implements the paper's logic, not just a stub.

**Independent Test**: Can be tested by comparing the generated PDF checksums or text extraction against the paper's referenced figures or by visual diffing (if baseline images exist) to confirm no "placeholder" or "broken image" errors exist.

**Acceptance Scenarios**:

1. **Given** the generated `notation_example.pdf`, **When** the file is opened in a PDF viewer, **Then** it renders without missing glyphs, broken image links, or "file not found" errors.
2. **Given** the paper's description of the "EVA-A" and "EVA-X" metrics, **When** the generated documentation is parsed, **Then** the text explicitly mentions these metric definitions.
3. **Given** the generated artifacts, **When** the file size is checked, **Then** the PDF is greater than 50KB (indicating actual content) and less than 10MB (indicating no infinite loop generation).

---

### User Story 3 - Document Reproduction Constraints & Discrepancies (Priority: P3)

As a project maintainer, I want a clear log of any deviations between the vendored code's behavior and the paper's claims (e.g., missing data, specific hardware requirements, or runtime errors) so that the team can address gaps or mark the reproduction as "partial."

**Why this priority**: Reproduction often reveals hidden dependencies. Documenting these ensures transparency and prevents false claims of full success.

**Independent Test**: Can be tested by checking for a generated `reproduction_report.md` that lists specific error codes, missing files, or runtime warnings encountered during the P1 execution.

**Acceptance Scenarios**:

1. **Given** a successful run, **When** the `reproduction_report.md` is generated, **Then** it contains a "Pass/Fail" status for the core execution.
2. **Given** a run with warnings, **When** the report is generated, **Then** it lists at least one warning or constraint (e.g., "Assumed TeX Live 2023").
3. **Given** a failed run, **When** the report is generated, **Then** it explicitly cites the exit code and the last 10 lines of the error log.

### Edge Cases

- What happens if the `make.sh` script relies on a specific TeX distribution version not present on the default GitHub Actions runner?
- How does the system handle the case where the submodule `dlbook_notation` is empty or corrupted (git clone failure)?
- What happens if the generated PDF requires a specific font that is missing on the Linux runner (common in LaTeX builds)?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `make.sh` script within the `external/dlbook_notation` directory without requiring GPU acceleration or CUDA libraries. (See US-1)
- **FR-002**: The system MUST generate at least one valid PDF artifact (`notation_example.pdf`) and one text log file upon successful execution. (See US-1)
- **FR-003**: The system MUST detect and report any "CUDA", "GPU", or hardware-specific dependency errors in the standard error stream. (See US-1)
- **FR-004**: The system MUST validate that the generated PDF contains non-empty content (file size > 50KB) and renders without fatal errors. (See US-2)
- **FR-005**: The system MUST generate a `reproduction_report.md` file summarizing the execution status, any warnings, and specific discrepancies found. (See US-3)
- **FR-006**: The system MUST complete the entire reproduction workflow within 6 hours on a standard free-tier GitHub Actions runner. (See US-1)

### Key Entities

- **Vendored Codebase**: The `dlbook_notation` directory containing the LaTeX source and build scripts.
- **Artifacts**: The output files (PDFs, logs) generated by the build process.
- **Reproduction Report**: The summary document generated by the validation logic.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The execution time of the `make.sh` script is measured against the 6-hour limit, with a target of < 300 seconds. (See US-1)
- **SC-002**: The file size of the generated `notation_example.pdf` is measured against the 50KB minimum threshold to ensure content validity. (See US-2)
- **SC-003**: The number of fatal errors in the build log is measured against 0, requiring zero non-recoverable errors for a "Pass" status. (See US-1)
- **SC-004**: The presence of the `reproduction_report.md` file is measured against 1 (must exist) to confirm the validation step completed. (See US-3)
- **SC-005**: The count of "CUDA" or "GPU" keywords in the error log is measured against 0, ensuring the build is CPU-only compliant. (See US-1)

## Assumptions

- The `dlbook_notation` submodule is correctly initialized and contains valid LaTeX source files (`.tex`, `.bib`, `.cls`) upon project checkout.
- The GitHub Actions runner environment includes a standard TeX Live distribution (e.g., TeX Live 2023 or later) sufficient to compile the document without additional package installation.
- The paper's claims regarding "EVA-A" and "EVA-X" metrics are descriptive of the framework's capabilities rather than requiring the execution of a complex simulation engine in this specific reproduction step; the focus is on the build and documentation artifacts.
- The `make.sh` script is designed to be idempotent and does not require interactive user input (e.g., no prompts for user confirmation).
- The repository URL ` is accessible and stable for the duration of the CI job.
