# Implementation Plan: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Branch**: `001-gene-regulation` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a CPU-first pipeline to evaluate zero-shot Large Language Models (LLMs) against static analyzers for identifying security vulnerabilities in C, Python, and JavaScript code. The system ingests verified datasets (VulDeePecker, NIST Juliet, JSVulnDB), extracts structural (AST depth, cyclomatic complexity) and semantic (taint API frequency) features, and performs logistic regression to correlate these features with LLM prediction accuracy. The pipeline includes a static analyzer baseline (Bandit, cppcheck) and rigorous statistical validation (McNemar's test, multiple-comparison correction) within strict GitHub Actions compute limits (limited CPU, constrained RAM, bounded execution time).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `tree-sitter`, `transformers` (CPU-optimized), `scikit-learn`, `pandas`, `pyyaml`, `ruff`, `black`, `bandit` (CLI), `cppcheck` (CLI), `datasets` (streaming), `jsonschema`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`) with JSONL/Parquet intermediates.  
**Testing**: `pytest` with `pytest-cov`, `hypothesis` for edge cases, and `jsonschema` for contract validation.  
**Target Platform**: GitHub Actions Linux Runner (vCPU, 7 GB RAM).  
**Project Type**: Data Science / Research Pipeline.  
**Performance Goals**: End-to-end pipeline completion ≤ 6 hours for max [deferred] samples; per-sample inference ≤ 4.32s.
**Constraints**: No GPU access (CPU-first); memory footprint ≤ 7 GB; no PII in data; strict stratified sampling.  
**Scale/Scope**: Several languages (C, Python, JS); A maximum of several thousand total samples will be collected (stratified); baseline tools; A selected LLM model family (quantized/distilled) will be evaluated to address the research question regarding model efficiency and performance trade-offs. The method involves comparative analysis across quantization and distillation techniques. References: [Insert DOI/arXiv/author-year here]..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; datasets fetched from canonical HF URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are from the verified block; no fabricated citations. |
| **III. Data Hygiene** | **PASS** | Checksums recorded in `state/`; raw data immutable; derived data in `data/processed`; PII scan on commit. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace to `data/results/analysis_metrics.csv` which MUST conform to `contracts/analysis_metric.schema.yaml`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; `updated_at` timestamps managed by state file. |
| **VI. Computational Resource Limits** | **PASS** | Plan uses CPU-only inference (quantized/distilled models); streaming data to fit 7 GB RAM; A timeout is enforced to limit execution duration.. |
| **VII. Baseline Comparison** | **PASS** | Bandit (Python) and cppcheck (C) integrated as mandatory baselines; McNemar's test planned. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Canonical Schemas)
│   ├── analysis_metric.schema.yaml
│   ├── dataset.schema.yaml
│   ├── feature_vector.schema.yaml
│   └── prediction_result.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-282-evaluating-the-effectiveness-of-llms-for/
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   ├── processed/       # Feature vectors, cleaned snippets (raw_snippets.parquet)
│   ├── results/         # Predictions, analysis metrics, plots
│   └── logs/            # Execution logs, stratification_verification.json, dataset_substitution_justification.json
├── src/
│   ├── data/
│   │   ├── ingest.py            # Dataset loading & stratified sampling
│   │   ├── feature_extractor.py # AST, semantic extraction (US-2)
│   │   └── baseline_runner.py   # Bandit/cppcheck execution (US-4)
│   ├── models/
│   │   ├── llm_inference.py     # Zero-shot LLM execution (CPU) (US-1)
│   │   └── regression.py        # Logistic regression & stats (US-3)
│   ├── utils/
│   │   ├── config.py            # Constants, seeds, paths
│   │   └── validators.py        # Schema validation (jsonschema)
│   └── main.py                  # Orchestrator
├── tests/
│   ├── unit/                    # Unit tests for parsers, extractors
│   ├── integration/             # Pipeline integration tests
│   └── contract/                # Schema validation tests (jsonschema)
├── .ruff.toml                   # Linting config
├── pyproject.toml               # Dependencies & formatting config (black, ruff)
└── requirements.txt             # Pinned dependencies
```

**Structure Decision**: Selected a single `src/` directory structure with clear separation of data, models, and utils. This minimizes overhead for the small-scale research pipeline while maintaining modularity for testing. `data/` is strictly partitioned into `raw` (immutable), `processed` (derived), and `results` (final outputs) to satisfy Data Hygiene principles.

## Contract Testing Strategy

To ensure Data Hygiene and Reproducibility (Principles I & III), the pipeline enforces strict schema validation:
1.  **Canonical Schemas**: The `contracts/` directory (located in `specs/.../contracts/`) contains the single source of truth for data structures:
    *   `analysis_metric.schema.yaml` (for `data/results/analysis_metrics.csv`)
    *   `dataset.schema.yaml` (for `data/processed/raw_snippets.parquet`)
    *   `feature_vector.schema.yaml` (for `data/processed/features.parquet`)
    *   `prediction_result.schema.yaml` (for `data/results/predictions.csv`)
2.  **Runtime Validation**: The `src/utils/validators.py` module uses `jsonschema` to validate every output file against its corresponding schema before writing.
3.  **Contract Tests**: The `tests/contract/` directory contains `pytest` tests that load the schema and sample data to ensure the pipeline logic produces valid JSON/Parquet conforming to the definitions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Static Analyzer Baseline** | Constitution Principle VII requires a baseline comparison to claim "effectiveness". | A simple accuracy report without baseline comparison would fail the constitutional requirement and not answer the research question. |
| **Stratified Sampling** | Dataset sizes (VulDeePecker, JSVulnDB) exceed memory/runtime limits; need representative subset. Mandated by FR-001, US-1. | Random sampling without stratification risks under-representing rare vulnerability types, biasing the logistic regression results. |
| **CPU-First Inference** | GitHub Actions free tier has no GPU; 6-hour limit. | GPU-based models (e.g., full CodeLlama 7B) are infeasible; quantized/distilled CPU models are the only valid path. |
| **McNemar's Test** | Required to statistically validate if LLM > Static Analyzer (US-3). | Simple metric comparison (e.g., F1 difference) lacks statistical significance testing for paired data. |

## Statistical Analysis Plan (Detailed)

1.  **Performance Metrics**:
    *   Precision, Recall, F1, ROC-AUC calculated per vulnerability category and model (LLM vs. Static Analyzer).
    *   **Multiple-Comparison Correction**: Bonferroni correction applied to the family of correlation tests for each category to control Family-Wise Error Rate (FWER).

2.  **Regression Analysis**:
    *   **Model**: Logistic Regression (GLM with logit link) predicting `is_correct` (1/0) from features:
        *   `ast_depth` (Structural)
        *   `cyclomatic_complexity` (Structural)
        *   `taint_api_count` (Semantic)
        *   `sanitization_present` (Semantic)
        *   `language` (Categorical control)
        *   **`cwe_category`** (Categorical control: one-hot encoded to prevent confounding between vulnerability type difficulty and code complexity).
    *   **Excluded Features**: `embedding_similarity_score` is **excluded** from the primary regression to prevent tautological correlation (predictor derived from same vulnerability definitions as ground truth). It is retained for exploratory analysis only.
    *   **Metrics**: Adjusted R² (McFadden's Pseudo R²), coefficient p-values.
    *   **Success Criteria**: Model adjusted R² > 0.10 OR p < 0.05 for at least one predictor (SC-002).
    *   **Hypothesis**: Deeper nesting and higher complexity correlate with lower accuracy (negative coefficient for `ast_depth`).

3.  **Baseline Comparison (McNemar's Test)**:
    *   **Mapping**: LLM output `Uncertain` is mapped to `Safe` (Negative) for the binary contingency table to represent a conservative failure mode (false negative). This ensures a valid 2x2 table for McNemar's test.
    *   **Test**: Paired test comparing LLM predictions vs. Static Analyzer predictions on the same samples.
    *   **Significance**: p < 0.05 required to claim statistical superiority (SC-006).

4.  **Sensitivity Analysis (FR-011)**:
    *   **Subset**: Random sample of n=100.
    *   **Protocol**: Independent ground-truth re-labeling by a secondary expert or cross-reference with a secondary labeled dataset.
    *   **Metric**: Compare original metrics vs. re-labeled metrics to quantify impact of label noise.

## Risks & Mitigations

-   **Risk**: NIST Juliet raw code not available via HF.
    -   **Mitigation**: Use official `git clone` of NIST Juliet (standard academic source).
-   **Risk**: LLM inference exceeds 6-hour limit.
    -   **Mitigation**: Strict sample cap ([deferred]); batch processing; fallback to smaller model.
-   **Risk**: Ground truth noise in community datasets.
    -   **Mitigation**: Sensitivity analysis (FR-011) on a subset (n=100) using independent re-labeling.
-   **Risk**: Data starvation for JavaScript.
    -   **Mitigation**: Use JSVulnDB instead of BigVul to ensure sufficient JS samples.
-   **Risk**: Circular validity in embedding features.
    -   **Mitigation**: Exclude `embedding_similarity_score` from primary regression; use only for exploratory analysis.