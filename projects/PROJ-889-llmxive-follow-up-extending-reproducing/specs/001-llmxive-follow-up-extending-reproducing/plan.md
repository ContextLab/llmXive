# Implementation Plan: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary

This feature implements a statistical detection pipeline for "reward hacking" in LLM-as-a-Judge systems. The core approach involves ingesting time-series training logs from the CHERRL repository, computing a divergence gap ($G(t)$) between biased and unbiased reward signals, and applying a sliding-window z-score detector (with sensitivity analysis and potential non-parametric alternatives) to flag anomalies. The system validates these detections against ground-truth hacking labels derived exclusively from drops in an independent gold-score signal ($J_{\text{gold}}$), ensuring statistical independence per the project constitution through extended correlation checks on both $J_{\text{unbiased}}$ and $J_{\text{biased}}$ against $J_{\text{gold}}$. The final output includes per-rubric performance metrics (Precision, Recall, F1) and a statistical significance test (Wilcoxon signed-rank test) comparing the detector against neutral baselines (random-guess and mean-divergence).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas` (data manipulation), `numpy` (numerical ops), `scipy` (statistical tests), `requests` (data fetching), `pyyaml` (contract loading), `jsonschema` (schema validation), `pytest` (testing).  
**Storage**: Local filesystem (`data/raw`, `data/processed`); no external database.  
**Testing**: `pytest` with contract-based tests validating schema adherence via `jsonschema`.  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, 7GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete analysis of N=5 seeds within 4 hours; memory usage < 6GB.  
**Constraints**: CPU-only execution; no GPU; strict adherence to statistical independence of ground truth (extended correlation checks); handling of zero-variance edge cases; contract validation at runtime.  
**Scale/Scope**: Processing time-series logs for multiple random seeds and bias types (Lexical, Format, Tone, Self-praise).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: **COMPLIANT**. Plan mandates pinning random seeds in `code/`, using canonical CHERRL sources (with explicit halt if source is missing), and re-running `code/` against `data/` on fresh runners.
2.  **II. Verified Accuracy**: **COMPLIANT**. Citations to CHERRL (arXiv) will be validated by the Reference-Validator Agent; no fabricated URLs. Data source must be verified before implementation proceeds.
3.  **III. Data Hygiene**: **COMPLIANT**. Plan requires checksumming raw data in `data/`, preserving raw files unchanged, and creating new files for derived data.
4.  **IV. Single Source of Truth**: **COMPLIANT**. All figures/stats will trace to `data/processed` CSVs and `code/` scripts; no hand-typed numbers.
5.  **V. Versioning Discipline**: **COMPLIANT**. Artifacts will carry content hashes; state updates will reflect changes.
6.  **VI. Statistical Independence of Ground Truth**: **COMPLIANT**. Plan explicitly enforces extended FR-006: ground truth derived *only* from $J_{\text{gold}}$ drops, with runtime correlation checks for both $r(J_{\text{unbiased}}, J_{\text{gold}})$ and $r(J_{\text{biased}}, J_{\text{gold}})$ to prevent circular validation. If either exceeds a predefined threshold, the system halts with an error.
7.  **VII. Generalization Across Rubric Taxonomies**: **COMPLIANT**. Evaluation phase (FR-005, SC-003) explicitly tests performance across Lexical, Format, Tone, and Self-praise rubrics. If the standard deviation of F-scores exceeds a significant threshold (universal threshold fails), the system triggers a **rubric-specific tuning step** (separate grid search per rubric type, implemented in `code/tune_rubric_specific.py`). Results are reported with explicit statement of whether a universal or rubric-specific threshold was used.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-889-llmxive-follow-up-extending-reproducing/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # FR-001, FR-002, FR-003: Load CHERRL logs, compute G(t), dG(t), z-score, detector logic
│   ├── ground_truth.py        # FR-004, FR-006: Gold drops, extended independence check (both J_unbiased and J_biased vs J_gold)
│   ├── evaluation.py          # FR-005: Metrics, Wilcoxon test, generalization, baseline comparison
│   ├── tune_rubric_specific.py # Conditional rubric-specific tuning (invoked if SC-003 fails)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded CHERRL logs (checksummed)
│   └── processed/             # Derived CSVs (trajectories_divergence.csv, trajectories_gt.csv, metrics.csv)
├── tests/
│   ├── contract/              # Schema validation tests (jsonschema-based)
│   ├── unit/                  # Unit tests for math functions
│   └── integration/           # End-to-end pipeline tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a research pipeline. All logic resides in `code/` with strict separation of concerns (ingestion, detection, ground truth, evaluation) to ensure traceability per Constitution Principle IV. Contract validation is enforced at runtime using `jsonschema`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Extended independence check (both $J_{\text{unbiased}}$ and $J_{\text{biased}}$ vs $J_{\text{gold}}$) | Prevents circular validation where divergence is coupled to ground truth. | Single check on $J_{\text{unbiased}}$ is insufficient if $J_{\text{biased}}$ is the primary driver of divergence. |
| Sensitivity analysis (grid search over W and $\tau$) | Arbitrary hyperparameters (W=20, $\tau=3.0$) are underpowered for RL training dynamics. | Fixed thresholds risk high false negatives/positives; grid search ensures data-driven tuning. |
| Wilcoxon signed-rank test (non-parametric) | N=5 seeds; t-test normality assumption is unreliable. | Parametric t-test risks invalid p-values; Wilcoxon is robust for small samples. |
| Neutral baselines (random-guess, mean-divergence) | Static-threshold baseline is methodologically unsound (time-biased). | Neutral controls ensure fair comparison and valid significance claims. |
| Rubric-specific tuning fallback | Principle VII mandates generalization; SC-003 may fail with fixed threshold. | Without fallback, failure to generalize leaves the study incomplete. |
