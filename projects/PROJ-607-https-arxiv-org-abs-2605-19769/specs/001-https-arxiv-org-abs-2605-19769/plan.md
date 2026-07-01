# Implementation Plan: Reproduce & Validate OpenComputer

**Branch**: `607-reproduce-opencomputer` | **Date**: 2026-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/607-reproduce-opencomputer/spec.md`

## Summary

This project reproduces the core validation loop of the "OpenComputer: Verifiable Software Worlds for Computer-Use Agents" paper within the constraints of a free-tier CI runner. The primary requirement is to execute a smoke test and a small-batch validation (N=5) of the OpenComputer verifier against manual human adjudication. The technical approach involves orchestrating Docker containers to provision environments, running the `smoke_loop` and `run_eval` scripts from the vendored `external/OpenComputer` submodule, collecting artifacts, and executing a **dual-inspection** manual adjudication protocol to calculate alignment consistency. The plan explicitly avoids statistical significance testing due to the small sample size (N=5), pivoting to a qualitative narrative focused on the *feasibility* of the validation loop.

## Technical Context

**Language/Version**: Python 3 (for orchestration scripts), Bash modern versions (for Docker/CI)
**Primary Dependencies**: `docker` (CLI), `pytest` (for validation scripts), `pandas` (for data aggregation), `pyyaml` (for schema validation). The `external/OpenComputer` submodule provides the core `smoke_loop`, `run_eval`, and verifier logic.
**Storage**: Local filesystem (`projects/607-reproduce-opencomputer/results/`, `projects/607-reproduce-opencomputer/data/`) for JSON/CSV artifacts and Docker image layers.
**Testing**: `pytest` for unit tests of helper scripts; `smoke_loop` exit codes and JSON schema validation for integration.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, 14 GB disk).
**Project Type**: Computational Research / Reproduction Pipeline.
**Performance Goals**: Total pipeline execution < 6 hours; Docker image build < 45 minutes; single task execution < 15 minutes.
**Constraints**: No GPU; strict 14 GB disk quota; must handle missing API keys gracefully; must not crash on container failures.
**Scale/Scope**: 1 smoke test task; 5 batch evaluation tasks; 1 final report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle I (Evidence)**: The plan relies *only* on the `external/OpenComputer` submodule for task definitions and verifiers. No fabricated datasets or URLs are introduced. The **dual-inspection** manual adjudication step provides the primary evidence for alignment.
2.  **Principle II (Verification)**: All claims in the final report are backed by generated JSON artifacts (`smoke_report.json`, `verification_report.json`, `blinded_ground_truth.json`) and the `reproduction_report.md`. The "verifier_alignment_rate" is explicitly defined as a simple count of matches for the qualitative narrative, avoiding unverified statistical claims.
3.  **Principle III (Reproducibility)**: The pipeline is fully scripted (`run_smoke_test.sh`, `run_batch_eval.sh`, `generate_report.py`). The `blinded_ground_truth.json` ensures the manual inspection is auditable and reproducible by future researchers.
4.  **Principle IV (Constraints)**: The plan explicitly targets CPU-only execution and a sample size of N=5 to fit within the 14 GB disk and 7 GB RAM limits of the CI runner.

## Project Structure

### Documentation (this feature)

```text
specs/[607-reproduce-opencomputer]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/607-reproduce-opencomputer/
├── scripts/
│   ├── run_smoke_test.sh        # Orchestrates smoke test (FR-001)
│   ├── run_batch_eval.sh        # Orchestrates 5-task batch (FR-002)
│   ├── prepare_ground_truth.py  # Generates blinded manual inspection data (T023)
│   ├── collect_artifacts.py     # Copies artifacts from Docker to host (T022)
│   ├── compare_verdicts.py      # Merges verifier results with manual ground truth (T024)
│   └── generate_report.py       # Aggregates data into reproduction_report.md (FR-004)
├── data/
│   ├── summary.json             # Metadata and aggregate stats
│   ├── verification_results.csv # Detailed row-level results
│   └── blinded_ground_truth.json # Manual inspection records (Dual-Inspection)
├── results/
│   ├── smoke_report.json        # Smoke test output
│   └── verification_report.json # Batch evaluation output
├── figures/
│   └── verifier_comparison.png  # (Optional) Visualization of alignment
├── contracts/
│   ├── task.schema.yaml         # Schema for task definitions
│   ├── verification_report.schema.yaml # Schema for batch results
│   ├── smoke_report.schema.yaml # Schema for smoke test output
│   └── verification_results.schema.yaml # Schema for merged results
└── docs/
    └── reproducibility/
        └── reproduction_report.md # Final deliverable (FR-004)
```

**Structure Decision**: The structure is organized around the pipeline phases (Smoke, Batch, Analysis, Reporting) to ensure modularity and prevent token truncation in monolithic scripts. Data is separated from results to maintain a clear audit trail for the manual inspection process.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-Inspection Protocol | Required to mitigate single-point-of-failure in ground truth validity (Methodology Concern). | Single-inspector protocol was rejected as it introduces high risk of bias and error, compromising the "ground truth" required for verifier validation. |
| N=5 Sample Size | Necessary to fit within 6-hour CI limit and 14 GB disk quota while running Docker containers. | Larger sample sizes (e.g., N=50) would exceed CI runtime limits and risk OOM errors on the free-tier runner. |
| Qualitative Narrative | Required because N=5 is statistically insufficient for p-value calculations (e.g., McNemar's test). | Attempting statistical significance on N=5 would be methodologically flawed and flagged by reviewers. |

## FR/SC Coverage Matrix

| ID | Type | Plan Element | Description |
| :--- | :--- | :--- | :--- |
| **FR-001** | FR | `run_smoke_test.sh` | Executes `smoke_loop` against `audacity_export_wav_440` with Docker backend. |
| **FR-002** | FR | `run_batch_eval.sh` | Runs `run_eval.py` for 5 tasks and generates `verification_report.json`. |
| **FR-003** | FR | `compare_verdicts.py` | Computes alignment consistency (simple count of matches) by comparing hard-coded verdicts to `blinded_ground_truth.json`. |
| **FR-004** | FR | `generate_report.py` | Generates `reproduction_report.md` with comparison to paper claims. |
| **FR-005** | FR | `run_batch_eval.sh` (error handling) | Catches Docker/build errors, logs them, and marks tasks as "failed" or "skipped" without crashing. |
| **SC-001** | SC | `compare_verdicts.py` | Measures alignment consistency (count of matches) against dual manual inspection of 5 artifacts. |
| **SC-002** | SC | `verification_report.json` | Measures task success rate against `task.json` expected outcomes. |
| **SC-003** | SC | `reproduction_report.md` | Measures completeness against the requirement to cite paper abstract claims. |
| **SC-004** | SC | `data/summary.json` | Measures pipeline reliability (% of tasks not crashing). |
| **SC-005** | SC | CI Job Timeout | Measures execution time against 6-hour limit. |

## Data Flow & Contract Validation

The pipeline explicitly validates data against the contracts defined in `contracts/`:
1.  **Ingest**: `run_batch_eval.sh` generates `verification_report.json`, which is validated against `contracts/verification_report.schema.yaml`.
2.  **Extract**: `collect_artifacts.py` moves artifacts to `results/blinded_artifacts/`.
3.  **Blind**: `prepare_ground_truth.py` creates `blinded_ground_truth.json` (initially with `uninspected` verdicts).
4.  **Inspect**: Two independent researchers inspect artifacts and update `blinded_ground_truth.json`.
5.  **Merge**: `compare_verdicts.py` reads both JSONs, validates the merged output against `contracts/verification_results.schema.yaml`, and writes `data/verification_results.csv` and `data/summary.json`.
6.  **Report**: `generate_report.py` reads `summary.json` and `verification_results.csv` to produce `reproduction_report.md`.

Each step explicitly references its corresponding schema file to ensure data integrity.