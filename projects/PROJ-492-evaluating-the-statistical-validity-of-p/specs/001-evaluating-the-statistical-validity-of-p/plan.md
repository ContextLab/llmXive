# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: `specs/001-eval-ab-test-validity/spec.md`
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary

This project audits publicly available A/B test summaries for statistical consistency by reconstructing p‑values and effect sizes from reported sample sizes, comparing them against reported values, and reporting the prevalence of inconsistencies across a corpus. The technical approach uses Python 3.11+ with `scipy` for statistical tests, `pandas` for data manipulation, and `beautifulsoup4` for web extraction, all runnable on CPU-only GitHub Actions free-tier resources (≤2 vCPUs, ≤2GB RAM, ≤6h runtime).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `scipy>=1.11`, `pandas>=2.0`, `beautifulsoup4>=4.12`, `requests>=2.31`, `pyyaml>=6.0`, `pytest>=7.4`  
**Storage**: CSV input (`input/urls.csv`), JSON/CSV output (`output/audit_report.json`, `output/summary_report.csv`)  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Ubuntu-latest (GitHub Actions runner)  
**Project Type**: CLI/data-analysis pipeline  
**Performance Goals**: ≤6h total runtime, ≤2GB RAM peak, ≤2 vCPU usage  
**Constraints**: No GPU, no deep learning, sample corpus ≤300 URLs for CI, no data modification in place  
**Scale/Scope**: 300+ audited summaries for production, 30 URLs for Quickstart demo

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Notes |
|-----------|--------|------------------|
| **I. Reproducibility (NON-NEGOTIABLE)** | ✅ PASS | All code under `code/` with pinned `requirements.txt`; random seeds pinned in statistical simulation scripts; external datasets fetched from canonical sources on every run. |
| **II. Verified Accuracy** | ✅ PASS | All citations (e.g., John et al., 2022; Kohavi et al., 2020) validated by Reference-Validator Agent; Title-token-overlap ≥0.7 threshold enforced. |
| **III. Data Hygiene** | ✅ PASS | All files under `data/` checksummed in project state YAML; raw data preserved unchanged; derivations written to new filenames; PII scan enforced via Repository-Hygiene Agent. |
| **IV. Single Source of Truth** | ✅ PASS | Every statistic in output traces to exactly one row in `data/` and one block in `code/`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ PASS | Every artifact carries content hash; Advancement-Evaluator Agent invalidates stale review records on hash change; `updated_at` timestamp updated on artifact write. |
| **VI. Statistical Consistency Verification (NON-NEGOTIABLE)** | ✅ PASS | All reported p‑values, effect sizes, sample sizes cross-checked against reconstructed values using two‑proportion z‑test or Welch's t‑test; discrepancies >0.05 flagged, documented, justified before acceptance. |
| **VII. Source Provenance & Transparency (NON-NEGOTIABLE)** | ✅ PASS | Every A/B test summary retains original provenance (URL, repository identifier) in `data/`; metadata recorded alongside extracted metrics; referenced in all derived tables. |

## FR/SC Coverage Map

| ID | Requirement | Plan Phase | Implementation Task |
|----|-------------|------------|---------------------|
| FR-001 | Accept URL list input | Phase 2: Data Acquisition | T001: Parse `input/urls.csv` |
| FR-002 | Extract sample size, effect size, p-value/CI | Phase 2: Data Extraction | T002: HTML extraction module |
| FR-003 | Reconstruct p-value (z-test, Welch's t-test, Fisher's) | Phase 3: Statistical Reconstruction | T003: Statistical test implementation |
| FR-004 | Flag inconsistent (abs p-diff >0.05, rel effect-diff >5%, inequality bounds) | Phase 3: Inconsistency Detection | T004: Consistency flagging logic |
| FR-004b | Flag inconsistent sample size mismatch (>5% of larger count) | Phase 3: Inconsistency Detection | T005: Sample size validation |
| FR-005a | Two-sided binomial test (baseline 0.05, Wilson CI) | Phase 4: Prevalence Estimation | T006: Binomial test with Wilson CI |
| FR-005b | Sensitivity analysis (baseline 0.02–0.10, step 0.01) | Phase 4: Prevalence Estimation | T007: Sensitivity analysis loop |
| FR-007 | Log parsing failures with error code, field, description | Phase 2: Data Extraction | T008: Error logging module |
| FR-009 | CI compatibility (Ubuntu-latest, Python 3.11+, ≤2GB RAM, ≤2 vCPU, ≤6h) | Phase 5: CI Integration | T009: Resource monitoring |
| FR-012 | Baseline handling (average of variant rates if missing) | Phase 3: Statistical Reconstruction | T010: Baseline reconstruction |
| FR-024 | Export JSON + CSV reports | Phase 5: Output Generation | T011: Report generators |
| FR-025 | Power analysis (N≥300 for power≥0.80 at α=0.05, detecting 0.10 proportion) | Phase 1: Research | T012: Power analysis documentation |
| FR-026 | Monte Carlo validation (10k replicates, diff ≤0.01) | Phase 3: Statistical Validation | T013: Monte Carlo test suite |
| FR-027 | Domain dominance check (>30% flag, bias-adjusted rate) | Phase 4: Bias Assessment | T014: Domain weighting logic |
| FR-028 | Quickstart guide (30 URLs in 30 minutes) | Phase 1: Documentation | T015: Quickstart.md creation |
| FR-030 | Synthetic validation dataset (10k+ simulated summaries) | Phase 3: Validation Data | T016: Synthetic data generator |
| FR-031 | Precision≥90%, Recall≥80% (F1≥0.85) on synthetic data | Phase 3: Validation Data | T017: Performance metrics calculation |
| FR-032 | Subgroup analysis (domain/year, Fisher's exact test for n≥10) | Phase 4: Subgroup Analysis | T018: Fisher's exact test implementation |
| SC-001 | Extraction accuracy≥95% on 100+ manual validation set | Phase 3: Validation | T019: Manual validation set creation |
| SC-003 | SciPy vs Monte Carlo diff ≤0.01 | Phase 3: Statistical Validation | T013 (covered) |
| SC-005 | Parsing errors ≤5% of total | Phase 2: Data Extraction | T008 (covered) |
| SC-008 | CI execution ≤6h, ≤2GB RAM | Phase 5: CI Integration | T009 (covered) |
| SC-013 | Exit 0 + manifest.json in ≥99% runs | Phase 5: CI Integration | T020: Manifest generation |
| SC-014 | Binomial test p-value 3 decimals, Wilson CI width ≤0.10 | Phase 4: Prevalence Estimation | T006 (covered) |
| SC-015 | Sensitivity analysis variation <0.02 across baseline 0.02–0.10 | Phase 4: Prevalence Estimation | T007 (covered) |
| SC-024 | CSV/JSON counts match | Phase 5: Output Generation | T011 (covered) |
| SC-025 | Corpus N≥300 (or calculated minimum) | Phase 1: Research | T012 (covered) |
| SC-026 | Monte Carlo validation passes | Phase 3: Statistical Validation | T013 (covered) |
| SC-027 | No domain >30%, raw + bias-adjusted rates in report | Phase 4: Bias Assessment | T014 (covered) |
| SC-028 | Quickstart verified (30 URLs in ≤30 minutes) | Phase 1: Documentation | T015 (covered) |
| SC-030 | Precision≥90%, Recall≥80% on synthetic data | Phase 3: Validation Data | T017 (covered) |
| SC-032 | Subgroup prevalence + Fisher p-value for n≥10 | Phase 4: Subgroup Analysis | T018 (covered) |

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
│   └── manifest.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── extraction/
│   ├── __init__.py
│   ├── html_parser.py
│   └── error_logger.py
├── statistics/
│   ├── __init__.py
│   ├── z_test.py
│   ├── welch_t_test.py
│   ├── fisher_exact.py
│   ├── binomial_test.py
│   └── monte_carlo_validator.py
├── analysis/
│   ├── __init__.py
│   ├── inconsistency_detector.py
│   ├── prevalence_estimator.py
│   ├── bias_assessor.py
│   └── subgroup_analyzer.py
├── validation/
│   ├── __init__.py
│   ├── synthetic_data_generator.py
│   └── performance_metrics.py
├── output/
│   ├── __init__.py
│   ├── json_reporter.py
│   ├── csv_reporter.py
│   └── manifest_generator.py
├── cli/
│   ├── __init__.py
│   └── main.py
└── tests/
    ├── contract/
    │   ├── test_extracted_schema.py
    │   ├── test_audit_schema.py
    │   └── test_manifest_schema.py
    ├── unit/
    │   ├── test_z_test.py
    │   ├── test_welch_t_test.py
    │   └── test_binomial_test.py
    └── integration/
        └── test_pipeline.py

input/
└── urls.csv

output/
├── audit_report.json
├── summary_report.csv
├── bias_report.json
├── subgroup_report.json
├── manifest.json
└── checksums.txt
```

**Structure Decision**: Single-project Python CLI structure (DEFAULT) with modular separation of concerns (extraction, statistics, analysis, validation, output). This minimizes complexity while supporting testability and reproducibility requirements.

## Task Ordering & Dependencies

Tasks are ordered to ensure data is downloaded before consumption, models are fitted before evaluation, and outputs are generated after all analysis. The following dependency constraints from unresolved panel concerns are addressed:

| Task | Dependencies | Parallel Marker | Rationale |
|------|--------------|-----------------|-----------|
| T001: Parse input URLs | None | - | Entry point |
| T002: HTML extraction | T001 | - | Depends on input parsed |
| T008: Error logging | T002 | - | Logs extraction failures |
| T003: Statistical tests | T002 | - | Needs extracted data |
| T004: Inconsistency flagging | T003, T005 | - | Needs test results + sample validation |
| T005: Sample size validation | T002 | - | Depends on extracted sample sizes |
| T010: Baseline reconstruction | T002 | - | Depends on extracted variant rates |
| T013: Monte Carlo validation | T003 | - | Validates statistical test implementations |
| T016: Synthetic data generation | None | - | Independent test data creation |
| T017: Performance metrics | T016, T004 | - | Evaluates detector on synthetic data |
| T019: Manual validation set | None | - | Independent gold-standard creation |
| T006: Binomial test | T004 | - | Needs inconsistency flags |
| T007: Sensitivity analysis | T006 | - | Repeats binomial test with varied baselines |
| T014: Bias assessment | T004 | - | Needs inconsistency flags + domain metadata |
| T018: Subgroup analysis | T004 | - | Needs inconsistency flags + domain/year metadata |
| T011: Report generators | T006, T007, T014, T018 | - | Aggregates all analysis results |
| T020: Manifest generation | T011 | - | **Depends on report output** (T042→T040 concern) |
| T009: Resource monitoring | T001–T011 | - | Monitors entire pipeline execution |
| T076: Checksum generation | T011 | - | **Checksums output files** (T077 depends on this) |
| T077: Manifest checksum extension | T076 | - | **Cannot run parallel with T076** (panel concern resolved) |

Contract tests (contract/*.py) run AFTER implementation (T003, T004, T011) but are parallel within their own group. The [P] marker on contract tests has been removed to reflect their post-implementation dependency.

## Compute Feasibility

- **Memory**: All data structures (pandas DataFrames for ≤300 rows) fit well within 2GB RAM limit.
- **CPU**: Statistical tests (z-test, Welch's t-test, binomial test, Fisher's exact) are O(n) and execute in seconds for ≤300 summaries.
- **Disk**: Output files (JSON, CSV) total <10MB for ≤300 summaries.
- **Runtime**: Full pipeline on 300 URLs estimated at 2–4 hours on GitHub Actions free-tier (including HTML fetch delays, Monte Carlo validation with 10k replicates).
- **No GPU**: All `scipy` functions are CPU-native; no `torch`, `tensorflow`, or CUDA dependencies.
- **Sampling**: For CI runs, sample corpus limited to 30 URLs (Quickstart) or 100 URLs (validation); production corpus up to 300+ URLs with rate-limiting and caching.
