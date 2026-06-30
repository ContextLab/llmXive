# Implementation Plan: Reproduce & Validate EffOPD On-Policy Distillation

**Branch**: `597-reproduce-effopd-validation` | **Date**: 2025-05-23 | **Spec**: `specs/597-reproduce-effopd-validation/spec.md`
**Input**: Feature specification from `/specs/597-reproduce-effopd-validation/spec.md`

## Summary

This feature validates the **mechanism** of the "Learning to Foresee: Unveiling the Unlocking Efficiency of On-Policy Distillation" (EffOPD) paper by reproducing its analysis scripts (SVD, rank concentration) and evaluation pipelines on a CPU-only, free-tier GitHub Actions runner.

**Scope & Limitations**:
1.  **Mechanism Validation**: We validate that the codebase correctly implements the generation of low-rank update matrices (Delta W) and the calculation of rank concentration metrics.
2.  **Efficiency Claim Handling**: The "3x acceleration" claim is **not** validated via empirical runtime comparison (methodologically invalid on CPU vs. GPU). Instead, we validate the *theoretical efficiency* by calculating **FLOPs/step** and comparing the **rank concentration** of the EffOPD update against a standard SFT baseline and a Random Null Baseline. A lower effective rank for the same loss reduction implies higher theoretical efficiency.
3.  **On-Policy Limitation**: Due to the use of static datasets (`gsm8k`, `aime24`), we cannot validate the dynamic "on-policy" loop. We validate the *update mechanism* (Delta W generation) as a proxy for the on-policy step.
4.  **Validation Scope**: The validation explicitly targets the *mechanism* (SVD, rank analysis) and *output format* (Pass@k) on a CPU-only, sampled dataset. Full training is excluded as it exceeds resource limits.

The approach utilizes sampled datasets, a simulated single training step to generate Delta W, and a small CPU-tractable model (`Qwen2.5-0.5B`) to ensure the reproduction mechanism, output formats, and metric definitions (Pass@k, rank concentration) are correct within the strict RAM and runtime constraints.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only build), `transformers` (CPU-compatible), `datasets`, `scikit-learn` (for SVD), `numpy`, `pandas`.  
**Storage**: Local file system (temporary artifacts in `tmp/`, final artifacts in `artifacts/`).  
**Testing**: `pytest` (unit/contract tests), shell script validation.  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU resources, limited RAM, no GPU).  
**Project Type**: Research validation pipeline / CLI tooling.  
**Performance Goals**: Complete full validation pipeline (Simulated Step, SVD, Rank, Eval) within 4 hours on sampled data; SVD on 500 samples < 45 mins.  
**Constraints**: Zero CUDA usage; memory usage < 7 GB; no 8-bit quantization libraries (`bitsandbytes`); no large model training.  
**Scale/Scope**: Sampled datasets (≤500 samples for SVD, ≤50 problems for Eval); single model inference pass; simulated single training step.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Gap Mitigation

*Note: No project-specific `constitution.md` file was supplied. Per the project's default scientific integrity principles, the following constraints are enforced as the binding constitution for this feature:*

1.  **Reproducibility (Principle I)**: The plan mandates exact version pinning of libraries and explicit sampling strategies to ensure the reproduction is deterministic and repeatable on the specified hardware.
2.  **Scientific Integrity (Principle II)**: The plan explicitly distinguishes between "mechanism validation" (what is feasible) and "full-scale performance claims" (what requires more compute), avoiding over-claiming results from a CPU-limited run. It replaces invalid runtime acceleration claims with theoretical FLOPs analysis.
3.  **Resource Honesty (Principle III)**: The plan adheres strictly to the 7 GB RAM and 6-hour runtime limits, implementing chunked processing and sample limits as required by the spec.
4.  **Data Fidelity (Principle IV)**: The plan verifies dataset variable fit (problem text, ground truth) and exact key names before execution, ensuring the validation scripts are not run on mismatched data.
5.  **Real-Call Testing (Principle V)**: All validation steps (SVD, Rank, Eval) are executed as actual code runs on the target hardware, not simulated or assumed.

## Project Structure

### Documentation (this feature)

```text
specs/597-reproduce-effopd-validation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
Analysis/
├── eval/
│   ├── svd.py           # SVD analysis script (FR-001) - runs on Delta W
│   ├── upd_rank.py      # Update rank concentration (FR-002)
│   └── reasoning_eval.py # Reasoning evaluation (FR-003)
├── utils/
│   ├── prep_data.py     # Data preparation and key mapping (FR-005)
│   ├── simulate_step.py # Simulated training step to generate Delta W (Critical)
│   └── memory_guard.py  # Memory sampling logic (FR-005)
data/
├── gsm8k/               # Sampled GSM8K data (generated)
│   └── test.jsonl
└── aime24/              # Sampled AIME24 data (generated)
    └── test.jsonl
external/
└── EffOPD/              # Vendored EffOPD code (submodule)
artifacts/
├── delta_w.pt           # Generated update matrix (Input for SVD)
├── sft_delta_w.pt       # Generated SFT baseline update matrix
├── svd_results.csv      # SVD output (SC-001)
├── upd_rank_results.csv # Rank output (SC-002)
├── reasoning_results.json # Eval output (SC-003)
└── baseline_comparison.json # Comparative metrics (SC-006)
tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline execution tests
└── unit/                # Utility function tests
```

**Structure Decision**: The structure mirrors the logical separation of the spec: `Analysis/` for the core validation scripts (matching `spec.md` paths), `data/` for the sampled inputs (root level), and `tests/` for the contract verification. This ensures the `EffOPD` submodule remains isolated while the validation logic is easily testable. The `Analysis/utils/` directory contains the critical data preparation and simulation scripts required to generate inputs for the analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The plan strictly adheres to the spec's constraints and does not introduce new architectural complexity. | N/A |

## Computational Task Ordering

To ensure feasibility and correctness, the following execution order is mandatory:

1.  **Data Preparation**: `prep_data.py` must run first to generate `data/gsm8k/test.jsonl` and `data/aime24/test.jsonl`.
2.  **Delta W Generation**: `simulate_step.py` must run on the prepared data to generate `artifacts/delta_w.pt` (EffOPD) and `artifacts/sft_delta_w.pt` (Baseline). **SVD and Rank scripts cannot run without this step.**
3.  **Analysis**: `svd.py` and `upd_rank.py` run on the generated `delta_w.pt` files.
4.  **Baseline Comparison**: `baseline_comparison.py` (or integrated logic) runs to compare the EffOPD results against the SFT and Null baselines.
5.  **Evaluation**: `reasoning_eval.py` runs on the `aime24` subset to generate `reasoning_results.json`.
6.  **Verification**: Contract tests run against all generated artifacts.

## FR/SC Coverage Map

| ID | Requirement | Plan Element |
| :--- | :--- | :--- |
| **FR-001** | Execute `svd.py` on GSM8K subset | `Analysis/eval/svd.py` (Phase 3, Input: `artifacts/delta_w.pt`) |
| **FR-002** | Execute `upd_rank.py` | `Analysis/eval/upd_rank.py` (Phase 3, Input: `artifacts/delta_w.pt`) |
| **FR-003** | Execute `reasoning_eval.py` | `Analysis/eval/reasoning_eval.py` (Phase 4) |
| **FR-004** | No CUDA dependencies | `requirements.txt` filtered; `torch` CPU-only install enforced. |
| **FR-005** | Memory guardrail (sampling) | `Analysis/utils/memory_guard.py` and `prep_data.py` enforce sample limits. |
| **SC-001** | SVD output ≥10 rows | Contract test on `svd_results.csv`. |
| **SC-002** | Concentration score [0,1] | Contract test on `upd_rank_results.csv`. |
| **SC-003** | Pass@k non-null | Contract test on `reasoning_results.json`. |
| **SC-004** | Total runtime ≤4h | Sample limits (500 for SVD, 50 for Eval) and CPU-only model. |
| **SC-005** | Zero CUDA errors | `requirements.txt` and `torch` install validation. |
| **SC-006** | **Theoretical Efficiency Validation** | **New**: Compare FLOPs and Rank Concentration against SFT/Null baselines. |