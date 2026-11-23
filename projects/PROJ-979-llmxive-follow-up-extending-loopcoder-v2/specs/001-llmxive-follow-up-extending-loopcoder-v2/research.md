# Research: llmXive follow-up: extending "LoopCoder-v2"

## Dataset Strategy

| Dataset | Source URL (Verified) | Loader Strategy | Variables Used |
|:--- |:--- |:--- |:--- |
| **HumanEval** | ` | `datasets.load_dataset("parquet", data_files=...)` | `prompt`, `canonical_solution`, `test` (for execution) |
| **MBPP** | ` | `datasets.load_dataset("parquet", data_files=...)` | `text`, `code`, `test_list` (for execution) |
| **CodeLlama** | ` | Reference only (Model weights via `transformers`) | Model checkpoint: `meta-llama/CodeLlama-7b-Instruct-hf` |

**Dataset Rationale**:
- **HumanEval/MBPP**: These are the standard benchmarks for code generation. They provide the necessary `prompt` (input) and `canonical_solution`/`test` (ground truth) to compute convergence trajectories.
- **CodeLlama-7b**: Selected as the target model for iterative refinement. The 7B size balances capability with feasibility on a single T4/V100 GPU (Kaggle).
- **Variable Fit**: Both datasets contain the exact variables needed: `prompt` for entropy extraction, `canonical_solution` or `test` for convergence verification. No required variables are missing.
- **Feasibility**: Both are open, directly downloadable via HuggingFace `parquet` files, and fit within the CI runner's memory when streamed or processed in batches.

## Methodology & Statistical Rigor

### 1. Semantic Entropy Extraction (FR-001)
- **Method**: For each input $x$, generate $N=10$ samples using the model at temperature $T=0.8$.
- **Clustering**: Cluster samples by semantic equivalence.
 - **Implementation**: Parse code to AST. Normalize AST using `ast.unparse` with a standardized variable naming scheme. Compute a hash of the normalized AST using `hashlib.sha256`. Group samples by identical AST hashes.
 - **Correction**: The spec requires clustering on *unseen* inputs. We will use the `test` suite execution results *only* for convergence, not for clustering. Clustering relies solely on AST normalization of the generated code.
- **Entropy Calculation**: $H = -\sum p_i \log p_i$, where $p_i$ is the proportion of samples in cluster $i$.
- **Edge Case**: If all samples have identical AST (deterministic), assign minimal entropy $\epsilon = 10^{-9}$ or exclude the sample, documenting the exclusion rate (See **FR-007**).

### 2. Convergence Trajectory (FR-002, FR-003)
- **Execution**: Run iterative refinement for a range of iterations.
 - $k=1$: Single pass.
 - $k=2, 3$: Feed previous output + prompt back into the model.
- **Convergence Definition**: First $k$ where the generated code passes all unit tests in the benchmark's `test` suite.
- **Censored Data**: If no solution passes at $k=3$, mark as censored at $k=3$.
- **Analysis**: Use **Kaplan-Meier Estimator** to compute survival curves (probability of *not* converging by step $k$). Compute **Spearman's $\rho$** between initial entropy and the *median survival time* (or use a Cox proportional hazards model if covariates are added).

### 3. Dynamic Router Simulation (FR-004, FR-006)
- **Model**: **Ordinal Logistic Regression** to predict optimal loop count $k \in \{1, 2, 3\}$.
- **Training**: 5-fold cross-validation on the dataset.
- **Baselines**:
 - **Random Baseline**: Predict $k=1$ for all samples (or uniform random).
 - **Static Baseline (k=2)**: Always predict $k=2$. This is the realistic deployment target for the non-inferiority test.
 - **Oracle Baseline**: Knows the true optimal $k$ (used **only** to calculate theoretical maximum FLOPs savings, NOT for statistical non-inferiority testing).
- **Metrics**:
 - **Accuracy**: Classification accuracy of predicting the optimal $k$.
 - **FLOPs Savings**: $(\text{Static } k_{avg} - \text{Router } k_{avg}) \times \text{FLOPs per step}$. The "Static $k_{avg}$" for the *savings calculation* can be compared against the Oracle's theoretical minimum, but the *statistical test* is against the Static k=2 baseline.
 - **Non-Inferiority**: One-sided t-test or equivalence test (equivalence margin $\delta = 0.05$) comparing Router Accuracy vs **Static k=2** baseline accuracy. The Oracle is excluded from this statistical test as it represents a theoretical upper bound, not a deployable baseline.

### 4. Robustness & Sensitivity (FR-005, FR-007)
- **Multiple Comparisons**: Apply **Holm-Bonferroni** correction to p-values from strata-specific correlations.
- **Sensitivity**: Sweep convergence threshold $k \in \{, 3, 4\}$ (if data permits) and report variation in $\rho$.
- **Strata**: Define difficulty strata based on baseline pass@1 rates from literature (fixed a priori). Use **Hierarchical Mixed-Effects Models** for small strata ($<50$ samples) to borrow strength across groups.

## Compute Feasibility & GPU Strategy

- **CPU vs. GPU**:
 - **CPU**: Infeasible for CodeLlama-7b inference at the required scale ($N=164 \times 10 \times 3 \approx 5000$ forward passes).
 - **GPU**: Required. We will use the **Kaggle GPU escape hatch**.
- **Scaling**:
 - **Batching**: Process inputs in batches sized to fit VRAM.
 - **Precision**: Use `float16` or `bfloat16` to reduce memory footprint.
 - **Streaming**: If dataset size exceeds memory, stream batches from HuggingFace.
- **Runtime Estimate**:
 - Large-scale model inference: approximately a few seconds per sample (with batching).
 - Total samples: several thousand.
 - Total time: within Kaggle's time limit.

## Statistical Power & Limitations

- **Power Analysis**:
 - **Sample Size**: HumanEval ($N=164$) + MBPP (subset). Total $N \approx 400-500$.
 - **Effect Size**: Target MDES $\rho = 0.2$ (small-to-medium).
 - **Power**: With $N=400$, power to detect $\rho=0.2$ at $\alpha=0.05$ is $\approx 0.85$.
 - **Limitation**: If the true effect is smaller ($\rho < 0.1$), the study will be underpowered. This will be explicitly stated.
- **Causal Claims**:
 - **Observational**: No random assignment of architecture. All findings regarding the relationship between entropy and convergence will be framed as associational, not causal.
 - **Collinearity**: Entropy and convergence are distinct; however, if predictors are highly correlated, collinearity diagnostics (VIF) will be reported.