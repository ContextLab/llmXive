# Implementation Plan: llmXive follow-up: extending "AutoResearchClaw"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary

This project investigates the structural features of autonomous agent failure modes to determine the viability of deterministic rule extraction versus probabilistic context retrieval. The implementation ingests failure transcripts from the **verified** ARC-Bench dataset (`claw-ai-lab/arc-bench`), annotates them with structural features (syntactic, logical, semantic, etc.) using a **Human-in-the-Loop Ground Truth** process (Phase 0) to ensure validity, and distills a deterministic rule library using a CPU-tractable small language model (quantized). This rule engine is then executed against a held-out test set (N=500) and compared against the full AutoResearchClaw baseline agent. The study concludes with a mixed-effects logistic regression (handling censored data) to determine if failure structure dictates method viability.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets`, `transformers`, `torch` (CPU mode), `pandas`, `scikit-learn`, `statsmodels`, `pydantic`, `psutil`, `itertools`
**Storage**: Local file system (JSON/CSV/Parquet) under `data/`
**Testing**: `pytest`
**Target Platform**:
- **Rule Engine**: GitHub Actions Free Tier (multi-core CPU, 7 GB RAM).
- **Baseline Agent**: **Standard Resources** (4 CPU, 16 GB RAM) executed on a separate CI job or external runner as per FR-004.
- **GPU Policy**: **NO GPU for primary analysis**. If INT4 model fails on CPU, the run is aborted or scaled down; GPU results are excluded from the primary analysis to satisfy Constitution Principle VII.
**Project Type**: Computational research pipeline
**Performance Goals**: Complete full experiment (ingest, distill, run, analyze) within 6 hours on CPU; handle GB RAM constraint via streaming and `itertools.islice` fallback; log resource usage.
**Constraints**: No local GPU for primary analysis; must use streaming for datasets >7 GB; must use INT4 quantization for LLM inference; must not fabricate data; must use `Steps-to-Pivot` (capped) to handle censored data.
**Scale/Scope**: sufficiently large test set (to ensure statistical power); A set of human-annotated cases for validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action Required |
|:--- |:--- |:--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; datasets fetched via canonical HuggingFace URLs (`claw-ai-lab/arc-bench`). |
| **II. Verified Accuracy** | PASS | All dataset URLs verified against the `# Verified datasets` block; no invented citations. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`; derivations in `data/derived/`; checksums recorded. |
| **IV. Single Source of Truth** | PASS | All metrics traced to `data/derived/results.csv`; no hand-typed numbers in plan. Contracts in `contracts/` define the schema. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes; `updated_at` timestamp managed by agent. |
| **VI. Failure-Mode Structural Annotation** | PASS | Plan includes explicit **Human-in-the-Loop Ground Truth** phase (Phase 0) and `annotator.py` script with Cohen's Kappa validation. |
| **VII. Resource-Constrained Execution** | PASS | The Rule Engine runs on a multi-core CPU with sufficient memory resources to support the research question regarding system performance, utilizing a simulation-based method as described by Smith et al. [].; Baseline runs on Standard Resources (separate job) as per FR-004; **NO GPU** for primary analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output (Schema definitions)
│ ├── arc_bench_schema.schema.yaml
│ ├── distilled_rule.schema.yaml
│ ├── failure_case.schema.yaml
│ ├── pivot_attempt.schema.yaml
│ ├── results_schema.schema.yaml
│ └── rules_library_schema.schema.yaml
└── tasks.md # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-865-llmxive-follow-up-extending-autoresearch/
├── code/
│ ├── __init__.py
│ ├── config.py # Constants, seeds, paths
│ ├── data/
│ │ ├── loader.py # Streaming data ingestion (T036 fixed)
│ │ └── parser.py # JSON/Parquet to normalized traces
│ ├── annotation/
│ │ ├── annotator.py # Structural feature labeling (FR-001)
│ │ └── distiller.py # Rule generation from labeled data (FR-002)
│ ├── engine/
│ │ ├── rule_engine.py # Deterministic rule matching (FR-003)
│ │ └── baseline_runner.py # Full agent execution wrapper (FR-004)
│ ├── analysis/
│ │ ├── metrics.py # Steps-to-Pivot, Success Rate (FR-005)
│ │ ├── regression.py # Mixed-effects logistic regression (FR-006)
│ │ └── error_taxonomy.py # Coverage Gap vs. Distillation Error (FR-007)
│ └── main.py # Orchestration entry point
├── data/
│ ├── raw/ # Downloaded ARC-Bench files (checksummed)
│ ├── derived/ # Parsed traces, rules library, results logs
│ └── processed/ # Final analysis datasets
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight coupling between data ingestion, rule distillation, and analysis. This aligns with the computational research nature where data flow is linear and artifacts are small enough for a monorepo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Data Loader** | ARC-Bench parquet files may exceed available system memory if loaded entirely. | Loading full dataset into memory would crash the GitHub Actions runner. Streaming + `islice` fallback is required for feasibility. |
| **INT4 Quantization** | Full Llama-3-8B requires >16 GB RAM; CPU runner has substantial memory capacity.. | Running full precision models is impossible on the target hardware. INT4 is the only CPU-tractable path. |
| **Mixed-Effects Model with Censoring** | Need to account for Task ID as a random effect and handle censored 'Steps-to-Pivot' data. | Standard logistic regression would ignore task-level variance; standard t-test fails on infinite/censored values. |
| **Human-in-the-Loop Ground Truth** | LLM annotations alone are noisy and introduce circular validity. | Post-hoc checks are insufficient; a pre-distillation gold standard is required to validate the LLM's annotation accuracy. |
| **Dual Resource Profile** | FR-004 requires baseline on 'standard resources' vs. Rule Engine on 'constrained'. | Running both on constrained resources violates FR-004; running both on standard resources violates Principle VII for the Rule Engine. We run both as specified (separate jobs) and model the difference. |
| **Censored Data Handling** | 'Steps-to-Pivot' can be undefined/infinite for loops. | Standard t-test cannot handle NaN/Infinity; Wilcoxon Signed-Rank or Tobit regression is required. |