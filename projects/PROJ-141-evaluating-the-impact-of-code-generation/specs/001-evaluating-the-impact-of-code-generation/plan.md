# Implementation Plan: Evaluating the Impact of Code Generation Models on Developer Productivity

**Branch**: `001-code-gen-productivity` | **Date**: 2024-01-15 | **Spec**: `specs/001-code-gen-productivity/spec.md`
**Input**: Feature specification from `/specs/001-code-gen-productivity/spec.md`

## Summary

This project implements a controlled within-subject experiment to evaluate how LLM code-generation tools affect developer task-completion time and code quality. The system presents coding problems from HumanEval/Codeforces, records timestamps and code submissions under two conditions (LLM-assisted vs. baseline), computes quality metrics (pass rate, cyclomatic complexity, coverage, static-analysis warnings), and performs statistical analysis with multiple-comparison correction. The implementation must run on GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Flask (experiment interface), radon (cyclomatic complexity), coverage.py (test coverage), pylint (static analysis), scipy/statsmodels (statistical tests), torch (CPU-only LLM inference), datasets (HuggingFace dataset loading)  
**Storage**: SQLite (Participant, Session, Problem, Submission, Metric data), files (code submissions, logs)  
**Testing**: pytest (unit/integration), contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: web-service + analysis pipeline  
**Performance Goals**: ≤6 h total runtime for full analysis pipeline; ≤1s timestamp precision; ≥95% problem loading rate  
**Constraints**: NO GPU/CUDA; models ≤1GB and CPU-tractable; 7 GB RAM, 14 GB disk limits; no PII in committed data  
**Scale/Scope**: 30 participants, within-subject design (2 conditions), HumanEval + medium Codeforces problems

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
|-----------|--------|-----------------|
| I. Reproducibility | ✅ PASS | Pin random seeds in `code/`; fetch datasets from canonical sources on every run |
| II. Verified Accuracy | ⚠️ FLAG | HumanEval/Codeforces URLs verified; StarCoder verified; JaCoText has NO verified source (see research.md); must record exact commit/API snapshot in `data/metadata.yaml` |
| III. Data Hygiene | ✅ PASS | Checksum all files under `data/`; no PII; derivations produce new files |
| IV. Single Source of Truth | ✅ PASS | All figures/statistics trace to exactly one row in `data/` and one block in `code/` |
| V. Versioning Discipline | ✅ PASS | Content hashes for all artifacts; `updated_at` timestamp on state file |
| VI. Benchmark Integrity | ⚠️ FLAG | HumanEval/Codeforces verified URLs added; exact version (commit hash/API snapshot) MUST be recorded in `data/metadata.yaml`; JaCoText has NO verified source |
| VII. Human Participant Ethics | ✅ PASS | Informed consent before data collection; anonymized, encrypted at rest; secure deletion after analysis |

**Note**: Principle II and VI are both flagged by the same unverified-source issue (JaCoText). JaCoText has NO verified public source—this is a spec-root cause requiring kickback. See research.md for alternatives.

**Dataset Coverage Gap**: FR-001 requires HumanEval/Codeforces problems. HumanEval and Codeforces URLs are now verified (see research.md). JaCoText (FR-013) has NO verified source—this MUST be resolved before proceeding with data collection. Phase 0 research IS the gap-resolution step; data collection cannot proceed until verified sources are confirmed.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-gen-productivity/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── submission.schema.yaml
│   ├── metric.schema.yaml
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── experiment/
│   ├── app.py                 # Flask experiment interface
│   ├── consent.py             # Informed consent flow
│   ├── problem_loader.py      # HumanEval/Codeforces problem loading
│   └── randomization.py       # Participant, Session condition assignment, Latin square counterbalancing
├── quality/
│   ├── pass_rate.py           # Test suite execution, pass rate calculation
│   ├── complexity.py          # radon cc integration
│   ├── coverage.py            # coverage.py integration
│   └── static_analysis.py     # pylint/checkstyle integration
├── analysis/
│   ├── statistical_tests.py   # Paired t-test, Wilcoxon, Cohen's d, 95% CI
│   ├── correction.py          # Bonferroni/Holm multiple-comparison correction
│   └── sensitivity.py         # Threshold sensitivity analysis
├── data/
│   ├── raw/                   # Downloaded benchmarks (checksummed)
│   ├── derived/               # Processed data (new files, documented derivations)
│   └── metadata.yaml          # Version info, commit hashes, timestamps
├── models/
│   ├── jacotext_cpu.py        # JaCoText for Java (CPU-only) - see research.md for gap
│   └── starcoder_cpu.py       # StarCoder for Python (CPU-only)
├── logs/
│   └── experiment.log         # Participant, Session IDs, condition assignments, seeds
└── requirements.txt           # Pinned dependencies

tests/
├── contract/                  # Schema validation tests
├── integration/               # End-to-end experiment tests
└── unit/                      # Quality metric, statistical test unit tests
```

**Structure Decision**: Single project structure under `code/` with modular subdirectories for experiment, quality assessment, and analysis. This matches the research pipeline flow and simplifies reproducibility (single requirements.txt, single virtualenv).

**Entity Mapping**: Plan consistently names Participant, Session, Problem, Submission, Metric entities matching data-model.md (previously Session was implicit; now explicit).

## Complexity Tracking

> No violations requiring justification. All complexity is mandated by FR/SC requirements.

## Contract-to-Plan Mapping

| Contract Schema | FR/SC References | Test Suite |
|-----------------|------------------|------------|
| submission.schema.yaml | FR-003, FR-012, US-1 | tests/contract/test_submission.py |
| metric.schema.yaml | FR-004-007, US-2 | tests/contract/test_metric.py |
| analysis_result.schema.yaml | FR-008-011, US-3, SC-001-005 | tests/contract/test_analysis_result.py |

## Testing

```bash
# Contract tests (schema validation)
pytest tests/contract/ -v
  # - test_submission.py: validates Submission schema (FR-003, FR-012)
  # - test_metric.py: validates Metric schema (FR-004-007)
  # - test_analysis_result.py: validates Analysis Result schema (FR-008-011)

# Integration tests (end-to-end experiment)
pytest tests/integration/ -v

# Unit tests (quality metrics, statistical tests)
pytest tests/unit/ -v
```

## Compute Feasibility Decision

**Constraint**: GitHub Actions free-tier: 2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h

**Feasibility Assessment**:
- **LLM Inference**: StarCoder verified CPU-tractable (HuggingFace). JaCoText has NO verified source—blocking gap. If JaCoText unavailable, use StarCoder for both languages or limit to Python-only condition.
- **Quality Assessment**: radon, coverage.py, pylint are all CPU-only and lightweight. Feasible.
- **Statistical Analysis**: scipy/statsmodels are CPU-only. With 30 participants, negligible compute. Feasible.
- **Experiment Interface**: Flask is lightweight. Feasible if participants access remotely (not on GitHub Actions).
- **Total Runtime**: 30 participants × 2 conditions × [deferred]/problem × N problems. For N=2 problems, [deferred] per participant. Full experiment: 30 × 30 min = 900 min = 15 h (exceeds 6 h). **Decision**: Limit to N=2 problems per condition; experiment runs on separate server, analysis pipeline on GitHub Actions.

**Decision/Rationale**: Proceed with CPU-only models (verify sizes); limit problems to 2 per condition; use sampled data for quality assessment if needed; document all constraints in paper.