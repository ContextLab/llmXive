# Feature Specification: Reproduce & Validate Code as Agent Harness

**Feature Branch**: `606-reproduce-validate-harness`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Code as Agent Harness (arXiv 2605.18747) via vendored submodule"

## User Scenarios & Testing

### User Story 1 - Execute Vendored Repository End-to-End (Priority: P1)

The researcher MUST be able to clone the project, initialize the git submodule `Awesome-Code-as-Agent-Harness-Papers`, and execute the repository's primary entry point (as defined in its `README.md`) within a standard GitHub Actions free-tier runner (standard CPU, standard RAM) without GPU acceleration, resulting in the successful generation of at least one non-empty artifact (e.g., a figure, a processed JSON file, or a log report).

**Why this priority**: This is the foundational verification step. If the vendored code does not run in the target environment, no validation or reproduction of the paper's claims can occur. It confirms the "code as agent harness" implementation is executable and fits the compute constraints.

**Independent Test**: Run the `bash` script or `python` command specified in the submodule's `README.md` quickstart section. The test passes if the process exits with code 0 and creates a file in the `projects/PROJ-606-.../external/.../output` (or equivalent) directory that is >0 bytes.

**Acceptance Scenarios**:

1. **Given** the project is checked out and the submodule is initialized, **When** the researcher runs the entry command `python main.py` (or equivalent), **Then** the process completes within 60 minutes and a file `output/validation_report.json` (or equivalent) is created with size > 0 bytes.
2. **Given** the environment has no GPU, **When** the researcher runs the entry command, **Then** the script executes without raising `CUDA` or `device_map` errors and utilizes only CPU resources.

---

### User Story 2 - Validate Artifacts Against Paper Claims (Priority: P2)

The system MUST parse the generated artifacts (figures, data logs) and compare them against the specific claims made in the `Code as Agent Harness` abstract (e.g., "unified view," "three connected layers," "scaling from single to multi-agent") to produce a structured validation report indicating which claims are supported by the code's output.

**Why this priority**: This moves beyond "it runs" to "it works as described." It validates the core scientific contribution of the paper by ensuring the code actually demonstrates the three layers (interface, mechanisms, scaling) mentioned in the abstract.

**Independent Test**: Generate a `validation_report.md` that explicitly maps code output (e.g., "Figure 3 generated") to a specific abstract claim (e.g., "Scaling the harness"). The test passes if the report contains at least 3 distinct mappings.

**Acceptance Scenarios**:

1. **Given** the execution artifacts from User Story 1, **When** the validation script processes the artifacts, **Then** it produces a report listing ≥ 3 distinct sections corresponding to the abstract's three layers (Interface, Mechanisms, Scaling).
2. **Given** the paper claims "execution-based verification," **When** the system analyzes the artifacts, **Then** the report confirms the presence of execution logs or verification results in the output.

---

### User Story 3 - Document Reproducibility Limitations & Sensitivity (Priority: P3)

The system MUST identify any missing dependencies, hardcoded paths, or external API calls that prevent full reproducibility on a fresh CI runner and generate a `limitations.md` document that lists these gaps and proposes a sensitivity analysis for any fixed thresholds found in the code (e.g., if the code uses a fixed temperature or timeout).

**Why this priority**: Reproducibility is the ultimate goal. Identifying barriers ensures the project is transparent about what *can* and *cannot* be reproduced, satisfying the "methodological soundness" requirement for empirical studies.

**Independent Test**: Run the validation pipeline and verify the existence of `limitations.md`. The test passes if the file contains at least one identified gap (e.g., "Missing API key for external model") or one sensitivity analysis recommendation.

**Acceptance Scenarios**:

1. **Given** the code relies on an external service (e.g., Hugging Face API), **When** the system runs without credentials, **Then** the `limitations.md` explicitly flags this dependency and suggests a mock or offline alternative.
2. **Given** the code uses a fixed parameter (e.g., `temperature=0.7`), **When** the system analyzes the code, **Then** the `limitations.md` recommends a sensitivity sweep over a range of low, medium, and high values and notes the potential impact on results.

---

### Edge Cases

- **What happens when the submodule is missing or corrupted?** The system MUST detect the missing `.git` directory in the submodule path and fail fast with a clear error message instructing the user to run `git submodule update --init --recursive`, rather than attempting to run a broken script.
- **How does the system handle a "No GPU" environment error?** If the code attempts to load a CUDA-only library, the system MUST catch the `ImportError` or `RuntimeError`, log it, and attempt to fall back to CPU-only execution if the library supports it (e.g., via `torch.device('cpu')`), otherwise it MUST report the failure as a "Compute Constraint Violation."
- **What if the paper's claims are vague?** If the abstract claims "scaling" but the code only runs a single-agent test, the validation report MUST explicitly flag this as "Claim Not Fully Reproduced: Scaling not demonstrated in current code run."

## Requirements

### Functional Requirements

- **FR-001**: System MUST initialize the git submodule `Awesome-Code-as-Agent-Harness-Papers` and verify its integrity (checksum or commit hash match) before execution. (See US-1)
- **FR-002**: System MUST execute the primary entry point of the submodule using only CPU resources, ensuring no CUDA/GPU calls are made. (See US-1)
- **FR-003**: System MUST generate at least one non-empty artifact (file > 0 bytes) as proof of successful execution. (See US-1)
- **FR-004**: System MUST parse the generated artifacts and map them to the three specific layers described in the paper's abstract (Interface, Mechanisms, Scaling). (See US-2)
- **FR-005**: System MUST generate a `validation_report.md` that explicitly states whether the code output supports the "execution-based verification" claim. (See US-2)
- **FR-006**: System MUST scan the code for hardcoded thresholds (e.g., timeouts, temperature, limits) and generate a sensitivity analysis recommendation for each. (See US-3)
- **FR-007**: System MUST produce a `limitations.md` file listing any external dependencies (APIs, datasets) that prevent full offline reproducibility. (See US-3)

### Key Entities

- **Artifacts**: The output files (figures, logs, JSON reports) generated by the submodule execution.
- **Validation Report**: The structured document mapping code output to paper claims.
- **Limitations Log**: The document recording reproducibility barriers and sensitivity recommendations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Execution Success Rate is measured against the requirement that the process exits with code 0 and produces ≥ 1 artifact > 0 bytes. (See US-1)
- **SC-002**: Claim Coverage is measured against the requirement that the `validation_report.md` contains ≥ 3 distinct mappings between code output and abstract claims. (See US-2)
- **SC-003**: Reproducibility Gap Identification is measured against the requirement that `limitations.md` contains ≥ 1 identified gap or sensitivity recommendation. (See US-3)
- **SC-004**: Compute Compliance is measured against the constraint that the entire process completes within 6 hours on a 2-CPU, 7 GB RAM runner without GPU errors. (See US-1)

## Assumptions

- The vendored submodule `Awesome-Code-as-Agent-Harness-Papers` contains a valid `README.md` with a clear "Quickstart" or "Run" section that defines the entry point.
- The paper's claims are descriptive of the code's capabilities, and the code is intended to be runnable without proprietary API keys for the basic validation (or the assumption is that the CI runner has access to a free-tier API key if required).
- The "Code as Agent Harness" implementation does not require training a large model from scratch; it relies on inference or static analysis that fits within the 7 GB RAM constraint.
- The `MISSING_URLS.md` or `TODO.md` files in the submodule are up-to-date and accurately reflect the current state of the repository's external dependencies.
- The GitHub Actions free-tier runner provides sufficient disk space. to clone the submodule and generate artifacts.
