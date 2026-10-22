# Research: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Research Question
How does the topological complexity (`nesting_depth` and `branching_factor`) of logical dependency graphs influence the convergence speed and success rate of the Reflective Masking (RM) inference loop in Mask Diffusion Models?

## Theoretical Background
The original “Multi‑Turn Reflective Masking” work demonstrates that iterative masking can elicit reasoning in diffusion models. We hypothesize a **non‑linear degradation** in performance as graph complexity increases, with a “tipping point” in depth beyond which the RM loop either fails or requires substantially more turns.

## Dataset Strategy
### Primary Data Source – Synthetic Generation (orthogonalized)
No public dataset supplies the required per‑instance topology metadata. Therefore we will generate a synthetic dataset of 500 logical puzzles with controlled `nesting_depth` (1–10) and `branching_factor` (1–5).

| Step | Description |
|------|-------------|
| **Seed Structure** | GSM8K used only as a *conceptual* inspiration; no GSM8K data is consumed. |
| **Graph Construction** | Directed Acyclic Graph (DAG) where nodes are propositions, edges are logical dependencies. `nesting_depth` = longest path length; `branching_factor` = average in‑degree of non‑root nodes. |
| **Stratified Orthogonalization** | Target grid of (depth, branch) pairs; reject samples with |Pearson r| ≥ 0.2 to keep predictors orthogonal. |
| **Deterministic Text Mapping** | Template engine creates a strict isomorphism between DAG and natural‑language puzzle (no LLM). |
| **Randomized Path Perturbation** (FR‑007) | Ground‑truth path deliberately differs from the longest path. |
| **Validation** | Enforce acyclicity, unique solvable path, and orthogonality before inclusion. |
| **Output** | `data/raw/synthetic_puzzles.jsonl` (JSONL). |

*Verified Datasets (for seed only)*:  
- **GSM8K** (parquet): https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet  

No other external datasets are required; everything is generated locally.

## Methodology

### Phase 1 – Synthetic Data Generation
Implemented in `code/graph_generator.py` (see `data-model.md`). Generates DAGs, applies orthogonalization, produces deterministic text, and writes JSONL.

### Phase 2 – CPU‑Feasible RM Execution
Implemented in `code/rm_executor.py`. Loads the Mask Diffusion model on CPU, runs the RM loop with a hard turn limit (50 primary, 1000 extended), and validates each step with the Independent Logical Validator (ILV). Outputs `data/processed/execution_log.csv`.

### Phase 3 – Statistical Analysis
Implemented in `code/analyzer.py`:
1. **Survival Analysis (Cox PH)** – models time‑to‑convergence with right‑censoring.
2. **Segmented Regression** – identifies depth breakpoint (tipping point).
3. **Spearman Correlation** – descriptive only (FR‑004).
4. **Sensitivity Analysis** – failure rates at thresholds 40, 50, 60 turns.
5. **Extended Budget Comparison** – proportion of 50‑turn failures that succeed by 1000 turns.

Results written to `results/statistical_report.json` and accompanying figures.

## Statistical Rigor & Constraints
- **Multiple Comparisons**: Bonferroni correction applied.
- **Power**: `[deferred]` – script will compute post‑hoc power.
- **Causal Framing**: Associational; synthetic control of topology permits limited causal inference.
- **Measurement Validity**: Graph metrics are exact; text is deterministic.
- **Collinearity**: Enforced orthogonalization (|r| < 0.2); VIF reported.
- **Censoring**: All turn‑count analyses use survival methods.

## Compute Feasibility (CPU‑First)
- Model runs on `torch` CPU backend.
- Data streamed if necessary; 500 puzzles comfortably fit in < 2 GB RAM.
- **GPU Escape Hatch**: If CPU loading fails, we will down‑sample to 50 puzzles and run on a free Kaggle GPU (real computation, not a mock).

## Risks & Mitigations
(See Implementation Plan table.)

---
