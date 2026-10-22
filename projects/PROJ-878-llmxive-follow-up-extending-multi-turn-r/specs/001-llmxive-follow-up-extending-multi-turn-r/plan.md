# Implementation Plan: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Branch**: `001-llmxive-topological-limits` | **Date**: 2026-08-18 | **Spec**: `specs/001-llmxive-topological-limits/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-topological-limits/spec.md`

## Summary

This feature implements a controlled empirical study to investigate the relationship between the topological complexity of logical dependency graphs (specifically `nesting_depth` and `branching_factor`) and the convergence behavior of the Reflective Masking (RM) inference loop in Mask Diffusion Models. The plan involves: (1) generating a synthetic dataset of logical puzzles with explicit, verified topological metadata derived from directed acyclic graphs (DAGs) using a deterministic template engine and stratified orthogonalization; (2) executing the RM loop on a CPU‑only environment with a termination condition after a bounded number of turns per instance; and (3) performing survival analysis (Cox proportional hazards) and segmented regression to identify non‑linear degradation patterns and “tipping points,” explicitly handling censored data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU‑only), `transformers`, `datasets`, `networkx`, `lifelines`, `scikit-learn`, `pandas`, `numpy`, `pytest`  
**Storage**: Local filesystem (`data/` for generated JSONL, `results/` for logs)  
**Testing**: `pytest` (unit tests for graph generation, integration tests for RM loop + ILV, contract tests for schema validation)  
**Target Platform**: Linux (GitHub Actions free‑tier runner: 2 CPU cores, ~7 GB RAM, ~14 GB disk)  
**Performance Goals**: Generation of 500 instances < 30 min; RM execution on 500 instances < 6 h (CPU)  
**Constraints**: CPU‑only execution; hard turn limits (50 primary, 1000 extended); strict memory budgeting; orthogonalized topology variables  
**Scale/Scope**: Synthetic logical puzzles; pre‑trained Mask Diffusion Model (CPU‑loadable)

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | Pass | Random seeds pinned; `requirements.txt` version‑pinned |
| II. Verified Accuracy | Pass | Citations to the original RM paper and GSM8K will be validated |
| III. Data Hygiene | Pass | Checksums recorded; no in‑place modifications |
| IV. Single Source of Truth | Pass | All figures/statistics derived from `data/` files |
| V. Versioning Discipline | Pass | Content hashes recorded in `state/` |
| VI. Topological Metric Traceability | Pass | `nesting_depth` & `branching_factor` stored per instance |
| VII. Synthetic Graph Construction Integrity | Pass | Generation logs seed & parameters; DAG validity enforced |

## Project Structure

### Documentation (this feature)

```
specs/001-llmxive-topological-limits/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis_result.schema.yaml
│   ├── execution_log.schema.yaml
│   └── synthetic_puzzle.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```
projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/
├── data/
│   ├── raw/
│   │   └── synthetic_puzzles.jsonl
│   ├── processed/
│   │   └── execution_log.csv
│   └── checksums.txt
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── graph_generator.py
│   ├── rm_executor.py
│   ├── analyzer.py
│   └── utils/
│       ├── graph_utils.py
│       └── logging_utils.py
├── tests/
│   ├── test_graph_generator.py
│   ├── test_rm_executor.py
│   └── test_analyzer.py
└── results/
    └── paper_figures/
```

**Structure Decision**: A single‑project layout is sufficient; the pipeline is linear (Generate → Execute → Analyze) and does not require separate services.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Synthetic Data Generation | Controls `nesting_depth` & `branching_factor` | Real datasets lack explicit topological metadata |
| CPU‑Only Constraint | CI free‑tier has no GPU | GPU offload would break the execution budget |
| Extended Budget Run | Distinguish budget exhaustion vs. reasoning failure (FR‑008) | 50‑turn cap alone cannot separate these cases |
| Survival Analysis (Cox PH) | Properly handles right‑censored turn counts | Simple Spearman would bias estimates |
| Independent Logical Validator (ILV) | Prevents string‑matching shortcuts | String matching would invalidate topology‑convergence correlation |
| Stratified Orthogonalization | Decouples depth & branching (collinearity < 0.2) | Random generation often couples the two variables |

## Methodology

### Phase 1 – Synthetic Data Generation
1. **Graph Construction** (`graph_generator.py`): Use `networkx` to build DAGs on a target grid of (`depth`, `branching_factor`) pairs; reject samples where |Pearson r| ≥ 0.2.
2. **Deterministic Text Mapping**: A template engine converts each DAG into a formal logical statement set (e.g., “If A then B; …”). No LLM is used.
3. **Randomized Path Perturbation** (FR‑007): Choose a ground‑truth path that is *not* the longest path.
4. **Validation**: Enforce acyclicity, solvability, and orthogonality; discard invalid instances.
5. **Output**: `data/raw/synthetic_puzzles.jsonl` (JSONL, one `LogicalPuzzle` per line).

### Phase 2 – CPU‑Feasible RM Execution
1. Load the pre‑trained Mask Diffusion Model on `device="cpu"`.
2. For each puzzle, run the Reflective Masking loop:
   - Mask → Predict → Unmask → Check convergence.
   - Terminate at 50 turns (primary) or 1000 turns (extended subset).
3. **Independent Logical Validator (ILV)** parses model output into a graph, computes `path_coverage`, and declares success only if `path_coverage ≥ 0.95` **and** final state matches the ground truth.
4. **Batch Processing**: Small batches (size = 5) to stay within ~7 GB RAM.
5. **Output**: `data/processed/execution_log.csv`.

### Phase 3 – Statistical Analysis
1. **Survival Analysis** (`lifelines.CoxPHFitter`): Model time‑to‑convergence with right‑censoring; predictors = `nesting_depth`, `branching_factor`.
2. **Segmented Regression** (`pwlf` or `statsmodels` piecewise) to locate the “tipping point” depth where hazard changes.
3. **Spearman Correlation** (descriptive only) between depth and turn count.
4. **Sensitivity Analysis**: Re‑compute failure rates at thresholds 40, 50, 60 turns.
5. **Extended Budget Comparison**: Percent of 50‑turn failures that succeed by 1000 turns.
6. **Output**: `results/statistical_report.json` plus PNG figures in `results/paper_figures/`.

## Statistical Rigor & Constraints
- **Multiple‑Comparison**: Bonferroni correction applied across tests.
- **Power Analysis**: Deferred to script (`[deferred]`); N = 500 provides > 80 % power for hazard ratios > 1.5.
- **Causal Language**: Findings framed as *associational*; synthetic control of topology permits causal interpretation of structural effects only in a limited sense.
- **Measurement Validity**: Depth & branching are exact graph‑theoretic quantities; text is deterministic.
- **Collinearity**: Orthogonalization ensures |r| < 0.2; VIF will be reported.
- **Censoring**: All turn‑count analyses use survival methods.

## Compute Feasibility (CPU‑First)
- Model runs on CPU; no 8‑bit CUDA quantization required.
- Data streamed where possible; full 500‑puzzle set fits comfortably in RAM (< 2 GB).
- **GPU Escape Hatch**: If the model refuses CPU loading, we will down‑sample to N = 50 and off‑load to a free Kaggle GPU (still respecting the plan’s “real” GPU computation).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model OOM | High | Reduce batch size; stream data |
| Infinite Loop | High | Hard turn caps (50/1000) |
| Invalid Graphs | Medium | Strict validation loop, regenerate |
| No Convergence | Medium | Record as censored; survival analysis |
| High Collinearity | High | Orthogonal sampling; regenerate if |r| ≥ 0.2 |
| String‑Match Bias | High | ILV enforces logical path verification |
| Text Ambiguity | High | Deterministic template engine |

---
