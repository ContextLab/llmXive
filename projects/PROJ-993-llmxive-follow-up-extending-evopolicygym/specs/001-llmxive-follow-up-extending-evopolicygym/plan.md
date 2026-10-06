# Implementation Plan: llmXive follow-up: extending "EvoPolicyGym" with Counterfactuals

**Branch**: `001-llmxive-counterfactual-extension` | **Date**: 2026-08-05 | **Spec**: `specs/001-llmxive-counterfactual-extension/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-counterfactual-extension/spec.md`

## Summary

This feature extends the EvoPolicyGym benchmark suite to evaluate if counterfactual failure explanations improve policy robustness under dynamic environmental shifts. The plan implements:  a `DynamicShiftEnvironment` wrapper that alters reward/transition logic at [deferred] of the interaction budget across available base environments; (2) a CPU-tractable counterfactual explanation generator using a quantized LLM (e.g., TinyLlama-1.1B) with deterministic fallback to template-based natural language explanations; and (3) an evolutionary harness that compares baseline scalar-reward policies against counterfactual-feedback policies using mixed-effects models to control for code complexity.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `gymnasium`, `torch` (CPU-only), `transformers` (bitsandbytes for Low-bit quantization

The specific value to remove/generalize: 'low-bit'

Rewritten passage:
Low-bit quantization), `radon` (static analysis), `statsmodels` (mixed-effects), `pandas`, `pyyaml`, `jsonschema`  
**Storage**: Local `data/` directory for logs, CSVs, and JSON schemas; no external DB.  
**Testing**: `pytest` with fixed seeds for reproducibility; contract tests against YAML schemas.  
**Target Platform**: GitHub Actions free-tier runner (limited CPU, 7GB RAM) with a fallback mechanism to offload GPU-heavy inference to a scaled-down Kaggle kernel if `torch.cuda` is detected as required (though the plan targets CPU-first via 4-bit quantization).  
**Project Type**: Research library / CLI tool  
**Performance Goals**: Run 5 evolutionary seeds per condition within 6 hours (pilot scope); LLM inference <30s per failure (with 30s timeout fallback).  
**Constraints**: No local GPU on CI; must use -bit quantized models for LLM; strict memory limit requires streaming data or small batch sizes.  
**Scale/Scope**: Pilot study uses a representative subset of environments, conditions (baseline vs. counterfactual), Several seeds each (total multiple runs). The full 16-env study is acknowledged as a future iteration due to compute constraints.

> Empirical specifics (exact run counts, token limits) are deferred to research/implementation phases, citing the spec where applicable.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Check Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched via `gymnasium` (canonical source). |
| **II. Verified Accuracy** | ✅ PASS | Citations (e.g., 1809.08503) referenced in `idea/`; no fabricated URLs. |
| **III. Data Hygiene** | ✅ PASS | `data/` files will be checksummed; no in-place edits; `data/fallbacks.log` tracks failures. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics derived from `data/evolution_results.csv` and `data/sensitivity_report.csv`. |
| **V. Versioning** | ✅ PASS | Artifacts hashed; `state/` updated on changes. |
| **VI. Counterfactual Fidelity** | ✅ PASS | Generator uses deterministic rule mapping + LLM; fallback returns `TemplateExplanation` (text), not scalar, preserving fidelity. |
| **VII. Dynamic-Shift Independence** | ✅ PASS | **Mechanism**: The shift configuration (step N, shift type) is injected via a `DynamicShiftEnvironment` wrapper that modifies the environment's internal state *after* the step count. Crucially, the shift parameters are **not exposed** to the agent's observation space or reward function prior to the shift step, ensuring the agent cannot "memorize" the shift. |

## Contract Mapping

| Contract File | Plan Phase | Code Module | Action |
| :--- | :--- | :--- | :--- |
| `contracts/dynamic_shift_env.schema.yaml` | Phase 0 (Research) | `environments/dynamic_shift_env.py` | Defines shift config; validated at env init. |
| `contracts/explanation.schema.yaml` | Phase 2 (Implementation) | `explanation/generator.py` | Validates LLM output; ensures Rule ID presence. |
| `contracts/sensitivity_report.schema.yaml` | Phase 0 (Research) | `analysis/sensitivity_test.py` | Pre-generated schema; validates report output. |
| `contracts/evolution_results.schema.yaml` | Phase 2 (Implementation) | `analysis/statistical_test.py` | Validates final metrics before analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-counterfactual-extension/
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
├── environments/
│   ├── __init__.py
│   ├── dynamic_shift_env.py      # FR-001: Extension logic
│   └── registry.py               # FR-001: Load 16 envs (reads data/discovered_envs.json)
├── agents/
│   ├── __init__.py
│   ├── evolutionary_harness.py   # FR-003: Evolution loop
│   └── static_agent.py           # Test agent for US-1
├── explanation/
│   ├── __init__.py
│   ├── generator.py              # FR-002: LLM + Fallback
│   ├── rules_schema.py           # FR-002: Rule ID mapping
│   └── templates.py              # FR-002: Fallback templates
├── analysis/
│   ├── __init__.py
│   ├── complexity_metrics.py     # FR-004: Radon wrapper
│   └── statistical_test.py       # FR-005: Mixed-effects model
├── data/
│   ├── raw/                      # Downloaded env specs
│   ├── processed/                # Evolution results, logs
│   └── schemas/                  # Contract schemas
├── main.py                       # Entry point
└── requirements.txt
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`environments`, `agents`, `explanation`, `analysis`) to maintain isolation between the environment extension, the explanation generation, and the statistical analysis. This supports the "Producer before consumer" dependency chain required by the spec.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-effects model** | Spec (FR-005) requires controlling for nested data (runs within seeds). | Simple t-test ignores seed variance, inflating Type I error. |
| **4-bit Quantized LLM** | CPU constraints (7GB RAM) prevent full precision LLM inference. | CPU-only full precision models are too large/slow; synthetic stand-ins violate "Counterfactual Fidelity". |
| **Template Fallback (Text)** | Spec (US-2) requires *natural language* explanation even on LLM failure. | Returning a scalar reward violates the core hypothesis (counterfactuals vs. scalar). |
| **Pilot Scope (4 envs)** | Full 16-env run exceeds 6h/7GB CPU limit. | Synthetic data violates "Data Hygiene"; skipping the study is not an option. |

## Compute Feasibility & Scheduling

- **Pilot Scope**: The plan targets 4 environments (subset of 16) x 2 conditions x 5 seeds = 40 runs. The full multi-environment study is acknowledged as a future iteration.
- **CPU-First**: The LLM is run in 4-bit quantization on CPU. If this exceeds RAM limits, the plan falls back to a smaller subset of the trajectory or a simpler rule-based generator (template-only) for the "counterfactual" condition, clearly noting the deviation.
- **GPU Escape Hatch**: If the CPU run fails due to memory, the execution layer will auto-offload the LLM inference step to a Kaggle GPU kernel (scaled to available VRAM) using a 4-bit quantized model. The rest of the pipeline (evolution, analysis) remains on CPU.
- **Data Streaming**: Trajectories are streamed and processed incrementally to avoid loading full episode logs into memory.
- **Time Budget**: A series of runs estimated at several hours on CPU (including Timeout fallbacks

The research question concerns how to handle request failures within a distributed system. The method involves implementing a configurable timeout mechanism with a fallback strategy, as detailed in [Author, Year] (DOI/ArXiv). References include [Author, Year] (DOI/ArXiv).). The full study is estimated at [deferred], requiring the GPU escape hatch or distributed runs.

## Scope Limitation

This study uses a subset of representative environments as a pilot. FR-001 requires A diverse set of environments for the full study and this will be addressed in a future iteration. The count of environments is derived from `data/discovered_envs.json` (see `data-model.md`).