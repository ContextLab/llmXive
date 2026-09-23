# Model Selection Document

## Selected Model: Qwen1.5-1.5B

### Rationale
- **Requirement Compliance**: This selection strictly adheres to FR-002, which mandates a model size of approximately 1.5B parameters.
- **CPU Tractability**: The 1.5B parameter count allows for inference on CPU within a reasonable timeframe for the 500-example limit, whereas larger models (e.g., 7B+) would be computationally prohibitive for the entropy profiling pipeline.
- **Performance**: Qwen1.5-1.5B demonstrates strong reasoning capabilities on GSM8K and instruction following, making it suitable for generating the baseline sequences required for validity labeling.

### Configuration
- **Model ID**: `Qwen/Qwen1.5-1.5B`
- **Precision**: Float16 (if CUDA available) or Float32 (CPU)
- **Generation Params**: `temperature=0.0` (deterministic), `max_new_tokens=512`

### Limitations
- **Context Length**: Limited to 32k context, sufficient for GSM8K problems.
- **Reasoning Depth**: While capable, it may struggle with very complex multi-step reasoning compared to larger models, which is acceptable for the validity prediction research goal (comparing entropy to ground truth).
- **Speed**: Inference on CPU will be slower than GPU; the 500-example cap is designed to mitigate this.
