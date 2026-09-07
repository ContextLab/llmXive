# Research: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

## Research Question
Does the "deliberation reward" mechanism of Anti-Self-Distillation (AntiSD) generalize to non-verifiable reasoning domains where the privileged context consists of diverse, high-quality rationales rather than a single ground-truth solution?

## Dataset Strategy

The project relies on the **UltraFeedback** and **Dolly** datasets, which contain multi-turn instruction following data with multiple annotated reasoning traces (or can be processed to simulate them via the "UltraFeedback" binarized versions which often contain preference pairs that can be expanded if multiple candidates exist, though the spec explicitly requires ≥4 traces).

### Verified Datasets
The following datasets are the **only** sources used, verified for accessibility via Hugging Face:

| Dataset Name | Source URL | Format | Suitability for Spec |
|:--- |:--- |:--- |:--- |
| **UltraFeedback** | ` | Parquet | Contains preference pairs. **Note**: The spec requires ≥4 distinct traces. We must verify if the `ko_Ultrafeedback` version contains multi-way comparisons or if we must aggregate multiple sources (e.g., `openbmb/UltraFeedback`) to find prompts with ≥4 distinct rationales. If a single source lacks ≥4 traces, we will merge sources or filter for the subset that does. |
| **UltraFeedback (Original)** | ` | JSONL | Contains evolved instructions. Likely contains multiple candidate responses. |
| **UltraFeedback (Paired)** | `https://huggingface.co/datasets/pushdeep/UltraFeedback-paired/resolve/main/data/train-00000-of-00002-768e0107a0996369.parquet` | Parquet | Paired comparison data. |

**Dataset Fit Analysis**:
The spec requires prompts with **≥4 distinct annotated high-quality reasoning traces**.
* **Risk**: Standard UltraFeedback datasets often provide binary comparisons (chosen vs. rejected) or pairs. Finding a prompt with 4+ *distinct* traces in a single download might be rare.
* **Mitigation**: The research plan will first perform a "Data Audit" phase (FR-001) to scan the verified URLs. If no single dataset provides the required density, the plan will:
 1. Merge the verified sources.
 2. Filter for prompts where the `responses` field contains a list of length ≥ 4.
 3. If the count is insufficient (< 30 prompts), the project will proceed with the maximum available sample size (N < 30), noting the reduced statistical power (FR-013, SC-007).
* **Variable Fit**: The datasets contain `prompt` and `response` fields. The `response` field in the merged data will be treated as the list of rationales. The "Privileged Context" will be sampled from this list.

### Data Access Method
* **Method**: Programmatic download via `datasets.load_dataset` (HuggingFace Hub) or direct `requests` for the verified URLs.
* **Streaming**: To respect the 7GB RAM limit, the `datasets` library will be used with `streaming=True`. This allows iterating over the dataset to find valid prompts (≥4 traces) without loading the entire file into memory.
* **Caching**: Downloaded shards will be cached in `data/raw/` with checksums (Constitution Principle III) to ensure reproducibility.

## Methodological Rigor

### Statistical Power & Sample Size (FR-013, FR-018)
* **Target**: N ≥ 30 prompts to detect Cohen's d = 0.5 with Power ≥ 0.8.
* **Reality Check**: If the verified datasets yield fewer than 30 prompts with ≥4 traces, the project will:
 * Report the actual N.
 * Calculate the observed power.
 * Use the **Wilcoxon signed-rank test** (FR-017) which is robust to small N, but explicitly state the limitation in the final report (SC-007).
 * *No synthetic data will be generated* to fake N=30.

### Causal Inference & Identification
* **Observational Nature**: This is an experimental simulation. The "cause" is the training algorithm (AntiSD vs. Standard SD).
* **Randomization**: The "Privileged Context" is randomly sampled (FR-002) to ensure independence from the specific content of the other rationales.
* **Assumptions**: The assumption is that the diversity of the *unselected* rationales is a valid proxy for the "true" distribution of high-quality reasoning in non-verifiable domains.

### Multiple Comparison Correction
* **Scenario**: Multiple metrics are tested (Deliberation Frequency, BLEU, Semantic Similarity, Quality Score).
* **Correction**: The plan will apply the **Benjamini-Hochberg procedure** to control the False Discovery Rate (FDR) across the primary success criteria (SC-001, SC-002, SC-006).

### Measurement Validity
* **Deliberation Tokens**: Defined as a specific lexicon ("Wait", "Let's think", "However"). Validity relies on the correlation with the Self-Consistency metric (formerly Human Evaluation Proxy).
* **Self-Consistency:** 'Reasoning Quality' is now measured by comparing the generated trajectories against themselves and evaluating the internal agreement of the model's output.

### Predictor Collinearity
* **Issue**: The "Privileged Context" is one of the rationales. The "Teacher Distribution" is the average of *all* rationales (including the privileged one).
* **Handling**: The Teacher Distribution is computed as the average logit distribution of the **unselected** rationales (FR-003, FR-014). The privileged context is *excluded* from the teacher distribution calculation to ensure the student is not simply distilling from the context it was given. This avoids the collinearity trap.

## Compute Feasibility

### CPU-First Strategy
* **Model**: `TinyLlama-1.1B-Chat-v1.0`.
* **Training**: 250 steps per prompt.
* **RAM Management**:
 * Batch size = 1 (single prompt at a time).
 * Gradient accumulation not used (on-policy RL).
 * Intermediate activations cleared after each step.
* **Time Budget**:
 * Estimated time per prompt: [deferred] on a standard CPU configuration.
 * Max prompts: ~30-40 prompts to stay within 5.5 hours.
 * **Timeout**: Hard stop at 5.5 hours (FR-007).

### GPU Escape Hatch
* **Removed**: The project will no longer attempt to use a GPU. All training and analysis will be performed on the CPU.

## Decision Rationale

1. **Why UltraFeedback/Dolly?** They are the only verified sources (per the prompt) containing high-quality reasoning traces.
2. **Why Streaming?** To avoid OOM on the 7GB RAM CI runner.
3. **Why Wilcoxon?** Non-parametric, robust to small N and non-normal distributions of LLM metrics.
4. **Why Gradient Inversion?** Required to implement the "AntiSD" hypothesis (maximizing divergence) rather than standard distillation.
