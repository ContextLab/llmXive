# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Branch**: `001-gene-regulation` | **Date**: 2026-06-26 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary

This project implements a **Feasibility Verification** pipeline to determine if the correlation between gut microbiome alpha-diversity and sleep quality can be investigated using public datasets.

**CRITICAL STATUS**: The project is **TERMINATED** for this revision. The `# Verified datasets` block provided for this revision contains **NO** verified URL for the American Gut Project (AGP) with the specific required variables (`antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`).

The **ONLY** valid deliverable for this revision is a **Feasibility Report** (JSON and Markdown) that documents this termination. No statistical analysis (Spearman, BH correction, alpha-diversity) will be performed. The research question is currently unanswerable with available resources.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `pyyaml` (for feasibility check only)
**Storage**: Local filesystem (`data/`, `outputs/`)
**Testing**: `pytest` (unit tests for feasibility check logic, schema validation)
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPUs, ~7 GB RAM)
**Project Type**: Feasibility Verification / CLI
**Performance Goals**: Complete feasibility check within 1 hour; memory usage < 1 GB.
**Constraints**:
- Must not fabricate data.
- Must halt gracefully if no verified URL exists in `plan.md`.
- Must generate a valid "Feasibility Report" if the dataset is unavailable.
- All statistical tests are **DEFERRED** until a verified dataset is found.

> **Dataset Feasibility Note**: The `# Verified datasets` block provided for this revision contains URLs for generic OTU tables, BMI datasets, and CPU-only benchmarks, but **NO** verified URL for the American Gut Project (AGP) with the specific sleep metadata required by FR-001/FR-002. Therefore, the "Happy Path" is unreachable. The implementation must execute the "Feasibility Termination" path as the primary deliverable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Feasibility Report will be deterministic based on `plan.md` content hash. Random seeds pinned. |
| **II. Verified Accuracy** | **BLOCKED** | No citations to unverified datasets. The project is halted because the required data is unverified/missing. |
| **III. Data Hygiene** | **COMPLIANT** | No raw data modified. Feasibility Report is a new file with `status: blocked` metadata. Checksums will be recorded for this artifact. |
| **IV. Single Source of Truth** | **COMPLIANT** | Final report (Feasibility Report) will trace back to the `plan.md` feasibility check failure. |
| **V. Versioning Discipline** | **COMPLIANT** | Feasibility Report will carry content hash derived from `plan.md` content hash. `state/` YAML will be updated. |
| **VI. Statistical Rigor** | **BLOCKED** | The project is halted. No statistical tests are performed. The report will explicitly state "Analysis not performed due to data unavailability." |
| **VII. Cross-Source Metadata** | **COMPLIANT** | No merging will occur in the blocked state. The plan explicitly rejects imputation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-correlation-between-gu/
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
├── feasibility.py       # Feasibility check logic (FR-001, FR-002)
└── utils.py             # Helpers, schema validation, Feasibility Report generation

tests/
├── unit/
│   └── test_feasibility.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # (Empty in blocked state, or placeholder)
└── processed/
    └── feasibility_report.json         # (Feasibility Report: status, reason, timestamp)

outputs/
└── reports/
    └── feasibility_report.md           # (Feasibility Report: human-readable)
```

**Structure Decision**: Single-project structure selected. The `src/` directory contains the feasibility check module. The `data/processed/` directory will contain the "Feasibility Report" as the primary output for this revision, ensuring the pipeline produces a valid, reproducible result (the report of unavailability) rather than crashing.

## Complexity Tracking

| Design Decision | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Feasibility Termination Handling** | The `# Verified datasets` block lacks the required AGP URL. | A "happy path" implementation is impossible without fabricating data, which violates the Constitution (Principle III & VI) and the "No Fabrication" rule. |
| **Feasibility Report as Primary Deliverable** | Must support both real data processing and blocked reporting. | A single path that crashes or returns empty results fails the "Graceful Failure" requirement (Edge Cases). |
| **Blocked State as Termination** | The research question cannot be answered without the specific dataset. | Attempting to "simulate" a result with generic data is fabrication and invalidates the research. |

## Task List

### Phase 0: Feasibility Verification (Blocked State)

- [ ] **T001** — **Execute Feasibility Script** [FR-001, FR-002]
  - **Action**: Run `python src/feasibility.py`. This script reads `plan.md` and checks the `# Verified datasets` block for an AGP URL.
  - **Outcome**: If no verified URL is found, the script exits with code 0 (success) and generates a `feasibility_report.json` with `status: blocked`.
  - **Verification**: Assert `src/feasibility.py` exists and runs without error. Assert output indicates "no verified URL found".

- [ ] **T002** — **Generate Blocked Diversity Report** [FR-003]
  - **Action**: Generate a "Feasibility Report" entry stating that alpha-diversity computation was not performed due to data unavailability.
  - **Verification**: Assert `data/processed/feasibility_report.json` contains a `diversity_computation_status` field with value `blocked`.

- [ ] **T003** — **Generate Blocked Correlation Report** [FR-004, FR-005]
  - **Action**: Generate a "Feasibility Report" entry stating that correlation analysis was not performed due to data unavailability.
  - **Verification**: Assert `data/processed/feasibility_report.json` contains a `correlation_analysis_status` field with value `blocked`.

- [ ] **T004** — **Generate Blocked Visualization Report** [FR-006]
  - **Action**: Generate a "Feasibility Report" entry stating that visualization was not performed due to data unavailability.
  - **Verification**: Assert `data/processed/feasibility_report.json` contains a `visualization_status` field with value `blocked`.

- [ ] **T005** — **Report Exclusion Rates as Unmeasurable** [SC-001]
  - **Action**: Generate a "Feasibility Report" entry stating that exclusion rates are unmeasurable due to data unavailability.
  - **Verification**: Assert `data/processed/feasibility_report.json` contains an `exclusion_rates_status` field with value `unmeasurable`.

- [ ] **T006** — **Report Correlation Strength and FDR as Unmeasurable** [SC-002, SC-003]
  - **Action**: Generate a "Feasibility Report" entry stating that correlation strength and FDR are unmeasurable due to data unavailability.
  - **Verification**: Assert `data/processed/feasibility_report.json` contains a `correlation_metrics_status` field with value `unmeasurable`.

- [ ] **T007** — **Verify Blocked Artifact Structure for Reproducibility** [SC-005]
  - **Action**: Verify the structure of `data/processed/feasibility_report.json` and `outputs/reports/feasibility_report.md`. State that SHA-256 hash comparison is not applicable for blocked artifacts (hash is derived from `plan.md` content).
  - **Verification**: Assert `data/processed/feasibility_report.json` and `outputs/reports/feasibility_report.md` exist and contain expected fields.

- [ ] **T008** — **Generate Final Feasibility Report**
  - **Action**: Compile all blocked status reports into a single human-readable `outputs/reports/feasibility_report.md`.
  - **Verification**: Assert `outputs/reports/feasibility_report.md` exists and contains a summary of all blocked tasks.

### Phase 1: Data Model (Blocked State)

- [ ] **T009** — **Define Feasibility Report Schema**
  - **Action**: Define the schema for `data/processed/feasibility_report.json` with fields for status, reason, timestamp, and measurement status.
  - **Verification**: Assert `contracts/feasibility_report.schema.yaml` exists and is valid YAML.

### Phase 2: Research (Blocked State)

- [ ] **T010** — **Document Data Unavailability**
  - **Action**: Document the absence of a verified AGP URL in `research.md`.
  - **Verification**: Assert `research.md` contains a section documenting the data unavailability.

### Phase 3: Quickstart (Blocked State)

- [ ] **T011** — **Document Feasibility Report Generation**
  - **Action**: Document the process for generating the Feasibility Report in `quickstart.md`.
  - **Verification**: Assert `quickstart.md` contains a section documenting the Feasibility Report generation.

### Phase 4: Contracts (Blocked State)

- [ ] **T012** — **Define Feasibility Report Contract**
  - **Action**: Define the contract for `data/processed/feasibility_report.json` with fields for status, reason, timestamp, and measurement status.
  - **Verification**: Assert `contracts/feasibility_report.schema.yaml` exists and is valid YAML.

## Future Work (Conditional on Data Availability)

*If a verified AGP URL is found in a future revision, the following tasks will be enabled:*

- **T013** — Download AGP data [FR-001]
- **T014** — Filter samples [FR-002]
- **T020a** — Compute alpha-diversity [FR-003]
- **T021** — Perform Spearman correlation [FR-004]
- **T022** — Apply BH correction [FR-005]
- **T027** — Generate visualizations [FR-006]
- **T035** — Verify reproducibility [SC-005]