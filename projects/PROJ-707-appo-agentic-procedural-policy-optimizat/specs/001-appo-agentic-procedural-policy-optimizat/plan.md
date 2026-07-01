# Implementation Plan: APPO: Agentic Procedural Policy Optimization

**Branch**: `001-appo-branching-score` | **Date**: 2026-06-18 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-appo-branching-score/spec.md`

## Summary

This project implements and evaluates the **Agentic Procedural Policy Optimization (APPO)** algorithm, specifically investigating the impact of a **Branching Score** heuristic on sample efficiency. The Branching Score is defined as the product of token-level entropy and a pre-trained, frozen future-value estimate. The system will compare the `Score-Default` variant against a `No-Score` baseline (standard PPO) on the **MATH** and **Tool-Calling** benchmarks (proxies for HotpotQA/WebShop due to URL verification constraints) to measure **"steps-to-threshold"** (environment interactions required to reach [deferred] of the best pilot success rate). The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners, requiring careful optimization of model loading (4-bit quantization), data sampling, and training loop efficiency.

**Critical Constraint**: The spec assumes a multi-core/high-memory runner, but the CI environment is a lower-configuration runner with reduced CPU cores and RAM. To ensure feasibility, the plan explicitly reduces the seed count (3 for baseline/default, 1 for ablation) and model size (TinyLlama 1.1B proxy) to fit within the 6-hour job limit.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU wheel), `transformers`, `llama-cpp-python` (for CPU quantization), `trl`, `datasets`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`.  
**Storage**: Local filesystem (`data/`, `results/`); HuggingFace Hub for model/dataset caching.  
**Testing**: `pytest` (unit tests for score calculation, integration tests for training loop).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Research/Algorithmic Benchmarking.  
**Performance Goals**: Complete 3 seeds (No-Score) + 3 seeds (Score-Default) + 12 seeds (Ablation, 1 each) within 6 hours of wall-clock time on a 2-core/7GB RAM runner.  
**Constraints**: No GPU; Max moderate RAM; Max 14GB disk; No 8-bit/4-bit quantization requiring CUDA kernels; Max 2M steps per run.  
**Scale/Scope**: ~B parameters (TinyLlama 1.1B quantized) × 18 training runs; ~50k episodes total.

> **Model Feasibility Note**: The spec's target of a "Llama large-parameter 4-bit" model is infeasible on a 7GB RAM runner with context and overhead.. The plan **explicitly targets TinyLlama 1.1B (4-bit)** as the primary executable model. This is a documented deviation from the spec's model choice to ensure CI feasibility.

## Constitution Check

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Partially Met / Deviation** | Seeds pinned, but reduced from multiple to a baseline/default and further reduced for ablation due to hardware constraints. |
| **II. Verified Accuracy** | **Met** | Dataset URLs verified against the `# Verified datasets` block. No external URLs invented. |
| **III. Data Hygiene** | **Met** | Raw data downloaded to `data/raw/` with checksums. Processed data (logs) written to `data/processed/` with new filenames. |
| **IV. Single Source of Truth** | **Met** | All metrics (steps-to-threshold, tool calls) derived from `results/training_logs/` CSVs. |
| **V. Versioning** | **Met** | Artifacts tracked via content hashes in `state/`. |
| **VI. Sample-Efficiency Transparency** | **Met** | "Steps-to-threshold" calculated via interpolation. Threshold defined as a high percentage of `No-Score` max pilot score (derived from 3 seeds). |
| **VII. Benchmark & Tool-Call Integrity** | **Partially Met / Deviation** | WebShop/HotpotQA excluded due to missing verified URLs. **Tool-Calling dataset** used as a proxy for agentic behavior. |

## Project Structure

### Documentation (this feature)

```text
specs/001-appo-agentic-procedural-policy-optimizat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── training_log.schema.yaml
```

### Source Code (repository root)

```text
code/
├── config/
│   ├── base.yaml        # Base hyperparameters
│   ├── ablation_grid.yaml # Grid for FR-003
│   └── seeds.yaml       # Seed list
├── data/
│   ├── raw/             # Downloaded datasets (cached)
│   └── processed/       # Preprocessed batches, logs
├── models/
│   ├── loader.py        # CPU-safe model loading (GGUF/Quantized)
│   └── branching_score.py # Implementation of FR-001
├── training/
│   ├── loop.py          # Main PPO loop with APPO logic
│   ├── ablation_runner.py # Orchestrator for FR-003
│   └── utils.py         # Logging, interpolation
├── analysis/
│   ├── stats.py         # Wilcoxon tests (FR-007)
│   └── report_gen.py    # Report generation (FR-008)
├── benchmarks/
│   ├── tool_calling.py  # Tool-Calling environment wrapper
│   └── math.py          # MATH wrapper
├── tests/
│   ├── unit/
│   │   └── test_branching_score.py
│   └── integration/
│       └── test_training_loop.py
└── requirements.txt

results/
├── logs/                # Per-run JSON/CSV logs
├── stats/               # Statistical test outputs
└── report.md            # Final aggregated report
```

**Structure Decision**: Monolithic Python project under `code/`. Separation of concerns between `training` (logic), `benchmarks` (envs), and `analysis` (stats) ensures modularity. `config/` allows easy grid search without code changes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Ablation Grid (12 configs)** | Required by FR-003 to map sensitivity (SC-002). | Testing only 1 config fails to address the "lack of systematic evaluation" in the spec. |
| **Multiple Benchmarks** | Required by spec to ensure generalizability. | Single benchmark (e.g., MATH) risks overfitting to specific task dynamics. |
| **CPU-Only Constraint** | Mandatory for CI feasibility (7GB RAM). | GPU training is impossible on free-tier runners; 8-bit quantization often requires CUDA kernels. |
| **Seed Reduction** | Mandatory for CI feasibility (6h limit). | Multiple seeds per variant would exceed runtime budget on 2-core CPU. |

## Phase Plan

### Phase 0: Research & Feasibility
*   **Goal**: Confirm dataset availability, model feasibility, and define the Frozen Value Network (FVN) signal.
*   **Research Task**: Select the executable proxy model (TinyLlama 1.1B) and define the FVN training signal (Tool-Success Heuristic).
*   **Implementation Task**: Define the `BranchingScoreConfig` and `TrainingRun` schemas (pre-implementation).
*   **Output**: `research.md`, `data-model.md`.

### Phase 1: Data & Contracts
*   **Goal**: Establish data schemas and download mechanisms.
*   **Task**: Implement `BranchingScoreConfig` and `TrainingRun` schemas.
*   **Task**: Define `StatisticalResult` schema (FR-007/008 data model only).
*   **Output**: `contracts/*.schema.yaml`, `quickstart.md`.

### Phase 2: Implementation (Code Generation)
*   **Goal**: Generate code for training loop, ablation runner, and analysis.
*   **FR-001**: Implement `branching_score.py` with FVN integration.
*   **FR-002**: Implement `No-Score` and `Score-Default` configs.
*   **FR-003**: Implement `ablation_runner.py` (12 runs, 1 seed each).
*   **FR-004/005**: Implement logging and threshold detection (80% of 3-seed pilot).
*   **FR-006**: Implement seed loop (3 seeds for baseline/default, 1 for ablation).
*   **FR-007/008**: Implement `stats.py` and `report_gen.py`.
*   **Output**: `code/` directory.

### Phase 3: Execution & Validation
*   **Goal**: Run experiments and validate results.
* **FR-004**: Verify "threshold-not-reached" handling (fallback to [deferred] oracle).
*   **FR-007**: Verify p-values and CIs (acknowledge low power).
*   **FR-008**: Generate final report.
*   **Output**: `results/`, `paper/`.

## Risk Mitigation

1.  **RAM Overflow (1.1B Model)**:
    *   *Mitigation*: Use `llama-cpp-python` with `q4_0` GGUF. If RAM < 2GB, fallback to a 0.5B model (TinyLlama-0.5B) and note this limitation.
2.  **Runtime > 6h**:
    *   *Mitigation*: Aggressive sampling of benchmarks (e.g., first k samples of Tool-Calling). Limit max steps to a sufficiently large number to ensure convergence.
3.  **Dataset Missing Variables**:
    *   *Mitigation*: Verify "tool call" capability in Tool-Calling dataset. If missing, redefine metric as "tokens generated" (documented in `research.md`).
4.  **Threshold Undefined**:
    *   *Mitigation*: If No-Score baseline fails to reach a stable rate, threshold defaults to a proportion of the max possible score (oracle fallback).

## Assumptions

- The TinyLlama model (quantized to 4-bit, ggml-compatible) is available on the HuggingFace Hub and can be loaded and run on a 2-core CPU environment with 7GB RAM.
- The MATH (`math`) and Tool-Calling (`Mustafaege/qwen3.5-toolcalling-v2`) benchmarks are accessible via the HuggingFace `datasets` library and fit within the 14 GB disk limit.
- The "maximum pilot score" is defined as the highest success rate achieved by the `No-Score` baseline across its **3 seeds** in a preliminary run.
- The total runtime for the full experimental suite (multiple runs) is estimated at [deferred] on the specified hardware.
- The "future-value estimate" component is a frozen network trained on a distinct reward signal (Tool-Success Heuristic) derived from ground-truth labels.
- The statistical power of 3 seeds is considered adequate for an **exploratory** study, with results reported as effect sizes rather than strict significance.
- The "steps-to-threshold" metric is the primary measure of sample efficiency, not "episodes-to-threshold".