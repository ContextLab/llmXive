# Implementation Plan: Evaluating the Impact of Code Style on LLM Code Understanding and Generation

**Branch**: `001-evaluating-code-style-impact` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-the-impact-of-code-style-on-l/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-style-on-l/spec.md`

## Summary

This project implements a rigorous **pilot experimental pipeline** to quantify how code style (formatting, commenting) and semantic obfuscation (naming) impact Large Language Model (LLM) performance. The approach involves transforming a base corpus (CodeSearchNet) into style variants, executing LLM tasks on a CPU-tractable model (CodeGen-2B), and performing mixed-effects statistical analysis with strict multiple-comparison corrections. 

**Critical Scope Adjustment**: Due to CPU constraints and the nature of the "Generic Naming" transformation (which alters semantics, not just style), this study is framed as an **exploratory pilot**. Causal claims regarding "style" are restricted to Formatting and Commenting factors. The "Generic Naming" factor is analyzed as a "Semantic Obfuscation" effect. A formal power analysis simulation is conducted to determine if the pilot sample (N=30) is sufficient for variance estimation; if power < 0.5, the study remains descriptive.

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: `datasets` (HuggingFace), `transformers` (CPU-only), `scikit-learn`, `statsmodels`, `black`, `tokenizers`, `rouge-score`, `codebleu`, `mutmut` (for synthetic bug injection).
**Storage**: Local file system (`data/` for raw/derived, `results/` for outputs). No external database.
**Testing**: `pytest` for unit/integration tests; contract tests against YAML schemas.
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7GB RAM, no GPU).
**Project Type**: Research pipeline / CLI tool.
**Performance Goals**: Total runtime ≤ 6 hours; memory usage ≤ 6GB; successful execution of multiple variants per function on sampled data.
**Constraints**: No GPU/CUDA; no 8-bit quantization; no large-LLM inference; strict adherence to verified dataset sources.
**Scale/Scope**: Sampled subset of CodeSearchNet Python functions (N=30 functions, 240 variants) as a pilot for variance estimation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Reference in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`; `requirements.txt` pins; data fetched from canonical HF URLs. |
| **II. Verified Accuracy** | **Pass** | FR-010 pre-flight validation script; citations limited to `# Verified datasets` block; no invented URLs. |
| **III. Data Hygiene** | **Pass** | Raw data checksummed; transformations produce new files; PII scan included in CI. |
| **IV. Single Source of Truth** | **Pass** | All stats/figures trace to `data/` and `code/`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Pass** | Content hashes for artifacts; state file updated on change. |
| **VI. Deterministic Style** | **Pass** | Transformation pipeline (`code/transform/generator.py`) uses fixed seeds; **`seed_manager.py` logs `transform_seed` for every variant** to ensure full reproducibility of the 8-way factorial set. |
| **VII. Task-Specific Metric** | **Pass** | Metrics strictly mapped (ExactMatch/CodeBLEU, P/R/F1, ROUGE-L/BLEU); **GLMM (Binomial) for Exact Match, LMM (Gaussian) for continuous metrics**; mixed-effects ANOVA for stats. |

## Contract Traceability

| Plan Phase | Activity | Contract Schema |
| :--- | :--- | :--- |
| **Data Transformation** | Generate multiple variants per function | `contracts/dataset.schema.yaml`, `contracts/style_variant.schema.yaml` |
| **LLM Inference** | Execute tasks, calculate metrics | `contracts/task_result.schema.yaml` |
| **Statistical Analysis** | Fit models, generate report | `contracts/analysis_output.schema.yaml`, `contracts/statistical_result.schema.yaml` |
| **Validation** | Verify accuracy and schemas | `contracts/dataset_schema.schema.yaml` (Source) |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-code-style-on-l/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── task_result.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-194-evaluating-the-impact-of-code-style-on-l/
├── data/
│   ├── raw/             # Downloaded CodeSearchNet parquet files
│   ├── derived/         # Style variants, processed datasets
│   └── checksums.txt    # Manifest of data integrity
├── code/
│   ├── __init__.py
│   ├── transform/       # Style transformation logic (black, renaming, stripping)
│   │   ├── generator.py
│   │   ├── validator.py # Syntax check
│   │   └── seed_manager.py # **Records transform_seed for Principle VI**
│   ├── evaluate/        # LLM inference and metric calculation
│   │   ├── runner.py    # CPU-safe inference wrapper
│   │   ├── metrics.py   # ExactMatch, CodeBLEU, ROUGE, etc.
│   │   └── task_prompts.py
│   ├── analyze/         # Statistical analysis
│   │   ├── normality_check.py
│   │   ├── mixed_effects.py
│   │   └── report_gen.py
│   ├── mutation/        # **Synthetic bug injection (ast-based)**
│   │   └── mutator.py
│   ├── validation/      # Pre-flight checks (Constitution Principle II)
│   │   └── verify_accuracy.py
│   └── main.py          # Orchestration entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/        # Schema validation tests
├── results/             # Generated plots, CSVs, PDF reports
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular `code/` directories. This minimizes overhead for a research pipeline and ensures all dependencies are managed in a single `requirements.txt` for the CI runner.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Modeling (GLMM/LMM)** | Required by FR-005 to handle random intercepts for function ID and control for intra-function correlation. **Separate models used for binary (Exact Match) and continuous (CodeBLEU) metrics.** | Standard ANOVA would violate independence assumptions and fail to handle mixed outcome types. |
| **CPU-Only Inference** | Mandatory constraint of the CI environment (no GPU). | GPU-based inference is faster but infeasible on the target runner; requires careful sampling and model selection. |
| **8-Way Factorial Design + GN-PC Control** | Required by US-1 to isolate orthogonal effects. **Added GN-PC (Generic Naming + Preserved Comments) to isolate semantic loss from style.** | Simplified designs would fail to distinguish "style impact" from "semantic obfuscation". |
| **Pilot Study Framing** | CPU constraints limit N to a moderate scale. **Formal power analysis simulation confirms this is an exploratory pilot.** | Larger samples are impossible on free-tier CI; claiming confirmatory results would be statistically invalid. |