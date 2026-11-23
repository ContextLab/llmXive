# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

**Branch**: `001-eval-code-vuln-density` | **Date**: 2026-06-27 | **Spec**: `specs/001-eval-code-vuln-density/spec.md`

## Summary

This project evaluates the security implications of using Large Language Models (LLMs) for code generation by comparing vulnerability density in LLM-generated code versus human-written reference solutions. The technical approach involves: (1) downloading and running open-source models (StarCoder, CodeGen) on HumanEval and MBPP benchmarks to generate code samples; (2) executing static analysis tools (Bandit) to count vulnerabilities; (3) applying robust statistical methods (ZINB regression with fallback to permutation tests, using Benjamini-Hochberg for multiple comparisons) to compare groups; and (4) generating visualizations and reports. All processes are designed for CPU-first execution within GitHub Actions free-tier constraints.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers`, `torch`, `datasets`, `bandit`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `pytest`, `huggingface_hub`
**Storage**: File-based (CSV, JSON, Parquet) in `data/`, `results/`, `state/`
**Testing**: `pytest` (unit, integration, contract tests)
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, standard memory allocation.)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Complete full pipeline (generation + analysis) within 6 hours; memory < 7340 MB
**Constraints**: CPU-first execution; no local GPU; open datasets only; pinned tool versions; reproducibility via fixed seeds.
**Scale/Scope**: A sufficient number of valid samples per model/benchmark will be collected; models (StarCoder, CodeGen); Benchmarks (HumanEval, MBPP); Vulnerability categories (if n ≥ 5).

> **Dataset Note**: The spec requires HumanEval and MBPP. All datasets are open, directly downloadable via HuggingFace `datasets` library. No access-gated data is planned.

## Constitution Check

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **Compliant** | Fixed random seeds in `code/` for generation and sampling. Pinned versions in `requirements.txt`. Datasets fetched from canonical HF sources on every run. Reproducibility verification step included. |
| **II. Verified Accuracy** | **Compliant** | FR-014 mandates execution of a Reference-Validator Agent (rule-based heuristics + deterministic seed) on stratified samples. Citations in `research.md` and `data-model.md` are restricted to the verified URLs block. The agent uses a custom heuristic based on known CWE patterns, combined with manual audit for ground truth validation.|
| **III. Data Hygiene** | **Compliant** | All raw data files in `data/raw` will be checksummed (SHA-256) and recorded in `state/`. Derived files in `data/processed` will be new files, never in-place modifications. PII scan included. |
| **IV. Single Source of Truth** | **Compliant** | `results/summary.md` will be generated programmatically from `data/processed` only. No hand-typed statistics. Traceability enforced via file paths in the report generator. |
| **V. Versioning Discipline** | **Compliant** | Content hashes for all artifacts in `data/` and `code/` will be updated in `state/` upon completion. |
| **VI. Static Analysis Consistency** | **Compliant** | Bandit version pinned in `requirements.txt`. Configuration file (`.bandit.yaml`) committed to `code/` to ensure identical rule-sets are applied consistently across analyses.|
| **VII. Functional Equivalence** | **Compliant** | FR-002 enforces that only samples passing benchmark tests (HumanEval/MBPP) are included in vulnerability analysis. Failed generations are excluded. Selection bias is addressed via sensitivity analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── vulnerability_report.schema.yaml
    ├── statistical_result.schema.yaml
    ├── adjusted_counts.schema.yaml
    ├── analysis.schema.yaml
    ├── report.schema.yaml
    └── stats_results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── requirements.txt
├── .bandit.yaml         # Pinned Bandit config
├── generation/
│   ├── __init__.py
│   ├── download_models.py
│   ├── generate_samples.py
│   └── validate_samples.py
├── analysis/
│   ├── __init__.py
│   ├── run_bandit.py
│   ├── calculate_metrics.py
│   ├── statistical_tests.py
│   └── power_analysis.py
├── reporting/
│   ├── __init__.py
│   ├── generate_plots.py
│   ├── generate_report.py
│   └── validator_agent.py
├── utils/
│   ├── __init__.py
│   ├── data_hygiene.py
│   └── reproducibility.py
└── main.py

data/
├── raw/
│   ├── humaneval/
│   ├── mbpp/
│   └── models/
├── processed/
│   ├── valid_samples/
│   ├── vulnerability_reports.csv
│   ├── vulnerability_counts.csv
│   ├── fpr_metrics.json
│   ├── validator_flags.csv
│   └── statistical_results.json
├── checksums.json
└── pii_scan.log

results/
├── plots/
│   ├── boxplot_vuln_density.png
│   └── bar_chart_vuln_types.png
└── summary.md

state/
├── project_state.yaml
├── reproducibility_logs/
├── test_results/
└── pii_scan.log

tests/
├── unit/
├── integration/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_vulnerability_schema.py
└── fixtures/
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`, `state/`) selected to align with the computational research pipeline nature. Modules are separated by function (generation, analysis, reporting) to ensure maintainability and testability.

## Complexity Tracking

No violations found in Constitution Check. The complexity is managed by:
1. **Modular Design**: Separation of generation, analysis, and reporting allows independent testing and debugging.
2. **Fallback Strategies**: ZINB fallback to permutation test (FR-005) and sample size checks (FR-009).
3. **CPU-first**: Designing for CPU-first execution ensures feasibility on the target platform; GPU escape hatch is only for model inference if strictly necessary.
4. **Bias Mitigation**: Explicit sensitivity analysis for selection bias and use of Benjamini-Hochberg for correlated tests.
5. **Real Data**: All metrics are computed from real data; no fabricated values are permitted.

## Revised Methodology Notes

### Selection Bias Mitigation
The plan explicitly addresses the concern that "valid" samples (those passing benchmark tests) may have a different vulnerability profile than the full population of generated code.
- **Strategy**: We will perform a sensitivity analysis comparing the distribution of vulnerability types between "valid" and "invalid" samples (if enough invalid samples exist) to detect if the validity filter biases the vulnerability profile.
- **Modeling**: The statistical model will explicitly state that the sample is conditioned on functional correctness. The ZINB model will include a covariate for the validity mechanism where applicable, or the results section will explicitly discuss this limitation.

### Multiple Comparison Correction
- **Method**: Benjamini-Hochberg (BH) procedure for False Discovery Rate (FDR) control.
- **Rationale**: Vulnerability categories (CWEs) are not independent; a single code snippet can contain multiple vulnerabilities. BH is more appropriate for dependent tests than Bonferroni, reducing the risk of over-conservative results that mask true effects.

### Data Integrity & Reproducibility
- **Real Data Only**: The pipeline strictly forbids hardcoded or simulated metrics. All statistical results must be derived from the actual execution of the pipeline on real data.
- **Reproducibility Check**: The pipeline includes a step to run the generation and analysis twice with the same seed. Outputs are compared for identical floating-point values (≤ 1e-6 difference).
- **Test Execution**: All unit, integration, and contract tests must pass. Logs are stored in `state/test_results/`.
- **PII Scan**: A PII scan is run on all data and report files. The pipeline halts if PII is detected.