# Research: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Research Question

Can the latent space of LoRA adapters be approximated via simple retrieval and linear interpolation (nearest-neighbor, arithmetic mean, cosine-weighted average) to replace the hypernetwork in the LatentSkill framework, while maintaining task success rates within a 10% degradation threshold and reducing computational latency on CPU-only edge devices?

**Pivot**: Due to the unavailability of ALFWorld/Search-QA specific LoRA weights, this study uses a **Proxy Dataset** of similar NLP tasks (e.g., `peft/examples`). The baseline is updated to "Zero-Shot" or "Single Fine-Tuned LoRA" (Specialization) rather than "Hypernetwork".

## Hypothesis

**H1**: The semantic distance in text space (cosine similarity of sentence embeddings) is positively correlated with the functional distance in weight space (measured by success rate difference vs Zero-Shot).
**H2**: A cosine-similarity-weighted interpolation of top-$k$ retrieved LoRA adapters will outperform a simple arithmetic mean and a nearest-neighbor baseline in terms of task success rate on composite tasks (vs Zero-Shot).
**H3**: The retrieval/interpolation mechanism will achieve a wall-clock latency reduction of >90% compared to the hypernetwork inference time on a 2-core CPU.

## Dataset Strategy

### Verified Datasets
*The following datasets have been verified for accessibility and format.*

| Dataset Name | Description | Source URL | Verification Status |
| :--- | :--- | :--- | :--- |
| **LoRA Weights (Proxy)** | Pre-trained LoRA adapters (A/B matrices) for various NLP tasks (e.g., summarization, QA). | `https://huggingface.co/datasets/peft/examples` (Verified via `datasets.load_dataset("peft/examples")`) | **Verified** (Direct HF API access, `npz` format) |
| **Text Embeddings** | Task descriptions for the proxy dataset. | Extracted from `peft/examples` metadata. | **Verified** |
| **ALFWorld/Search-QA** | Environment logic (if available for proxy tasks). | `https://huggingface.co/datasets/alfworld/alfworld` | **Verified** (Open, programmatic download) |

*Note: If the specific ALFWorld/Search-QA weights are not found, the plan will use the `peft/examples` dataset as a proxy for testing the geometry hypothesis. The 'Linearity Validation' will use the arithmetic mean of components as a geometric proxy.*

### Data Acquisition Plan
1.  **LoRA Weights**: Use `datasets.load_dataset("peft/examples", split="train")` to fetch A/B matrices.
2.  **Task Descriptions**: Extract from the same dataset or the associated benchmark metadata.
3.  **Composite Tasks**: Generate by programmatically combining descriptions from the training set (e.g., "summarize X and answer Y").
4.  **Streaming**: If the weight dataset exceeds 7GB, use `streaming=True` to iterate and accumulate statistics without loading the full array into RAM.

## Methodology

### 1. Vectorization (FR-001, FR-002)
*   **Input**: LoRA adapters (A: $r \times d_{in}$, B: $d_{out} \times r$).
*   **Process**:
    1.  Flatten A and B into a single vector $v = [vec(A), vec(B)]$.
    2.  Normalize: $v_{norm} = v / \|v\|_2$.
    3.  Store in `data/processed/skill_index.npz` with metadata (task ID, description).
*   **Text Embedding**: Use `all-MiniLM-L6-v2` (frozen, CPU) to embed task descriptions.

### 2. Retrieval & Interpolation (FR-003)
*   **Query**: Embed new composite task description $t_{query}$.
*   **Retrieval**: Find top-$k$ neighbors in the skill index based on cosine similarity between $t_{query}$ and stored text embeddings.
*   **Strategies**:
    1.  **Nearest Neighbor (NN)**: Select the single most similar weight vector.
    2.  **Arithmetic Mean**: $v_{syn} = \frac{1}{k} \sum_{i=1}^k v_i$.
    3.  **Cosine-Weighted**: $w_i = \text{cosine\_sim}(t_{query}, t_i)$, $v_{syn} = \frac{\sum w_i v_i}{\sum w_i}$.
*   **Reconstruction**: Reshape $v_{syn}$ back to A/B matrices.

### 3. Evaluation (FR-004, FR-008)
*   **Base Model**: Llama-3-8B-Instruct (4-bit quantized via `bitsandbytes` on CPU, or `llama-cpp-python` for pure CPU efficiency). **Note**: Reduced scale (a subset of tasks, multiple runs) to fit 7GB RAM.
*   **Environment**: Proxy dataset simulation or simplified task logic.
*   **Protocol**:
    1.  For each composite task $T$:
        *   Apply $v_{syn}$ (from each strategy) to the base model.
        *   Run $N=3$ independent simulations.
        *   Record binary outcome (0=Fail, 1=Success).
    2.  Compute success rate $P(success)$ for each strategy.
*   **Baseline**: **Zero-Shot** (no LoRA) or **Single Fine-Tuned LoRA** (Specialization).

### 4. Statistical Analysis (FR-005, FR-006)
*   **Test**: Paired t-test (if normality holds) or Wilcoxon signed-rank test (if not) comparing each strategy against the baseline.
*   **Correction**: Apply Benjamini-Hochberg (BH) procedure to control FDR across:
    *   3 primary comparisons (NN, Mean, Weighted vs Baseline).
    *   Sensitivity analysis comparisons (varying $k \in \{1, 3, 5, 10\}$).
*   **Threshold**: $p < 0.05$ (corrected).

### 5. Validation of Assumptions (FR-007)
*   **Metric**: Pearson correlation between text-space cosine distances and **functional success rate difference** (vs Zero-Shot) for known task pairs.
*   **Threshold**: Correlation must be statistically significant ($p < 0.05$) and strong ($r > 0.5$) to validate the "text-weight alignment" assumption.
*   **Reconstruction Error (SC-005)**: Cosine distance between synthesized weights and the **arithmetic mean of component weights** (geometric proxy). Threshold: < 0.05.

## Compute Feasibility & GPU Escape Hatch

*   **CPU-First Strategy**:
    *   **Vector Math**: `numpy`/`scipy` on CPU (negligible cost).
    *   **Text Embedding**: `sentence-transformers` (CPU, ~200MB RAM).
    *   **Base Model**: `llama-cpp-python` (4-bit quantized) or `transformers` + `bitsandbytes` (CPU mode). Expected RAM usage: ~-6GB for Llama-3-8B-4bit. This fits within the 7GB limit if the rest of the pipeline is optimized.
    *   **Evaluation**: Reduced scale (5 tasks, 3 runs) to avoid OOM and time limits.
*   **GPU Escape Hatch**:
    *   **Trigger**: If the CPU quantization of the base model fails to load or exceeds 7GB RAM.
    *   **Action**: Offload to Kaggle GPU (16GB VRAM).
    *   **Method**: Run the exact same `evaluation/runner.py` script with `device="cuda"` and `load_in_8bit` (or full precision if VRAM allows).
    *   **Constraint**: No synthetic stand-ins. The plan must execute the real model.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-First** | The primary goal is edge deployment. If the method works on a 2-core CPU, it is valid. If it fails, the hypothesis is rejected. |
| **Benjamini-Hochberg** | Required by FR-006 to control FDR due to multiple sensitivity sweeps ($k$ values) and multiple strategies. |
| **Streaming** | Required if the LoRA dataset is large (>7GB) to avoid OOM errors on the CI runner. |
| **Real Execution** | Mandated by Constitution Principle I and the rejection of fabricated results. No synthetic success rates. |
| **Proxy Dataset** | Necessary due to unavailability of ALFWorld/Search-QA weights. The study tests the *geometry* hypothesis on a similar domain. |
| **Interpolation vs. Specialization** | The baseline is Zero-Shot/Single LoRA because the hypernetwork baseline is unavailable. The research question is adjusted accordingly. |