# Implementation Plan: Reproduce & Validate OpenComputer

**Branch**: `607-reproduce-opencomputer` | **Date**: 2026-05-22 | **Spec**: `specs/607-reproduce-opencomputer/spec.md`

## Summary

This project reproduces the core claims of "OpenComputer: Verifiable Software Worlds for Computer-Use Agents" by executing a smoke test and a small batch of tasks (≥5) within a local Docker backend on a free-tier CI runner. The technical approach involves orchestrating the OpenComputer submodule, provisioning CPU-only Docker containers for specific desktop applications (e.g., Audacity), and comparing the system's `hardcode` verifier outputs against a **blinded, independent human adjudication** of the generated artifacts.

**Critical Scope Adjustment**: The study is explicitly framed as a **Pipeline Viability & Qualitative Case Study**. Due to the small sample size (N=5) and the constraints of the free-tier CI environment, the plan **does not** calculate a statistical `verifier_alignment_rate` with a confidence interval. Instead, it generates a qualitative narrative of alignment for each task. The plan acknowledges that the source spec's requirement for a "10% margin of error" (US-2) is mathematically impossible for N=5 and flags this as a spec-root cause limitation; the plan will not attempt to meet this impossible statistical target but will instead provide the most rigorous qualitative validation possible.

## Technical Context

**Language/Version**: Python 3.11 (host), Bash (orchestration)  
**Primary Dependencies**: `docker-py`, `pytest`, `pandas`, `jinja2` (for report generation), OpenComputer submodule dependencies (as per `requirements.txt`)  
**Storage**: Ephemeral Docker volumes for task execution; JSON artifacts written to `external/OpenComputer/results/`  
**Testing**: `pytest` (unit tests for scripts), **Blinded Manual Inspection** for ground truth (US-2)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research reproduction / CLI tooling  
**Performance Goals**: Total runtime ≤ 6 hours; Memory usage < 7GB during container build/execution; No GPU usage.  
**Constraints**: Must run on CPU-only runner; Docker daemon must be available; No external API keys required for `hardcode` verifier (agents requiring keys are skipped gracefully).  
**Scale/Scope**: A smoke test task; 5 batch tasks; a final report (Qualitative Case Study).

## Constitution Check

*Gates determined based on standard research integrity principles (as no specific constitution was supplied, we adhere to the project's implicit SSoT and Research Integrity principles):*

1.  **Reproducibility**: The plan explicitly defines the subset of tasks (5 tasks), the exact scripts (`smoke_loop.py`, `run_eval.py`), and the **Blinding Protocol** for manual inspection, ensuring the experiment can be repeated by a different adjudicator.
2.  **Transparency**: The `reproduction_report.md` will explicitly state limitations (e.g., small sample size, CPU-only constraints, the impossibility of the spec's 10% margin requirement) rather than overclaiming alignment with the full paper corpus.
3.  **Validity**: The `alignment_observation` is defined by **independent manual inspection** of artifacts (ground truth), not just the system's internal log. The human adjudicator is blinded to the verifier's logic to prevent confirmation bias.
4.  **Feasibility**: The plan restricts scope to tasks solvable on a resource-constrained, CPU-only runner. The "Manual Inspection" step is a **one-time ground-truth establishment** for the specific sample, not a recurring automated test, satisfying the "Real-call testing" principle by being a documented, reproducible scientific step rather than an automated CI gate.
5.  **Spec-Root Cause Flag**: The source spec (US-2) requires a "10% margin of error" and a statistical "rate" (FR-003). This plan explicitly notes that for N=5, these are mathematically impossible. The plan deviates to a qualitative case study approach, flagging the spec's requirement as a limitation that cannot be met without increasing the sample size beyond CI constraints.

## Project Structure

### Documentation (this feature)

```text
specs/607-reproduce-opencomputer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── task.schema.yaml
│   ├── verification_report.schema.yaml
│   └── smoke_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── OpenComputer/        # Submodule containing source code, tasks, and verifiers

projects/607-reproduce-opencomputer/
├── scripts/
│   ├── setup_plan.sh    # Mechanical setup
│   ├── run_smoke_test.sh
│   └── run_batch_eval.sh
├── results/             # Generated JSON artifacts
│   ├── smoke_report.json
│   └── verification_report.json
└── reports/
    └── reproduction_report.md
```

**Structure Decision**: The implementation relies on the vendored `external/OpenComputer` submodule. No new core logic is written; instead, wrapper scripts (`run_smoke_test.sh`, etc.) are created in `projects/607-reproduce-opencomputer/scripts/` to manage the execution flow, error handling, and report aggregation within the CI constraints. The `verification_report.json` schema has been updated to include `manual_ground_truth` and `manual_judgment_notes` to support the new qualitative methodology.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Docker Backend Complexity | Required to simulate the "Verifiable Software World" environment where agents interact with GUI apps. | Running agents directly on the host OS fails to provide the isolated, verifiable state required by the OpenComputer architecture. |
| Manual Inspection Step | Required to establish independent ground truth for `alignment_observation` (US-2). | Relying solely on the system's internal logs would be circular reasoning and fail to validate the "human adjudication" claim. The **Blinding Protocol** ensures independence. |
| Qualitative vs. Quantitative | Required due to N=5 sample size and CI constraints. | Attempting to calculate a statistical "rate" with a "10% margin of error" for N=5 is mathematically impossible and scientifically unsound. |
