# Research: Assessing Energy Consumption of LLM Inference for Code Completion

## 1. Research Question & Hypotheses

**Primary Question**: What is the observed relationship between model parameter count and energy consumption per token during inference on the HumanEval benchmark?

**Hypotheses**:
1. **H1 (Descriptive Trend)**: Larger models are observed to exhibit higher energy-per-token (Joules/token) compared to smaller models. *Note: This is a descriptive observation, not a statistical inference.*
2. **H2 (Trade-off)**: There exists an observed trade-off where increased accuracy (pass@1) comes at a higher energy cost.

**Statistical Framework**:
- **Null Hypothesis (H0)**: There is no difference in mean energy-per-token across GPT-2-small, CodeBERT, and StarCoder-1B.
- **Alternative Hypothesis (H1)**: At least one model's mean energy-per-token differs significantly from the others.
- **Analysis Method**: Repeated-Measures ANOVA (blocking by `problem_id`) followed by Tukey HSD for pairwise comparisons. Linear regression is performed **only as a descriptive tool** to visualize the scaling trend, with no p-values or confidence intervals reported for the slope due to N=3.

## 2. Dataset Strategy

### 2.1 Primary Benchmark: HumanEval
The HumanEval dataset is the standard benchmark for code generation. It consists of a set of programming problems with a function signature, docstring, and body, and a set of unit tests.

- **Source**: Verified via HuggingFace `openai/openai_humaneval`.
- **Verified URL**: `
- **Loading Strategy**: The system will load this parquet file using `pandas` or `datasets` library. No modification of raw data; it is stored in `data/raw/humaneval.parquet`.
- **Variable Fit**: The dataset provides `task_id` and `prompt` (code signature + docstring). The model must generate the completion. This matches the requirement for code completion inference.

### 2.2 Model Sources
The three models are selected based on architecture diversity and size, ensuring they fit the 7GB RAM constraint:
1. **GPT-2-small**: ~117M parameters. Baseline.
2. **CodeBERT**: ~125M parameters. Transformer-based, trained on code.
3. **StarCoder-1B**: ~1.3B parameters. *Revised from StarCoder-base (B) to ensure feasibility on CPU-only 7GB RAM.*
 - *Feasibility Confirmation*: The model fits comfortably within the 7GB RAM limit in FP32/FP16, allowing the experiment to proceed without OOM errors that would invalidate the ANOVA design.
 - *Decision*: `bigcode/starcoder-1b` is the definitive target. No fallback logic is required for the primary run.

### 2.3 Energy Instrumentation
- **Library**: `codecarbon`
- **Configuration**: CPU-only mode.
- **Calibration**: A **CPU-bound load loop** (e.g., repeated numpy array operations with memory access patterns similar to inference) will be run at startup to verify `codecarbon` detects power draw. If deviation > 10% from theoretical, the run halts (FR-010). *Note: Matrix multiplication was rejected as it does not simulate the memory-bound nature of Transformer inference.*

## 3. Statistical Methodology & Rigor

### 3.1 Repeated-Measures ANOVA
- **Factor**: Model ID (3 levels: GPT-2, CodeBERT, StarCoder-1B).
- **Blocking Factor**: `problem_id` (164 levels).
- **Rationale**: Since every model attempts the exact same 164 problems, the variance due to problem difficulty is removed from the error term, increasing statistical power.
- **Assumption Check**: Sphericity (Mauchly's test). If violated, Greenhouse-Geisser correction will be applied.
- **Missing Data Strategy**: **Listwise Deletion**. Any `problem_id` where any model fails (OOM, timeout, or null energy) will be excluded from the ANOVA. This ensures the complete data matrix required for the test, preventing bias from unbalanced data.

### 3.2 Post-Hoc Analysis
- **Method**: Tukey HSD (Honestly Significant Difference).
- **Purpose**: To identify which specific pairs of models differ (e.g., GPT-2 vs. StarCoder-1B).
- **Correction**: Family-wise error rate controlled at α=0.05.

### 3.3 Linear Regression (Descriptive Only)
- **X**: Parameter Count (log-scale).
- **Y**: Mean Energy per Token.
- **Constraint**: N=3 data points (one per model).
- **Interpretation**: The slope will be reported as a **descriptive trend** only. No p-values for the regression slope will be claimed as significant inference due to N=3 (0 degrees of freedom for error). This adheres to FR-008 (associational framing) and corrects the statistical impossibility of testing a trend with 3 points.

### 3.4 Sensitivity Analysis
- **Method**: **Bootstrap Resampling** of the problem-level residuals (1000 iterations).
- **Purpose**: To assess the robustness of the ANOVA F-statistic and p-value against the variability in the data, rather than arbitrary perturbation of the dependent variable.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, ~ GB RAM).
- **Memory Management**: Models are loaded sequentially. `torch.cuda.empty_cache` (if applicable) and `del model; gc.collect()` are mandatory between runs.
- **Model Fit**: StarCoder-1B (1.3B) is confirmed to fit within 7GB RAM. This resolves the previous hardware mismatch.

## 5. Dataset Variable Fit Check

| Required Variable | Source Dataset | Availability | Notes |
|-------------------|----------------|--------------|-------|
| `task_id` | HumanEval (parquet) | **YES** | Unique identifier for each problem. |
| `prompt` | HumanEval (parquet) | **YES** | The code signature/docstring to complete. |
| `canonical_solution` | HumanEval (parquet) | **YES** | Used for `pass@1` evaluation. |
| `test` | HumanEval (parquet) | **YES** | The unit tests for evaluation. |
| `energy_kwh` | `codecarbon` (Runtime) | **YES** | Measured, not from dataset. |
| `tokens_generated` | `transformers` (Runtime) | **YES** | Measured, not from dataset. |

*Conclusion*: The HumanEval dataset provides all necessary static inputs. Dynamic metrics are measured at runtime. The model selection (StarCoder-1B) ensures all variables can be observed for all models.