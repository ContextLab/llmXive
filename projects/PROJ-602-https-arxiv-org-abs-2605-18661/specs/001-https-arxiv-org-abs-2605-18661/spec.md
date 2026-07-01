# Feature Specification: AI for Auto-Research: Roadmap & User Guide Reproduction

**Feature Branch**: `602-reproduce-auto-research`  
**Created**: 2026-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: AI for Auto-Research: Roadmap & User Guide (arXiv:2605.18661) using vendored code at external/awesome-ai-auto-research."

## User Scenarios & Testing

### User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1)

**Description**: As a researcher, I want to execute the vendored `awesome-ai-auto-research` pipeline on a standard CPU-only CI runner so that I can confirm the implementation runs end-to-end and produces the artifacts claimed in the paper (figures, data summaries, and generated text) without manual intervention.

**Why this priority**: This is the foundational step. Without a successful execution of the code, no validation of the paper's claims regarding cost, speed, or artifact quality can occur. It is the minimum viable product (MVP) for a reproduction project.

**Independent Test**: The CI job runs the entry script defined in the vendor's `README.md` and exits with code 0, producing a specific set of output files (e.g., `output/phase1.png`, `output/report.md`) in the workspace.

**Acceptance Scenarios**:

1. **Given** the git submodule `external/awesome-ai-auto-research` is initialized, **When** the CI runner executes the primary entry command defined in the vendor's documentation, **Then** the process completes within 6 hours and exits with status code 0.
2. **Given** the execution starts, **When** the pipeline reaches the "Writing" phase, **Then** the system generates a markdown draft file of at least 500 words without raising a "CUDA required" or "GPU not found" exception.
3. **Given** the pipeline completes, **When** the output directory is scanned, **Then** at least 3 distinct artifact types (e.g., a figure, a data table, and a text document) are present and non-empty.

---

### User Story 2 - Validate Artifact Integrity Against Paper Claims (Priority: P2)

**Description**: As a reviewer, I want to compare the generated artifacts against the specific claims in the paper (e.g., "$15 cost," "fabrication rates," "novelty assessment") so that I can determine if the implementation actually reproduces the reported results or if it fails silently.

**Why this priority**: Running the code is insufficient; the outputs must be verified against the paper's specific assertions to validate the research integrity claims. This distinguishes a "code run" from a "reproduction study."

**Independent Test**: A validation script parses the generated artifacts and compares them against the "Done" criteria defined in the project idea (real artifacts, no fabrication) and reports a pass/fail status.

**Acceptance Scenarios**:

1. **Given** the generated artifacts from User Story 1, **When** the validation script checks for the presence of "fabricated" markers or empty placeholders, **Then** the script reports a [deferred] rate of empty/fake content in the generated text.
2. **Given** the execution logs, **When** the cost estimator parses the API usage logs, **Then** the total estimated cost is calculated and reported (even if the specific dollar amount differs from the paper's claim, the calculation must exist).
3. **Given** the generated figures, **When** the image validation tool checks file headers, **Then** all images are confirmed to be valid raster/vector formats and not corrupted or placeholder images.

---

### User Story 3 - Document Methodological Limitations and Failure Modes (Priority: P3)

**Description**: As a stakeholder, I want a structured report documenting any deviations from the paper's methodology, resource constraints encountered (e.g., CPU limitations vs. paper's implied GPU), and specific failure modes observed, so that the community understands the boundaries of this reproduction.

**Why this priority**: The paper explicitly discusses "integrity problems" and "failure modes." A successful reproduction must explicitly document where the implementation *failed* to meet the paper's standards or where the environment (CPU-only) forced a deviation from the original method.

**Independent Test**: A `REPRODUCTION_REPORT.md` is generated containing a "Limitations" section that explicitly lists at least two deviations or observed failure modes.

**Acceptance Scenarios**:

1. **Given** the execution logs, **When** the report generator analyzes the runtime environment, **Then** the report explicitly states "No GPU detected" and details how the code adapted (or failed to adapt) to CPU-only inference.
2. **Given** the generated text, **When** the report generator checks for hallucinated citations, **Then** the report lists any detected hallucinated references or confirms their absence.
3. **Given** the full pipeline output, **When** the report is finalized, **Then** it includes a "Methodological Deviation" section with at least one concrete example of a constraint imposed by the free-tier CI environment.

---

### Edge Cases

- **What happens when the vendor's entry script requires specific environment variables not present in the CI?** The system MUST fail gracefully with a clear error message listing the missing variables, rather than hanging or producing empty files.
- **How does the system handle API rate limits during the "Creation" phase?** The system MUST implement a retry mechanism with exponential backoff (limited to a bounded number of attempts) before failing the job., ensuring transient network issues do not invalidate the reproduction.
- **What happens if the generated text contains no novel ideas (degradation)?** The validation script MUST flag this as a "Content Degradation" event rather than a success, explicitly noting that the "novelty" claim of the paper was not met.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the vendored `awesome-ai-auto-research` entry point without requiring GPU acceleration or CUDA libraries (See US-1).
- **FR-002**: System MUST generate at least three distinct artifact types (text, figure, data) as defined in the paper's "Creation" phase (See US-1).
- **FR-003**: System MUST log all API interactions and resource usage to calculate a reproducible cost estimate (See US-2).
- **FR-004**: System MUST detect and report any "fabricated" or empty placeholder content in the generated outputs (See US-2).
- **FR-005**: System MUST produce a final `REPRODUCTION_REPORT.md` containing a structured summary of deviations, failure modes, and methodological limitations (See US-3).
- **FR-006**: System MUST implement a retry mechanism with exponential backoff for external API calls to handle rate limiting (See Edge Cases).

### Key Entities

- **Reproduction Run**: A single execution instance of the vendor pipeline, characterized by a unique run ID, start time, and set of output artifacts.
- **Generated Artifact**: A file produced by the pipeline (e.g., `draft.md`, `phase1.png`), containing metadata about its generation phase and validity status.
- **Validation Report**: The structured output document summarizing the success of the run against the paper's claims.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The "Reproduction Run" MUST complete successfully (exit code 0) within 6 hours on a standard CPU-only runner (See US-1).
- **SC-002**: The "Generated Artifacts" MUST include at least 3 non-empty, non-placeholder files in valid formats (See US-1).
- **SC-003**: The "Validation Report" MUST explicitly list at least one methodological deviation or failure mode observed during the run (See US-3).
- **SC-004**: The "Cost Estimation" MUST produce a numeric value (or a clear "N/A" with justification) derived from logged API usage, not a hardcoded placeholder (See US-2).
- **SC-005**: The "Fabrication Check" MUST identify and flag any empty or obviously fake content in the generated text (See US-2).

## Assumptions

- The vendor's `README.md` provides a valid, executable entry point that does not require manual code modifications to run on a standard Linux environment.
- The "Cost" claim of "$15" in the paper is based on API usage that can be approximated or logged; if the vendor code does not log API costs, the reproduction will report "Cost not calculable from logs" rather than fabricating a number.
- The paper's "Creation" phase can be simulated or run in a "dry-run" or "mock" mode if the full LLM inference is too heavy for the free-tier CI, provided the mock mode produces the *structure* of the artifacts for validation.
- The vendor repository does not contain malicious scripts or require access to private, unauthenticated APIs that are blocked by the CI environment.
- The "fabrication" detection in the paper relies on heuristic checks (e.g., empty strings, "TODO" markers) rather than a second LLM judge, to ensure CPU feasibility.
