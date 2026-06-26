# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-24 | **Spec**: `/specs/001-eval-ab-test-validity/spec.md`
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary

This project audits publicly available A/B test summaries for statistical consistency between reported metrics (p-values, effect sizes, sample sizes) and reconstructed values. The pipeline extracts metrics from HTML summaries, reconstructs p-values using appropriate statistical tests (two-proportion z-test for binary outcomes, Welch's t-test for continuous), flags inconsistencies exceeding an absolute 0.05 p-value threshold (Constitution Principle VI), and reports prevalence with bias-adjustment for domain dominance. All computation runs on CPU-only GitHub Actions free-tier resources (2 vCPUs, ≤2GB RAM, ≤6h).

**Methodological Limitations** (CRITICAL): Internal consistency ≠ external accuracy. This audit validates whether reported numbers are mathematically consistent with each other, NOT whether they accurately reflect the actual experiment. A summary can be internally consistent but externally inaccurate (e.g., fabricated data that happens to satisfy statistical relationships). This constraint MUST be prominently acknowledged when interpreting prevalence estimates.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: scipy, pandas, requests, beautifulsoup4, pytest, statsmodels (for independent validation per FR-030)  
**Storage**: Local files (CSV, JSON, YAML) under `data/`, `output/`  
**Testing**: pytest with contract tests against inline schema definitions  
**Target Platform**: Ubuntu-latest GitHub Actions runner  
**Project Type**: CLI data analysis pipeline  
**Performance Goals**: ≤6 hours total runtime, ≤2GB RAM peak, ≤2 vCPUs  
**Constraints**: No GPU usage, no deep learning, no external API rate-limit violations  
**Scale/Scope**: N≥300 audited summaries (per FR-025), 10,000 synthetic validation samples (per FR-030), Multiple real-world validation samples (per FR-031b)

> Dataset sizes and corpus counts are mandated by the specification (FR-025, FR-030, FR-031b), not empirically measured.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Action | Status |
|-----------|-------------------|--------|
| I. Reproducibility | Pin random seeds in `code/`; `requirements.txt` at `projects/PROJ-492/code/`; run in isolated venv | ✅ |
| II. Verified Accuracy | Reference-Validator Agent verifies citations before review points; title-token-overlap ≥0.7 | ✅ |
| III. Data Hygiene | All `data/` files checksummed; no in-place modification; PII scan passes | ✅ |
| IV. Single Source of Truth | All statistics trace to one row in `data/` and one code block; no hand-typed numbers | ✅ |
| V. Versioning Discipline | Content hashes for all artifacts; `state/*.yaml` updated on artifact changes | ✅ |
| VI. Statistical Consistency Verification | Absolute 0.05 p-value threshold enforced (per Constitution Section VI); discrepancies flagged and documented | ✅ |
| VII. Source Provenance & Transparency | URL and provenance metadata recorded for every summary in `data/` | ✅ |

**Gates determined**: All seven principles are satisfied by design. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-ab-test-validity/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── abs_summary.schema.yaml
│   ├── audit_record.schema.yaml
│   └── summary_report.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-492-evaluating-the-statistical-validity-of-p/
├── code/
│   ├── __init__.py
│   ├── extraction.py           # HTML parsing, field extraction (FR-002)
│   ├── reconstruction.py       # Statistical test reconstruction (FR-003)
│   ├── inconsistency.py        # Inconsistency detection logic (FR-004, FR-004b)
│   ├── prevalence.py           # Binomial test, Wilson CI (FR-005a, FR-005b)
│   ├── bias.py                 # Domain bias assessment & adjustment (FR-027)
│   ├── validation.py           # Monte Carlo validation (FR-026)
│   ├── synthetic.py            # Synthetic dataset generation (FR-030)
│   ├── subgroup.py             # Subgroup analysis with Bonferroni (FR-032)
│   ├── cli.py                  # Command-line interface (FR-001)
│   └── main.py                 # Pipeline orchestration
├── data/
│   ├── raw/                    # Raw downloaded HTML (checksummed)
│   ├── processed/              # Extracted ABSummary records
│   ├── synthetic_validation.csv
│   ├── synthetic_ground_truth.json
│   └── real_world_validation_labels.csv
├── output/
│   ├── audit_report.json       # Per-summary audit results (FR-024)
│   ├── summary_report.csv      # Aggregate CSV (FR-024)
│   ├── bias_report.json        # Domain proportions & adjusted rate
│   ├── subgroup_report.json    # Per-domain/year prevalence
│   ├── monte_carlo_validation_report.json
│   ├── real_world_validation_report.json
│   ├── synthetic_validation_report.json
│   ├── checksums.txt           # File checksums (T076)
│   └── manifest.json           # Run manifest with checksums (T077)
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # Pipeline integration tests
│   └── unit/                   # Unit tests for statistical functions
└── requirements.txt            # Pinned dependencies (Constitution Principle I)
```

**Structure Decision**: Single project under `projects/PROJ-492/` with modular `code/` directory. This structure satisfies Constitution Principle III (Data Hygiene) by separating raw/processed data, enables reproducibility (Principle I) via pinned `requirements.txt`, and supports single source of truth (Principle IV) by keeping all artifacts under version control with content hashes.

## Phase Breakdown

### Phase 0: Research & Environment Setup (Week 1)

**Objective**: Verify statistical methodology, confirm dataset availability, establish CI environment.

| Task ID | Description | FR/SC Coverage | Deliverable |
|---------|-------------|----------------|-------------|
| T000 | Implement CLI interface to accept URLs from `input/urls.csv` | FR-001 | `code/cli.py` |
| T001 | Set up GitHub Actions workflow with Python 3.11, pin dependencies | FR-009, SC-008 | `.github/workflows/audit.yml` |
| T002 | Implement Monte Carlo validation framework (sufficient replicates) | FR-026, SC-003, SC-026 | `tests/unit/test_monte_carlo.py` |
| T003 | Verify statistical test implementations (z-test, Fisher's, Welch's) | FR-003, FR-026 | `code/validation.py` |
| T004 | Document power analysis for N≥300 corpus size | FR-025, SC-025 | `research.md` section |
| T005 | Confirm Constitution Principles I-VII compliance in CI | All Principles | CI check script |

**Statistical Rigor Notes**:
- Multiple-comparison correction: Bonferroni applied to subgroup tests (FR-032) AND sensitivity analysis (FR-005b); baseline binomial test (FR-005a) is single test requiring no correction.
- Power justification: N≥300 calculated for power≥0.80 at α=0.05 to detect inconsistency proportion≥0.10 (double baseline 0.05 from FR-005a).
- Causal framing: Audit is observational; claims are associational (internal consistency only, not external accuracy per Methodological Limitations).
- Measurement validity: Statistical test implementations validated via Monte Carlo (FR-026); extraction accuracy validated via human annotation (FR-031b).
- Collinearity: No predictor collinearity issues (no regression model; direct reconstruction from reported numbers).
- Sensitivity analysis: Testing a range of baseline proportions (0.02–0.10, with incremental steps) requires Bonferroni correction (adjusted α = 0.05/9 ≈ 0.0056) to control family-wise error rate.

### Phase 1: Data Extraction & Validation (Week 2)

**Objective**: Build extraction pipeline, create synthetic validation dataset, annotate real-world validation set.

| Task ID | Description | FR/SC Coverage | Deliverable |
|---------|-------------|----------------|-------------|
| T006 | Implement HTML extraction for sample sizes, effect sizes, p-values | FR-002, FR-007 | `code/extraction.py` |
| T007 | Generate synthetic validation dataset (10,000 samples) | FR-030, T026 | `data/synthetic_validation.csv` |
| T008 | Compute ground-truth p-values using independent implementation | FR-030 | `data/synthetic_ground_truth.json` |
| T009 | Create manually annotated real-world validation set (multiple summaries) | FR-031b, T081 | `data/real_world_validation_labels.csv` |
| T010 | Implement extraction accuracy evaluation (precision/recall/F1) | FR-031b, SC-001, SC-031b | `tests/integration/test_extraction_accuracy.py` |
| T011 | Validate extraction precision≥85%, recall≥75% (F1≥0.80) | FR-031b, SC-031b | `output/real_world_validation_report.json` |
| T011b | Validate extraction accuracy ≥95% on 100 summaries across 5 domains | SC-001 | `output/sc001_validation_report.json` |

**Dataset-Variable Fit**:
- Synthetic dataset: Programmatically generated with known ground truth (FR-030); no external dataset required.
- Real-world validation: Requires manual annotation of 100 public A/B test summaries from multiple domains (tech, e-commerce, finance, healthcare, SaaS per the relevant requirement specification). **NO external dataset URL available** (verified datasets list shows "NO verified source found" for FR-031b, FR-031, SC-030, T026). Summaries must be manually sourced from public engineering blogs, GitHub archives, or OpenML experiment reports.
- Corpus collection: URLs provided via `input/urls.csv` (FR-001); no pre-existing dataset URL required.

### Phase 2: Statistical Reconstruction & Inconsistency Detection (Week 3)

**Objective**: Implement reconstruction logic, flag inconsistencies, handle edge cases.

| Task ID | Description | FR/SC Coverage | Deliverable |
|---------|-------------|----------------|-------------|
| T012 | Implement two-proportion z-test for binary outcomes | FR-003 | `code/reconstruction.py` |
| T013 | Implement Fisher's exact test when cell count≤5 | FR-003 | `code/reconstruction.py` |
| T014 | Implement Welch's t-test for continuous outcomes | FR-003 | `code/reconstruction.py` |
| T015 | Implement inconsistency flagging (|Δp|>0.05 absolute threshold) | FR-004, Constitution Principle VI | `code/inconsistency.py` |
| T016 | Handle inequality p-values (e.g., "p<0.001") | FR-004 | `code/inconsistency.py` |
| T017 | Handle missing baseline conversion rate (average of variants) | FR-012 | `code/reconstruction.py` |
| T018 | Flag sample size mismatches (>5% difference) | FR-004b | `code/inconsistency.py` |
| T019 | Log parsing failures with ERR-### codes, field names, ≤200 char descriptions | FR-007, SC-005 | `code/extraction.py` |

**Statistical Rigor Notes**:
- Absolute p-value threshold of 0.05 is mandated by Constitution Principle VI (not statistical optimization).
- Relative threshold of 5% for effect size difference is per spec (FR-004); not constrained by Constitution.
- For inequality p-values, reconstructed p-value must exceed bound to flag inconsistent (FR-004).
- Missing baseline handling (FR-012) is heuristic; flagged in audit notes with reduced statistical rigor caveat.
- **Construct validity limitation**: The absolute 0.05 threshold creates non-uniform inconsistency detection across the p-value distribution (50x difference for p=0.001 vs [deferred] for p=0.4). This biases prevalence estimates toward studies with smaller p-values. Documented as policy choice per Constitution Principle VI, not statistical optimization.

### Phase 3: Prevalence Estimation & Reporting (Week 4)

**Objective**: Compute inconsistency prevalence, bias-adjustment, subgroup analysis, export reports.

| Task ID | Description | FR/SC Coverage | Deliverable |
|---------|-------------|----------------|-------------|
| T020 | Implement two-sided binomial test vs. baseline 0.05 | FR-005a, SC-014 | `code/prevalence.py` |
| T021 | Compute Wilson 95% CI for inconsistency proportion | FR-005a, SC-014 | `code/prevalence.py` |
| T022 | Sensitivity analysis for baseline 0.02–0.10 (step 0.01) | FR-005b, SC-015 | `code/prevalence.py` |
| T022b | Sensitivity analysis: compare prevalence with/without missing-metric entries | SC-005, FR-004b | `output/missing_metric_sensitivity.json` |
| T023 | Implement domain bias assessment (no domain>30%) | FR-027, SC-027 | `code/bias.py` |
| T024 | Compute bias-adjusted inconsistency rate (domain-weighted) | FR-027 | `output/bias_report.json` |
| T025 | Implement domain subsampling if any domain>30% | FR-027, T044 | `code/bias.py` |
| T026 | Subgroup analysis by domain/year with Fisher's exact test | FR-032, SC-032 | `code/subgroup.py` |
| T027 | Apply Bonferroni correction to subgroup tests | FR-032, SC-032 | `code/subgroup.py` |
| T028 | Export JSON audit report with all required fields | FR-024, SC-024 | `output/audit_report.json` |
| T029 | Export CSV summary report with Wilson CI | FR-024, SC-024 | `output/summary_report.csv` |
| T030 | Compute and record file checksums | T076, SC-013 | `output/checksums.txt` |
| T031 | Extend manifest.json with checksum entries | T077, SC-013 | `output/manifest.json` |

**Statistical Rigor Notes**:
- Baseline binomial test (FR-005a) is single test; no multiple-comparison correction needed.
- Subgroup tests (FR-032) require Bonferroni correction (adjusted α = 0.05 / number_of_subgroups).
- **Sensitivity analysis (FR-005b)**: Testing 9 baseline proportions (0.02–0.10 step 0.01) inflates Type I error rate without correction. Apply Bonferroni correction (adjusted α = 0.05/9 ≈ 0.0056) to all 9 binomial tests.
- Wilson CI width must be ≤0.10 (SC-014); if exceeded, N≥300 corpus may need expansion.
- Sensitivity analysis must show prevalence variation <0.02 across baseline range (SC-015).
- **Unaddressed confounds**: Domain bias control (FR-027) addresses one confound but not others like publication year trends, company size, or industry-specific reporting practices. Subgroup analysis by year (FR-032) partially addresses this, but no adjustment is made for these factors in the overall prevalence estimate. Documented in Methodological Limitations.

### Phase 4: Validation & Documentation (Week 5)

**Objective**: Validate synthetic detection performance, complete documentation, CI verification.

| Task ID | Description | FR/SC Coverage | Deliverable |
|---------|-------------|----------------|-------------|
| T032 | Evaluate inconsistency detection on synthetic dataset | FR-031, SC-030 | `output/synthetic_validation_report.json` |
| T033 | Verify precision≥90%, recall≥80% (F1≥0.85) on synthetic data | FR-031, SC-030 | `output/synthetic_validation_report.json` |
| T034 | Create Quickstart guide (README) with CLI examples | FR-028, SC-028 | `quickstart.md` |
| T035 | Verify Quickstart: novice completes 30 URLs in ≤30 minutes | FR-028, SC-028 | User test report |
| T036 | CI end-to-end test on sample corpus (≤6 hours) | FR-009, SC-008 | GitHub Actions run |
| T037 | Verify manifest.json created in ≥99% of CI runs | SC-013 | CI logs |
| T038 | Verify parsing error rate ≤5% of total summaries | FR-007, SC-005 | CI logs |

**Statistical Rigor Notes**:
- Synthetic validation precision/recall targets apply only to synthetic data (FR-031); real-world performance may differ (Methodological Limitations).
- Real-world extraction validation (FR-031b) measures field-level capture accuracy, not inconsistency detection accuracy (ground truth is human verification of reported numbers, not statistical correctness).

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| HTML structure varies across sources | High extraction failure rate | Implement robust parsing with multiple fallback strategies; log ERR-### codes (FR-007) |
| Corpus N<300 achievable | Insufficient power (FR-025) | Power analysis shows N≥300 required; if unavailable, document power limitation explicitly |
| Domain dominance (>30% from single source) | Biased prevalence estimate | Subsample dominant domain (FR-027); report bias-adjusted rate |
| CI runtime exceeds 6 hours | Pipeline fails (SC-008) | Optimize extraction parallelization; limit corpus to N=300-500 for CI sample |
| Memory exceeds 2GB | OOM on GitHub Actions | Process summaries in batches; stream data where possible |
| Synthetic validation targets not met | Implementation bugs | Debug reconstruction logic; verify against analytical formulas |
| **Missing metrics selection bias** | Prevalence estimate biased if missing metrics correlate with inconsistency | Perform sensitivity analysis (T022b) comparing prevalence with/without missing-metric entries; document bias magnitude |

## Timeline

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Phase 0 | Week 1 | CI environment ready, statistical tests validated |
| Phase 1 | Week 2 | Extraction pipeline functional, validation sets created |
| Phase 2 | Week 3 | Inconsistency detection operational |
| Phase 3 | Week 4 | Reports generated, bias adjustment complete |
| Phase 4 | Week 5 | All validation targets met, documentation complete |

**Total Duration**: 5 weeks to `research_complete` stage.