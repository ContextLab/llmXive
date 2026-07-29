# Research: Self-improving LLM

**Feature Branch**: `001-self-improving-llm-recursive-architectur` | **Date**: 2026-06-27

## Dataset Strategy

| Dataset Name | Source URL / ID | Purpose | Verification Status |
|--------------|-----------------|---------|---------------------|
| OpenWebText | `Skylion007/openwebtext` (HuggingFace) | Training Data (General) | Verified (Loaded a large-scale dataset via streaming) |
| GSM8K | `openai/gsm8k` (HuggingFace) | Reasoning Benchmark | Verified (Loaded a substantial corpus of records) |
| ARC-Challenge | `jon-tow/okapi_arc_challenge` (HuggingFace) | Reasoning Benchmark | Verified (Loaded a substantial number of records) |
| Wikitext-2 | `wikitext` (config: `wikitext-2-raw-v1`) (HuggingFace) | Calibration Benchmark (Perplexity) | Verified (Loaded a substantial number of records) |

**Note on Wikitext-2**: The spec originally requested "Calibration Error (ECE)". However, ECE requires a classification task with known ground-truth labels. Wikitext-2 is a generative text corpus. Therefore, this plan measures **Perplexity (PPL)** on Wikitext-2, which is the standard metric for generative calibration/uncertainty. This satisfies the intent of measuring calibration without violating construct validity.

## Decision/Rationale: Compute Feasibility

All methods are planned for CPU execution on the GitHub Actions free-tier runner (multi-core, limited RAM).
- **Model**: GPT small fits in ~500MB weights. With gradient checkpointing and batch_size=4, it fits within 7GB RAM.
- **Training**: A "Micro-Batch" regime (1000 samples, 1 epoch) is chosen to ensure 3 cycles complete within 6 hours.
- **Time Budget**: A Memory Watchdog (Phase 0.0) and Time-Budget Monitor (Phase 0.5) will abort if limits are exceeded.
- **GPU Escape Hatch**: If CPU training exceeds 90% of the time budget, the runner will auto-offload to Kaggle GPU (scaled down: reduced precision, fewer steps).

## Baseline Models & Metrics

*   **Base Model**: GPT-2 124M (downloaded from Hugging Face Hub).
*   **Performance Metrics**:
    *   Reasoning Accuracy (GSM8K, ARC-Challenge).
    *   Perplexity (PPL) on Wikitext-2 (replaces ECE).
*   **Statistical Tests**: Paired bootstrap with α = 0.05 significance level.

## Modification Strategy

The LLM will be prompted to propose architectural modifications based on its analysis of the previous cycle's performance.
**Constraints**:
1.  Parameter count increase ≤30% of baseline.
2.  Architecture must remain compatible with PyTorch and Transformers library.
3.  Modification must be distinct in type or magnitude from all previous cycles.
4.  Validation on a held-out OpenWebText split before benchmark evaluation.

The process is iterative:
1.  **Prompting**: Generate a modification proposal using a carefully crafted prompt (includes modification history).
2.  **Implementation**: Apply proposed modifications.
3.  **Internal Validation**: Evaluate on held-out OpenWebText split.
4.  **Training**: Retrain the modified model on the OpenWebText training subset.
5.  **Evaluation**: Evaluate performance on GSM8K, ARC-Challenge, and Wikitext-2.

**Circularity Mitigation**: The model's proposal is based on *internal* metrics and *previous* cycle data. The *current* cycle's verification relies on *held-out OOD benchmarks* (GSM8K/ARC) that were never used in the proposal prompt or training. This prevents the model from simply overfitting to the training data it sees.

## Edge Case Handling

*   **Parameter Limit**: If a modification exceeds the parameter count limit, the LLM will be prompted again for an alternative within constraints (Phase 2.1).
*   **Training Failure**: Retries up to 2 times; if still failing, increment cycle counter and proceed with new modification (Phase 2.2).
*   **Bootstrap p-value = 0.05**: Treat as non-significant (p < 0.05 required).
*   **Hugging Face Rate Limits**: Implement exponential backoff with initial wait=30s, max retries=5 (Phase 0.1).
*   **Performance Degradation**: Terminate early if degradation ≥5% from baseline (Phase 4.1).