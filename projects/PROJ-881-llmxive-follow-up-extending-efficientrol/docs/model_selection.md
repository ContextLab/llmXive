# Model Selection: Qwen1.5-1.5B for CPU Feasibility

## Executive Summary

This document justifies the selection of **Qwen1.5-1.5B** as the primary model for the llmXive entropy-guided validity prediction pipeline. The selection is based on the project's strict CPU feasibility requirements (FR-002), memory constraints (≤7GB RAM), and the need for a balance between inference speed and semantic capability required for GSM8K and MiniGrid tasks.

## Selection Criteria

### 1. CPU Feasibility (Primary Constraint)
- **Requirement**: The model must run entirely on CPU with peak RAM usage ≤ 7GB.
- **Rationale**: The pipeline is designed for environments without GPU acceleration.
- **Evaluation**:
 - Qwen1.5-0.5B: ~1.5GB RAM (Too small for complex reasoning)
 - **Qwen1.5-1.5B: ~3.5-4.5GB RAM (Optimal fit)**
 - Qwen1.5-4B: ~8GB+ RAM (Exceeds limit)
 - Qwen1.5-7B: ~14GB+ RAM (Exceeds limit)

### 2. Semantic Capability (Secondary Constraint)
- **Requirement**: The model must demonstrate sufficient reasoning capability to generate valid token sequences for GSM8K (math word problems) and MiniGrid (navigation tasks).
- **Rationale**: Entropy analysis is only meaningful if the model's baseline behavior contains a mix of valid and invalid paths.
- **Evaluation**:
 - 0.5B models often fail to maintain long-horizon coherence in MiniGrid or multi-step math in GSM8K.
 - 1.5B models show significantly improved instruction following and chain-of-thought stability compared to 0.5B.
 - Larger models (4B+) offer diminishing returns for the specific tasks relative to the memory cost.

### 3. Tokenization Efficiency
- **Requirement**: Efficient tokenization to minimize sequence length overhead.
- **Evaluation**: Qwen1.5 uses a BPE tokenizer with a vocabulary size of 151,936, which provides a good balance between sequence compression and vocabulary coverage for English and code-like structures (MiniGrid actions).

## Memory Analysis

### Theoretical Calculation (FP16)
- Model Parameters: 1.5 Billion
- Precision: FP16 (2 bytes per parameter)
- Model Weights: 1.5B × 2B = 3.0 GB
- KV Cache (Sequence Length 512, Batch 1, Layers 28, Hidden 1536): ~0.5 GB
- Overhead (Python, Transformers, OS): ~1.0 GB
- **Total Estimated Peak**: ~4.5 GB

### Execution Safety Margin
- **Limit**: 7.0 GB
- **Estimated Usage**: 4.5 GB
- **Safety Margin**: 2.5 GB (35% headroom)
- **Conclusion**: The model fits comfortably within the 7GB constraint, allowing for memory spikes during the entropy extraction phase (T024) where intermediate layer outputs are cached.

## Compatibility Verification

The selected model is compatible with the following project dependencies:
- `transformers >= 4.37.0` (Supports Qwen1.5 architecture)
- `torch >= 2.1.0` (Required for CPU inference optimizations)
- `minigrid >= 2.3.0` (Environment compatibility)

The model identifier to be used is: `Qwen/Qwen1.5-1.5B`

## Contingency Plan

If T012c (Model Feasibility Check) reports peak RAM > 7GB:
1. The pipeline will pause and generate `spec_amendment_proposal.md`.
2. A fallback to **Qwen1.5-0.5B** will be considered *only* if the spec is amended to relax the performance requirements, as 0.5B may not meet the semantic validity requirements for GSM8K.
3. Automatic fallback is **not** implemented to prevent silent degradation of research quality.

## Conclusion

**Qwen1.5-1.5B** is the optimal choice for this project. It satisfies the strict CPU memory constraints while providing the necessary reasoning capabilities for the target datasets. It represents the largest model that can be reliably run within the 7GB RAM limit, maximizing the signal quality for entropy-guided validity prediction.