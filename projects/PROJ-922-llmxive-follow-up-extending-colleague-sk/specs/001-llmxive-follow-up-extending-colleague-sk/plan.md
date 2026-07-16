# Implementation Plan: llmXive follow-up: extending "COLLEAGUE.SKILL"

**Branch**: `001-llmxive-skill-separation` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-skill-separation/spec.md`
**Input**: Feature specification regarding decoupled capability/behavior prompts in LLM agents.

## Summary

This project investigates whether explicitly decoupling capability heuristics (what the agent knows) from behavioral style (how the agent speaks) reduces hallucination and style drift compared to monolithic prompts. The technical approach involves:
1.  **Data Synthesis**: Generating expert profiles (capability + behavior) and multi-turn task scenarios (coding, math, logic, creative, factual) using rule-based Python scripts. *Scale reduced for CI feasibility.*
2.  **Inference Engine**: Running a quantized small language model (e.g., Llama-3-8B-Q4 or Phi-3-mini) on a CPU-only backend (`llama.cpp` or `transformers` with `torch.float32`) under three prompt conditions: Monolithic, Separated Tracks, and Generic Baseline.
3.  **Deterministic Evaluation**: Calculating Heuristic Adherence (via AST/SymPy/Z3), Style Consistency (via NLI/Style Classifier), and Hallucination Rate (via NLI/External Truth) via rule-based scripts without LLM judges.
4.  **Statistical Analysis**: Fitting a Generalized Linear Mixed Model (GLMM) to test for significant differences in metrics across conditions, applying Bonferroni correction for multiple comparisons.

**Total Scale**: [deferred] total inference runs (10 profiles × 50 tasks × 2 conditions). This fits within the established CI time limit (total runtime with parallelization).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU build), `llama-cpp-python` (fallback), `statsmodels`, `pandas`, `numpy`, `pytest`, `pyyaml`, `sympy`, `z3-solver`, `scikit-learn`, `deberta-v3`  
**Storage**: Local filesystem (`data/` for raw/generated data, `data/interim/` for processed results)  
**Testing**: `pytest` (unit tests for prompt generation, evaluation logic; integration tests for inference pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: <15s per inference task (optimized CPU quantized); <7GB RAM peak usage; <14GB disk usage (streaming/cleanup)  
**Constraints**: CPU-only inference (no CUDA); quantized models only; deterministic evaluation (no LLM judges); strict memory limits.  
**Scale/Scope**: [deferred] total inference runs (10 profiles × 50 tasks × 2 conditions); expert profiles; task scenarios.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **COMPLIANT**. The plan mandates pinned random seeds in `code/`, deterministic rule-based evaluation (no LLM judges), and fetching of open datasets (or simulated equivalents) from canonical sources.
- **II. Verified Accuracy**: **COMPLIANT**. **Verified Accuracy Gate**: The `Reference-Validator` runs as a **pre-commit hook** and a **blocking CI gate before data generation**. If any citation in `research.md` is unreachable or mismatched, the build fails immediately. All citations in `research.md` will be validated against primary sources.
- **III. Data Hygiene**: **COMPLIANT**. Generated data (profiles, tasks, outputs) will be checksummed. Raw generated data will be preserved; processed results will be new files. No PII in generated synthetic profiles.
- **IV. Single Source of Truth**: **COMPLIANT**. All statistics in the final paper will trace to specific rows in `data/processed/` and code blocks in `code/`.
- **V. Versioning Discipline**: **COMPLIANT**. **Versioning Trigger**: `scripts/update_state.py` is executed as a **mandatory post-inference CI step** immediately after data generation and evaluation. It recalculates checksums for all `data/` artifacts and updates `state/` timestamps. If checksums do not match the expected values, the CI job **fails immediately**, enforcing the discipline.
- **VI. Deterministic Evaluation**: **COMPLIANT**. The plan explicitly forbids LLM judges. Heuristic Adherence, Style Consistency, and Hallucination Rate are defined as rule-based calculations (AST, SymPy, Z3, NLI models).
- **VII. Resource-Constrained Model Validation**: **COMPLIANT**. The plan mandates CPU-only inference with quantized models (Llama-3-8B-Q4 or Phi-3-mini). No GPU-accelerated results are planned for primary hypothesis testing.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-colleague-sk/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_generation/
│   ├── profiles.py      # Generate expert profiles (capability + behavior)
│   └── tasks.py         # Generate a set of task scenarios (stratified)
├── inference/
│   ├── engine.py        # Load model, run 3 prompt conditions
│   └── prompts.py       # Define Monolithic, Separated, Generic templates
├── evaluation/
│   ├── metrics.py       # Calculate Adherence (AST/SymPy), Style (NLI), Hallucination (NLI/Ext)
│   └── validators.py    # Ground-truth logic checks, AST parsers
├── analysis/
│   ├── stats.py         # GLMM fitting, Bonferroni correction, sensitivity analysis
│   └── plots.py         # Generate figures for paper
├── utils/
│   ├── config.py        # Seed pinning, path management
│   └── logging.py       # Structured logging
├── tests/
│   ├── unit/            # Test prompt generation, metric logic
│   └── integration/     # Test full inference pipeline (small subset)
└── requirements.txt     # Pinned dependencies

data/
├── raw/                 # Generated profiles, tasks (checksummed)
├── interim/             # Model outputs, intermediate logs
└── processed/           # Aggregated metrics, final dataset for analysis

state/
└── projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/
    └── artifacts.yaml   # Checksums and timestamps
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen for simplicity and direct alignment with the research pipeline. No frontend/backend split needed as this is a CLI-based research tool.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Generalized Linear Mixed Model (GLMM) | Required by FR-006 (revised) to handle binary/ratio outcomes (Heuristic Adherence, Hallucination Rate) which violate LMM normality assumptions. | LMM would produce invalid p-values for bounded data. |
| Rule-based Evaluation (No LLM Judges) | Required by FR-005 and Constitution Principle VI to avoid circularity and ensure determinism. | LLM judges are non-deterministic, prone to bias, and violate the "single source of truth" principle for metrics. |
| Quantized CPU Inference | Required by FR-001 and Constitution Principle VII to validate the hypothesis on resource-constrained hardware. | Full-precision GPU models would invalidate the "resource-constrained" premise and exceed CI runner limits. |
| AST/SymPy/Z3 for Evaluation | Required to validly measure Heuristic Adherence and Hallucination without circularity or false positives from simple string matching. | Regex matching cannot distinguish valid multi-hop inference from hallucination or verify logical correctness of code/math. |

## Statistical Power & Feasibility Note

- **Scale**: 10 profiles × 50 tasks × 2 conditions = 1,000 runs.
- **Runtime**: Estimated [deferred] per run (CPU, quantized). Total duration scales linearly with the number of runs if sequential.
- **CI Strategy**: The pipeline is split into 2 parallel jobs (one per condition). Each job runs a set of tasks. Wall-clock time per job: 500 × 15s = 7,500s ([deferred]). Total wall-clock time: estimated to be within the CI limit.
- **Power**: With [deferred] observations, we have >80% power to detect a moderate effect size (Cohen's d ≈ 0.3) for the primary hypothesis (Hallucination Rate reduction) in a GLMM framework.