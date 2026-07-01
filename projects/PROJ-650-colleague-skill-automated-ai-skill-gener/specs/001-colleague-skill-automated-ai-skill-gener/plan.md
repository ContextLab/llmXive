# Implementation Plan: Automated AI Skill Generation via Expert Knowledge Distillation

**Branch**: `650-colleague-skill-automated-ai-skill-gener` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification for reproduction and validation of COLLEAGUE.SKILL paper implementation.

## Summary

This project implements the **reproduction of the artifact format and pipeline logic** for the "COLLEAGUE.SKILL" paper. The technical approach is procedural: ingesting example trace data (specifically `example_tianyi`), applying **deterministic pattern matching** against predefined heuristics to extract text segments, and generating structured "Skill Packages" (`meta.json`, `persona.md`, `work.md`). 

**Methodological Boundary**: This project validates the **Pipeline Validation** (can we generate the correct files with the correct structure?) and **Artifact Reproducibility** (does the output match the schema?), but **cannot** perform **Scientific Validation** of the distillation algorithm itself (i.e., whether the extracted content represents "true" expert knowledge vs. template artifacts). The "distillation" is a deterministic text-processing workflow that simulates the *output* of the paper's method without replicating its *mechanism* (LLM-based inference).

## Technical Context

**Language/Version**: Python +  
**Primary Dependencies**: `pyyaml`, `jsonschema`, `pytest`, `requests` (for potential dataset fetch if needed), `rich` (for CLI logging).  
**Storage**: File system (local directory structure for `skills/`, `prompts/`, `examples/`).  
**Testing**: `pytest` (unit tests for schema validation, integration tests for CLI lifecycle).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: CLI / Library  
**Performance Goals**: End-to-end execution ≤ 60 minutes (SC-005); memory usage < 7 GB.  
**Constraints**: No GPU; no external LLM API calls for generation (use local prompts/templates); strict adherence to `tools/skill_schema.py`.  
**Scale/Scope**: Single feature branch; processing of small example datasets (`example_tianyi`).

**Distillation Logic Clarification**: The system performs **pattern matching** against the input trace using predefined templates. It does **not** perform "latent reasoning extraction" or "novel mental model generation". The output is a **Template Artifact** that mimics the format of a Distilled Skill, validated for structural completeness and keyword presence, but not for semantic correctness or novelty.

## Constitution Check

*Note: No `constitution.md` file was supplied for this project (as per input). The plan adheres to **standard scientific reproducibility principles** as a fallback mechanism.*

1.  **Reproducibility (Fallback)**: The plan strictly adheres to the spec's requirement to reproduce the paper's workflow using provided example data (`example_tianyi`). No external data collection is planned unless the example data is insufficient, in which case the plan flags a spec gap.
2.  **Transparency (Fallback)**: All generated artifacts (`meta.json`, `persona.md`, `work.md`) will be validated against a public schema (`tools/skill_schema.py`) to ensure structural integrity.
3.  **Feasibility (Fallback)**: The plan explicitly avoids GPU-heavy methods or large model training, utilizing only CPU-tractable text processing and validation logic, ensuring the project runs on the target CI environment.
4.  **Validation (Fallback)**: The plan includes a dedicated validation phase (US-2) to verify that generated content meets the "capability" and "bounded behavior" tracks defined in the paper, not just structural validity.
5.  **Error Handling (Fallback)**: The plan mandates explicit error handling for missing/malformed inputs (Edge Cases) and API-like timeouts (if simulated), ensuring robust execution.

## Project Structure

### Documentation (this feature)

```text
specs/[650-colleague-skill-automated-ai-skill-gener]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── __init__.py
│   └── main.py              # CLI entry point (FR-001)
├── distillation/
│   ├── __init__.py
│   ├── intake.py            # Input validation & loading (Edge Cases)
│   ├── processor.py         # Core distillation logic (FR-004)
│   └── templates.py         # Prompt templates for extraction
├── validation/
│   ├── __init__.py
│   ├── schema_validator.py  # FR-002, SC-002
│   └── content_checker.py   # SC-004 (Keyword Density/Section Presence)
├── installation/
│   ├── __init__.py
│   └── install_claude_generated_skill.py  # FR-005, US-3
├── models/
│   └── skill_schema.py      # JSON Schema definition (Generated from YAML)
├── examples/
│   └── example_tianyi/      # Input trace data
└── tests/
    ├── unit/
    │   └── test_schema.py
    ├── integration/
    │   └── test_cli_lifecycle.py  # US-1, SC-001
    └── contract/
        └── test_installation.py   # US-3, SC-003

tools/
└── research/
    └── (if needed for data fetch)
```

**Structure Decision**: A single-project structure is selected. The separation into `cli`, `distillation`, `validation`, and `installation` modules aligns with the distinct phases of the workflow (Input -> Process -> Validate -> Deploy) described in the User Stories. This modular approach facilitates unit testing of each component independently.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is limited to reproducing a procedural workflow with small example data. | N/A |

## Phase Plan

### Phase 0: Research & Feasibility
*   **Goal**: Confirm dataset availability and validate the "distillation" logic against the paper's claims (as a *format* reproduction).
*   **Tasks**:
    *   Verify `example_tianyi` data format and content (US-1).
    *   Review `tools/skill_schema.py` to ensure it captures the "capability" and "bounded behavior" tracks (US-2).
    *   Confirm that the "distillation" logic can be implemented via local prompt templates without external LLM calls (Compute Feasibility).
    *   **Output**: `research.md`

### Phase 1: Data Model & Contracts
*   **Goal**: Define the strict data contracts and schemas for the Skill Package.
*   **Tasks**:
    *   Formalize the `skill_schema.json` (or Python dict) to match `tools/skill_schema.py`.
    *   Define the expected structure for `persona.md` and `work.md` (FR-004).
    *   Create the `contracts/skill_package.schema.yaml` as the **Single Source of Truth (SSoT)** for the schema.
    *   **Action**: Ensure `tools/skill_schema.py` is generated from or manually synced to match the YAML contract.
    *   **Output**: `data-model.md`, `quickstart.md`, `contracts/skill_package.schema.yaml`

### Phase 2: Implementation & Validation
*   **Goal**: Implement the CLI, distillation logic, and validation scripts.
*   **Tasks**:
    *   Implement `cli/main.py` to orchestrate the pipeline (FR-001).
    *   Implement `distillation/processor.py` to generate artifacts from traces (FR-004).
    *   Implement `validation/schema_validator.py` and `validation/content_checker.py` (FR-002, SC-002, SC-004).
    *   Implement `installation/install_claude_generated_skill.py` (FR-005).
    *   Implement error handling for empty/malformed inputs (Edge Cases).
    *   Implement retry logic for simulated API calls (Edge Cases).
    *   **Output**: Source code (via Implementer Agent).

### Phase 3: Testing & Verification
*   **Goal**: Execute the test suite and verify success criteria.
*   **Tasks**:
    *   Run `test_cli_lifecycle.py` (US-1, SC-001).
    *   Run schema validation on generated artifacts (US-2, SC-002).
    *   Run installation verification (US-3, SC-003).
    *   Verify `persona.md` content (SC-004) using **Keyword Density/Section Presence** (Syntactic Proxy).
    *   Measure execution time (SC-005).
    *   **Output**: Test reports, validation logs.

## Mapping of Requirements to Plan

| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR-001 | Execute CLI to generate skill package | Phase 2: `cli/main.py`, `distillation/processor.py` |
| FR-002 | Validate artifacts against schema | Phase 2: `validation/schema_validator.py` |
| FR-003 | `meta.json` with `skill_id`, `version`, `source` | Phase 1: `skill_schema.json`; Phase 2: `processor.py` |
| FR-004 | Separate capability/bounded behavior tracks | Phase 1: `persona.md` structure; Phase 2: `templates.py` |
| FR-005 | Installation script for deployment | Phase 2: `installation/install_claude_generated_skill.py` |
| FR-006 | Handle missing/malformed input | Phase 2: `distillation/intake.py` (error handling) |
| SC-001 | `test_cli_lifecycle.py` pass rate | Phase 3: `tests/integration/test_cli_lifecycle.py` |
| SC-002 | % schema validation pass | Phase 3: `tests/unit/test_schema.py` |
| SC-003 | Installation success log | Phase 3: `tests/contract/test_installation.py` |
| SC-004 | `persona.md` has ≥3 heuristics | Phase 2: `validation/content_checker.py` (Keyword Density/Section Presence Proxy) |
| SC-005 | Execution ≤ 60 mins | Phase 0: Compute Feasibility check; Phase 2: CPU-only logic |