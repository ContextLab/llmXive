# Implementation Plan: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

**Branch**: `579-https-arxiv-org-abs-2605-15155-repro` | **Date**: 2026-06-30 | **Spec**: `specs/579-https-arxiv-org-abs-2605-15155-repro/spec.md`
**Input**: Feature specification from `specs/579-https-arxiv-org-abs-2605-15155-repro/spec.md`

## Summary

This project reproduces the core *mechanism* of the "Self-Distilled Agentic Reinforcement Learning" (SDAR) paper (arXiv:2605.15155) within the strict constraints of a CPU-only GitHub Actions runner (CPU, sufficient RAM, 6h limit). The primary objective is **mechanism execution validation**, not statistical superiority. We verify:
1.  The SDAR training loop (gating + RL) executes without CUDA errors on a small-scale proxy model (`distilbert-base-uncased`).
2.  The SDAR gate loss term is generated and logged as specified in the paper.
3.  A comparative baseline run (SDAR vs. PPO) is executed to verify *implementation parity* (i.e., both run without crashing).

**Scope Limitation**: Due to the 6-hour CPU limit and 2-core constraint, the training horizon (a sufficient number of steps) is insufficient for policy convergence. Therefore, the statistical comparison (paired t-test) is **diagnostic only**. A non-significant result (p > 0.05) is expected and does not invalidate the reproduction; it simply reflects the lack of training convergence. The project does *not* claim that SDAR is superior to PPO, only that the SDAR mechanism is correctly implemented and runnable.

## Technical Context

**Language/Version**: Python 3.10 (compatible with ALFWorld/PyTorch CPU wheels)  
**Primary Dependencies**: `torch` (CPU-only), `ray`, `alfworld` (text-only mode fallback), `scikit-learn`, `pandas`, `pytest`, `transformers` (CPU-compatible), `distilbert-base-uncased` (proxy backbone)  
**Storage**: Local filesystem (`data/` for artifacts, `outputs/` for logs/checkpoints)  
**Testing**: `pytest` for unit tests; integration tests via shell scripts executing `train.py` and `eval.py`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Research / Reproduction Pipeline  
**Performance Goals**: Complete full pipeline (sanity + baseline comparison) within 6 hours on 2 CPU cores.  
**Constraints**: 
- **NO GPU**: All models must be forced to `device="cpu"`. 
- **Memory**: Data subsets and model sizes must fit within 7GB RAM. 
- **Time**: Hard timeout per ALFWorld task; A total job limit is established. 
- **Reproducibility**: Random seeds pinned; no synthetic data.
- **Model Size**: `distilbert-base-uncased` (80M params) used as a CPU-tractable proxy for the LLM agent.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Implementation Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `external/SDAR` submodule used. `requirements.txt` ensures dependency consistency. |
| **II. Verified Accuracy** | **PASS** | Citations to arXiv:2605.15155 and ALFWorld will be validated by Reference-Validator. No hallucinated URLs. |
| **III. Data Hygiene** | **PASS** | Raw logs from `train.py`/`eval.py` are preserved. Derived CSVs/JSONs are generated via scripts with checksums recorded in `state/`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` will trace to specific rows in `data/sdar_results.csv` generated from actual log parsing. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be checksummed. `state/projects/...yaml` updated on change via `parse_logs.py`. |
| **VI. Self-Distillation Stability** | **PASS** | Plan explicitly logs "SDAR Gate Loss", `gate_activation` boolean, and teacher update frequency. |
| **VII. Computational Constraint** | **PASS** | Plan enforces CPU-only, `distilbert` model, downsampling (A fixed number of steps per seed), and Task timeouts

The research question remains: How do task timeouts affect system reliability? The method involves simulating variable timeout durations to measure failure rates, as described in [Author et al., Year; DOI].. |

## Project Structure

### Documentation (this feature)

```text
specs/579-https-arxiv-org-abs-2605-15155-repro/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-579-https-arxiv-org-abs-2605-15155/
├── code/
│   ├── requirements.txt       # Pinned dependencies (CPU-only torch, ray, alfworld, distilbert)
│   ├── run_sanity_check.sh    # Executes Ray health check
│   ├── run_training.sh        # Executes SDAR training (10 steps)
│   ├── run_baseline.sh        # Executes PPO baseline (5 seeds)
│   ├── run_evaluation.sh      # Executes SDAR evaluation (5 tasks)
│   ├── parse_logs.py          # Parses real logs into data artifacts (updates state/)
│   ├── extract_gate_metrics.py # Extracts gate_activation and teacher_update counts
│   └── analyze_results.py     # Performs t-test on baseline results (diagnostic only)
├── data/
│   ├── raw/                   # Raw logs from SDAR/PPO execution
│   ├── processed/             # Parsed CSV/JSON artifacts
│   └── checksums.yaml         # Hashes of raw/processed data
├── outputs/
│   ├── logs/                  # Runtime logs (stdout/stderr captures)
│   └── checkpoints/           # Model checkpoints (.pt)
└── docs/
    └── reproducibility/
        └── reproducibility_report.md
```

**Structure Decision**: The project uses a single `code/` directory for all execution scripts and analysis tools, keeping the repository flat and focused on the reproduction pipeline. `external/SDAR` is treated as a vendored dependency (submodule) and not modified directly; wrappers in `code/` invoke its entry points.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Baseline Comparison (5 seeds)** | Required by FR-008/FR-009 to execute the *code path* for statistical comparison. | A single run (N=1) cannot execute the t-test logic, failing the spec requirement. |
| **Aggressive Downsampling (1000 steps)** | Required to fit 5 seeds + SDAR + PPO into 6h CPU limit. | Running full-scale training would exceed the 6h CI limit, preventing any result from being generated. |
| **Log Parsing Scripts** | Required by FR-007/SC-006 to ensure data hygiene. | Manual extraction or synthetic data generation violates the "Single Source of Truth" and "Data Hygiene" principles, leading to rejection by reviewers. |
| **Fixed Evaluation Set** | Required to ensure the paired t-test is valid (controlling for task difficulty). | Random task selection per seed would confound the results with task difficulty variance. |

## Implementation Phases

### Phase 0: Environment & Sanity Check
1.  **Setup**: Clone repo, init submodules, create virtualenv, install `requirements.txt`.
2.  **Health Check**: Execute `tests/ray_cpu/check_worker_alive/main.py`. Verify "CPUs detected", no CUDA errors.
3.  **Model Verification**: Verify `distilbert-base-uncased` loads on CPU within 7GB RAM.

### Phase 1: Mechanism Execution (Sanity Run)
1.  **Training**: Run SDAR training for a limited number of steps on a single ALFWorld task.
2.  **Logging**: Verify `train.py` outputs "SDAR Gate Loss" and `gate_activation` logs.
3.  **Checkpoint**: Verify `step_5.pt` is generated.

### Phase 2: Baseline Comparison (Diagnostic Run)
1.  **Configuration**: Set `num_steps=1000`, `seeds=0..4`, `tasks=[fixed_ids]`.
2.  **Execution**: Run SDAR and PPO baselines sequentially (to avoid memory contention).
3.  **Fallback**: If ALFWorld Thor binary fails, switch to `alfworld-text-only` or mock environment mode.
4.  **Parsing**: Run `parse_logs.py` to extract metrics and update `state/projects/...yaml`.
5.  **Analysis**: Run `analyze_results.py` to compute p-value (diagnostic only).

### Phase 3: Reporting
1.  **Reproducibility Report**: Generate `docs/reproducibility/reproducibility_report.md` citing actual log files.
2.  **Artifact Verification**: Confirm `data/processed/statistical_analysis.json` exists and contains a p-value.
3.  **State Update**: Ensure `state/projects/...yaml` reflects new artifact hashes.