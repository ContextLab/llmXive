# Implementation Plan: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

**Branch**: `001-reward-fidelity-error-recovery` | **Date**: 2026-09-08 | **Spec**: `specs/001-reward-fidelity-error-recovery/spec.md`
**Input**: Feature specification from `/specs/001-reward-fidelity-error-recovery/spec.md`

## Summary

This project extends the **AgentBench** analysis to quantify the trade-off between **reward signal fidelity** and **context pruning density**. The core hypothesis is that coarsening reward signals (e.g., from dense continuous to binary) causes pruning logic to discard "recovery-critical" context segments, leading to a non-linear drop in agent error recovery success rates. The implementation will execute a lightweight open-source agent (Qwen-1.8B or Llama-8B-int4 via `llama.cpp`) on the available benchmark tasks under varying fidelity levels, log recovery segments, and model the inflection point where fidelity loss degrades recovery capability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `llama-cpp-python` (CPU), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`  
**Storage**: Local `data/` (raw benchmark), `results/` (execution logs, CSVs), `artifacts/` (checksummed)  
**Testing**: `pytest` (unit), `contract` tests against YAML schemas  
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, GB Disk) — **CPU Only**.  
**Project Type**: Computational Research / Data Science Pipeline  
**Performance Goals**: Complete all tasks within 6 hours on CPU. If the 8B model (int4) fails to load, the system defaults to Qwen-1.5-1.8B (int4) to ensure reproducibility.  
**Constraints**: No external API keys; strict memory budget (7 GB); no synthetic data generation; no un-reproducible GPU offloads.  
**Scale/Scope**: A subset of tasks from the AgentBench `os` and `web` environments.; Multiple experimental conditions (Baseline, Binary Pruning, Dense Pruning).

> **Compute Feasibility Note**: The plan strictly adheres to CPU execution using `llama-cpp-python` with `int4` quantization. The 8B model is the primary target; if it exceeds 7 GB RAM, the system automatically switches to Qwen-1.5-1.8B (int4) which is guaranteed to fit. No GPU offload is permitted to maintain reproducibility on a fresh runner.

## Constitution Check

This plan explicitly addresses every numbered principle in the project's constitution:

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Dataset fetched via `datasets.load_dataset` (canonical HF source). `requirements.txt` pins all versions. Execution is CPU-only to ensure identical results on any fresh runner. |
| **II. Verified Accuracy** | Citations in `research.md` reference the primary source (AgentBench paper/docs). The "Verified Datasets" block is a *record* of this verification, not the source of truth itself. |
| **III. Data Hygiene** | Raw benchmark data downloaded to `data/raw/` with SHA256 checksum. Derivatives (logs, pruned contexts) written to `data/processed/` with new filenames. |
| **IV. Single Source of Truth** | All statistics in `results/` trace to specific rows in `data/processed/execution_logs.csv`. No hand-typed numbers in the final report. |
| **V. Versioning Discipline** | Content hashes for `data/` and `code/` tracked in `state/...yaml`. Artifact changes trigger `updated_at` updates. |
| **VI. Reward Fidelity Traceability** | Every log entry includes a `reward_fidelity_level` tag (e.g., "dense", "binary"). Pruning logic is hard-coded to use *only* this signal. |
| **VII. Error Recovery Grounding** | Recovery segments are identified via *independent* state-diff heuristics (not model attention). Claims of "self-correction" require a matching `recovery_segment_id` derived from natural success/failure trajectories. |

## Project Structure

### Documentation (this feature)

```text
specs/001-reward-fidelity-error-recovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── execution_log.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-1052-llmxive-follow-up-extending-long-horizon/
├── data/
│   ├── raw/                  # AgentBench (downloaded)
│   └── processed/            # Execution logs, pruned contexts, stats
├── code/
│   ├── __init__.py
│   ├── download.py           # Dataset ingestion
│   ├── agent_runner.py       # llama-cpp wrapper, context manager, fidelity logic
│   ├── analysis.py           # Cochran-Armitage test, inflection point detection
│   ├── utils/
│   │   ├── state_diff.py     # FR-007: Recovery segment identification (semantic diff)
│   │   └── pruning.py        # Pruning logic based on reward signals
│   └── tests/
│       ├── test_agent_runner.py
│       └── test_analysis.py
├── requirements.txt          # Pinned dependencies
└── README.md
```

**Structure Decision**: Single-project structure (`code/`) chosen for a research pipeline. No separate frontend/backend. Tests are co-located with source for rapid iteration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CPU-Only Execution** | GPU offload violates reproducibility on a fresh runner. | A GPU-dependent plan cannot be verified on the declared target platform (GitHub Actions Free Tier). The plan commits to a model size (B or B-int4) that fits in 7 GB RAM. |
| **Independent Heuristic (FR-007)** | Need to programmatically identify "recovery-critical" segments without circularity. | Using the model's own attention weights creates a tautology. The plan uses an *independent* semantic state-diff metric to ensure validity. |
| **AgentBench Dataset** | "Long-Horizon-Terminal-Bench" does not exist as a public dataset. | Using a non-existent dataset makes the plan infeasible. AgentBench is a verified, accessible alternative with the necessary trajectory data. |