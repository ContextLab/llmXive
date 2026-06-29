# Implementation Plan: Neuro‑Symbolic Learning Networks

**Branch**: `[PROJ-559-neuro-symbolic]` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/PROJ-559-neuro-symbolic/spec.md`

## Summary

Implement a lightweight neuro‑symbolic explanation framework that generates three explanation types (neural‑only, symbolic‑only, neuro‑symbolic) for mathematics/logic problems from educational datasets. Simulate student responses using a BKT‑based model calibrated against human pilot data, then run mixed‑effects regression to compare reasoning accuracy, response time, and self‑reported comprehension across conditions. The pipeline must complete within GitHub Actions free‑tier constraints (2 CPU cores, ≤7 GB RAM, ≤6 h).

**Scope Note**: This plan proceeds with ASSISTments dataset only. Khan Academy dataset referenced in spec has no verified source; FR-001 scope is reduced accordingly. Human participant data (≥50 pilot, ≥200 real) requires IRB‑approved study and is a prerequisite before full simulation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU‑only), `transformers`, `scikit‑learn`, `pandas`, `statsmodels`, `pyyaml`  
**Storage**: Local files under `data/` (CSV, JSON, JSONL artifacts)  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free‑tier runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: ≤6 h total runtime, ≤7 GB peak memory, ≤2 CPU cores  
**Constraints**: No GPU/CUDA; no deep‑net training from scratch; dataset subset to fit RAM  
**Scale/Scope**: ≥6,000 simulated interactions + ≥200 real student records; ≥50 human pilot participants for calibration  

> Domain‑specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

| Principle | Compliance Status | Plan Action |
|-----------|-------------------|-------------|
| I. Reproducibility (NON‑NEGOTIABLE) | **COMPLIANT** | Pin random seeds in `code/`; fetch external datasets from canonical HuggingFace sources; `requirements.txt` at `code/` |
| II. Verified Accuracy | **PARTIAL** | Reference‑Validator Agent gates all citations; only cite verified dataset URLs from the `# Verified datasets` block; Khan Academy gap documented |
| III. Data Hygiene | **COMPLIANT** | Checksum all `data/` files; no in‑place modification; PII scan on commits |
| IV. Single Source of Truth | **COMPLIANT** | All figures/statistics trace to `data/` rows and `code/` blocks; derived numbers auto‑generated |
| V. Versioning Discipline | **COMPLIANT** | Content hashes for all artifacts; `updated_at` timestamp updated on artifact change |
| VI. Educational Evaluation Rigor | **PARTIAL** | Mixed‑effects regression with fixed effects for condition, prior knowledge, problem difficulty; random intercepts for problem_id, student_id; report effect sizes with 95% CI; human data collection prerequisite |
| VII. Explanation Traceability | **COMPLIANT** | Persist neuro‑symbolic traces under `data/` with metadata linking to problem instance, model version, and condition |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-559-neuro-symbolic/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── download/
│   └── fetch_datasets.py        # FR-001, FR-007: dataset download with timeout
├── generate/
│   ├── neural_explanation.py    # FR-002: neural-only explanation
│   ├── symbolic_explanation.py  # FR-002: symbolic-only explanation
│   ├── neuro_symbolic_explanation.py  # FR-002: hybrid explanation
│   └── explanation_generator.py # US-1: orchestrator
├── simulate/
│   ├── bkt_simulator.py         # FR-003, US-2: BKT-based student simulator
│   ├── calibration.py           # FR-010, US-5: human pilot calibration
│   └── run_simulation.py        # FR-009: full simulation run
├── analyze/
│   ├── mixed_effects.py         # FR-006, US-3, US-7: regression analysis
│   └── effect_sizes.py          # FR-006: Cohen's d with CI
├── utils/
│   ├── config.py                # random seeds, timeouts
│   └── logging.py               # SC-005, SC-006: resource monitoring
└── tests/
    ├── contract/
    │   └── test_schemas.py      # validate Problem, Explanation, SimulationLog schemas
    ├── integration/
    │   └── test_pipeline.py     # end-to-end pipeline test
    └── unit/
        └── test_bkt.py          # BKT simulator unit tests

data/
├── raw/                         # downloaded datasets (checksummed)
├── derived/                     # explanation artifacts, simulation logs
└── pilot/                       # human calibration data (≥50 participants)

contracts/
├── problem.schema.yaml          # Problem entity schema
├── explanation.schema.yaml      # Explanation entity schema
├── simulation_log.schema.yaml   # SimulationLog entity schema
└── analysis_output.schema.yaml  # Regression output schema
```

**Structure Decision**: Single project structure under `code/` with modular subdirectories for download, generate, simulate, analyze, and utils. This matches the computational research pipeline nature of the feature and keeps CI‑friendly simplicity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate calibration phase (FR-010) | Required to avoid circularity per spec; calibration must occur BEFORE full simulation | Running simulation without calibration would produce biased results and violate SC-007 |
| Mixed‑effects regression (FR-006) | Required by Constitution Principle VI for educational evaluation rigor | Simple ANOVA would not control for problem difficulty and prior knowledge |
| Human pilot dataset (≥50) + real student dataset (≥200) | Required by FR-010 and FR-011 for scientific validity | Simulation alone cannot support generalizable claims about real learners |
| Three explanation conditions | Required by FR-002 to compare neural, symbolic, and neuro‑symbolic approaches | Single or dual condition would not address the core research question |

## Validation Steps (Addressing Success Criteria)

### SC-001: ≥95% Explanation Generation Success Rate
- **Validation**: Contract test in `test_schemas.py` counts generated explanation files vs. problem count
- **Threshold**: 95% success rate enforced before simulation proceeds
- **Failure**: Pipeline aborts with clear error message listing failed problems

### SC-003: Effect-Size CI Width ≤0.20
- **Validation**: `analysis_output.schema.yaml` includes `ci_width` field; regression script computes and validates
- **Threshold**: CI width for neuro‑symbolic vs. neural comparison must be ≤0.20
- **Failure**: Results flagged as insufficient precision; sample size may need increase

### SC-005: Data Completeness and Distribution
- **Validation**: Contract test checks that logs have all required fields
- **Distribution Check**: Histogram bin width = 1 second; no more than 2 consecutive empty bins allowed
- **Failure**: Logs with missing fields excluded; distribution violation logged

## Human Data Collection Timeline

| Milestone | Timeline | Fallback |
|-----------|----------|----------|
| IRB Approval | Weeks 1‑4 | Simulation proceeds with limitation note |
| Pilot Data Collection (≥50) | Weeks 5‑8 | Use synthetic calibration with explicit limitation |
| Calibration Validation | Week 9 | If RMSE >0.15, iterate BKT parameters |
| Real Student Data (≥200) | Weeks 10‑16 | Final analysis limited to simulated data if unavailable |

**Note**: Simulation can proceed with synthetic calibration if human data collection fails, but all generalizability claims will be explicitly limited per Constitution Principle II.