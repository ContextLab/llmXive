# Research: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

## Problem Statement

The core research question is whether the initial semantic uncertainty (entropy) of a hidden state in an iterative refinement model predicts its convergence trajectory on complex code generation tasks. Specifically, we investigate if high initial entropy correlates with a need for more refinement loops ($k$) to reach a correct solution. This is an **observational study**; findings will be framed as **associational**, not causal. The router simulation is an **ex-post feasibility analysis** to determine if the observed correlation could theoretically be leveraged for FLOPs savings.

## Dataset Strategy

The study utilizes two primary code generation benchmarks: HumanEval and MBPP. These datasets provide the necessary ground truth (reference solutions) to determine convergence.

| Dataset | Source URL | Format | Usage |
|---------|------------|--------|-------|
| **HumanEval** | https://huggingface.co/datasets/openai/openai_humaneval/resolve/main/openai_humaneval/test-00000-of-00001.parquet | Parquet | Primary benchmark for code generation correctness. |
| **MBPP** | https://huggingface.co/datasets/google-research-datasets/mbpp/resolve/main/full/prompt-00000-of-00001.parquet | Parquet | Secondary benchmark to ensure generalizability across code styles. |
| **Model** | https://huggingface.co/codellama/CodeLlama-3b-Instruct-hf | PyTorch | **Pivot**: Replaces unverified "LoopCoder-v2". CodeLlama-Instruct is a verified open-weight model capable of iterative refinement via manual loop logic. Fits in ~6GB RAM (FP32) for 1.3b, satisfying CPU constraints for validation. |

**Dataset-variable Fit**: Both HumanEval and MBPP contain the `prompt` and `canonical_solution` fields required to compute correctness. They do not contain internal model states; these must be generated via inference. The study requires an iterative model; CodeLlama-3b is used with a manual loop implementation to satisfy this.

**Model Pivot Rationale**: The "LoopCoder-v2" checkpoint is not verified or publicly available. The plan pivots to `CodeLlama-3b-Instruct` (GPU) and `CodeLlama-1.3b-Instruct` (CPU) as verified alternatives that support iterative refinement.

## Methodology

### Phase 1: Entropy Extraction (FR-001)
For each input problem $x$:
1. Generate $N=10$ samples using the model at loop count $k=1$.
2. **Clustering**: Cluster samples by **exact code match** (string hashing) to determine semantic equivalence.
   - **Sandboxed Execution**: Generated code is executed in a `docker` container or restricted `subprocess` environment with a 5-second timeout to prevent hanging/unsafe code.
   - If execution fails or times out, the sample is treated as a unique cluster.
   - **Crucial Distinction**: Entropy is computed based on the distribution of *unique code strings* (or execution results if available, but primarily string matching to avoid circularity with ground truth correctness). If the model generates the correct solution, it is just one cluster; this does not force entropy to zero unless all 10 samples are identical.
3. Compute Shannon entropy $H = -\sum p_i \log p_i$ over cluster probabilities.
4. **Edge Cases**: If $N$ samples are identical (zero entropy), assign a minimal non-zero value $\epsilon$ or exclude (log exclusion rate).
5. **Output**: Write results to `data/processed/entropy_results.csv`. **Strict Separation**: This step does not run convergence loops.

### Phase 2: Convergence Tracking (FR-002)
For each input $x$:
1. Run iterative refinement for $k \in \{1, 2, 3\}$.
2. Record the first $k$ where the output matches the canonical solution.
3. **Non-Convergence Handling**: If no match at $k=3$, label as "non-convergence" (mapped to $k=4$ for router simulation).
4. **Output**: Write results to `data/processed/convergence_results.csv`.

### Phase 3: Correlation Analysis (FR-003)
1. Compute Spearman rank correlation ($\rho$) between initial entropy and convergence step.
2. **Statistical Validity**: Use a **permutation test** (1000 permutations) to calculate p-values, avoiding assumptions of bivariate normality required by t-test approximations.
3. Report p-value and effect size.
4. **Null Hypothesis**: $H_0: \rho = 0$ (no association).

### Phase 4: Router Simulation (FR-004, FR-006)
1. **Ex-Post Feasibility Study**: Train a logistic regression model to predict "optimal $k$" (binary: $k=1$ vs $k>1$) using entropy as the sole predictor.
   - **Label Definition**: "Optimal $k$" is $1$ if convergence occurs at $k=1$, otherwise $>1$. Non-convergence ($k=4$) is grouped into $>1$.
   - **Data Leakage Warning**: The label is derived from ground truth. This simulation tests if entropy *could* predict convergence, not if it can be deployed without ground truth. The router is **non-deployable** in a real-time setting without access to the ground truth label used for training.
 - **Out-of-Sample Validation**: The dataset is split into a training set and a held-out test set using stratified sampling. The model is trained on the [deferred] and evaluated on the [deferred] to ensure the decision boundary generalizes.
2. **Random Baseline**: Compare against a baseline that always predicts $k=1$.
3. **Statistical Test**: Use **McNemar's test** to compare the router's accuracy against the random baseline (paired data: router vs baseline on the same test set samples).
4. **FLOPs Savings**: Compare total FLOPs of the dynamic router vs. a static $k=2$ baseline.
5. **Non-Inferiority**: Perform a paired t-test (or non-inferiority test) to ensure accuracy does not drop significantly compared to static $k=2$.

### Phase 5: Robustness & Sensitivity (FR-005, SC-003, SC-004)
1. **Multiple Comparisons**: Apply Holm-Bonferroni correction to p-values if correlations are computed across difficulty strata.
2. **Sensitivity Analysis**: Sweep convergence threshold $k \in \{2, 3, 4\}$ and report variation in $\rho$.
3. **Underpowered Strata**:
   - If a stratum has $n < 50$, it is flagged as "underpowered".
   - **Dynamic Handling**: If the total sample size (e.g., N=50 for CPU validation) prevents creating strata with $n \ge 50$, the analysis will proceed on the full unstratified set or merge strata (e.g., Easy/Hard) to maintain statistical validity. The 'underpowered' flag is recorded in the output for transparency.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational. Claims will be framed as "associational" rather than causal. No randomization of model architecture occurs.
- **Multiple Comparisons**: If testing correlations across multiple difficulty strata, the Holm-Bonferroni method will be used to control the family-wise error rate.
- **Power Limitations**: The sample size is constrained by the fixed size of HumanEval and MBPP. The plan acknowledges that for fine-grained strata, power may be low. If a stratum is underpowered ($n < 50$), it will be merged or excluded, and results reported with caution. The CPU validation run (N=50) is a feasibility check; full statistical power is only available in the GPU run.
- **Collinearity**: Entropy and convergence are distinct variables. However, if multiple predictors are used in the router (e.g., entropy + prompt length), collinearity diagnostics (VIF) will be reported.
- **Measurement Validity**: Semantic entropy is computed using the standard method (Kuhn et al., 2023): $N=10$ samples, clustering by semantic equivalence (exact code match).

## Compute Feasibility

- **Hardware**:
  - **Validation Mode**: CPU-only (2 vCPU, 7GB RAM). Uses `CodeLlama-1.3b-Instruct` (FP32, ~3GB). Sample size restricted to N=50 to fit within 6 hours.
  - **Full Analysis Mode**: GPU (T4/V100, 16GB+ VRAM). Uses `CodeLlama-3b` or `7b` (FP32). Runs full dataset to satisfy SC-005.
- **Strategy**: 
  - **Model Pivot**: `LoopCoder-v2` is not verified. `CodeLlama-1.3b` (CPU) and `CodeLlama-3b/7b` (GPU) are used as verified alternatives.
  - **Sandboxing**: Code execution is restricted to prevent hanging.
  - **Parallelism**: Inference will be sequential or limited to a small number of parallel processes to avoid memory swapping on CPU.
  - **Fallback**: If `CodeLlama-1.3b` exceeds memory on CPU, the plan falls back to `CodeLlama-0.5b` (if available) or reduces sample size further.

## Decision Rationale

- **Why CodeLlama?** It is a verified, open-weight model that fits within the memory constraints of the validation environment and supports iterative refinement via manual logic.
- **Why $N=10$ samples?** This is a standard compromise between computational cost and entropy estimation accuracy (Kuhn et al.).
- **Why $k \in \{1, 2, 3\}$?** The spec limits this range. Extending to $k=4$ or higher would increase runtime linearly and may not be necessary for the "early exit" hypothesis.
- **Why Permutation Test?** It is robust for small sample sizes and discrete data, avoiding the normality assumptions of t-tests.
- **Why McNemar's Test?** It is appropriate for comparing paired nominal data (router vs. random baseline on the same samples).
- **Why 80/20 Split?** To ensure the router's decision boundary is validated on unseen data, preventing overfitting and providing a realistic estimate of performance.