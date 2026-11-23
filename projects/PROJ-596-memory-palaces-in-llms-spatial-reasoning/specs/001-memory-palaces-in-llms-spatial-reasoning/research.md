# Research: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

## Overview

This research investigates whether explicit spatial organization of episodic memories in transformer architectures improves recall accuracy on sequential memory benchmarks. The study compares a "Spatial Memory" variant of `gpt2-medium` against a "Non-Spatial External Memory" baseline across three datasets: bAbI task 3, LAMBADA, and Story Cloze.

## Dataset Strategy

The study relies on publicly available, programmatic datasets to ensure reproducibility on the GitHub Actions free tier.

| Dataset | Source / Verified URL | Load Method | Relevance to Study |
| :--- | :--- | :--- | :--- |
| **bAbI Task** | `facebook/babi` (Hugging Face) | `datasets.load_dataset("facebook/babi", "task3")` | Tests temporal reasoning and object tracking in a controlled, synthetic environment. Maps to episodic recall of specific events. |
| **LAMBADA** | `EleutherAI/lambada_openai` (Hugging Face) | `datasets.load_dataset("EleutherAI/lambada_openai")` | Tests long-context prediction. The "last word" prediction requires integrating context over long distances, simulating episodic retrieval. |
| **Story Cloze** | `rocstories` (Hugging Face) | `datasets.load_dataset("rocstories")` | Tests narrative coherence. The task is to choose the correct ending for a 4-sentence story. **Note**: If `rocstories` is unavailable, the third benchmark is dropped; no proxy dataset is used to preserve construct validity. |

**Dataset-Variable Fit**:
- **bAbI**: Contains explicit "stories" with entities and locations. The task requires recalling the location of an object after a sequence of movements. This maps directly to the "episodic recall" outcome.
- **LAMBADA**: Contains long paragraphs where the last word is predicted. The "variable" is the context window; the "outcome" is the correct word. This maps to the ability to hold episodic traces over long distances.
- **Story Cloze**: Contains five-sentence stories. The task is to choose the correct ending. This maps to narrative coherence and long-term dependency.

**Access Gated Data**: No access-gated data (e.g., ADNI, HCP) is used. All datasets are open and downloadable via `datasets` library.

## Methodology

### Architectural Mapping (Address vs. Content)

To address concerns regarding the distinction between address and content (John von Neumann concern), the architecture explicitly separates the spatial coordinate (address) from the stored representation (content).

1.  **Address Generation (Spatial Index)**:
    -   The hidden state $h_t$ of the current token is projected through a small Multi-Layer Perceptron (MLP) to a 2D vector $z_t \in \mathbb{R}^2$.
    -   $z_t$ is normalized and clamped to the grid coordinates $(x, y) \in [0, 7] \times [0, 7]$. This $(x, y)$ pair serves as the **Address**.
    -   This mechanism is distinct from the content; the address is a soft pointer to a location, not the data itself.

2.  **Content Storage (Memory Buffer)**:
    -   The episodic chunk $c_t$ (a vector representation of the text) is stored at the location $(x, y)$ in the grid.
    -   The grid is a tensor of shape $(8, 8, D)$, where $D$ is the embedding dimension.
    -   This separation ensures that the "spatial" property is the index, while the "memory" is the content stored at that index.

3.  **Retrieval (Soft-Addressed)**:
    -   Retrieval uses cosine similarity between the current hidden state $h_t$ and the stored vectors in the grid.
    -   This allows for "fuzzy" retrieval where the model can attend to nearby slots if the exact address is noisy, mimicking human memory reconstruction.

### Model Architecture

1.  **Base Model**: `gpt2-medium` (355M parameters), loaded with 4-bit quantization (`bitsandbytes` or `llama.cpp` equivalent for CPU) to fit within 6 GB RAM.
2.  **Spatial Memory Module**:
    -   **Grid**: 8x8 (64 slots).
    -   **Assignment**: A learned embedding lookup based on content (not deterministic hash). The hidden state of the current token is projected to a 2D coordinate $(x, y)$ via a small MLP, then clamped to the grid.
    -   **Storage**: Each slot stores a vector representation of the episodic chunk.
    -   **Retrieval**: Soft-addressed retrieval using cosine similarity between the current hidden state and slot embeddings.
    -   **Eviction**: FIFO (First-In-First-Out) if the grid is full.
3.  **Non-Spatial Baseline**:
    -   **Definition**: A variant with a standard external memory buffer (a flat list of vectors) of the same capacity (64 slots).
    -   **Mechanism**: The buffer is accessed via a learned attention mechanism that does **not** use spatial coordinates. The address generation MLP is removed; the model attends to the buffer based solely on content similarity.
    -   **Purpose**: This isolates the effect of spatial organization. Both models have the same memory capacity and access mechanism (attention), but only the spatial model has the coordinate-based index.

### Training Protocol

-   **Fine-tuning**: 3 epochs, batch size 8 (reduced to 4 if RAM > 6 GB), learning rate 5e-5.
-   **Random Seeds**: 5 seeds (0, 1, 2, 3, 4) for both spatial and non-spatial variants.
-   **Datasets**: bAbI task 3, LAMBADA, Story Cloze.
-   **Metrics**:
    -   **Exact-Match Recall**: Percentage of correct predictions.
    -   **Interference Distance**: Drop in recall under forced collision (see below).
    -   **Slot Occupancy**: Distribution of items per slot.
    -   **Coordinate Variance**: Trace of the 2D covariance matrix of assigned coordinates.

### Statistical Analysis

-   **Primary Test**: Paired two-tailed t-tests comparing spatial vs. non-spatial recall accuracy across 5 seeds (as mandated by FR-005).
-   **Robustness Check**: Due to low power (N=5), **permutation tests** (10,000 iterations) and **bootstrap confidence intervals** (95%) will be computed alongside t-tests. Results are interpreted primarily through effect sizes and robustness checks, acknowledging the exploratory nature.
-   **Correction**: Bonferroni or Holm-Bonferroni for multiple comparisons (datasets).
-   **Effect Size**: Cohen's d with 95% confidence intervals.
-   **Assumption Check**: Shapiro-Wilk test for normality; if violated, Wilcoxon signed-rank test is reported as a secondary check, but permutation tests remain the primary robust metric.

## Structural Correlates & Metrics

To address the "John von Neumann" and "Rosalind Franklin" concerns regarding measurable structural correlates:

1.  **Interference Distance (Retrieval Robustness)**: Measures the robustness of the retrieval mechanism under forced collision.
    -   **Protocol**: An **Inference-Time Intervention** is applied. For the spatial model, the retrieval key is perturbed to target an *adjacent* grid coordinate (Manhattan distance = 1). For the non-spatial model, the retrieval index is perturbed to a *random* index (simulating a collision in a flat buffer).
    -   **Metric**: $\Delta \text{Recall} = \text{Recall}_{\text{clean}} - \text{Recall}_{\text{collision}}$.
    -   **Hypothesis**: Spatial variant will show a smaller $\Delta \text{Recall}$ (more robust) than non-spatial. This is a valid comparison because both tests measure the drop in performance under a "collision" condition, even if the collision topology differs (adjacent vs. random).
2.  **Slot Occupancy Distribution**: Logs the count of items per slot. A uniform distribution suggests effective spatial organization; a skewed distribution suggests clustering or failure.
3.  **Coordinate Variance**: Measures how "spread out" the memory assignments are.
    -   **Note**: This is a **Descriptive Diagnostic**, not a standalone validation metric. High variance does not prove better recall. It must be **correlated** with recall accuracy in the results section to be meaningful. Low variance (clustering) is logged as a potential failure mode.

## Decision/Rationale

-   **CPU-First**: The plan prioritizes CPU execution with 4-bit quantization to fit the GitHub Actions free tier. If the model fails to fit even with 4-bit, the plan falls back to a smaller model (e.g., `gpt2-small`) or a smaller dataset subset, but never fabricates a CPU approximation of a GPU-only method.
-   **Dataset Choice**: bAbI, LAMBADA, and Story Cloze are chosen for their direct mapping to episodic recall and long-context prediction. They are open and programmatic.
-   **Statistical Rigor**: Paired t-tests are performed as required, but supplemented by permutation tests to address the low power (N=5) concern. The low power is explicitly acknowledged.
-   **Eviction Policy**: FIFO is essential to test the spatial capacity hypothesis. If the grid is full, the oldest item is evicted. This is logged and the interference metric is computed only on non-evicted samples.
-   **Baseline Definition**: The baseline is strictly defined as the "Non-Spatial External Memory" variant to isolate the spatial variable. A "no memory" condition is excluded from the primary comparison.

## Limitations

-   **Construct Validity**: bAbI, LAMBADA, and Story Cloze measure different phenomena. Results are reported separately.
-   **Convergence**: 3 epochs may be insufficient for full convergence on a 355M model. Results are interpreted with this limitation.
-   **Confounding Variable**: The "external memory buffer" is a confound. A control variant with a non-spatial buffer is included.
-   **Statistical Power**: N=5 seeds limits the ability to detect small effects. Results are framed as exploratory effect size estimates.
-   **Interference Metric**: The interference metric measures retrieval robustness under forced collision, not the model's natural spatial reasoning during training. This is an external stress test.