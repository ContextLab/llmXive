# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary

This project audits publicly available A/B test summaries for statistical consistency between reported metrics (p-values, effect sizes, sample sizes) and reconstructed values using standard statistical tests. The technical approach involves: (1) extracting summary statistics from public web pages, (2) reconstructing p-values using two-proportion z-tests, Fisher's exact tests, and Welch's t-tests, (3) flagging inconsistencies exceeding absolute 0.05 p-value difference or [deferred] effect size relative difference, (4) computing prevalence estimates with Wilson confidence intervals, and (5) validating the pipeline against synthetic (at least 10,000 samples) and real-world (at least 100 samples) validation sets.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas`, `scipy`, `statsmodels`, `pyyaml`, `pytest`  
**Storage**: CSV/JSON files (no database)  
**Testing**: `pytest` with contract tests, Monte Carlo validation  
**Target Platform**: Ubuntu-latest (GitHub Actions)  
**Project Type**: CLI/data-analysis pipeline  
**Performance Goals**: ≤6 hours runtime, ≤2 GB RAM, ≤2 vCPUs  
**Constraints**: CPU-only (no GPU), ≤14 GB disk, Python 3.11+ only  
**Scale/Scope**: ≥300 audited summaries, at least 10,000 synthetic validation samples, at least 100 real-world validation samples  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | ✅ COMPLIANT | Random seeds pinned; `requirements.txt` at `code/`; CI runs end-to-end |
| II. Verified Accuracy | ✅ COMPLIANT | All citations validated by Reference-Validator; title overlap ≥0.7 (explicitly enforced) |
| III. Data Hygiene | ✅ COMPLIANT | Checksums for all `data/` files; raw data preserved unchanged |
| IV. Single Source of Truth | ✅ COMPLIANT | All statistics trace to `data/` rows and `code/` blocks |
| V. Versioning Discipline | ✅ COMPLIANT | Content hashes in `state/projects/...yaml`; timestamp updates on changes |
| VI. Statistical Consistency Verification | ✅ COMPLIANT | All p-values cross-checked with absolute 0.05 threshold (FR-004) |
| VII. Source Provenance & Transparency | ✅ COMPLIANT | URL provenance recorded in `data/` and referenced in outputs |

## Project Structure

### Documentation (this feature)

```text
specs/[001-evaluating-the-statistical-validity-of-p/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── ABSummary.schema.yaml
│   ├── AuditRecord.schema.yaml
│   ├── abs-summary.schema.yaml
│   ├── audit-record.schema.yaml
│   ├── audit_record.schema.yaml
│   ├── extracted_summary.schema.yaml
│   ├── manifest.schema.yaml
│   ├── output-report.schema.yaml
│   ├── synthetic_dataset.schema.yaml
│   └── synthetic_validation.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/[PROJ-492-evaluating-the-statistical-validity-of-p]/
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── abs_summary.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── reconstructor.py
│   │   ├── validator.py
│   │   └── analyzer.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── run_audit.py
│   └── lib/
│       ├── __init__.py
│       └── monte_carlo.py
├── tests/
│   ├── contract/
│   │   ├── test_abs_summary.py
│   │   └── test_audit_record.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── unit/
│       ├── test_extractor.py
│       ├── test_reconstructor.py
│       └── test_analyzer.py
├── data/
│   ├── raw/
│   │   └── urls.csv
│   ├── processed/
│   │   ├── extracted_summaries.csv
│   │   ├── synthetic_validation.csv
│   │   └── real_world_validation_labels.csv
│   └── output/
│       ├── audit_report.json
│       ├── summary_report.csv
│       ├── bias_report.json
│       ├── subgroup_report.json
│       └── checksums.txt
├── requirements.txt
└── quickstart.md
```

**Structure Decision**: Single project structure under `projects/[PROJ-492]/` with `code/`, `tests/`, and `data/` subdirectories. This aligns with the constitution's reproducibility requirements and CI execution model.

## Phase Breakdown

### Phase 0: Research & Feasibility

**Goal**: Confirm dataset availability, validate statistical methods, and assess compute feasibility.

| Task | Description | FR/SC Coverage | Dependencies |
|------|-------------|----------------|--------------|
| P0-T01 | Research public A/B test summary sources (engineering blogs, GitHub archives, OpenML) | FR-001, FR-027 | None |
| P0-T02 | Verify statistical test implementations (z-test, Fisher's, Welch's) in SciPy/statsmodels | FR-003, FR-026 | None |
| P0-T03 | Assess compute feasibility: Measure CPU time, peak memory (MB), disk I/O, and runtime per Monte Carlo replicate; benchmark against limits (≤6h, ≤2GB RAM, ≤2 vCPUs); optimization via multiprocessing | FR-009, SC-008 | None |
| P0-T04 | Document dataset strategy: synthetic generation (FR-030) vs. real-world collection (FR-031b) | FR-030, FR-031b | P0-T01 |

**Deliverables**: `research.md` with dataset strategy, methodological justification, and compute feasibility assessment.

### Phase 1: Data Model & Contracts

**Goal**: Define data structures and validation schemas.

| Task | Description | FR/SC Coverage | Dependencies |
|------|-------------|----------------|--------------|
| P1-T01 | Implement `ABSummary` Pydantic model with inline schema validation | FR-002 | None |
| P1-T02 | Implement `AuditRecord` model for consistency check results | FR-004, FR-004b | P1-T01 |
| P1-T03 | Create contract schemas in `contracts/` directory (ABSummary, AuditRecord, extracted_summary, manifest, synthetic_dataset, synthetic_validation, output-report, abs-summary, audit-record, audit_record) | FR-002, FR-024, SC-024 | P1-T01, P1-T02 |
| P1-T04 | Define output schemas for `audit_report.json` and `summary_report.csv` | FR-024, SC-024 | P1-T02 |
| P1-T05 | Generate Quickstart guide with command-line examples | FR-028, SC-028 | P1-T03 |

**Deliverables**: `data-model.md`, `quickstart.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation (Tasks)

**Goal**: Implement all functional requirements with task dependencies resolved.

| Task | Description | FR/SC Coverage | Dependencies |
|------|-------------|----------------|--------------|
| T001 | Implement URL input handler (FR-001) | FR-001 | None |
| T002 | Implement web extraction service (FR-002) - extracts to `ExtractedSummary` entity | FR-002, SC-001 | T001 |
| T003 | Implement statistical test reconstruction (FR-003) | FR-003, SC-003 | T002 |
| T004 | Implement inconsistency detection (FR-004) | FR-004 | T003 |
| T005 | Implement sample size discrepancy detection (FR-004b) | FR-004b | T003 |
| T006 | Implement binomial prevalence test (FR-005a) | FR-005a, SC-014 | T004 |
| T007 | Implement sensitivity analysis (FR-005b) | FR-005b, SC-015 | T006 |
| T008 | Implement logging with error codes (FR-007) - logs to `ExtractedSummary` notes | FR-007, SC-005 | T002 |
| T009 | Implement CI compatibility checks (FR-009) | FR-009, SC-008 | None |
| T010 | Implement baseline handling heuristic (FR-012) | FR-012 | T003 |
| T011 | Implement result export (FR-024) | FR-024, SC-024 | T004, T006 |
| T012 | Implement power analysis (FR-025) | FR-025, SC-025 | None |
| T013 | Implement Monte Carlo validation (FR-026) | FR-026, SC-003, SC-026 | T003 |
| T014 | Implement bias assessment and adjustment (FR-027) | FR-027, SC-027 | T004 |
| T015 | Implement Quickstart documentation (FR-028) | FR-028, SC-028 | P1-T05 |
| T016 | **T026: Synthetic validation dataset generation** - Generate at least 10,000 synthetic A/B test summaries with BOTH binary AND continuous outcomes, ground-truth p-values computed via scipy.stats (independent library) | FR-030, FR-031, SC-030 | T003 |
| T017 | **T062: Monte Carlo validation module implementation** | FR-026, SC-026 | T013 |
| T018 | **T074: Run Monte Carlo validation as pipeline start-up** | FR-026 | [DEPENDS ON: T062] |
| T019 | **T076: Compute checksums for output files** | SC-013 | T011 |
| T020 | **T077: Extend manifest.json with checksums** | SC-013 | T019, T011 |
| T021 | **T081: Real-world validation set annotation** | FR-031b, SC-031b | P0-T04 |
| T022 | **T082: Real-world validation evaluation** - Evaluate detector on validation set stratified across FIVE MAJOR DOMAINS (tech, e-commerce, finance, healthcare, SaaS) | FR-031b, SC-031b | T021, T004 |
| T023 | Implement subgroup analysis with Bonferroni correction (FR-032) | FR-032, SC-032 | T004, T006 |
| T024 | **T040: Create manifest.json** - generates `Manifest` entity | SC-013 | T011, T019, T020 |
| T025 | **T042: Validate manifest.json** | SC-013 | [DEPENDS ON: T040] |
| T026 | **T046: Add resource-monitoring module** | FR-009, SC-008 | None |
| T027 | **T048: Update CI workflow to include resource-monitor check** | FR-009, SC-008 | [DEPENDS ON: T046] |
| T028 | **T096: Create manual validation dataset** | FR-031b, SC-001 | P0-T04 |
| T029 | **T096b: Compute checksums for data files** | SC-005 | [DEPENDS ON: T096] |

**Task Dependency Resolution**: All unresolved panel concerns addressed:
- T096b → T096: Checksums depend on file creation [DEPENDS ON: T096]
- T042 → T040: Manifest validation depends on manifest creation [DEPENDS ON: T040]
- T048 → T046: CI workflow check depends on monitoring module [DEPENDS ON: T046]
- T074 → T062: Pipeline Monte Carlo run depends on module implementation [DEPENDS ON: T062]

### Phase 3: Testing & Validation

**Goal**: Verify all success criteria are met.

| Task | Description | FR/SC Coverage | Dependencies |
|------|-------------|----------------|--------------|
| P3-T01 | Run contract tests on ABSummary and AuditRecord models; validate extraction accuracy ≥95% (SC-001) | SC-001, SC-024 | P1-T03 |
| P3-T02 | Execute Monte Carlo validation (multiple replicates) | SC-003, SC-026 | T017 |
| P3-T03 | Validate synthetic dataset precision/recall targets | SC-030 | T016, T022 |
| P3-T04 | Validate real-world dataset precision/recall targets - **requires inter-annotator agreement ≥85% before computing metrics** | SC-031b | T021, T022 |
| P3-T05 | CI resource usage verification | SC-008, SC-013 | T009, T026, T027 |
| P3-T06 | Quickstart user test (30 URLs in ≤30 minutes) | SC-028 | T015 |

### Phase 4: CI Integration

**Goal**: Automate pipeline execution on GitHub Actions.

| Task | Description | FR/SC Coverage | Dependencies |
|------|-------------|----------------|--------------|
| P4-T01 | Create GitHub Actions workflow file | FR-009, SC-008 | T009 |
| P4-T02 | Configure resource monitoring in CI | FR-009, SC-008 | T026, T027 |
| P4-T03 | Set up artifact upload (JSON/CSV outputs) | FR-024, SC-013 | T011 |
| P4-T04 | Configure nightly audit schedule | FR-009 | P4-T01 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Monte Carlo validation (10,000 replicates) | FR-026 requires independent statistical software validation per best-practice standards | Fewer replicates would not achieve stable estimates (SC-003 requires ≤0.005 difference) |
| Synthetic dataset (at least 10,000 samples) | FR-030 requires stable precision/recall estimates per Kohavi et al. | Smaller datasets would not detect implementation bugs reliably |
| Real-world validation (at least 100 summaries) | FR-031b requires independent human annotation for real-world performance validation | Synthetic validation alone cannot confirm actual detection performance |
| Bias adjustment (domain-weighted) | FR-027 prevents confounding from domain-dominance in prevalence estimate | Raw rates would be biased if single domain >30% of corpus |
| Bonferroni correction | FR-032 controls family-wise error rate for multiple subgroup tests | Uncorrected p-values would inflate Type I error |