# Research: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

## Research Question

Does an iterative, feedback-driven exploration strategy yield higher line-level coverage and ranking efficiency on ambiguous or unsolvable issues compared to the static, one-shot exploration evaluated in the original SWE-Explore benchmark?

## Background & Motivation

The original SWE-Explore benchmark evaluates static retrieval strategies for coding agents. However, real-world debugging often involves iterative refinement based on error feedback. This study extends the benchmark by:
1.  Focusing on the "long tail" of difficult issues (low initial coverage).
2.  Introducing synthetic ambiguity to test robustness.
3.  Implementing a lightweight, 8-bit quantized LLM agent that reformulates queries based on static analysis errors and **sandboxed execution feedback**.

## Verified Datasets

| Dataset | Source URL | Usage in Plan |
| :--- | :--- | :--- |
| **SWE-Explore** | https://huggingface.co/datasets/SWE-Explore-Bench/SWE-Explore-Bench/resolve/main/bench.final.public.jsonl | Primary source for "hard" instances (bottom [deferred] coverage) and ground-truth code. |

*Note: No access-gated datasets (e.g., ADNI, HCP) are used. All data is open and programmatically downloadable. The "CPU-Only Overlap" dataset was removed as it is mismatched; a local proxy is used instead.*

## Dataset Strategy

### 1. "Hard" Instance Selection
- **Method**: Download `bench.final.public.jsonl`. Filter for issues where `initial_coverage_score` is in the bottom percentile.
- **Fallback**: If `initial_coverage_score` is missing, perform a **local AST-based retrieval simulation** to compute a proxy coverage score for each issue, then filter the bottom [deferred].
- **Validation**: Generate a `validation_report.md` listing a random sample of "hard" issues and their characteristics to confirm low coverage correlates with genuine ambiguity (FR-010).
- **Integrity**: This subset is saved as `data/curated/hard_subset.jsonl` with a checksum.

### 2. Synthetic Ambiguous Issues
- **Method**: Select a representative subset of solvable tasks from the dataset. Apply deterministic mutations:
  - Variable renaming (e.g., `calculate_total` -> `calc_tot`).
  - Comment removal.
  - **Structural Obfuscation**: Reordering control flow, changing API signatures (FR-009).
- **Ground Truth Mapping**: For synthetic issues, ground-truth relevant lines are **re-mapped** from the original solution code to the mutated file using **token-based matching** (ignoring whitespace/comments) to ensure the coordinate system aligns with the mutated file (Scientific Soundness).
- **Integrity**: Saved as `data/curated/synthetic_ambiguous.jsonl`.

### 3. Data Streaming & Feasibility
- The full SWE-Explore dataset is loaded via `datasets.load_dataset(..., streaming=True)` to avoid memory spikes.
- Only the curated subsets are materialized in memory for the agent loop.

## Methodology

### A. Agent Implementation

#### Static Baseline (One-Shot)
- **Input**: Issue description + repository context.
- **Process**: Single retrieval pass using a lightweight vector search or AST-based index.
- **Execution**: **Distinct, independent execution** from the iterative agent (not just Turn 1) to avoid shared condition bias.
- **Output**: Top-k code snippets.

#### Iterative Agent (3-Turn Loop + Sweep)
- **Architecture**: CPU-quantized LLM (8-bit, e.g., Qwen-1.5-1.8B or similar) wrapped in `transformers` + `bitsandbytes` (Low-bit quantization strategy per 2110.02861).
- **Loop Logic**:
  1.  **Turn 1**: Agent retrieves initial context based on issue.
  2.  **Static Analysis & Sandbox**: Run `pylint`/`ast` **and attempt sandboxed execution** of retrieved snippets to detect runtime logic errors and missing imports.
  3.  **Feedback Filtering**: Compare detected errors against the original issue description. If an error is unrelated to the issue intent, mark as "neutral" to avoid circular optimization (Scientific Soundness).
  4.  **Feedback**: If valid errors detected, formulate new query: "Previous attempt failed due to [error_msg]. Refine search for [intent]."
  5.  **Turn 2/3**: Repeat retrieval with updated context.
  6.  **Turn Limit Sweep**: Log results for 1, 2, and 3 turns simultaneously to measure sensitivity (SC-006).
  7.  **Termination**: Stop after a limited number of turns or if solution found. **Detect repeated queries (loops) and exit early** (Edge Case handling).
- **Model Validation**: A pilot run compares 8-bit vs. full-precision (if feasible on a tiny subset) or cites literature. If 8-bit degrades reformulation quality significantly, the plan switches to a smaller, non-quantized model (e.g., TinyLlama) that fits in RAM without quantization, ensuring the strategy is not confounded by model failure.
- **Feasibility**: Low-bit quantization ensures the model fits in a constrained memory footprint suitable for resource-limited environments. A limited number of turns constrains CPU time per issue.

### B. Metric Calculation

1.  **Line-Level Coverage**: Percentage of ground-truth relevant lines found in the retrieved context.
2.  **Precision**: Relevant lines retrieved / Total lines retrieved.
3.  **Effective Coverage**: Coverage * Precision (Composite metric to balance quality).
4.  **Ranking Efficiency**: Position of the first relevant line in the retrieval list.
5.  **Statistical Test**:
    - **Primary**: Wilcoxon signed-rank test (paired differences between Independent Static vs. Iterative final results).
    - **Tie Handling**: If ties > 50% of data (substantial proportion), switch to **exact permutation test on the non-zero differences** or report the proportion of 'no improvement' cases as a primary descriptive statistic (FR-006, Methodology Rigor).
    - **Multiplicity Correction**: Bonferroni correction applied to the family of tests (Coverage, Ranking, Effective Coverage) to control Family-Wise Error Rate (SC-004).
    - **Framing**: Results reported as associational differences (FR-007).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied (SC-004).
- **Power**: Sample size is limited by the "hard" subset size (a minority portion of SWE-Explore). Power analysis is deferred to the implementation phase, but the non-parametric test is robust to small sample sizes.
- **Causal Claims**: Framed as associational (FR-007). No randomization of the "hard" subset; the "hard" status is an observed property.
- **Collinearity**: Metrics (Coverage vs. Ranking) are correlated; tests are reported separately with correction.
- **Dataset Fit**: The SWE-Explore dataset contains the necessary ground-truth lines. If the "initial coverage score" is missing, a local proxy is computed.

## Compute Feasibility Decision

- **CPU-First**: The 8-bit quantized model (Qwen/LLaMA 1.8B) is the primary choice. It runs on CPU within 7GB RAM.
- **GPU Escape Hatch**: If the 8-bit CPU inference is too slow (>6h total), the execution stage will offload to a Kaggle GPU with sufficient VRAM capacity running the *same* 8-bit model code. No synthetic CPU approximation of a GPU-only method is planned.
- **Runtime Measurement**: The pipeline logs `total_runtime_seconds` and `pass/fail` status against the 6h limit to `data/results/metrics.csv` (SC-005).
