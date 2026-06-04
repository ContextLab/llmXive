# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: specs/001-knot-complexity-analysis/spec.md
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary

This project quantifies knot diagram complexity by analyzing the joint predictive relationship between crossing number and braid index for hyperbolic volume, stratified by alternating/non-alternating classification. Phase 1 focuses on alternating/non-alternating dichotomy with validated completeness for crossing number ≤10 (data collection extends to ≤13). The approach involves downloading knot data from Knot Atlas, computing additional invariants (arc index, Seifert circle count, bridge number), performing exploratory analysis, fitting multiple regression models, and constructing a composite complexity score—all with rigorous reproducibility documentation per project constitution.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml, pyarrow (for parquet I/O)
**Knot Theory Libraries**: pyknotid (for invariant computation fallback), sagemath (optional, for advanced computations)
**Storage**: File-based (data/ directory with parquet/CSV files)
**Testing**: pytest with contract tests against schema definitions
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: computational research library
**Performance Goals**: Complete data download and analysis for ≤10 crossing knots within 30 minutes; ≤13 within 2 hours
**Scale/Scope**: ~49 (Wikipedia: 49 (number), https://en.wikipedia.org/wiki/49_(number)) prime knots total; 2,977 at crossing number ≤10 [UNRESOLVED-CLAIM: c_d8fdbf0e — status=not_enough_info]; 92 at crossing number 13 per OEIS A002863

**Constraints & Validation Procedures**:
- API rate limiting on Knot Atlas: Implement exponential backoff with documented retry logs (FR-010)
- Memory limits for 9,988 knots at crossing number 13: Stream processing with chunked loading; validation: monitor peak memory usage <4GB
- Some c=13 knots may lack DT codes or braid word representations: Flag with missing_invariant_flags; validation: report completeness percentage in docs/reproducibility/uncomputable_invariants.md (target ≥99% of knots with available representations)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Implementation Status |
|-----------|-------------|----------------------|
| **I. Reproducibility** | Random seeds pinned; external datasets from canonical source; end-to-end runnable | Seeds pinned in code (FR-009); Knot Atlas as canonical source (FR-001); isolated virtualenv per requirements.txt |
| **II. Verified Accuracy** | External citations verified against primary source; title-token-overlap ≥0.7 | Reference-Validator Agent runs at artifact write and advancement gates; citations from verified datasets block only; **Knot Atlas UNVERIFIED — BLOCKING VIOLATION** (requires spec-level resolution: either verified dataset source OR constitution amendment with risk acceptance) |
| **III. Data Hygiene** | Checksums under data/; no in-place modification; no PII | SHA-256 checksums recorded (FR-009); new files for transformations (FR-002); PII scan enforced |
| **IV. Single Source of Truth** | All figures/statistics trace to one data row and one code block | Derivation notes document transformations (FR-009); checksums enable traceability |
| **V. Versioning Discipline** | Content hash for every artifact; state file updated on change | Artifact hashes in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` `artifact_hashes` map; validation scripts detect stale artifacts; hash mapping documented in data-model.md File Storage Convention |
| **VI. Mathematical Invariant Consistency** | Computed invariants verified against primary literature | Algorithm validation against KnotInfo (SC-012); ≥95% match threshold; derivation notes with citations |
| **VII. Statistical Significance Thresholds** | All claims include p-values, confidence intervals, effect sizes | Both Pearson AND Spearman reported (FR-008); effect sizes documented (Cohen's d, r²); Bonferroni correction for multiple model comparison |

**Success Criterion Coverage**:

| Success Criterion | Implementation Tracking |
|-------------------|------------------------|
| SC-001: Dataset completeness ≥95% for c≤10 | Dataset Strategy section; validation report at docs/reproducibility/validation_status.md |
| SC-002: 3 regression models compared | Statistical Analysis Plan section |
| SC-003: Composite score correlation reported | Composite Complexity Score section |
| SC-004: Reproducibility documentation | Reproducibility Requirements section |
| SC-005: Retry logic verified | Edge Case Handling section |
| SC-006: ≥99% computable invariants populated | missing_invariant_flags field in KnotRecord; validation report documents percentage; target ≥99% for knots with available representations |
| SC-007: Ambiguous classification handling | Edge Case Handling section |
| SC-008: Tie-breaking validation | Edge Case Handling section |
| SC-009: Exploratory plots generated | Statistical Analysis Plan section |
| SC-010: 3+ additional invariants computed | Invariant Computation Methodology section |
| SC-011: ANOVA with effect sizes | Statistical Analysis Plan section |
| SC-012: Algorithm validation ≥95% | Invariant Computation Methodology section |
| SC-013: Scope validation documentation | Dataset Strategy section |
| SC-014: HYPERBOLIC_VOLUME_COMPLETENESS: ≥95% for c≤13 | hyperbolic_volume field nullable; excluded_knots.md documents filtered records; target ≥95% completeness for prime knots with c≤13 |

**GATE STATUS**: BLOCKED — Constitution Principle II (Verified Accuracy) violation requires spec-level resolution before advancement. All other principles and success criteria addressed.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md # This file (/speckit-plan command output)
├── research.md # Phase 0 output (/speckit-plan command)
├── data-model.md # Phase 1 output (/speckit-plan command)
├── quickstart.md # Phase 1 output (/speckit-plan command)
├── contracts/ # Phase 1 output (/speckit-plan command)
│ ├── knot_record.schema.yaml # Canonical (active)
│ ├── invariants_dataset.schema.yaml # Canonical (active)
│ ├── regression_model.schema.yaml # Canonical (active)
│ ├── regression_output.schema.yaml # Canonical (active)
│ ├── composite_score.schema.yaml # Canonical (active)
│ ├── knot_data.schema.yaml # LEGACY (deprecated, retained for backward compatibility)
│ └── regression_result.schema.yaml # LEGACY (deprecated, retained for backward compatibility)
└── tasks.md # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── models/
│ ├── __init__.py
│ ├── knot_record.py
│ └── regression_model.py
├── services/
│ ├── __init__.py
│ ├── data_download.py
│ ├── invariant_computation.py
│ ├── exploratory_analysis.py
│ └── regression_analysis.py
├── cli/
│ ├── __init__.py
│ └── main.py
├── lib/
│ ├── __init__.py
│ └── reproducibility.py
├── config/
│ └── complexity_weights.yaml
└── requirements.txt

tests/
├── contract/
│ └── test_schemas.py
├── integration/
│ └── test_data_pipeline.py
└── unit/
 ├── test_invariant_computation.py
 └── test_reproducibility.py

docs/
└── reproducibility/
 ├── invariant_algorithms.md
 ├── algorithm_validation.md
 ├── tie_breaking_rules.md
 ├── excluded_knots.md
 ├── uncomputable_invariants.md
 ├── validation_scope.md
 └── validation_status.md

data/
├── raw/
│ └── knot_atlas_download.parquet
├── processed/
│ ├── knots_with_invariants.parquet
│ └── exploratory_validation_sample.parquet
└── plots/
 ├── crossing_vs_braid_alternating.png
 └── crossing_vs_braid_non_alternating.png
```

**Structure Decision**: Single project structure selected. Computational research projects benefit from unified codebase where data download, invariant computation, and analysis pipelines share common models and utilities. Separation of services enables independent testing per User Story priorities (P1→P4). Documentation under docs/reproducibility/ ensures all transformation artifacts are discoverable alongside analysis code.

**Legacy Schema Note**: Two legacy schema files (knot_data.schema.yaml, regression_result.schema.yaml) are retained for backward compatibility with existing data files. New implementations MUST use canonical schemas (knot_record.schema.yaml, regression_output.schema.yaml, composite_score.schema.yaml). Legacy schemas are marked deprecated in their description fields and will be removed in a future version once all data migration is complete.

## Complexity Tracking

> **No violations requiring justification** — All complexity decisions align with constitutional requirements and spec constraints.

## Artifact Hash Documentation (Constitution Principle V)

All artifacts carry content hashes recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml`:

| Artifact Type | Hash Location | Update Trigger |
|---------------|---------------|----------------|
| Data files (raw/processed) | `artifact_hashes.data` | On file write |
| Schema files (contracts/) | `artifact_hashes.schemas` | On schema change |
| Code files (code/) | `artifact_hashes.code` | On code commit |
| Documentation (docs/) | `artifact_hashes.docs` | On doc write |
| State file itself | `artifact_hashes.state` | On state update |

Hash computation: SHA-256 of file contents. State file updates trigger Advancement-Evaluator revalidation.