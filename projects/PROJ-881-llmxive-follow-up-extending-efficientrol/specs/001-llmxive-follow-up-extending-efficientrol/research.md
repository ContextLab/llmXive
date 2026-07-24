# Research: llmXive Follow-up: Entropy-Guided Token Validity Prediction in RL Rollouts

## Problem Statement

Can intermediate-layer Shannon entropy in transformer models serve as a predictive signal for token validity in RL rollouts? Specifically, does a threshold in entropy values correlate with the likelihood of a token being part of the **external ground-truth solution path** in GSM8K (math) and MiniGrid (navigation) tasks?

**Critical Scientific Correction**: Validity is defined by matching the generated token against the **dataset's ground-truth answer** (external to the model), not the model's own output. This breaks the circularity of testing if entropy predicts the model's own greedy choice.

## Dataset Strategy

The study utilizes two open, programmatic datasets verified for direct download. No access-gated or synthetic data is used.

| Dataset | Purpose | Verified Source URL | Loading Strategy |
| :--- | :--- | :--- | :--- |
| **GSM8K** | Math reasoning tasks (Ground Truth) | `openai/gsm8k` (split: `test`) | `datasets.load_dataset(..., streaming=True)`; sample a representative set of examples. |
| **MiniGrid** | Navigation tasks (Ground Truth) | `minari/babyai-go-to-door` | `minari.load_dataset(...)`; sample a representative set of examples. |

**Dataset Fit Verification**:
- **GSM8K**: Contains `question` and `answer` fields. The `answer` provides the external ground-truth sequence for validity labeling.
- **MiniGrid**: Contains environment states and **external ground-truth action paths** for the `GoToDoor` task. The `minari/babyai-go-to-door` dataset provides the specific ground-truth paths required for token labeling.
- **Fit**: Both datasets provide the necessary predictor (internal model state) and outcome (validity) variables. No missing variables detected.
- **Note on "Trivial" Concern**: The `minari/babyai-go-to-door` dataset contains non-trivial navigation tasks with explicit ground-truth paths, avoiding the "trivial-taster" issue.

## Methodological Rigor

### Statistical Approach
The core analysis uses **Mixed-Effects Logistic Regression (GLMM)** (primary) and **Fixed-Effects Logistic Regression with Clustered Standard Errors** (secondary/fallback) to model the binary outcome of token validity ($Y_{ij}$) as a function of entropy ($X_{ij}$).

**Primary Model (GLMM)**:
$$ \text{logit}(P(Y_{ij}=1)) = \beta_0 + \beta_1 \cdot \text{Entropy}_{ij} + u_{0j} + \epsilon_{ij} $$
Where $u_{0j}$ is the random intercept for sequence $j$, and $\epsilon_{ij}$ is the residual error. This handles nesting without biasing standard errors.

**Secondary/Exploratory Model (Clustered SE)**:
$$ \text{logit}(P(Y_{ij}=1)) = \beta_0 + \beta_1 \cdot \text{Entropy}_{ij} + \epsilon_{ij} $$
- **Trigger**: Only if the primary GLMM fails to converge (Hessian not positive definite) or shows singular fit.
- **Fallback**: If GLMM fails, report Clustered SE results as the primary finding with explicit caveats.

**Multiple Comparison Correction**:
- **Method**: Benjamini-Hochberg (BH) procedure.
- **Application**: Applied to p-values of the entropy coefficient ($\beta_1$) across all layers/tasks to control the False Discovery Rate (FDR).
- **Verification**: The resulting FDR will be explicitly compared against the nominal alpha level (0.05) to satisfy SC-005. The output will include a boolean `fdr_verified` flag.

### Power & Sample Size
- **Target**: 500 examples per task (Total 1000).
- **Power Limitation**: With 1000 examples, the study has sufficient power to detect moderate effect sizes in the **GLMM** model. The **Clustered SE** fallback is robust even if GLMM fails.
- **Fallback**: If GLMM fails to converge, the Clustered SE results are reported as the primary finding.

### Causal & Measurement Assumptions
- **Observational**: The relationship is correlational. The model predicts validity based on internal state, but does not claim entropy *causes* validity.
- **Measurement Validity**: Entropy is calculated directly from the model's logits ($-\sum p \log p$), ensuring high measurement validity.
- **Collinearity**: Layers are highly correlated. The plan uses **Layer Index as a continuous fixed effect** (not pooled) to preserve the "decay" hypothesis while avoiding multicollinearity issues in the primary model.

## Compute Feasibility

### CPU-First Strategy
- **Data Processing**: Streaming `datasets` library ensures RAM usage stays under a manageable threshold.
- **Token Batching**: Token processing is batched in groups of a fixed size. (per FR-007) to manage memory during forward passes.
- **Example Streaming**: Dataset examples are streamed to avoid loading the full dataset into RAM.
- **Model Choice**: Primary model is `TinyLlama-1.1B` (4-bit quantized). Memory calculation: ~0.6GB (weights) + ~2GB (activations) < 7GB RAM.

### GPU Escape Hatch
- **Trigger**: If the CPU run fails with `OOM` (Out of Memory) during model loading or forward pass.
- **Configuration**: Kaggle free tier (limited VRAM).
- **Scaling**: Model loaded with `load_in_8bit=True` or `device_map="auto"`; sequences processed in smaller batches if VRAM is constrained.
- **Rationale**: This ensures the *real* computation runs on appropriate hardware without fabricating a CPU approximation for GPU-bound tasks.

## Decision Rationale

1.  **GLMM over Clustered SE**: The spec (FR-004) and research question demand handling nested data (tokens within sequences). GLMM is the statistically valid primary approach. Clustered SE is the fallback if GLMM fails to converge due to sample size limitations.
2.  **Streaming over Full Load**: The 7GB RAM limit makes loading full datasets + model states impossible. Streaming is the only viable path for real data.
3.  **Benjamini-Hochberg**: With multiple layers and tasks tested, family-wise error rate control is mandatory. BH is preferred over Bonferroni for power retention in exploratory research.
4.  **External Ground Truth**: Validity is defined by matching the dataset's answer, not the model's output. This breaks the circularity and ensures the statistical test is meaningful.
5.  **Token-Batching vs Example-Streaming**: Distinction is made between processing 50 tokens at a time for inference (to manage VRAM) and streaming examples for data loading (to manage RAM). This resolves the ambiguity in batch definitions.
