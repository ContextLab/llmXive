# Implementation Plan: Automated Detection of Algorithmic Bias in Public Code Repositories

**Branch**: `001-auto-detect-bias` | **Date**: 2026-07-11 | **Spec**: `spec.md`
**Input**: Feature specification for automated bias detection via static analysis and synthetic simulation.

## Summary

This feature implements a research pipeline to investigate the associational relationship between "Textual Bias" (demographic terms and negative sentiment in code comments/variables) and "Bias Sensitivity" (the rate at which fairness metrics degrade as bias is injected into a simulated model). 

**Crucial Methodological Correction**: The study does *not* correlate text with a fixed synthetic fairness metric (which would be tautological). Instead, for each repository, we simulate a family of models by varying `injected_skew_magnitude` and calculate the **slope** of the fairness degradation curve (d(Fairness Metric)/d(Skew)). The hypothesis is that repositories with higher "Textual Bias Scores" exhibit **steeper slopes** (i.e., their simulated models are more fragile to bias injection). This tests whether textual artifacts predict *system fragility*, a valid associational claim.

The pipeline is strictly observational and non-execution-based for source code (static AST parsing) and relies on synthetic data generation for the outcome variable to ensure statistical independence between the predictor (text) and the simulation process (which uses a controlled parameter). The pipeline is designed to run on a 2-core CPU GitHub Actions runner, processing up to 500 repositories within 6 hours and 7 GB RAM.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `ast` (stdlib), `numpy`, `pandas`, `scipy`, `vaderSentiment`, `fairlearn`, `datasets` (HuggingFace), `pyyaml`
**Storage**: Local file system (`data/` for raw/processed artifacts, `state/` for manifests)
**Testing**: `pytest` (unit tests for parsers, integration tests for pipeline phases)
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, ~7 GB RAM)
**Project Type**: Research CLI / Data Pipeline
**Performance Goals**: Process 500 repos in ≤6h; RAM ≤7 GB; Disk ≤14 GB
**Constraints**: No code execution of target repos; no GPU required (CPU-first); strict independence of synthetic data from code text.
**Scale/Scope**: 500 Python repositories; 200 manually labeled comments for validation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned in `code/`. VADER lexicon and synthetic data generation logic are deterministic. External datasets (VADER) fetched from verified HuggingFace URLs. |
| **II. Verified Accuracy** | ✅ Pass | All citations (VADER, Fairlearn) will be validated against primary sources. `CITATION_TITLE_OVERLAP_THRESHOLD` (0.7) enforced for any new literature. |
| **III. Data Hygiene** | ✅ Pass | Raw data (VADER parquet, repo clones) checksummed. No in-place modification; derivations written to new files. PII scan enforced on commit. |
| **IV. Single Source of Truth** | ✅ Pass | **Design Phase**: This plan defines the schema for traceability. **Execution Phase**: All stats in `plan.md`/`research.md` will trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Pass | State file `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` updated on artifact changes. Content hashes tracked. |
| **VI. Synthetic Data Independence** | ✅ Pass | Synthetic data generated from domain-neutral distributions (Gaussian/Uniform) with no ingestion of code tokens. String-hash verification (FR-015) implemented in Step 3.2. |
| **VII. Static Analysis Fidelity** | ✅ Pass | Source code parsing uses `ast` module only. No `exec()` or import of target repos. |

## Project Structure

### Documentation (this feature)

```text
specs/001-auto-detect-bias/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── artifact.schema.yaml
    ├── correlation_results.schema.yaml
    ├── data_model.schema.yaml
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    ├── repo_scores.schema.yaml
    ├── result.schema.yaml
    ├── simulation_results.schema.yaml
    └── validation.schema.yaml
```

### Source Code (repository root)

```text
src/
├── bias_pipeline/
│   ├── __init__.py
│   ├── extractor.py          # FR-001, FR-002, FR-003 (AST + VADER)
│   ├── simulation.py         # FR-004, FR-005, FR-011, FR-012, FR-015
│   ├── validator.py          # FR-010, FR-013 (Kappa check)
│   ├── analyzer.py           # FR-006, FR-007, FR-008 (Correlation)
│   └── utils.py              # Logging, error handling (Edge Cases)
├── cli/
│   └── main.py               # Entry point
├── data/
│   ├── raw/                  # Cloned repos, VADER parquet
│   ├── processed/            # Bias scores, fairness metrics, sensitivity slopes
│   └── validation/           # Manually labeled comments
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure under `src/` to minimize overhead. `bias_pipeline` module encapsulates the three core phases (Extraction, Simulation, Analysis). `data/` mirrors the pipeline stages.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sensitivity Slope Simulation** | Required to avoid tautology (methodology-a39d8d77). Correlating text with a fixed synthetic metric is invalid. We must correlate text with the *rate of change* in fairness metrics. | Using a single-point simulation would yield a null result by construction, failing to test the "fragility" hypothesis. |
| **Multiple Comparison Correction** | Required by FR-007 and SC-001 due to testing multiple hypotheses (variables vs. comments, multiple alpha levels, multiple fairness metrics). | Ignoring correction inflates Type I error rate, invalidating statistical claims. |
| **Sensitivity Analysis** | Required by FR-008 to validate robustness of the significance threshold (alpha sweep). | Single-threshold reporting is fragile and does not meet the "Measurable Outcomes" (SC-002). |