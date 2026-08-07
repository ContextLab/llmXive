# Implementation Plan: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

**Branch**: `001-llmxive-counterfactual-extension` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-counterfactual-extension/spec.md`

## Summary

This feature extends the `EvoPolicyGym` suite to test the hypothesis that **counterfactual failure explanations** improve the discovery of robust policies under **dynamic environmental shifts**. The implementation involves three core phases: () extending the 16 existing environments to support "dynamic-shift" modes where reward/transition functions change at a substantial portion of the interaction budget; (2) implementing a CPU-tractable counterfactual explanation generator that maps trajectory failures to specific Rule IDs and *heuristic* corrective actions (not ground-truth optimal actions); and (3) executing an evolutionary harness comparing a scalar-reward baseline against a counterfactual-feedback condition, followed by a mixed-effects statistical analysis of generalization scores (measured on a held-out test set) while controlling for policy complexity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `gymnasium` (or `EvoPolicyGym` base), `transformers` (CPU-quantized), `scikit-learn`, `statsmodels`, `radon`, `pandas`, `numpy`, `pyyaml`.  
**Storage**: Local filesystem for logs, policies, and intermediate CSVs; no external database.  
**Testing**: `pytest` for unit tests (environment shift logic, explanation validation); integration tests for the full evolution loop.  
**Target Platform**: GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, no GPU).  
**Project Type**: Research simulation pipeline / CLI tool.  
**Performance Goals**: Complete multiple evolutionary runs per condition (baseline vs. counterfactual) within the CI job time limit.; LLM inference must complete within 30s per failure (fallback to template on timeout).  
**Constraints**: Must run entirely on CPU; no access to gated datasets; all random seeds must be pinned for reproducibility.  
**Scale/Scope**: environments extended; A sufficient number of evolutionary runs total (Multiple runs × 16 envs × 2 conditions); A large number of trajectory steps simulated.

> **Deferred Values**: Exact number of evolutionary generations per run, specific LLM model name (to be selected based on CPU feasibility), and exact power calculations are determined in the research phase.

## Constitution Check

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `requirements.txt` pins versions. CI runs fresh. |
| **II. Verified Accuracy** | **PASS** | Citations to `EvoPolicyGym` (arXiv) and statistical methods will be validated by the Reference-Validator Agent **as a required CI/CD gate** before results are accepted. |
| **III. Data Hygiene** | **PASS** | Raw trajectory logs and evolved policies stored in `data/` with checksums. No in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All metrics (p-values, effect sizes) derived programmatically from `data/` CSVs, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/` YAML. |
| **VI. Counterfactual Feedback Fidelity** | **PASS** | Explanation generator uses **deterministic rule mapping** (see `code/explanation/generator.py`) + lightweight LLM; fallback to templates ensures validity. |
| **VII. Dynamic-Shift Validation Independence** | **PASS** | Test set dynamics (shift point) are fixed and unknown to the agent during evolution; evaluation uses a separate, fixed test set with a *different* shift configuration to prevent circularity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-counterfactual-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dynamic_shift_env.schema.yaml
    ├── counterfactual_explanation.schema.yaml
    └── evolution_metrics.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/
├── __init__.py
├── main.py              # Entry point for CLI
├── envs/
│   ├── __init__.py
│   ├── base_env.py      # Original EvoPolicyGym wrapper
│   └── dynamic_shift_env.py # Extended environment with shift logic
├── agents/
│   ├── __init__.py
│   ├── evolutionary_harness.py # Main evolution loop
│   └── policy_parser.py # Radon integration for complexity
├── explanation/
│   ├── __init__.py
│   ├── generator.py     # LLM + Template logic (Deterministic mapping)
│   └── validator.py     # Schema validation
├── analysis/
│   ├── __init__.py
│   └── stats.py         # Mixed-effects model & visualization
├── utils/
│   ├── config.py        # Seed management, hyperparameters
│   └── logging.py       # Structured logging
└── tests/
    ├── test_env_shift.py
    ├── test_explanation.py
    └── test_stats.py
```

**Structure Decision**: Single project structure chosen. The feature is a research pipeline tightly coupled to the existing `EvoPolicyGym` codebase, requiring direct modification of environment logic and a unified analysis script. Separating into microservices would introduce unnecessary overhead for a CPU-bound simulation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Model** | Required by FR-005 to handle nested data (runs within seeds) and control for complexity. | Simple t-test would violate statistical assumptions due to non-independence of runs within the same seed. |
| **CPU-Quantized LLM** | Required for FR-002 to generate explanations without GPU access. | Using a cloud API would introduce latency variability and cost; a synthetic "mock" generator would violate FR-002's requirement for natural language output. |
| **Template Fallback** | Required by FR-006 to prevent pipeline crashes on LLM timeout. | Running without a fallback would cause the entire evolutionary run to abort on a single generation error, wasting compute. |