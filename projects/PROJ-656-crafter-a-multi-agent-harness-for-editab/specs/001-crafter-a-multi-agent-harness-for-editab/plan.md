# Implementation Plan: Crafter Multi-Agent Harness Validation

**Branch**: `656-crafter-validation` | **Date**: 2026-06-03 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/656-crafter-validation/spec.md`

## Summary

This project validates the `Crafter` multi-agent harness by reproducing its core capabilities: generating publication-quality figures from text prompts, converting them to editable SVGs, and executing the `CraftBench` evaluation suite. The technical approach distinguishes between two execution modes to preserve **Construct Validity**:
1.  **Dry-Run (CI Mode)**: Validates **Pipeline Integrity** (orchestration, logging, error handling) using "Mock Mode" for agents. This mode *does not* validate generation quality, agent reasoning, or multi-agent behavior. It confirms the *harness* can coordinate steps, not that the *agents* are intelligent.
2.  **Full-Run (Local/Research Mode)**: Validates **Functional Capabilities** (generation quality, editability, multi-agent reasoning) using real API calls and models. This mode is required to support claims about scientific insight and figure quality.

The project focuses on validating the *mechanism* of the harness (the "loom") rather than the *scientific design* of the figures (the "flowers"), consistent with the analogy that the loom executes the pattern but does not originate the design.

## Technical Context

**Language/Version**: Python 3.10+ (required by Crafter dependencies)  
**Primary Dependencies**: `torch` (CPU-only), `scikit-learn`, `requests`, `lxml`, `pyyaml`  
**Storage**: Local filesystem (`external/Crafter`, `output/`, `logs/`)  
**Testing**: `pytest` (for contract validation), manual execution of entry points  
**Target Platform**: GitHub Actions Free Tier (Linux, multiple CPU cores, 7 GB RAM, No GPU)  
**Project Type**: CLI / Reproduction Pipeline  
**Performance Goals**: End-to-end execution ≤ 6 hours (Dry-Run); Memory ≤ 7 GB; API timeout ≤ 30s  
**Constraints**: 
- No GPU usage.
- **Fail Fast is Default**: The system defaults to failing with a clear error if external dependencies are missing (Principle II).
- **Mock Mode is Explicit**: "Mock Mode" is an *optional, opt-in* override triggered ONLY by `CRAFTER_MODE=mock`. It is not silent and is explicitly flagged in logs and reports.
- **Scale/Scope**: Single feature validation; limited to provided `craftbench` sample set.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (SSoT)**: The `data-model.md` is the Single Source of Truth for all data structures. The `contracts/` directory contains schemas derived strictly from `data-model.md`. The plan enforces that `data-model.md` is finalized before contract generation in Phase 1.
- **Principle II (No Silent Fallbacks)**: The system defaults to "Fail Fast" if external dependencies (API keys) are missing. "Mock Mode" is a *deliberate, opt-in* fallback triggered only by the explicit environment variable `CRAFTER_MODE=mock`. It is not silent; it is logged and flagged in the output.
- **Principle III (Feasibility)**: The plan restricts dependencies to CPU-tractable libraries and enforces a 6-hour runtime limit on the free-tier runner. The "Dry-Run" mode ensures the CI job completes by skipping computationally heavy generation steps.
- **Principle IV (Transparency)**: All agent interactions (real or mocked) are logged to `logs/agent_trace.log`. The distinction between "Dry-Run" and "Full-Run" is explicitly recorded in the evaluation report.
- **Principle V (Real-Call Testing)**: While CI uses "Mock Mode" for feasibility, the plan mandates that a "Full-Run" be attempted in a local or privileged environment to validate the actual multi-agent behavior and generation quality, ensuring the "Real-Call" requirement is met where possible.

## Project Structure

### Documentation (this feature)

```text
specs/656-crafter-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (Source of Truth)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Derived from data-model.md)
│   ├── figure_spec.schema.yaml
│   └── evaluation_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── Crafter/             # Vendored repository
    ├── inference.py
    ├── convert.py
    ├── craftbench/
    │   ├── manifest.json
    │   └── evaluation/
    └── logs/

output/                  # Generated figures and SVGs
logs/                    # Agent traces and error logs
tests/
├── contract/            # Schema validation tests
└── integration/         # End-to-end pipeline tests
```

**Structure Decision**: The structure isolates the vendored `Crafter` code in `external/` to prevent modification of the original source while allowing the project's test suite to validate its outputs. The `output/` and `logs/` directories are kept at the root for easy CI artifact collection. The `data-model.md` is established as the SSoT, and contracts are generated from it in Phase 1.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mock API Layer | Required to run on CI without paid keys | Direct API calls would fail on free-tier runners, blocking reproducibility of the *pipeline*. |
| Dry-Run Mode | Required to validate orchestration without generation | Full generation is infeasible on CI; Dry-Run validates the harness logic, not the output quality. |
| Structural Element Overlap | Required for SVG comparison | String similarity is scientifically invalid for SVGs; DOM-based comparison is robust. |
| External Metric Validation | Required to avoid circularity | Internal metrics are self-scoring; an external validator is needed for scientific soundness. |

## Success Criteria & Validity

### Pipeline Integrity (CI/Dry-Run)
- **PI-001**: The `inference.py` entry point executes without runtime errors when `CRAFTER_MODE=mock` is set.
- **PI-002**: The `convert.py` script correctly identifies and skips placeholder images, logging a warning instead of generating invalid SVG.
- **PI-003**: The `agent_trace.log` contains structured entries for all pipeline steps (Planner, Drawer, Critic) even in mock mode.

### Functional Validity (Local/Full-Run)
- **FV-001**: The `craftbench` evaluation produces a `success_rate` ≥ 90% on the provided sample set when using real agents (SC-001).
- **FV-002**: Generated SVGs contain ≥ 80% of the text elements found in ground truth when compared via **Structural Element Overlap (SEO)** (SC-002).
- **FV-003**: The full end-to-end reproduction (generation + conversion + evaluation) completes within 6 hours on a CPU-only runner with ≤ 7 GB RAM (SC-003).
- **FV-004**: The `agent_trace.log` contains at least 3 distinct agent roles interacting for each generated figure (SC-004).

*Note: CI results (Dry-Run) satisfy PI-001 to PI-003 only. They do not satisfy FV-001 to FV-004, which require real agent execution.*