# Research: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Research Question
Does intermediate-layer Shannon entropy in transformer models serve as a reliable predictor of token validity (match with external ground truth) during autoregressive generation on GSM8K and MiniGrid tasks, and can an optimal entropy threshold be identified to balance computation skipping with accuracy?

## Dataset Strategy

| Dataset | Source / URL | Usage | Validation Strategy |
|:--- |:--- |:--- |:--- |
| **GSM8K** | https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet | Math reasoning tasks; ground-truth answers used to label token validity. | Verify schema contains `question` and `answer`; sample a representative subset of examples; check for non-empty answers. |
| **MiniGrid** | | Navigation tasks; ground-truth action sequences used to label token validity. | Verify schema contains `actions` and `observations`; load subset; check for valid action sequences. |
| **CPU-tractable Model** | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Small, open-weight model loaded via `transformers` on CPU. | Confirmed to run on CPU within 7GB RAM for 512-token sequences with intermediate hooks; used for both generation and entropy extraction. |

*Note: The MiniGrid URL now points to a specific Minari dataset containing actual trajectory data, not a metadata file. The model URL is a specific, verified source to ensure compute feasibility.*

## Methodology

### Phase 1: Single-Pass Generation & Labeling (US-1 & US-2)
1. **Download**: Fetch GSM8K and MiniGrid subsets (A balanced set of examples, with a comparable number of instances for each category, will be utilized.) using `datasets` library.
2. **Single-Pass Generation**: Run a full autoregressive forward pass on the **TinyLlama-1.1B** model with temperature=0.0.
 * **Simultaneous Capture**: During the forward pass, hooks capture the probability distribution at every intermediate transformer layer for every generated token.
 * **External Validity Labeling**: Tokens are labeled as "valid" (1) or "invalid" (0) by comparing the generated token against the **external ground truth** (GSM8K answer string, MiniGrid action sequence).
 * **GSM8K**: Token-level match against the solution string.
 * **MiniGrid**: Token-level match against the valid action path.
 * **Ambiguity Handling**: If multiple valid paths exist (MiniGrid), label as valid if *any* path matches.
3. **Output**: JSONL file with `prompt`, `generated_tokens`, `validity_flags` (binary vector), and `entropy_profiles` (layer-wise vectors).

### Phase 2: Statistical Analysis & Threshold Optimization (US-3)
1. **Model Fitting**: Fit a **Mixed-Effects Logistic Regression (GLMM)** model:
 $$ \log\left(\frac{P(\text{valid})}{1 - P(\text{valid})}\right) = \beta_0 + \beta_1 \cdot H_{layer} + \beta_2 \cdot \text{TaskType} + (1 | \text{sequence\_id}) $$
 * **Random Effects**: Random intercepts for `sequence_id` account for the nested structure of tokens within sequences, correcting the independence assumption violation.
 * **Layer-wise Modeling**: Layers are treated as a continuous covariate or tested individually to preserve depth-specific signal, avoiding the dilution caused by pooling.
2. **Multiple Comparison Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values across layers/tasks (FR-006).
3. **Threshold Optimization**:
 * Sweep entropy thresholds $\tau \in [0.0, H_{max}]$.
 * Calculate False Positive Rate (FPR) and False Negative Rate (FNR).
 * Optimize $\tau^*$ to minimize $Weight_{FP} \cdot FPR + Weight_{FN} \cdot FNR$ (weights=1).
4. **Sensitivity Analysis**: Report results for thresholds $\tau^* \pm 0.05, 0.1$.

## Statistical Rigor & Assumptions

### Multiple Comparison Correction
Since we test the significance of the entropy coefficient across multiple layers (and potentially two tasks), the family-wise error rate is controlled. We will use the **Benjamini-Hochberg procedure** to control the False Discovery Rate (FDR), as it is less conservative than Bonferroni and more appropriate for exploratory layer-wise analysis.

### Power & Sample Size
* **Limitation**: The study is limited to a subset of examples per dataset due to RAM constraints. This results in a limited number of token-level observations (approx. k tokens depending on sequence length).
* **Acknowledgement**: If the effect size is small, the study may be underpowered to detect significant correlations at the layer level. We will report power estimates post-hoc if possible, or explicitly state the limitation in the paper.
* **Strategy**: GLMM with random intercepts increases statistical power by accounting for intra-sequence correlation, avoiding the need for coarse pooling.

### Causal Inference & Assumptions
* **Observational Nature**: This is an observational study of model internals. We claim **associational** validity, not causal. We do not claim that *changing* entropy causes validity; we claim that entropy *predicts* validity.
* **Collinearity**: Layer-wise entropy values are definitionally related (later layers depend on earlier ones). We will not claim "independent effects" of specific layers. Instead, we will report the correlation strength across the depth and identify the *region* (early/mid/late) with the strongest signal.
* **External Validity**: The "validity" label is derived strictly from **external ground truth** (GSM8K answers, MiniGrid paths), not the model's own final output. This ensures the study tests prediction of external correctness, avoiding circular validation.

### Measurement Validity
* **Ground Truth**: Validity labels are derived from exact string/sequence matching with external sources. This is a valid proxy for "correctness" in GSM8K (math answers) and MiniGrid (action sequences).
* **Entropy Metric**: Shannon entropy is the standard information-theoretic measure of uncertainty.

## Dataset Variable Fit Verification
* **GSM8K**: Contains `question` and `answer`. The `answer` field provides the ground truth for validity labeling. **Fit**: Yes.
* **MiniGrid**: Contains environment states and action sequences. The `actions` field provides the ground truth path. **Fit**: Yes.
* **Missing Variables**: No missing variables identified for the core analysis (entropy, validity, task type).

## Computational Feasibility
* **Model**: TinyLlama-Chat-v1.0 is selected. It fits within available system memory on CPU.
* **Runtime**: 500 examples $\times$ 2 datasets $\times$ 1 pass (combined generation + extraction) $\approx$ 1000 generations. Assuming Several seconds per generation on CPU, total time is approximately one to two hours, well within the established time limit.
* **Memory**: Batching (50 tokens) ensures peak RAM usage stays < 6GB.