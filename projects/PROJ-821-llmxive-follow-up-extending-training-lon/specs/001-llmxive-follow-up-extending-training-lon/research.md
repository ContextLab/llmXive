# Research: llmXive follow-up: extending "Training Long-Context Vision-Language Models Effectively with Generali"

## Research Question

Does increasing **visual density** (number of images) in long-context inputs cause a non-linear degradation ("cliff") in retrieval accuracy for Vision-Language Models, independent of the total sequence length?

## Dataset Strategy

### Primary Dataset: Synthetic Generation (Dual-Arm Design)
Since no existing public dataset offers controlled variation of visual density while holding total context length constant, this project **generates its own synthetic dataset** using a Dual-Arm strategy.

- **Source**: `code/data_generation/generator.py` (Custom Script).
- **Arm A (Constant Text)**:
 - **Text**: Fixed token count (e.g., 128K).
 - **Visual**: Count varies (0, 5, 10, 15, 20).
 - **Total Context**: Increases with image count.
 - **Purpose**: Replicates the original spec requirement; tests performance under realistic "adding images to a fixed text" scenarios. **Secondary**.
- **Arm B (Constant Total)**:
 - **Total Context**: Fixed token count (e.g., 128K).
 - **Visual**: Count varies (0, 5, 10, 15, 20).
 - **Text**: Reduced proportionally as image count increases to maintain constant total.
 - **Purpose**: Isolates the "modality density" effect from the "total sequence length" effect. This is the **primary arm** for testing the "modality saturation" hypothesis.
- **Verification**:
 - Arm A: Text token count variance <1%.
 - Arm B: Total token count variance <1%.
 - Visual token count scales linearly with image count.
 - Needle difficulty score is identical across all samples.

### Model Source
- **Model**: `Qwen/Qwen2-VL-7B-Instruct` (HuggingFace ID: `Qwen/Qwen2-VL-7B-Instruct`).
- **Status**: **Verified**. This model is publicly available on HuggingFace and supports long-context inference.
- **Strategy**: Load via `transformers` with 4-bit quantization (via `bitsandbytes` or `llama.cpp` conversion if needed).
- **Quantization**: 4-bit quantization is mandatory to meet the 7GB RAM constraint.
- **Feasibility Note**: If `Qwen2-VL-7B-Instruct` fails to load or run within 7GB RAM at 128K context, the pipeline will attempt to switch to a smaller variant (e.g., 2B) or reduce context length, but the primary hypothesis test relies on the 7B model's capacity.

### Verified Datasets (Reference Only)
*No external datasets from the verified list are used for the primary experiment, as they do not meet the variable isolation requirements.*
- ONNX (json): ` (Reference for ONNX format only).
- ONNX (json): ` (Reference for ONNX format only).

## Methodology

### Phase 1: Synthetic Data Generation
1. **Seed Fixing**: Set global random seed (e.g., 42) for reproducibility.
2. **Text Generation**:
 - **Arm A**: Generate base text to target token count (e.g., 128K).
 - **Arm B**: Generate base text to `Target_Total - (Image_Count * Visual_Token_Estimate)`.
3. **Needle Insertion**: Insert a unique "needle" token at a random position.
4. **Visual Injection**:
 - Select $N$ images (where $N \in \{5, 10, 15, 20\}$), excluding the case of zero images.
 - Pad text (Arm A) or Reduce text (Arm B) to meet target constraints.
 - Append image references to the prompt structure.
5. **Validation**: Verify token counts and image counts.

### Phase 2: Feasibility Gate & Inference Execution
1. **Pilot Run**:
 - Run a single sample with max density (a representative set of images) and max context (128K).
 - **Memory Check**: If peak memory > 6.5GB, reduce max context to 64K for the main run.
2. **Model Loading**: Load `Qwen/Qwen2-VL-7B-Instruct` with 4-bit quantization.
 - **Fallback**: If `transformers` 4-bit fails on CPU, switch to `llama-cpp-python` with a converted GGUF file.
3. **Batch Processing**:
 - Iterate through samples.
 - **OOM Guard**: Wrap inference in `try/except` (catch `RuntimeError` or `MemoryError`).
 - **Action on OOM**: Log `sample_id`, `error_type`, `peak_memory`, skip to next sample.
 - **Output**: Binary retrieval result (Correct/Incorrect), inference time, peak memory.
4. **Short-Context Control**: Run a subset of samples (≤4K tokens, 1 image) to verify short-range visual grounding is intact.

### Phase 3: Statistical Analysis
1. **Aggregation**: Group results by `density_level` (a range of discrete levels) and `arm_type` (A or B).
2. **Model Fitting**:
 - **Arm A (Constant Text)**: Fit Logistic Regression: $P(\text{Correct}) \sim \text{Density} + \text{Density}^2$.
 - Tests if accuracy drops non-linearly as total length increases.
 - **Arm B (Constant Total)**: Fit Logistic Regression: $P(\text{Correct}) \sim \text{Density} + \text{Density}^2$.
 - **Primary Test**: Since total length is constant, any significant quadratic term indicates **modality-specific saturation**.
 - **Note**: TextLength is excluded as a covariate because it is perfectly collinear with Density in Arm B (Text = Total - k*Density). The model relies on the quadratic term of Density to detect the cliff.
 - **Non-Parametric Test**: Run Jonckheere-Terpstra test for ordered alternatives (Density low → high) on both arms to detect monotonic trends without distributional assumptions.
3. **Hypothesis Testing**:
 - **Null Hypothesis ($H_0$)**: Visual density has no effect on retrieval accuracy (linear or no relationship).
 - **Alternative Hypothesis ($H_1$)**: There is a significant non-linear degradation (cliff) at high density levels, specifically in Arm B.
 - **Metric**: P-value of the quadratic term ($Density^2$) or the Jonckheere-Terpstra statistic.
4. **Reporting**:
 - Plot Accuracy vs. Visual Density for Arm A and Arm B separately.
 - Flag "non-linear degradation" if the drop at high density is statistically significant (p < 0.05) in Arm B.

## Decision Rationale

### Why Dual-Arm Design?
Existing datasets do not allow independent control of image count and text length. Using a single arm (Constant Text) confounds "modality density" with "total sequence length". Arm B (Constant Total) isolates the modality effect, satisfying **Constitution Principle VI** and addressing **Scientific Soundness concerns**.

### Why Qwen2-VL-7B-Instruct?
The original model (`mmpro/MMProLong-7B-1.0`) was unverified. `Qwen2-VL-7B-Instruct` is a verified, accessible model with long-context capabilities and CPU-compatible quantization paths.

### Why 4-bit Quantization?
A large-scale model in 16-bit precision requires substantial RAM., exceeding the 7GB CI limit. Low-bit quantization reduces this to a significantly smaller footprint., leaving headroom for context window and OS overhead. This satisfies **Constitution Principle VII**.

### Why Quadratic/Non-Parametric Analysis?
Standard linear regression assumes a linear relationship. To detect a "cliff" (sharp drop), quadratic terms ($Density^2$) are required. Non-parametric tests provide robustness against non-normal distributions.

### Compute Feasibility & Memory Budget
- **Model Weights (4-bit)**: ~4.5 GB.
- **KV Cache (128K tokens)**: Estimated ~1.5 GB (assuming efficient attention).
- **OS/Overhead**: ~0.5 GB.
- **Total**: ~6.5 GB.
- **Conclusion**: 128K context fits within 7GB. 256K context is likely to exceed limits; the pilot run will automatically cap context at 128K if memory usage exceeds 6.5GB.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Model Unavailable** | High | If `Qwen/Qwen2-VL-7B-Instruct` is not accessible, the pipeline halts with a clear error. No fallback model is assumed to preserve scientific validity. |
| **OOM on CPU** | High | Pilot run and OOM guards ensure the job continues. If >50% samples fail, the experiment is flagged as "infeasible on target hardware." |
| **Quantization Artifacts** | Medium | If 4-bit quantization destroys visual grounding, the short-context control group (US-4) will detect it. |
| **Token Count Drift** | High | Validation scripts in `data_generation` ensure text/total token count variance <1%. |
| **Context Length Feasibility** | High | Pilot run automatically reduces context length to 128K (or 64K) if 256K exceeds memory limits. |