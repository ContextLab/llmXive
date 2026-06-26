# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary

This project implements an automated pipeline to audit publicly available A/B test summaries for **statistical consistency** (p-values, effect sizes, sample sizes). The system extracts reported metrics, reconstructs the statistical tests (two-proportion z-test, Welch's t-test), and flags inconsistencies based on an **absolute threshold of 0.05** for p-value discrepancy (Constitution VI). It generates JSON/CSV reports, performs power analysis (N≥300), validates implementations via Monte Carlo simulation, and adjusts for domain bias. The pipeline is designed to run within GitHub Actions free-tier constraints (CPU-only, ≤7GB RAM, ≤6h).

> **Construct Validity Limitation**: This project tests **internal consistency** of reported statistics, not ground-truth statistical validity. Without access to raw data, we cannot verify whether the reported p-values correctly reflect the actual statistical evidence. This limitation is acknowledged per methodology-c014d2d7.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scipy`, `pandas`, `requests`, `beautifulsoup4`, `pytest`, `pyyaml`  
**Storage**: Local filesystem (`data/` for inputs, `output/` for artifacts)  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Ubuntu-latest (GitHub Actions)  
**Project Type**: CLI/Data Pipeline  
**Performance Goals**: ≤6 hours runtime, ≤7GB RAM peak, ≤2 vCPUs  
**Constraints**: No GPU, no heavy LLM inference, **absolute p-value threshold 0.05** (Constitution VI)  
**Scale/Scope**: N ≥ 300 summaries (FR-025), 10,000 synthetic samples (FR-030)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All code in `code/` uses pinned `requirements.txt`. Random seeds set in `config.yaml`. CI runs on isolated GitHub Actions runner. |
| **II. Verified Accuracy** | Citations (e.g., Kohavi et al., John et al.) validated by Reference-Validator Agent before inclusion in reports. |
| **III. Data Hygiene** | All files in `data/` (including synthetic validation data) checksummed and recorded in `data/checksums.txt` (T076). Raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | Final statistics in paper/reports trace to `output/audit_report.json`. Checksums for run artifacts written to `output/checksums.txt` (T077). |
| **V. Versioning Discipline** | Content hashes tracked in `state/projects/PROJ-492-...yaml`. Artifact changes update `updated_at`. |
| **VI. Statistical Consistency** | Hard-coded threshold 0.05 for p-value discrepancy (FR-004). Reconstruction logic validated via Monte Carlo (FR-026). |
| **VII. Source Provenance** | URL metadata recorded in every `ABSummary` entity (FR-002). |

*Resolution of Unresolved Concerns:*
- **T005 (Constitution Compliance)**: T099 (Constitution Compliance Audit) verifies all Constitution Principles I-VII are implemented in code and data flows, not just CI.
- **T083 (Quickstart Runner)**: Updated to explicitly verify execution on "default GitHub Actions runner (2 vCPU, 7GB RAM)" per FR-028.
- **T076/T077 Checksum Separation**: T076 writes INPUT data checksums to `data/checksums.txt` (Constitution III). T077 writes OUTPUT artifact checksums to `output/checksums.txt` (Constitution IV). Both locations required per different principles. T096 removed to eliminate duplication.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
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
├── extraction/          # Web scraping and field extraction (FR-001, FR-002)
├── statistics/          # Reconstruction logic (FR-003, FR-004)
├── validation/          # Monte Carlo, Synthetic Data, Real-world Validation (FR-026, FR-030, FR-031b)
├── reporting/           # JSON/CSV export, Bias adjustment (FR-005a, FR-024, FR-027)
├── cli/                 # Entry point
└── config/              # Constants, Thresholds (Constitution VI)

tests/
├── contract/            # Schema validation
├── integration/         # Pipeline end-to-end
└── unit/                # Statistical function tests

data/
├── input/               # User-provided URLs (FR-001)
├── synthetic/           # Generated validation data (FR-030)
├── real_world/          # Manually annotated set (FR-031b)
└── checksums.txt        # Input data checksums (Constitution III, T076)

output/
├── audit_report.json    # Detailed results (FR-024)
├── summary_report.csv   # Aggregate results (FR-024)
├── bias_report.json     # Domain proportions (FR-027)
├── subgroup_report.json # Domain/Year analysis (FR-032)
└── checksums.txt        # Output artifact checksums (T077)
```

**Structure Decision**: Single project structure (`src/`, `tests/`, `data/`, `output/`) selected to minimize complexity and align with CLI tool requirements. Data and Output directories separated to satisfy Constitution Principles III (Data Hygiene) and IV (Single Source of Truth for artifacts).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Plan adheres to all constraints and principles. | N/A |

## Implementation Phases

### Phase 0: Research & Validation Setup
1.  **R01**: Verify statistical libraries (`scipy`) run within 7GB RAM on CPU.
2.  **R02**: Design synthetic data generator (FR-030) using independent logic from reconstruction (FR-026).
3.  **R03**: Define manual annotation protocol for real-world validation set (FR-031b, ≥100 samples).
4.  **R04**: Confirm power analysis calculation (FR-025) for N≥300.

### Phase 1: Data Model & Contracts
1.  **D01**: Define `ABSummary`, `AuditRecord` schemas (FR-002).
2.  **D02**: Create YAML contracts for `audit_report.json` and `summary_report.csv`.
3.  **D03**: Document Quickstart guide (FR-028) with explicit GitHub Actions runner verification (T083).

### Phase 2: Core Implementation
1.  **I01**: Implement URL ingestion and HTML extraction (FR-001, FR-002).
2.  **I02**: Implement statistical reconstruction (z-test, t-test, Fisher) (FR-003).
3.  **I03**: Implement inconsistency flagging logic (FR-004, Constitution VI). **Note**: Uses **absolute threshold 0.05 only** (no log-scale dual-criterion per methodology-5bca6076 resolution).
4.  **I04**: Implement bias adjustment and domain subsampling (FR-027). **Note**: Uses equal weighting per domain (scientific_soundness-64bd4091 resolution).
5.  **I05a**: Implement binomial test (FR-005a) and sensitivity analysis (FR-005b, SC-014, SC-015). **Note**: Explicitly quantifies effect size reconstruction uncertainty when baseline heuristic is used (FR-012, scientific_soundness-ad85a63f resolution).
6.  **I05b**: Implement report generation (JSON/CSV) (FR-024).

### Phase 3: Validation & Testing
1.  **V01**: Run Monte Carlo validation (a large number of replicates) to validate statistical reconstruction logic (two-proportion z-test, Welch's t-test) per Constitution VI (FR-026, SC-003). Acceptance criterion: absolute difference ≤ 0.005 between reconstructed and ground-truth p-values.
2.  **V02**: Generate synthetic dataset (10,000 rows) (FR-030, T026).
3.  **V03**: Evaluate extraction accuracy on real-world set (≥100 samples, FR-031b, SC-031b). **Note**: Human verification ensures ≥85% precision (methodology-42b0e48f resolution).
4.  **V04**: Execute Constitution Compliance Audit (T099) to verify all Principles I-VII in code and data flows.

### Phase 4: CI & Documentation
1.  **C01**: Configure GitHub Actions workflow (Ubuntu-latest).
2.  **C02**: Implement Input Data Checksumming Task (T076) writing to `data/checksums.txt`.
3.  **C03**: Implement Output Artifact Checksumming Task (T077) writing to `output/checksums.txt`.
4.  **C04**: Verify Quickstart execution time on **default GitHub Actions runner (2 vCPU, 7GB RAM, 14GB disk)** (T083).
5.  **C05**: Execute Constitution Compliance Audit (T099) to verify all Principles I-VII.
6.  **C06**: Final resource usage logging (SC-008).

## Compute Feasibility

- **Memory**: Data subset to ≤7GB. `pandas` operations on N=300 summaries are negligible. Synthetic data (10k rows) fits in RAM.
- **CPU**: Statistical tests (`scipy.stats`) are CPU-bound but lightweight. No GPU required.
- **Time**: Extraction (network bound) + Stats (CPU bound). 300 URLs estimated at <1 hour. Monte Carlo (10k reps) estimated at <2 hours. Total <6 hours.
- **Disk**: Output files <10MB. Synthetic data <50MB. Well within 14GB limit.

## FR/SC Coverage Map

| ID | Status | Plan Location |
|----|--------|---------------|
| FR-001 | Covered | Phase 2, I01 |
| FR-002 | Covered | Phase 2, I01; Data Model |
| FR-003 | Covered | Phase 2, I02 |
| FR-004 | Covered | Phase 2, I03; Constitution VI |
| FR-004b | Covered | Phase 2, I03 |
| FR-005a | Covered | Phase 2, I05a; Binomial Test |
| FR-005b | Covered | Phase 2, I05a; Sensitivity Analysis |
| FR-007 | Covered | Phase 2, I01; Logging |
| FR-009 | Covered | Phase 4, C01; Compute Feasibility |
| FR-012 | Covered | Phase 2, I05a; Baseline Handling (uncertainty impact documented) |
| FR-024 | Covered | Phase 2, I05b; Contracts |
| FR-025 | Covered | Phase 0, R04 |
| FR-026 | Covered | Phase 3, V01 |
| FR-027 | Covered | Phase 2, I04; Equal Domain Weighting |
| FR-028 | Covered | Phase 1, D03; Quickstart (T083 verification) |
| FR-030 | Covered | Phase 3, V02 |
| FR-031 | Covered | Phase 3, V02/V03 |
| FR-031b | Covered | Phase 3, V03 (≥100 real-world samples) |
| FR-032 | Covered | Phase 2, I05b; Subgroup |
| SC-001 | Covered | Phase 3, V03 |
| SC-003 | Covered | Phase 3, V01 |
| SC-005 | Covered | Phase 2, I01 |
| SC-008 | Covered | Phase 4, C06 |
| SC-013 | Covered | Phase 4, C02/C03 |
| SC-014 | Covered | Phase 2, I05a; Wilson CI |
| SC-015 | Covered | Phase 2, I05a; Sensitivity Analysis |
| SC-024 | Covered | Phase 2, I05b; Contracts |
| SC-025 | Covered | Phase 0, R04 |
| SC-026 | Covered | Phase 3, V01 |
| SC-027 | Covered | Phase 2, I04 |
| SC-028 | Covered | Phase 1, D03; T083 |
| SC-030 | Covered | Phase 3, V02 |
| SC-031b | Covered | Phase 3, V03 |
| SC-032 | Covered | Phase 2, I05b |

## Task Registry

| Task ID | Description | Phase | Status |
|---------|-------------|-------|--------|
| T026 | Synthetic Validation Dataset Generation ([deferred] rows) | Phase 3, V02 | Planned |
| T044 | Power Analysis Calculation (N≥300) | Phase 0, R04 | Planned |
| T062 | Monte Carlo Validation (10,000 replicates) | Phase 3, V01 | Planned |
| T076 | Input Data Checksumming (data/checksums.txt) | Phase 4, C02 | Planned |
| T077 | Output Artifact Checksumming (output/checksums.txt) | Phase 4, C03 | Planned |
| T081 | Constitution Compliance Audit (Principles I-VII) | Phase 4, C05 | Planned |
| T082 | Real-World Validation Set Annotation (≥100 samples) | Phase 3, V03 | Planned |
| T083 | Quickstart Runner Verification (default GitHub Actions runner standard vCPU, 7GB RAM) | Phase 4, C04 | Planned |
| T099 | Constitution Compliance Audit (code/data verification of Principles I-VII) | Phase 4, C05 | Planned |

**Note**: T076 handles input data checksums (Constitution III), T077 handles output artifact checksums (Constitution IV). Both locations required per different principles. T096 removed to eliminate duplication. T083 and T099 now explicitly verify default GitHub Actions runner and code-level Constitution compliance respectively.