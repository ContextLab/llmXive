# Implementation Plan: Heterogeneous Scientific Foundation Model Collaboration Benchmark

**Branch**: `[001-heterogeneous-collaboration]` | **Date**: 2026-06-24 | **Spec**: `specs/001-heterogeneous-collaboration/spec.md`
**Input**: Feature specification from `/specs/001-heterogeneous-collaboration/spec.md`

## Summary

**Primary requirement**: Evaluate whether heterogeneous scientific foundation models (time-series, tabular, text) achieve better collaborative task performance when maintaining modality-specific expertise through specialized interfaces, compared to unified language-only architectures.

**Technical approach**: Implement two parallel pipelines—(A) heterogeneous modality-specific orchestration routing raw inputs to native models (TimeSeries-Transformer, TabPFN, distilled LLM), and (B) unified text-only translation converting all modalities to text before single LLM inference. Compare performance via paired t-test and bootstrap CI across multiple multi-modal tasks.

**Dataset substitution strategy**: PhysioNet and PubMed have NO verified sources (⚠️ BLOCKING GAP). Substitute UCI_HAR for time-series, DROP/MUST for text. Document domain mismatch in paper limitations.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: scikit-learn>=1.3.0, pandas>=2.0.0, numpy>=1.24.0, pyyaml>=6.0, datasets>=2.14.0, scipy>=1.11.0, matplotlib>=3.7.0, reportlab>=4.0.0, requests>=2.31.0  
**Storage**: Local filesystem under `data/` with checksums in `state/`  
**Testing**: pytest>=7.4.0 with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk, no GPU)  
**Project Type**: scientific-benchmark/cli  
**Performance Goals**: Per-task inference ≤5 minutes on 2 CPU cores; full benchmark ≤4 hours wall-clock time  
**Constraints**: No GPU/CUDA; no deep-net training from scratch; no 8-bit/4-bit quantization; total dataset size ≤5 GB; runtime ≤6 hours per job  
**Scale/Scope**: 20 multi-modal tasks; multiple modalities (time-series, tabular, text); multiple random seeds for reproducibility

> Dataset sizes and empirical performance thresholds deferred to research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Plan Mapping |
|------------------------|-------------------|--------------|
| I. Reproducibility | ✅ COMPLIANT | FR-005 logs seeds/versions; Phase 3.1 pins requirements.txt; Phase 4.1 runs 5 seeds |
| II. Verified Accuracy | ⚠️ PARTIAL | Research.md cites ONLY verified dataset URLs; PhysioNet/PubMed gaps documented; Reference-Validator gate in constitution |
| III. Data Hygiene | ✅ COMPLIANT | Phase 1.1 checksums all datasets; raw data preserved; derivations to new files |
| IV. Single Source of Truth | ✅ COMPLIANT | All figures/statistics trace to `data/` rows and `code/` blocks; StatisticalSummary persisted to `data/statistical_summary.yaml` |
| V. Versioning Discipline | ✅ COMPLIANT | Content hashes in `state/`; artifact changes update `updated_at` timestamp |
| VI. Modality-Specific Processing | ✅ COMPLIANT | FR-002 routes native models; FR-003 logs text conversion with fidelity validation; Constitution VI explicitly followed |
| VII. Rigorous Comparative Evaluation | ✅ COMPLIANT | FR-007/FR-014 implement paired t-test, bootstrap CI (multiple resamples), Wilcoxon alternatives |

**GATE STATUS**: ⚠️ CONDITIONAL PASS — Dataset substitution strategy documented; PhysioNet/PubMed gaps flagged for paper limitations.

## Project Structure

### Documentation (this feature)

```text
specs/001-heterogeneous-collaboration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── task.schema.yaml
│   ├── results.schema.yaml
│   └── modality_model.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── benchmark/
│   ├── __init__.py
│   ├── run_benchmark.py          # Main entry point (FR-001, FR-006, FR-010)
│   ├── run_task.py               # Single task execution (FR-008, FR-009)
│   └── config/
│       ├── default.yaml          # Default benchmark configuration
│       └── modalities/           # Modality configuration directory (FR-008)
│           ├── timeseries.yaml
│           ├── tabular.yaml
│           └── text.yaml
├── models/
│   ├── __init__.py
│   ├── routing.py                # Heterogeneous orchestration (FR-002)
│   ├── translation.py            # Unified translation layer (FR-003)
│   ├── timeseries_model.py       # TimeSeries-Transformer wrapper
│   ├── tabular_model.py          # TabPFN wrapper
│   └── text_model.py             # Distilled LLM wrapper
├── tasks/
│   ├── __init__.py
│   ├── task_runner.py            # Task execution logic
│   └── task_definitions.yaml     # 20 multi-modal task definitions
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                # F1, MAPE computation (FR-004)
│   ├── statistical_tests.py      # t-test, Wilcoxon, bootstrap (FR-007, FR-014)
│   └── report_generator.py       # CSV + PDF report generation (FR-007)
├── data/
│   ├── download.py               # Dataset download with retry (FR-010)
│   ├── checksums.yaml            # Data integrity tracking (Constitution III)
│   ├── processed/                # Derived data (new filenames, Constitution III)
│   └── statistical_summary.yaml  # StatisticalSummary persistence (Constitution IV)
├── utils/
│   ├── __init__.py
│   ├── logging.py                # Seed/version logging (FR-005)
│   ├── timeout.py                # Per-task timeout enforcement (FR-006, FR-013)
│   └── missing_handler.py        # Missing modality handling (FR-009, FR-012)
└── contracts/
    └── schemas/                  # Validation schemas (contract tests)
        ├── dataset.schema.yaml
        ├── task.schema.yaml
        ├── results.schema.yaml
        └── modality_model.schema.yaml

tests/
├── contract/                     # Schema validation tests
├── integration/                  # End-to-end benchmark tests
└── unit/                         # Model wrapper, metric tests

requirements.txt                  # Pinned dependencies (Constitution I)
```

**Structure Decision**: Single project structure (DEFAULT) selected. Scientific benchmark requires tight integration between data download, model orchestration, and statistical evaluation. All components under `src/` with clear separation of concerns. Tests organized by type (contract, integration, unit) for maintainability.

## Phase Breakdown

### Phase 0: Research & Dataset Verification (Week 1)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 0.1 | Verify dataset availability for time-series, tabular, text modalities | FR-001 | research.md dataset table |
| 0.2 | Confirm model weights <1 GB and CPU-tractable | FR-002, SC-002 | research.md model inventory |
| 0.3 | Validate statistical methodology (t-test, bootstrap, Wilcoxon) | FR-007, FR-014 | research.md methodology section |
| 0.4 | Document dataset-variable fit; flag any missing variables | FR-001 | research.md dataset gap analysis |
| 0.5 | Verify model weights before implementation; fallback to smaller variants | FR-002 | research.md model verification report |

### Phase 1: Data Model & Contracts (Week 1-2)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 1.1 | Define dataset schema with checksums | Constitution III | contracts/dataset.schema.yaml |
| 1.2 | Define task schema (20 tasks, 3 modalities) | FR-008 | contracts/task.schema.yaml |
| 1.3 | Define results schema (CSV + PDF fields) | FR-007 | contracts/results.schema.yaml |
| 1.4 | Define modality_model schema | Plan Consistency | contracts/modality_model.schema.yaml |
| 1.5 | Create data-model.md with entity relationships | FR-001, FR-004 | data-model.md |
| 1.6 | Create quickstart.md with setup instructions | US-1 | quickstart.md |

### Phase 2: Core Implementation (Week 2-3)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 2.1 | Implement dataset download with 3-retry logic | FR-010 | src/data/download.py |
| 2.2 | Implement modality-specific model wrappers | FR-002 | src/models/*_model.py |
| 2.3 | Implement heterogeneous routing layer | FR-002 | src/models/routing.py |
| 2.4 | Implement unified translation layer with fidelity validation | FR-003 | src/models/translation.py |
| 2.5 | Implement missing modality handler | FR-009, FR-012 | src/utils/missing_handler.py |
| 2.6 | Implement timeout enforcement | FR-006, FR-013 | src/utils/timeout.py |

### Phase 3: Evaluation & Reporting (Week 3-4)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 3.1 | Implement metrics computation (F1, MAPE) | FR-004 | src/evaluation/metrics.py |
| 3.2 | Implement statistical tests (t-test, Wilcoxon, bootstrap) | FR-007, FR-014 | src/evaluation/statistical_tests.py |
| 3.3 | Implement StatisticalSummary creation and persistence | FR-007, Constitution IV | src/evaluation/report_generator.py |
| 3.4 | Implement seed/version logging | FR-005 | src/utils/logging.py |
| 3.5 | Create requirements.txt with pinned versions | Constitution I | requirements.txt |
| 3.6 | Persist StatisticalSummary to data/statistical_summary.yaml | Constitution IV | data/statistical_summary.yaml |

### Phase 4: Validation & Reproducibility (Week 4)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 4.1 | Run benchmark with 5 random seeds | SC-004 | reproducibility logs |
| 4.2 | Verify results within 95% CI across seeds | SC-004 | Phase 4 report |
| 4.3 | Validate all outputs against contract schemas | Constitution II | contract test results |
| 4.4 | Verify total runtime ≤4 hours on reference hardware | SC-003 | runtime benchmarks |
| 4.5 | Verify per-task inference ≤5 minutes | SC-002 | per-task timing logs |

### Phase 5: Documentation & Handoff (Week 5)
| Phase | Task | FR/SC Mapping | Deliverable |
|-------|------|---------------|-------------|
| 5.1 | Complete paper with all statistical artifacts | Constitution VII | final paper |
| 5.2 | Update constitution version if amended | Constitution V | updated constitution |
| 5.3 | Archive artifacts with content hashes | Constitution V, III | state/ artifact_hashes |
| 5.4 | Final reproducibility check on fresh runner | Constitution I | CI pass |

## Compute Feasibility Assessment

| Constraint | Requirement | Plan Compliance |
|------------|-------------|-----------------|
| CPU cores | 2 cores | All models CPU-tractable; no GPU dependencies |
| RAM | ~7 GB | Dataset subset to ≤5 GB; models <1 GB each |
| Disk | ~14 GB | Total dataset + processed data ≤10 GB |
| Runtime | ≤6 h/job | Full benchmark ≤4 hours; per-task ≤5 minutes |
| GPU | None | No CUDA, no quantization, no GPU-specific code |
| Library wheels | CPU-only | Pin torch (CPU wheel), scikit-learn, pandas |

**Risk Mitigation**: If any model exceeds 1 GB or inference exceeds 5 minutes, plan includes fallback to smaller distilled variants or sampled data (documented in research.md Decision/Rationale).

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Dataset missing required variables | Medium | Blocking | Phase 0.4 explicitly flags gaps; do NOT proceed without verified fit |
| Model inference >5 minutes | Medium | Blocking | Phase 0.5 verify weights; timeout enforcement (FR-013) |
| Total runtime >4 hours | Medium | Blocking | Phase 4.4 timing validation; sample data if needed |
| Dataset download fails after 3 retries | Low | Blocking | FR-010 retry logic; Phase 0.1 verify URL reachability |
| Statistical test assumptions violated | Medium | Moderate | FR-014 non-parametric alternatives (Wilcoxon) |
| Translation fidelity loss | Medium | Moderate | Phase 2.4 validate translation quality; measure information loss |
| Task selection bias | Medium | Moderate | Stratify tasks by difficulty; blocking analysis in statistical tests |
| Domain mismatch (substitute datasets) | High | Moderate | Document in paper limitations; frame results as exploratory |