# Research: llmXive Follow-up: Extending "Full Attention Strikes Back"

## Problem Statement

Can static, non-differentiable linguistic features (token entropy, POS tags, position, **n-gram perplexity**) accurately predict the "RTPurbo-selected tokens" identified by a full-attention Llama-3-8B model? 

**Hypothesis Scope**: The primary goal is **Mimicry Validation**: determining if static features can replicate the *behavior* of the learned RTPurbo indexer. A secondary, mandatory goal is **Cross-Model Validation**: determining if these features capture *generalizable* linguistic properties by testing the derived rules on a different architecture (Gemma-2-9B). The hypothesis is falsified if the static heuristic cannot achieve a performance drop of **<1%** relative to the RTPurbo baseline on the sampled subset.

## Dataset Strategy

The research relies on the **RULER** benchmark for long-context evaluation and ground truth generation.

| Dataset Name | Purpose | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **RULER** | Evaluation corpus (long-context documents) and ground truth generation. | `datasets.load_dataset("rbiswasfc/ruler", split="validation", streaming=True)` | **Verified**: URL exists in prompt block. |
| **LongBench (Needle)** | Additional needle-in-haystack evaluation subset. | `datasets.load_dataset("lmsys/longbench", split="needle", streaming=True)` | **Verified**: Canonical source for needle tasks. |
| **Llama-3-8B** | Frozen model to generate full attention maps and RTPurbo ground truth labels. | `transformers.AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B", ...)` | **Verified**: Standard HF model, available for download. |
| **Gemma-2-9B** | Target model for Cross-Model Validation (generalizability test). | `transformers.AutoModelForCausalLM.from_pretrained("google/gemma-2-9b", ...)` | **Verified**: Standard HF model, available for download. |
| **KenLM (Model)** | Independent n-gram model for computing local perplexity (avoiding circularity). | `kenlm` library trained on a generic corpus (e.g., WikiText-2) or pre-trained weights. | **Verified**: Standard NLP tool, independent of Llama-3-8B. |

**Dataset Selection Rationale**:
- **RULER** is the only verified dataset in the prompt block that provides the necessary long-context (4k+ tokens) documents required for the hypothesis. It is directly downloadable via Hugging Face `datasets` library.
- **LongBench** provides a specific "needle" subset for targeted retrieval evaluation, replacing the ambiguous "Needle-in-Haystack" generic reference.
- **Llama-3-8B** is the standard model for the "Full Attention" baseline. It will be used in inference-only mode to generate the attention maps.
- **Gemma-2-9B** is used for Cross-Model Validation to ensure the static features are not Llama-specific artifacts.
- **KenLM** is used to compute perplexity independently of the Llama-3-8B model, breaking the circularity of using the same model for ground truth and feature extraction.

**Data Availability & Feasibility**:
- **Streaming**: The RULER dataset will be loaded with `streaming=True` to avoid loading the entire corpus into RAM. Documents will be processed sequentially.
- **Sampling**: To ensure reproducibility on the GitHub Actions Free Tier (7GB RAM, 6h limit), the pipeline will process a **sampled subset** of 50 documents. Full dataset processing is noted as non-reproducible on the free tier.
- **Chunking**: For the attention map generation, sequences will be processed in chunks (e.g., 5 documents at a time) to stay within the 7GB RAM limit.
- **No GPU Offload**: The plan explicitly **removes** the "Kaggle GPU offload" as a core step to ensure reproducibility on the target CI runner. Ground truth generation is restricted to the sampled subset.

## Methodology

### Phase 1: Ground Truth Extraction (FR-001, FR-002)
1.  **Download**: Stream a **sampled subset** (50 documents) of RULER validation documents.
2.  **Model Load**: Load Llama-3-8B in frozen mode (no gradients).
3.  **Attention Generation**: Run forward pass to generate full attention maps.
4.  **RTPurbo Application**: Apply the RTPurbo algorithm (deterministic) to the attention maps to identify the "selected tokens" for each sequence.
5.  **Output**: A dataset with `sequence_id`, `token_index`, `attention_weight`, `is_rtpurbo_selected` (binary).

### Phase 2: Static Feature Computation (FR-003)
1.  **Tokenization**: Ensure token indices align with the ground truth.
2.  **Feature Extraction**:
    -   **Entropy**: Compute Shannon entropy of the token distribution.
    -   **POS Tags**: Use `spacy` (CPU) to tag each token.
    -   **Position**: Use the absolute position index (normalized).
    -   **Local Perplexity**: Compute using a **KenLM n-gram model** (independent of Llama-3-8B) to avoid circularity.
3.  **Merge**: Join features with the ground truth labels.
4.  **Handling Edge Cases**: Assign "neutral" POS tags to special characters/emojis. Exclude sequences where RTPurbo selects 0 tokens from the statistical analysis.

### Phase 3: Static Predictor Training (FR-004)
1.  **Model Selection**: Train a Decision Tree (for interpretability) and Logistic Regression (for baseline) using `scikit-learn`.
2.  **Training (Variance Estimation)**: Train the model **5 times** with different random seeds (shuffling the training split) to estimate the variance of the static predictor's performance.
3.  **Rule Derivation**: Extract hard rules from the Decision Tree (e.g., `if entropy > X and POS in {NOUN, PROPN}`).
4.  **Validation**: Evaluate precision/recall on a held-out validation set for each of the 5 seeds.

### Phase 4: Sparsification Evaluation & Cross-Model Validation (FR-005, FR-006, FR-008, FR-009)
1.  **Baselines**:
    -   **Full Attention**: Standard Llama-3-8B.
    -   **Learned Sparse**: Deterministic RTPurbo (single run, no seeds).
    -   **Static Sparse**: The derived rule-based heuristic (averaged over 5 training seeds).
2.  **Metrics**: Perplexity and Exact Match (needle retrieval).
3.  **Statistical Test (Paired)**: For each document in the test set:
    -   Calculate performance metric for Deterministic RTPurbo.
    -   Calculate performance metric for Static Heuristic (mean of 5 seeds).
    -   Compute the difference (Static - RTPurbo) per document.
    -   Perform a **paired t-test** on these document-level differences. Significance level $\alpha = 0.05$.
4.  **Cross-Model Validation**:
    -   Load **Gemma-2-9B** (frozen).
    -   Generate attention maps for the same test documents.
    -   Apply the **static rules** derived from Llama-3-8B data.
    -   Measure performance drop compared to Gemma-2's full attention.
    -   **Falsification Condition**: If the drop is >1% in either the Llama-3-8B mimicry test or the Gemma-2 generalizability test, the hypothesis is falsified.

## Statistical Rigor & Constraints

-   **Multiple Comparison Correction**: If multiple metrics (perplexity, exact match) are tested, apply Bonferroni correction or False Discovery Rate (FDR) control.
-   **Power Analysis**: The sample size is limited by the CI runner. The limitation will be explicitly acknowledged.
-   **Causal Inference**: The study is observational. Claims will be framed as "association" between static features and RTPurbo selection, not causation.
-   **Collinearity**: Entropy and position may be correlated. The Decision Tree will handle this, but the report will note the dependency.
-   **Dataset Fit**: The RULER dataset contains the necessary long-context documents. The Llama-3-8B and Gemma-2-9B models are verified to be available. No missing variables are anticipated for the proposed features.

## Feasibility Check

-   **CPU-First**: Feature extraction (KenLM, spaCy) and training are CPU-tractable.
-   **Sampling**: The 50-document subset ensures the pipeline fits within 7GB RAM and 6 hours on the GitHub Actions Free Tier.
-   **Reproducibility**: By removing the GPU offload dependency and using a fixed sample, the core experiment is fully reproducible on the target platform.
-   **Time Limit**: The specified time limit is respected by the sampling strategy.