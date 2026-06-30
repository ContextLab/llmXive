# EmbedFilter Adaptation: CPU-Scaled Verification

## Purpose
This adaptation reproduces the core claim of the paper **"Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"**: that projecting LLM embeddings through the unembedding matrix (LM head) and filtering specific dimensions improves semantic quality.

## Simplifications & Approximations
To run on a **CPU-only CI environment** (2 cores, ~7GB RAM) without fabricating data:
1.  **Model Replacement**: The original Llama/Mistral 8B models are replaced with **TinyLlama-1.1B-Chat-v1.0** (or a similar small decoder-only model available on HuggingFace). This is small enough to load on CPU RAM (~2-3GB) and run inference quickly.
2.  **Dataset Subsampling**: Instead of the full MTEB benchmark (thousands of examples), we use a **single representative task** from the `mteb` suite (e.g., `STS17` or a small subset of `SciDocs` if available) with **~100-200 samples**.
3.  **Metric Simplification**: We compute the **Cosine Similarity** between query and document embeddings for a few pairs to demonstrate the "filtering" effect. We do not run the full MTEB evaluation suite (which requires downloading massive datasets and running many tasks).
4.  **EmbedFilter Implementation**: We reimplement the core `EmbedFilter` logic (projection to vocabulary space, masking high-frequency dimensions, projection back) directly in `code/` without importing the full research repo's complex training loops.
5.  **No GPU**: All operations are forced to `cpu`. The code does not attempt to use CUDA.

## Core Logic Verified
-   **Standard Embedding**: `last_hidden_state` mean pooling.
-   **Unembedding Projection**: `embedding @ W_unembedding.T`.
-   **Filtering**: Masking top-k frequent token dimensions.
-   **Result**: Comparison of similarity scores before and after filtering.

## Artifacts
-   `data/similarity_results.json`: JSON containing similarity scores for standard vs. filtered embeddings.
-   `figures/similarity_comparison.png`: Bar chart visualizing the improvement (or lack thereof) on the small sample.
