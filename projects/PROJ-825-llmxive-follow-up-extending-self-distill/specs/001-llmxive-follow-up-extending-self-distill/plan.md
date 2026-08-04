# Implementation Plan: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Branch**: `001-llmxive-student-only-gating` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-student-only-gating/spec.md`

## Summary

This feature implements a "Student-Only Gating" variant of Self-Distilled Agentic Reinforcement Learning (SDAR). The core hypothesis is that replacing the computationally expensive teacher-student confidence gap with a student-only heuristic (token entropy $H_t$ and retrieved context stability $S_t$) preserves ≥80% of the performance gains while reducing per-step computational cost by ≥60%. The implementation will execute training loops on ALFWorld and WebShop environments, comparing the Student-Only variant against the Baseline SDAR (dual-model) and GRPO baselines, logging detailed metrics, and performing statistical hypothesis testing (Bootstrapping on continuous metrics) to validate significance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (>=4.40.0), `datasets` (streaming support), `sentence-transformers` (quantized), `torch` (CPU-first), `scikit-learn`, `pytest`, `wandb` (optional, local logging fallback), `alfworld`, `webshop`  
**Storage**: Local filesystem (`data/` for artifacts, `data/processed/` for logs), JSON/Parquet for metrics.  
**Testing**: `pytest` (unit tests for gating logic, integration tests for training loop), statistical validation scripts.  
**Target Platform**: Linux (GitHub Actions Free Tier: vCPU, ample RAM, no GPU). GPU escape hatch: Kaggle (1x T4, ~16GB VRAM) for specific model loading if CPU fails, but the plan prioritizes quantized CPU execution.  
**Project Type**: Research / Computational Experiment  
**Performance Goals**: Training loop must complete within 6 hours per run on CPU; Student-Only variant must show >60% CPU time reduction vs. Baseline.  
**Constraints**: Memory < 7GB RAM; Disk < 14GB; No external API calls for data; Must handle noisy context gracefully.  
**Scale/Scope**: Environments (ALFWorld, WebShop); Several Variants (GRPO, Baseline SDAR, Student-Only)

The specific value to remove/generalize: 'Several'

Rewritten passage:; Independent Runs per variant.

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/config.py`. `requirements.txt` pins versions. Environments (ALFWorld/WebShop) fetched via standard pip/conda installers. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be validated against primary sources (SDAR paper, ALFWorld repo). No unverified claims in final report. |
| **III. Data Hygiene** | **PASS** | Raw environment data is immutable. Derived metrics (gating scores, rewards) written to `data/processed/` with checksums. No PII expected (synthetic agent tasks). |
| **IV. Single Source of Truth** | **PASS** | All figures in `paper/` will be generated programmatically from `data/processed/` logs. No hand-typed statistics. |
| **V. Versioning Discipline** | **PASS** | Artifacts (checkpoints, logs) will be hashed. `state/` updated on completion. |
| **VI. Computational Efficiency** | **PASS** | Plan explicitly logs CPU time/memory per step (FR-003). Success metric SC-002 (>60% reduction) is a hard gate. |
| **VII. Student-Only Heuristic Fidelity** | **PASS** | Plan includes Pearson correlation analysis (FR-007) between $g_t$ (student) and teacher-gap (baseline) on paired trajectories to validate heuristic fidelity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-self-distill/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── training_run.schema.yaml
    └── gating_signal.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/
├── __init__.py
├── config.py                 # Seeds, hyperparameters, variant flags
├── main.py                   # Entry point for training runs
├── models/
│   ├── student_model.py      # Qwen2.5-1.7B wrapper
│   └── retriever.py          # Dense retriever (quantized)
├── agents/
│   ├── base_agent.py         # RL base logic
│   ├── grpo_agent.py         # Standard GRPO baseline
│   ├── baseline_agent.py     # Dual-model SDAR (Teacher + Student)
│   └── student_only_agent.py # Student-only gating (H_t + S_t)
├── environments/
│   ├── alfworld_env.py       # ALFWorld wrapper
│   └── webshop_env.py        # WebShop wrapper
├── metrics/
│   ├── cost_profiler.py      # CPU time/memory tracking
│   └── statistical_test.py   # Bootstrapping implementation
├── utils/
│   ├── logging.py            # JSON/CSV logging
│   └── gating.py             # Gating function implementation
└── tests/
    ├── test_gating.py
    └── test_training_loop.py
```

**Structure Decision**: Single project structure under `code/` to ensure tight integration of the training loop, environment wrappers, and metric collection. This minimizes overhead and simplifies dependency management for the constrained CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three Variants (GRPO, Baseline, Student-Only)** | Required to compute performance retention (SC-001) which relies on the GRPO baseline as a reference point. | Running only Student-Only and Baseline would leave the "performance improvement over GRPO" metric uncalculable. |
| **Bootstrapping Analysis** | Required for SC-003 (significance) due to low N=5 and non-normal distribution of RL success rates. | Relying on Mann-Whitney U on binary data with N=5 provides insufficient power (<0.2) to detect anything but massive effects. |
| **Quantized Retriever** | Required to fit dense retrieval within 7GB RAM on CPU. | Full precision retriever would exceed memory constraints on the free-tier runner, causing OOM. |

## Phased Implementation Plan

### Phase 0: Research & Dataset Verification
*Goal: Verify data sources, finalize heuristics, and validate compute feasibility.*

1.  **FR-002 / US-1**: Verify ALFWorld and WebShop environments are available via `pip` or `git` cloning without external credentials. Confirm Qwen2.5-1.7B is downloadable via Hugging Face `transformers` (CPU-quantized).
2.  **FR-001 / US-1**: Define the mathematical formulation for $S_t$ (retrieved context stability) using cosine similarity of retrieved chunks. Confirm `sentence-transformers` (all-MiniLM-L-v2 quantized) fits in RAM.
3.  **FR-005 / US-3**: Design the Bootstrapping pipeline for continuous metrics (cumulative reward). Determine sample size and acknowledge power limitations.
4.  **Constitution Check**: Re-verify that no new constraints (e.g., specific GPU models) are introduced.

### Phase 1: Data Model & Contracts
*Goal: Define schemas for inputs, outputs, and metrics.*

1.  **FR-001 / Data Model**: Define `GatingSignal` schema (entropy, stability, final score).
2.  **FR-003 / US-3**: Define `TrainingRun` schema (step metrics, cost, reward).
3.  **FR-004 / US-2**: Define artifact storage format (JSONL/Parquet) for cross-variant comparison, including `paired_trajectory_id`.
4.  **FR-006 / US-1**: Define error handling for NaN/Inf in gating scores.

### Phase 2: Implementation (Core Logic)
*Goal: Implement the gating mechanism and training loop.*

1.  **FR-001**: Implement `student_only_agent.py`. Calculate $H_t$ (token entropy) and $S_t$ (context stability). Apply sigmoid gating $g_t = \sigma(\alpha H_t + \beta S_t)$.
2.  **FR-002**: Implement `baseline_agent.py` (dual-model, same architecture for Teacher/Student) and `grpo_agent.py`.
3.  **FR-003**: Integrate `cost_profiler.py` to log CPU time and RSS memory per step.
4.  **FR-006**: Add robustness checks for $S_t \approx 0$ (noisy context) and ensure $g_t$ remains bounded.

### Phase 3: Execution & Analysis
*Goal: Run experiments and generate results.*

1.  **FR-002**: Execute 5 independent runs for **GRPO**, 5 for **Baseline SDAR**, and 5 for **Student-Only** on ALFWorld (then WebShop).
    *   *Early Stopping Protocol*: Runs terminate immediately upon reaching a predefined reward threshold OR after a fixed step cap to ensure full episodes and fit the 6-hour CI limit.
2.  **FR-007 / Constitution VII**: **Paired Trajectory Replay**: Save trajectories from Baseline runs. Replay them through the Student-Only agent to compute Student-Only scores on the *exact same* states, enabling valid Pearson correlation analysis against the Baseline Teacher-Student gaps.
3.  **FR-004**: Persist all logs to `data/processed/`.
4.  **FR-005**: Run Bootstrapping on continuous cumulative reward distributions to generate confidence intervals and effect sizes (Cohen's d). Calculate p-values for binary success rates as a secondary metric.
5.  **FR-007**: Compute Pearson correlation between Student-Only scores and Baseline Teacher-Student gaps on the paired trajectories.

### Phase 4: Reporting
*Goal: Generate final artifacts.*

1.  **SC-001**: Calculate performance retention % (Student-Only vs. Baseline vs. GRPO).
2.  **SC-002**: Calculate cost reduction % (CPU time).
3.  **SC-003**: Report significance (p < 0.05) and effect sizes with power analysis caveats.
4.  **SC-004**: Report convergence speed (steps to 0.8 reward).

## Compute Feasibility Strategy

- **CPU-First**: The plan relies on `torch` CPU execution with `bitsandbytes` 8-bit quantization for the Qwen2.5-1.7B model. The environment (ALFWorld/WebShop) is lightweight (text-based).
- **Memory Management**: The dense retriever will use a small, quantized model (`all-MiniLM-L-v` ~80MB) to ensure the total footprint stays under 7GB RAM.
- **GPU Escape Hatch**: If the Qwen model fails to load on CPU (OOM), the execution stage will auto-offload to Kaggle. The plan will use `device="cuda"` and `load_in_8bit` in that specific path, but the primary design is for CPU.
- **Time Limit**: Multiple runs will be conducted (GRPO, Baseline, and Student-Only configurations). Each run is capped at a predetermined time limit. The plan includes an **Early Stopping Protocol** (stop at 0.8 reward) to ensure average runtime fits the budget and data is not censored.

## Risk Mitigation

- **Risk**: Student entropy is high even for correct tokens (false negatives).
  - *Mitigation*: The gating formula includes $S_t$ (context stability) as a corrective term. If context is stable, $g_t$ increases even if entropy is moderate.
- **Risk**: Noisy context causes $S_t \approx 0$, breaking the gate.
  - *Mitigation*: FR-006 ensures fallback to entropy-only logic and bounds $g_t$ to prevent NaN.
- **Risk**: Memory OOM on CI.
  - *Mitigation*: Stream environment data; use quantized models; limit context window size.
- **Risk**: Low Statistical Power (N=5).
  - *Mitigation*: Use bootstrapping on continuous metrics (cumulative reward) rather than binary success rates. Report effect sizes (Cohen's d) to contextualize findings.