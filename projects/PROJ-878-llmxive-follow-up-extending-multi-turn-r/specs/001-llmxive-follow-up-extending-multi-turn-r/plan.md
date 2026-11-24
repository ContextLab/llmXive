# Implementation Plan: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Branch**: `001-llmxive-topological-limits` | **Date**: 2026-08-18 | **Spec**: `specs/001-llmxive-topological-limits/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-topological-limits/spec.md`

## Summary

This feature implements a controlled empirical study to investigate the relationship between the topological complexity of logical dependency graphs (specifically `nesting_depth` and `branching_factor`) and the convergence behavior of the Reflective Masking (RM) inference loop in Mask Diffusion Models. The plan involves: (1) generating a synthetic dataset of logical puzzles with explicit topological metadata derived from directed acyclic graphs (DAGs) using a deterministic template engine and orthogonalized sampling; (2) executing the RM loop on a CPU‑only environment with a termination condition after a bounded number of turns per instance; (3) performing survival analysis (Cox proportional hazards) with proportional‑hazards diagnostics, segmented regression, and sensitivity analyses to identify non‑linear degradation patterns and “tipping points,” explicitly handling censored data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU‑only), `transformers`, `datasets`, `networkx`, `lifelines`, `scikit-learn`, `pandas`, `numpy`, `pytest`  
**Storage**: Local filesystem (`data/` for generated JSONL, `results/` for logs)  
**Testing**: `pytest` (unit tests for graph generation, integration tests for RM loop + ILV, contract tests for schema validation)  
**Target Platform**: Linux (GitHub Actions free‑tier runner: a limited number of CPU cores, ~7 GB RAM, ~14 GB disk)  
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
| Control Covariates (Token Length, Lexical Complexity) | Mitigates confounds from textual difficulty (methodology‑fb092f1d) | Ignoring them would risk omitted‑variable bias |
| Proportional‑Hazards Diagnostics | Ensures Cox model assumptions hold (methodology‑ea39b345) | Ignoring could lead to miss‑specification |
| Exact‑Match Success Criterion | Required by SC‑006 (spec_coverage‑a3f4cf6b) | No measurement would violate success criteria |
| Full‑Dataset Extended Run | Avoids bias from a [deferred] subset (methodology‑c1dde97d) | Subset could misrepresent budget‑exhaustion rate |
| Divergence Metric | Required by SC‑006 (spec_coverage‑a3f4cf6b) | No measurement would cause validation failure |
| GPU Escape Hatch Removal | Respects CPU‑only policy and free‑tier limits (data_resources‑b5eb85f5) | GPU usage would be infeasible |
| Power Analysis (A Priori) | Guarantees sufficient sample size (methodology‑649189d9) | No power calculation would risk under‑powered study |

## Methodology

### Phase 1 – Synthetic Data Generation
1. **Graph Construction** (`graph_generator.py`): Use `networkx` to build DAGs on a target grid of (`depth`, `branching_factor`) pairs; reject samples where |Pearson r| ≥ 0.2 to maintain orthogonality.
2. **Deterministic Text Mapping**: A template engine creates a strict isomorphism between each DAG and a natural‑language puzzle (no LLM).
3. **Randomized Path Perturbation** (FR‑007): Select a ground‑truth path that is *not* the longest path.
4. **Additional Covariates**: Compute `token_length` (number of tokens) and `lexical_complexity` (Flesch‑Kincaid score) for each puzzle to control for textual difficulty (methodology‑fb092f1d).
5. **Validation**: Enforce acyclicity, solvability, orthogonality; discard invalid instances.
6. **Output** (`data/raw/synthetic_puzzles.jsonl`): Each JSONL record includes **all required fields** – `instance_id`, `text`, `ground_truth`, `ground_truth_path`, `nesting_depth`, `branching_factor`, `graph_structure`, `is_acyclic`, `is_solvable`, `text_generation_method`, **`target_path_id`**, **`seed`**, **`is_orthogonal`**, `token_length`, `lexical_complexity`.

### Phase 2 – CPU‑Feasible RM Execution
1. Load the pre‑trained Mask Diffusion Model on `device="cpu"`.
2. For each puzzle, run the Reflective Masking loop:
   - Mask → Predict → Unmask → Check convergence.
   - Terminate at **50 turns** (primary) or **1000 turns** (extended budget run on the **full** dataset).
3. **Independent Logical Validator (ILV)** parses model output into a graph and computes:
   - `path_coverage` (fraction of edges matched) – **diagnostic only**.
   - `exact_match` (boolean: inferred path equals ground‑truth path) – **the sole success criterion**.
   - `longest_path_divergence` (fraction of steps differing from the longest path) – recorded for SC‑006.
4. **Batch Processing**: Small batches (size = 5) to stay within ~7 GB RAM.
5. **CSV Output** (`data/processed/execution_log.csv`): Columns **exactly** matching the `execution_log` schema and include the required fields:

| Column | Description |
|--------|-------------|
| `instance_id` | FK to puzzle |
| `turns_to_converge` | Integer or `null` if censored |
| `convergence_status` | `"success"` or `"failure"` |
| `is_censored` | `true` if max‑turn limit hit |
| `limit_hit` | Duplicate of `is_censored` (schema compatibility) |
| `runtime_seconds` | Wall‑clock time |
| `path_coverage` | Diagnostic coverage (0‑1) |
| `exact_match` | `true` only if inferred path equals ground truth |
| `longest_path_divergence` | Fraction of steps differing from longest path |
| `final_token_sequence` | Model’s final output (truncated) |
| `error_message` | Error details if any |

### Phase 3 – Statistical Analysis
1. **Power Analysis (A Priori)** – Assuming a medium effect size (ρ ≈ 0.3), α = 0.05, power = 0.8 → required N ≈ 450. We generate **N = 500** to comfortably meet this target (methodology‑649189d9).
2. **Survival Analysis (Cox PH)** – models time‑to‑convergence with right‑censoring; includes **Schoenfeld residuals test** for proportional hazards. If the PH assumption fails, the pipeline **automatically falls back to an Accelerated Failure Time (AFT) model** (methodology‑ea39b345).
3. **Segmented Regression** – identifies depth breakpoint (tipping point).
4. **Spearman Correlation** – descriptive only (FR‑004).
5. **Sensitivity Analysis** – failure rates at thresholds 40, 50, 60 turns.
6. **Extended Budget Comparison** – runs the 1000‑turn analysis on the **full** 500‑instance dataset (methodology‑c1dde97d) and reports the proportion of 50‑turn failures that converge by 1000 turns (budget‑exhaustion rate).
7. **Divergence Metric Inclusion** – `longest_path_divergence` is added as a predictor in the survival model to satisfy SC‑006.
8. **Output** – `results/statistical_report.json` plus PNG figures in `results/paper_figures/`.

## Statistical Rigor & Constraints
- **Multiple‑Comparison**: Bonferroni correction applied across all hypothesis tests.
- **Power Analysis**: A priori calculation (see Phase 3) ensures N = 500 meets the required power.
- **Causal Framing**: Associational; synthetic control of topology permits limited causal inference.
- **Measurement Validity**: Depth & branching are exact graph‑theoretic quantities; token‑level covariates use standard NLP tools.
- **Collinearity**: Orthogonalization ensures |r| < 0.2; VIF will be reported.
- **Censoring**: All turn‑count analyses use survival methods; Schoenfeld residuals test proportional hazards, with AFT fallback.
- **Success Definition**: Binary success = `exact_match` = true; `path_coverage` ≥ 0.95 recorded **only** for diagnostics, not for the binary label (methodology‑79830ff7).
- **Extended Budget Run**: Executed on the **full** dataset (no subsampling) (methodology‑c1dde97d).
- **Divergence Metric**: `longest_path_divergence` recorded per execution (spec_coverage‑a3f4cf6b).

## Compute Feasibility (CPU‑First)
- Model runs on `torch` CPU backend.
- Data streamed where necessary; 500 puzzles comfortably fit in < 2 GB RAM.
- **GPU Escape Hatch**: **Removed** – all steps are guaranteed CPU‑only.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model OOM | High | Reduce `--batch-size`; stream data |
| Infinite Loop | High | Hard turn caps (50/1000) and ILV exact‑match check |
| Invalid Graphs | Medium | Strict validation loop, regenerate |
| No Convergence | Medium | Record as censored; survival analysis |
| High Collinearity | High | Orthogonal sampling; regenerate if |r| ≥ 0.2 |
| Textual Confounds | High | Record `token_length` & `lexical_complexity` as covariates |
| Proportional‑Hazards Violation | Medium | Schoenfeld test; fallback AFT model |
| False‑Positive Success | High | Require `exact_match` only for success |
| Budget‑Exhaustion Bias | Medium | Run extended budget on full dataset |
| Divergence Metric Missing | Medium | Record `longest_path_divergence` per execution |
| GPU Dependency | High | Eliminated GPU escape hatch |

---



## projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/specs/001-llmxive-follow-up-extending-multi-turn-r/research.md
# Research: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Research Question
How does the topological complexity (`nesting_depth` and `branching_factor`) of logical dependency graphs influence the convergence speed and success rate of the Reflective Masking (RM) inference loop in Mask Diffusion Models?

## Theoretical Background
The original “Multi‑Turn Reflective Masking” work demonstrates that iterative masking can elicit reasoning in diffusion models. We hypothesize a **non‑linear degradation** in performance as graph complexity increases, with a “tipping point” in depth beyond which the RM loop either fails or requires substantially more turns.

## Dataset Strategy
### Primary Data Source – Synthetic Generation (orthogonalized)
No public dataset supplies the required per‑instance topology metadata. Therefore we will generate a synthetic dataset of a sizable collection of logical puzzles with controlled `nesting_depth` (1–10) and `branching_factor` (1–5).

| Step | Description |
|------|-------------|
| **Seed Structure** | GSM8K used only as a *conceptual* inspiration; no GSM8K data is consumed. |
| **Graph Construction** | Directed Acyclic Graph (DAG) where nodes are propositions, edges are logical dependencies. `nesting_depth` = longest path length; `branching_factor` = average in‑degree of non‑root nodes. |
| **Stratified Orthogonalization** | Target grid of (depth, branch) pairs; reject samples with |Pearson r| ≥ 0.2 to keep predictors orthogonal. |
| **Deterministic Text Mapping** | Template engine creates a strict isomorphism between DAG and natural‑language puzzle (no LLM). |
| **Randomized Path Perturbation** (FR‑007) | Ground‑truth path deliberately differs from the longest path. |
| **Additional Covariates** | Compute `token_length` and `lexical_complexity` for each puzzle to control for textual difficulty (methodology‑fb092f1d). |
| **Validation** | Enforce acyclicity, unique solvable path, orthogonality before inclusion. |
| **Output** | `data/raw/synthetic_puzzles.jsonl` (JSONL). Includes `target_path_id`, `seed`, `is_orthogonal`, `token_length`, `lexical_complexity`, and all topological fields. |

*Verified Datasets (for seed only)*:  
- **GSM8K** (parquet): https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet  

No other external datasets are required; everything is generated locally.

## Methodology

### Phase 1 – Synthetic Data Generation
Implemented in `code/graph_generator.py` (see `data-model.md`). Generates DAGs, applies orthogonalization, produces deterministic text, records extra covariates, and writes JSONL.

### Phase 2 – CPU‑Feasible RM Execution
Implemented in `code/rm_executor.py`. Loads the Mask Diffusion model on CPU, runs the RM loop with hard turn limits (50 primary, 1000 extended **on the full dataset**), and validates each step with the Independent Logical Validator (ILV). **Success is defined solely by `exact_match == true`; `path_coverage` is retained only as a diagnostic metric**. Outputs `data/processed/execution_log.csv`.

### Phase 3 – Statistical Analysis
Implemented in `code/analyzer.py`:
1. **Power Analysis (A Priori)** – Assuming a medium effect size (ρ ≈ 0.3), α = 0.05, power = 0.8 → required N ≈ 450; we generate **N = 500** to meet this target (methodology‑649189d9).
2. **Survival Analysis (Cox PH)** – models time‑to‑convergence with right‑censoring; includes **Schoenfeld residuals test** for proportional hazards. If the PH assumption is violated, the pipeline **automatically falls back to an Accelerated Failure Time (AFT) model** (methodology‑ea39b345).
3. **Segmented Regression** – identifies depth breakpoint (tipping point).
4. **Spearman Correlation** – descriptive only (FR‑004).
5. **Sensitivity Analysis** – failure rates at thresholds 40, 50, 60 turns.
6. **Extended Budget Comparison** – runs the 1000‑turn analysis on the **full** 500‑instance dataset (methodology‑c1dde97d) and reports the proportion of 50‑turn failures that converge by 1000 turns (budget‑exhaustion rate).
7. **Divergence Metric** – computes `longest_path_divergence` (fraction of steps differing from the longest path) for each instance (spec_coverage‑a3f4cf6b) and includes it in the analysis.

Results written to `results/statistical_report.json` and accompanying figures.

## Statistical Rigor & Constraints
- **Multiple‑Comparison**: Bonferroni correction applied across all hypothesis tests.
- **Power Analysis**: A priori calculation (medium effect size ρ ≈ 0.3, α = 0.05, power = 0.8) yields required N ≈ 450; we generate N = 500 (methodology‑649189d9).
- **Causal Framing**: Associational; synthetic control of topology permits limited causal inference.
- **Measurement Validity**: Depth & branching are exact graph‑theoretic quantities; token‑level covariates use standard NLP metrics.
- **Collinearity**: Orthogonalization ensures |r| < 0.2; VIF will be reported.
- **Censoring**: All turn‑count analyses use survival methods; Schoenfeld residuals test proportional hazards, with AFT fallback.
- **Success Definition**: Binary success = `exact_match` = true; `path_coverage` ≥ 0.95 recorded **only** for diagnostics (methodology‑79830ff7).
- **Extended Budget Run**: Executed on the **full** dataset (no subsampling) (methodology‑c1dde97d).
- **Divergence Metric**: `longest_path_divergence` recorded for each execution (spec_coverage‑a3f4cf6b).

## Compute Feasibility (CPU‑First)
- Model runs on `torch` CPU backend.
- Data streamed where necessary; 500 puzzles comfortably fit in < 2 GB RAM.
- **GPU Escape Hatch**: **Removed** – all steps are guaranteed CPU‑only.

## Risks & Mitigations
(See Implementation Plan table.)

---


