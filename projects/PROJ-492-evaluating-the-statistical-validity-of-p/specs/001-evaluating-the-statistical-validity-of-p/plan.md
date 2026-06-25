# Implementation Plan: 001-eval-ab-test-validity

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary

Audit publicly available A/B test summaries for statistical consistency (p-values, effect sizes, sample sizes) and report the prevalence of inconsistencies. The technical approach involves: (1) web extraction of summary metrics, (2) reconstruction of statistical tests (two-proportion z-test for binary, Welch's t-test for continuous), (3) inconsistency detection with configurable thresholds, (4) domain-bias assessment and adjustment, (5) Monte Carlo validation of statistical implementations, and (6) synthetic dataset generation for precision/recall evaluation.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas`, `scipy`, `statsmodels`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (CSV, JSON, Parquet)  
**Testing**: pytest with contract tests against YAML schemas  
**Target Platform**: Linux (Ubuntu-latest GitHub Actions runner)  
**Project Type**: CLI tool / data pipeline  
**Performance Goals**: ≤6h runtime, ≤2GB RAM, ≤2 vCPUs  
**Constraints**: No GPU, no large LLM inference, CPU-tractable methods only  
**Scale/Scope**: ≥300 audited summaries (per FR-025 power analysis), [deferred] synthetic summaries (per FR-030), [deferred] Monte Carlo replicates (per FR-026)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Reproducibility | ✓ | Random seeds pinned in `code/`; external datasets from canonical sources |
| II. Verified Accuracy | ✓ | All citations validated against primary sources before review |
| III. Data Hygiene | ✓ | Checksums recorded; no in-place modifications; PII scan required |
| IV. Single Source of Truth | ✓ | All figures/statistics trace to exactly one row in `data/` and one block in `code/` |
| V. Versioning Discipline | ✓ | Content hashes for all artifacts; `updated_at` on stage transitions |
| VI. Statistical Consistency Verification | ✓ | P-values reconstructed via two-proportion z-test or Welch's t-test; discrepancies >0.05 flagged |
| VII. Source Provenance & Transparency | ✓ | URL and repository metadata recorded alongside extracted metrics |

**Gates passed**: All 7 principles verified. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-ab-test-validity/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── extracted_summary.schema.yaml
│   ├── audit_record.schema.yaml
│   ├── manifest.schema.yaml
│   └── synthetic_dataset.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-492-evaluating-the-statistical-validity-of-p/
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── ab_summary.py           # ABSummary entity (FR-002)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extractor.py            # URL → ABSummary (FR-001, FR-002)
│   │   ├── reconstructor.py        # Statistical test reconstruction (FR-003)
│   │   ├── auditor.py              # Inconsistency detection (FR-004, FR-004b)
│   │   ├── prevalence.py           # Binomial test, Wilson CI (FR-005a, FR-005b)
│   │   ├── bias.py                 # Domain-bias assessment (FR-027)
│   │   ├── subgroup.py             # Domain/year Fisher's exact test (FR-032)
│   │   ├── synthetic.py            # Synthetic dataset generation (FR-030)
│   │   └── validator.py            # Monte Carlo validation (FR-026)
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py                 # Entry point (FR-028)
│   └── lib/
│       ├── __init__.py
│       ├── schemas.py              # Schema loading/validation
│       └── utils.py                # Logging, checksums (FR-007, T076)
├── tests/
│   ├── contract/
│   │   ├── test_extracted_summary.py
│   │   ├── test_audit_record.py
│   │   └── test_manifest.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── unit/
│       ├── test_reconstructor.py
│       ├── test_auditor.py
│       └── test_validator.py
├── data/
│   ├── raw/                        # Downloaded/extracted summaries
│   ├── synthetic/                  # FR-030 synthetic dataset (10,000 records)
│   └── validation/                 # Manual annotations (SC-001)
├── output/
│   ├── audit_report.json           # FR-024
│   ├── summary_report.csv          # FR-024
│   ├── bias_report.json            # FR-027
│   ├── subgroup_report.json        # FR-032
│   ├── manifest.json               # SC-013
│   └── checksums.txt               # T076
├── input/
│   └── urls.csv                    # FR-001 input file
├── requirements.txt                # Reproducibility (Constitution I)
└── README_QUICKSTART.md            # FR-028
```

**Structure Decision**: Single project structure (Option 1) selected. All components are Python modules under `code/`, with tests under `tests/`. This matches the CLI/pipeline nature of the feature and keeps dependencies minimal (no separate backend/frontend).

## Complexity Tracking

No violations requiring justification. Constitution Check passed cleanly.