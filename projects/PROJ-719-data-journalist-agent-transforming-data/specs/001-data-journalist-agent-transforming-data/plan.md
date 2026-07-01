# Implementation Plan: Data Journalist Agent Reproduction

**Branch**: `001-data-journalist-agent-reproduction` | **Date**: 2024-05-23 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-data-journalist-agent-reproduction/spec.md`

## Summary

This plan outlines the reproduction and validation of the "Data Journalist Agent" pipeline (`data2story-skill`). The primary requirement is to execute the vendored `pro/skills/data2story-pro/` evaluation script against the `01_meteorite_flagship.md` scenario on a CPU-only CI environment. The technical approach involves orchestrating a multi-agent system (Detective, Analyst, Designer, Inspector) to generate a verifiable multimodal story. 

**Critical Methodological Update**: This plan introduces a **Gold Standard** validation mechanism to distinguish between hallucinated and valid claims, a **Dataset Fallback Strategy** with a verified external source, and a **Wrapper Script** to ensure fallback logic is executable. The study is explicitly defined as a **Reproduction Fidelity** test (n=1 scenario), with metrics defined as instance-specific descriptive statistics, not population estimates.

## Technical Context

**Language/Version**: Python 3.10 (standard for the `data2story-skill` repository)  
**Primary Dependencies**: `langchain`, `datasets` (HuggingFace), `requests`, `jinja2`, `pytest`, `pandas`, `pyyaml`.  
**Storage**: Filesystem (local temporary directories for scenario data, generated assets, and registry JSONs).  
**Testing**: `pytest` (custom validation scripts for `cell_registry.json`, `gold_standard` comparison, and asset existence).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier: 2 CPU, 7GB RAM, No GPU).  
**Project Type**: CLI / Automation Pipeline  
**Performance Goals**: Total execution < 6 hours; Memory peak < 6GB; Graceful degradation on API failure.  
**Constraints**: No CUDA/GPU; No external paid API keys (must handle 401/429/timeout); Dataset variables must match spec requirements.  
**Scale/Scope**: Single scenario (`01_meteorite_flagship.md`); A representative sample of claims; <10 multimodal asset requests.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

**Status**: **GATE - BLOCKED IF MISSING**

Per Constitution Principle I (SSoT) and FR-030, the plan MUST explicitly validate against the project's `constitution.md`.
1.  **Check**: The pipeline MUST verify the existence of `projects/<PROJ-ID>/.specify/memory/constitution.md` at the start of Phase 0.
2.  **Action**:
    *   **If Present**: The plan proceeds to validate the pipeline's design against the specific numbered principles listed in that file (e.g., Principle I, Principle II).
    *   **If Missing**: The pipeline MUST **HALT** immediately with exit code 1 and error message `BLOCKED: Missing constitution.md. Cannot verify compliance with SSoT (FR-030).`.
3.  **Compliance**: No principles are assumed. The plan does not proceed until the SSoT is loaded and validated.

## Project Structure

### Documentation (this feature)

```text
specs/001-data-journalist-agent-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schemas)
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT) - Reproduction of vendored skill
pro/
└── skills/
    └── data2story-pro/
        ├── evals/
        │   ├── scenarios/
        │   │   └── 01_meteorite_flagship.md
        │   └── scripts/
        │       └── run_evals.py
        └── [Agent implementations]

tests/
└── integration/
    ├── run_with_fallback.py   # NEW: Wrapper to handle dataset fetch before running evals
    ├── test_data2story_pipeline.py
    └── validate_traceability.py  # New: Gold Standard comparison script

artifacts/
└── [Generated output: index.html, cell_registry.json, assets/, gold_standard_claims.json]
```

**Structure Decision**: The plan utilizes the existing vendored structure. A new validation script `validate_traceability.py` is added to compare the generated registry against the Gold Standard. A wrapper script `run_with_fallback.py` is added to handle dataset fetching before invoking the core skill.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Gold Standard Validation | The spec requires validating "evidence-grounded claims" (US-2). Without a ground truth, we cannot distinguish hallucinations from valid claims. | Manual spot-checking is subjective and non-reproducible. A programmatic Gold Standard comparison is required for objective validation. |
| Dataset Fallback | The CI environment may lack the vendored submodule. | Relying solely on the vendored copy risks a silent failure or "dataset missing" crash without a clear path to recovery. |
| Wrapper Script | The vendored `run_evals.py` cannot be modified directly to fetch external data. | A wrapper script allows us to inject the fallback logic before invoking the core evaluation script, ensuring the pipeline is robust without modifying external code. |

## Plan Phases & Requirement Mapping

### Phase 0: Environment, Constitution, & Dataset Verification
*Addresses: FR-001, FR-005, SC-001, SC-004, Constitution Principle I*
1.  **Constitution Gate**: Check for `constitution.md`. If missing, **HALT** with `BLOCKED: Missing constitution.md`.
2.  **Setup**: Clone `data2story-skill` repo, install CPU-only dependencies.
3.  **Dataset Check & Fallback**:
    *   **Step A**: Verify `01_meteorite_flagship.md` references a dataset present in the vendored submodule.
    *   **Step B (Fallback)**: If missing, execute `tests/integration/run_with_fallback.py` which programmatically fetches the verified NASA GISS Meteorite Landings dataset (URL: `https://data.nasa.gov/Space-Science/Meteorite-Landings/ghg-9sfh`) using `datasets.load_dataset` or direct CSV fetch.
    *   **Step C (Variable Fit)**: Verify the fetched data contains required variables: `mass`, `year`, `name`, `class`, `latitude`, `longitude`.
    *   **Action**: If variables are missing, write `audit_report.json` with `status: "NEEDS_CLARIFICATION"` and **HALT**.
4.  **Run**: Execute the wrapper script `run_with_fallback.py` (which calls `run_evals.py`) with `scenario=01_meteorite_flagship.md`.
    *   *Error Handling*: Configure `try/except` blocks to catch API 429/500 errors and log them without exiting.

### Phase 1: Core Pipeline Execution (Detective & Analyst)
*Addresses: FR-001, FR-002, SC-002*
1.  **Detective**: Extract claims from the scenario.
2.  **Analyst**: Map claims to data cells.
3.  **Registry Generation**: Ensure `cell_registry.json` is created with valid `claim_id` -> `source_cell` mappings.
    *   *Validation*: Check that every claim in the narrative has a corresponding entry in the registry.

### Phase 2: Multimodal Generation & Designer
*Addresses: FR-003, FR-004, SC-003*
1.  **Designer Execution**: Trigger asset generation requests.
2.  **Fallback Logic**: If external API (OpenRouter/HF) fails or times out:
    *   Generate a placeholder file (e.g., `placeholder_image.png`) with metadata `generated_by: "Designer (Fallback)"` and `generation_mode: "fallback"`.
    *   Log the error reason.
3.  **Verification**: Confirm at least one asset (real or placeholder) exists in the output directory. Distinguish between "Native" and "Fallback" counts for metrics.

### Phase 3: Inspector & Final Report
*Addresses: FR-003, SC-002, SC-004*
1.  **Inspector**: Run verification logic to identify ungrounded claims.
2.  **Audit Report**: Generate `audit_report.json` summarizing success rates, error logs, and **Gold Standard metrics**.
3.  **Final Output**: Ensure `index.html` is generated and links to assets.

### Phase 4: Validation & Testing (Gold Standard Census)
*Addresses: All FRs and SCs*
1.  **Test 1 (US-1)**: Verify `run_evals.py` exit code 0 and output directory structure.
2.  **Test 2 (Census Validation)**: Run `validate_traceability.py`.
    *   **Input**: `cell_registry.json` and `gold_standard_claims.json` (manually curated from the scenario description/paper example).
    *   **Logic**: Compare **every** claim in the Gold Standard against the Registry (Census, not sample).
    *   **Metric**: Calculate `Precision` (Claims in Registry that match Gold) and `Recall` (Gold claims found in Registry).
    *   **Fail Condition**: If `Recall < 100%` (missing evidence) or `Precision < 100%` (hallucinated claims), mark test as **FAILED**.
3.  **Test 3 (US-3)**: Check `assets/` for non-HTML files. Distinguish between `native` and `placeholder` counts.
4.  **Test 4 (Edge Cases)**: Simulate an API failure (e.g., mock a 500 error) and verify the pipeline continues and logs `status: "placeholder"`.

## Statistical & Methodological Rigor

*   **Reproduction Fidelity**: The study is a **Reproduction** (n=1 scenario), not a generalization study. Success is defined as **Reproduction Fidelity**: the ability to replicate the paper's specific scenario execution and traceability claims exactly. Generalizability is explicitly out of scope.
*   **Instance-Specific Metrics**: The Precision and Recall metrics calculated in Phase 4 are **descriptive statistics** for this specific instance (the single scenario `01_meteorite_flagship.md`). They are NOT estimators of a population parameter and should not be interpreted as generalizable system capabilities.
*   **Dataset-Variable Fit**: The plan explicitly checks if the `01_meteorite_flagship.md` scenario contains the necessary variables (e.g., mass, year, name) before execution. If the dataset lacks these, the plan halts with a `NEEDS_CLARIFICATION` flag.
*   **Causal Claims**: The plan treats all generated claims as **associational** unless the source data explicitly supports causal inference. The `Inspector` agent is configured to flag any causal language not supported by the data schema.
*   **Sample Size**: The "sample" is the single scenario `01_meteorite_flagship.md`. The validation is a **Census** of the Gold Standard claims, not a random sample, ensuring [deferred] coverage of the available ground truth.
*   **Metric Definitions**:
    *   **Registry Completeness (Recall)**: `(Claims in Registry matching Gold / Total Claims in Gold Standard) * 100`.
    *   **Hallucination Rate (1 - Precision)**: `(Claims in Registry NOT in Gold / Total Claims in Registry) * 100`.
    *   **Native Asset Success Rate**: `(assets_native / assets_requested) * 100`.
    *   **Robustness Rate**: `(scenarios completing despite API errors / total scenarios) * 100`.

## Compute Feasibility Strategy

*   **CPU-Only**: All dependencies pinned to CPU wheels. No `cuda` device assignment.
*   **Memory Management**: Data loaded in chunks if the dataset > 1GB. The scenario `01_meteorite_flagship.md` is selected specifically for its small footprint.
*   **Timeout Handling**: API calls wrapped with `timeout=30s` to prevent hanging.
*   **Disk Space**: Output directory cleaned up after validation if needed, but kept for artifact inspection.