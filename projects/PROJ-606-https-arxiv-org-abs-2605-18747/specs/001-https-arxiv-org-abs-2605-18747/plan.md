# Implementation Plan: Reproduce & Validate Code as Agent Harness

**Branch**: `606-reproduce-validate-harness` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/606-reproduce-validate-harness/spec.md`

## Summary

This feature implements a reproducibility harness for the "Code as Agent Harness" paper (arXiv 2605.18747). The primary technical approach involves initializing a git submodule containing the reference implementation, executing its entry point on a CPU-only GitHub Actions runner, and generating structured artifacts that validate the paper's three-layer abstract (Interface, Mechanisms, Scaling) via **functional verification** rather than static checks. The plan includes a **sensitivity simulation protocol** (re-running with varied parameters where feasible) and a **resource control** mechanism to distinguish between code failures and runner constraints.

## Technical Context

**Language/Version**: Python 3.10+ (inferred from standard LLM research harnesses; if submodule specifies otherwise, adapt).
**Primary Dependencies**: `git` (for submodule), `subprocess` (for execution), `json`/`yaml` (for parsing), `pytest` (for validation). No heavy ML training libraries required for the *harness* itself, though the submodule may import them (handled via CPU fallback).
**Storage**: Filesystem (local runner storage) for artifacts and reports.
**Testing**: `pytest` for contract validation; shell scripts for execution verification.
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: CLI / Research Reproducibility Harness.
**Performance Goals**: Execution < 6 hours; Memory < 7 GB; Disk < 14 GB.
**Constraints**: NO GPU/CUDA; NO proprietary API keys required for basic run (or must fail gracefully); Submodule integrity verification required.
**Scale/Scope**: Single repository clone, single execution run, generation of core artifacts (`validation_report.md`, `limitations.md`, primary output file).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: No explicit `constitution.md` was supplied for this project. The principles below are mapped to the **Project Requirements (FR-030)** and **Explicit User Constraints** (CPU-only, reproducibility transparency) rather than a non-existent constitution file.

**Principles Verified (Mapped to FR-030 & Constraints)**:
1.  **Reproducibility First (FR-030)**: The plan mandates `limitations.md` generation (FR-007) and a **Sensitivity Simulation Protocol** (FR-006) to ensure gaps are documented and robustness is tested via re-execution, not just cataloging.
2.  **Compute Feasibility (User Constraint)**: The plan strictly enforces CPU-only execution and 7GB RAM limits, including a **Resource Control & Diagnostics** step to distinguish "Code Broken" from "Runner Too Small".
3.  **Evidence-Based Validation (FR-030)**: The validation report (FR-004, FR-005) requires **functional execution** and **semantic content verification** (e.g., checking metric trends) to map code output to paper claims, preventing hallucinated or tautological validation.
4.  **Transparency (FR-030)**: All hardcoded thresholds and external dependencies are flagged as "gaps" or "limitations" rather than ignored.

## Project Structure

### Documentation (this feature)

```text
specs/606-reproduce-validate-harness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (SCHEMA DEFINITIONS)
│   ├── artifact.schema.yaml
│   └── validation_report.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/606-reproduce-validate-harness/
├── .gitmodules                  # Submodule definition
├── external/
│   └── Awesome-Code-as-Agent-Harness-Papers/  # Vendored submodule
├── scripts/
│   ├── run_harness.sh           # Entry point execution (CPU enforced)
│   ├── validate_artifacts.py    # Parses outputs, maps to claims (USES contracts/)
│   └── scan_limitations.py      # Scans for API keys, hardcoded values
├── output/
│   ├── artifacts/               # Raw output from submodule
│   ├── validation_report.md     # Mapped claims vs. output
│   └── limitations.md           # Reproducibility gaps
└── tests/
    ├── test_execution.py        # Checks exit codes, file sizes
    └── test_contracts.py        # Validates JSON/YAML against contracts/
```

**Structure Decision**: Single project structure with a dedicated `external/` directory for the vendored submodule to isolate dependencies. Scripts are separated into `run`, `validate`, and `scan` to align with the three User Stories (Execution, Validation, Limitations). The `contracts/` directory is central to the validation logic, ensuring data model consistency.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Submodule Isolation | The reference code is external and may have conflicting dependencies. | Merging code directly would break version control and make updates/reverts impossible. |
| Separate Validation Script | Requires parsing arbitrary output formats (JSON, logs, figures) to map to abstract claims. | Hardcoding validation in the runner would be brittle and non-reusable for future papers. |
| Sensitivity Simulation | Code often contains "magic numbers" (timeouts, temps) that affect reproducibility. | A simple regex scan (FR-006 old) is insufficient for scientific rigor; we must attempt re-execution to measure impact. |
| Resource Control | The runner has strict RAM limits.; a large model would cause a false negative. | Ignoring resource constraints would lead to ambiguous failure modes (Code vs. Runner). |

## Computational Task Ordering

1.  **Pre-flight**: Initialize submodule, verify integrity, estimate resource usage.
2.  **Execution**: Run submodule with CPU enforcement and resource monitoring.
3.  **Validation**: Parse artifacts, validate against `contracts/` schemas, perform semantic content checks.
4.  **Sensitivity**: (If feasible) Re-run with varied parameters to measure impact.
5.  **Reporting**: Generate `validation_report.md` and `limitations.md`.
