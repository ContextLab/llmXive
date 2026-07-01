# Feature Specification: Automated AI Skill Generation via Expert Knowledge Distillation

**Feature Branch**: `650-colleague-skill-automated-ai-skill-gener`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Reproduction and validation of COLLEAGUE.SKILL paper implementation"

## User Scenarios & Testing

### User Story 1 - End-to-End Execution of the Distillation Pipeline (Priority: P1)

**Journey**: A researcher or engineer clones the project, installs dependencies, and executes the primary reproduction script to generate at least one valid "skill package" from the provided example data (e.g., `example_tianyi`) without manual intervention or code modification.

**Why this priority**: This is the foundational "Hello World" for the reproduction project. If the codebase cannot execute its own workflow to produce artifacts, the project fails the primary requirement of "running, validating, and reproducing." It validates the environment setup, dependency resolution, and core logic integrity.

**Independent Test**: The user runs the provided `quickstart` or `test_cli_lifecycle.py` script. The test passes if the script exits with code 0 and produces a valid JSON skill package file in the `skills/` directory.

**Acceptance Scenarios**:

1. **Given** the project is cloned and dependencies are installed, **When** the user executes the main CLI entry point with the `example_tianyi` dataset, **Then** the process completes successfully (exit code 0) and generates a `meta.json`, `persona.md`, and `work.md` file in the target output directory.
2. **Given** the pipeline is running, **When** the process encounters a missing optional dependency (e.g., a specific research tool not required for core logic), **Then** the system logs a warning but continues execution, ensuring the core skill generation is not blocked.
3. **Given** the pipeline has finished, **When** the user inspects the generated `meta.json`, **Then** it contains valid JSON with the required fields (`skill_id`, `version`, `source`) and matches the schema defined in `tools/skill_schema.py`.

---

### User Story 2 - Validation of Generated Artifacts against Schema and Paper Claims (Priority: P2)

**Journey**: A reviewer inspects the generated skill artifacts to confirm they adhere to the defined schema and that the content reflects the "capability" and "bounded behavior" tracks described in the paper.

**Why this priority**: Generating files is insufficient; they must be structurally valid and semantically meaningful. This story ensures the output is not garbage but a usable "skill package" that aligns with the paper's definition of a "versioned skill package."

**Independent Test**: A validation script (or manual check) parses the generated artifacts and verifies they conform to `tools/skill_schema.py` and contain non-empty content in the `persona` and `work` sections.

**Acceptance Scenarios**:

1. **Given** a generated skill package exists, **When** the `skill_schema.py` validator runs against it, **Then** it returns a success status with zero schema violations.
2. **Given** a generated `persona.md`, **When** the content is analyzed, **Then** it contains distinct sections for "practices/mental models" and "communication style" as defined in the paper's "capability track" and "bounded behavior track."
3. **Given** the `work.md` file, **When** inspected, **Then** it contains at least 3 distinct decision heuristics or interaction rules derived from the input trace, demonstrating the distillation process worked.

---

### User Story 3 - Verification of Installation and Portability Mechanisms (Priority: P3)

**Journey**: A user attempts to "install" the generated skill into a simulated agent host (or verify the installation script logic) to confirm the portability claim of the paper.

**Why this priority**: The paper claims the skills are "portable, correctable, and agent-usable." Verifying the installation script (`tools/install_*.py`) ensures the output format is actually consumable by downstream agents, completing the "end-to-end" loop.

**Independent Test**: The `test_install_claude_generated_skill.py` (or equivalent) runs against the generated artifact. The test passes if the installation script successfully parses the skill package and outputs a confirmation of "ready for deployment."

**Acceptance Scenarios**:

1. **Given** a valid skill package generated in US-1, **When** the `install_claude_generated_skill.py` script is invoked with the package path, **Then** the script parses the `meta.json` and `persona.md` and outputs a success message without raising exceptions.
2. **Given** the installation process, **When** the script detects a version mismatch between the skill and the target host (simulated), **Then** it logs a warning and offers a rollback or update path as described in the "correction lifecycle."
3. **Given** the installation is successful, **When** the user queries the "installed" state, **Then** the system reports the skill as active and available for invocation.

### Edge Cases

- **What happens when the input trace is empty or malformed?** The system MUST detect the empty input during the `intake` phase and fail fast with a clear error message indicating the file is missing or invalid, rather than generating an empty skill package.
- **How does the system handle API rate limits or timeouts during the "distillation" (if external LLM calls are simulated or used for validation)?** The system MUST implement a retry mechanism with exponential backoff (e.g., a limited number of retries with increasing intervals) and fail gracefully if all retries are exhausted, logging the specific failure reason.
- **What happens if the generated `persona.md` contains sensitive PII (if real data were used)?** The system MUST include a placeholder check or warning in the validation step if patterns resembling email addresses or phone numbers are detected in the `persona` section (deferring actual redaction to a security review, but flagging the presence).

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `colleague-skill` CLI entry point to ingest a defined input dataset (e.g., `example_tianyi`) and generate a structured skill package containing `meta.json`, `persona.md`, and `work.md` files. (See US-1)
- **FR-002**: System MUST validate all generated artifacts against the `tools/skill_schema.py` definition before considering the generation step complete. (See US-2)
- **FR-003**: System MUST produce a `meta.json` file that includes a unique `skill_id`, a `version` string, and a `source` reference linking back to the input dataset. (See US-2)
- **FR-004**: System MUST separate the distillation output into a "capability track" (mental models, heuristics) and a "bounded behavior track" (communication style, rules) within the generated markdown files. (See US-2)
- **FR-005**: System MUST provide an installation script (e.g., `install_claude_generated_skill.py`) that successfully parses the generated skill package and confirms readiness for deployment. (See US-3)
- **FR-006**: System MUST handle missing or malformed input files by failing fast with a specific error code (non-zero exit) and a descriptive error message. (See Edge Cases)

### Key Entities

- **Skill Package**: A versioned directory containing `meta.json`, `persona.md`, and `work.md` representing a distilled expert persona.
- **Input Trace**: The source material (e.g., transcripts, chat logs) used to distill the skill, represented as files in the `skills/` or `prompts/` directories.
- **Schema Definition**: The JSON schema (`tools/skill_schema.py`) that defines the mandatory structure and fields of a valid Skill Package.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reproduction pipeline MUST execute the `test_cli_lifecycle.py` suite with a [deferred] pass rate on the primary generation test, measured against the script's exit code. (See US-1)
- **SC-002**: [deferred] of generated skill packages MUST pass the `skill_schema.py` validation without errors, measured by the validator's return status. (See US-2)
- **SC-003**: The installation verification script MUST successfully parse and acknowledge the generated skill package, measured by the presence of a "success" log message. (See US-3)
- **SC-004**: The generated `persona.md` MUST contain at least 3 distinct, non-empty sections describing heuristics or rules, measured by counting top-level headers or bullet points in the file. (See US-2)
- **SC-005**: The end-to-end execution time (from script start to final artifact generation) MUST be ≤ 60 minutes on a standard CPU-only CI runner, measured by the job duration metric. (See Compute Feasibility)

## Assumptions

- **Assumption about Environment**: The reproduction environment assumes a standard Linux-based CI runner (GitHub Actions) with Python 3.9+ available and no GPU resources, as the implementation relies on CPU-tractable logic or pre-defined prompts rather than heavy model training.
- **Assumption about Data**: The `example_tianyi` and `example_jiaxiu` datasets provided in the repository are sufficient to demonstrate the full distillation workflow without requiring external data collection or API access to live LLM services.
- **Assumption about Scope**: The scope is limited to validating the *existing* codebase logic; no new algorithms or model architectures are being trained or modified. The "distillation" is a procedural generation of text based on the provided prompts.
- **Assumption about Dependencies**: All Python dependencies listed in `requirements.txt` are available via PyPI and compatible with the target CI environment without requiring system-level compilation or specialized hardware drivers.
- **Assumption about External Tools**: Any tools in `tools/research/` (e.g., `transcribe_audio.py`) that might require external binaries (like `ffmpeg`) are assumed to be either mockable or already present in the CI environment, or their failure is non-blocking for the core skill generation logic.
