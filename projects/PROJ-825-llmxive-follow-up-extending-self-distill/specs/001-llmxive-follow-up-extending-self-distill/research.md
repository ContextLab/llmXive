# Research: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

## Executive Summary

This research investigates the feasibility of replacing the teacher-student confidence gap in Self-Distilled Agentic Reinforcement Learning (SDAR) with a student-only heuristic. The hypothesis is that token entropy ($H_t$) and retrieved context stability ($S_t$) are sufficient proxies for the teacher's privileged information, allowing for a >60% reduction in computational cost while retaining ≥80% of the performance gains.

## Background & Motivation

### The Problem: Cost of Dual-Model SDAR
Self-Distilled Agentic Reinforcement Learning (SDAR) typically employs a "Teacher" model to generate distillation signals (confidence gaps) for a "Student" model. While effective, the forward pass of the Teacher model doubles inference costs, making the approach infeasible for edge devices or resource-constrained environments (e.g., mobile agents, local LLMs).

### The Proposed Solution: Student-Only Gating
The proposed variant eliminates the Teacher model entirely. Instead, it uses:
1.  **Token Entropy ($H_t$)**: Measures the model's uncertainty at each token. High entropy suggests the model is unsure, potentially requiring a stronger distillation signal or exploration.
2.  **Retrieved Context Stability ($S_t$)**: Measures the consistency of retrieved external knowledge. If the retrieved context is noisy or inconsistent, the gating signal is down-weighted to prevent learning from garbage data.

### Research Questions
1.  **RQ1**: Does the Student-Only gating mechanism ($g_t = \sigma(\alpha H_t + \beta S_t)$) achieve ≥80% of the performance improvement of the Baseline SDAR over a standard GRPO baseline?
2.  **RQ2**: Does the Student-Only variant achieve a >60% reduction in per-step computational cost (CPU time/memory) compared to the Baseline?
3.  **RQ3**: Is the correlation between the Student-Only heuristic and the Teacher-Student gap strong enough to justify the removal of the Teacher?

## Methodology

### Experimental Setup
- **Environments**:
  - **ALFWorld**: A text-based agent environment for household tasks.
  - **WebShop**: A text-based e-commerce environment requiring complex reasoning.
- **Models**:
  - **Student**: Qwen series model (quantized to 8-bit).
  - **Baseline Teacher**: **Same architecture** (Qwen2.5-1.7B) as Student. The Baseline SDAR performs *two* forward passes (Teacher + Student) to ensure the cost comparison isolates the gating mechanism, not model size differences.
  - **Retriever**: `sentence-transformers/all-MiniLM-L6-v2` (quantized).
- **Baselines**:
  - **GRPO**: Standard Group Relative Policy Optimization (no distillation).
  - **Baseline SDAR**: Dual-model SDAR with Teacher-Student gap (Same Architecture).
  - **Student-Only**: Proposed variant.

### Gating Mechanism
The gating score $g_t$ for token $t$ is computed as:
$$ g_t = \sigma(\alpha H_t + \beta S_t) $$
Where:
- $H_t = -\sum p_i \log p_i$ (Token entropy).
- $S_t = \text{cosine\_similarity}(\text{retrieved\_context}, \text{current\_state})$.
- $\alpha, \beta$: Hyperparameters (deferred to tuning).
- $\sigma$: Sigmoid activation.

### Statistical Analysis
- **Primary Metric**: **Cumulative Reward per Episode** (Continuous). This provides higher resolution than binary success rates.
- **Secondary Metric**: Task Success Rate (Binary: 1 if goal reached, 0 otherwise).
- **Test Method**: **Bootstrapping** (1000 iterations) on the distribution of cumulative rewards to generate 95% Confidence Intervals (CIs) and calculate effect sizes (Cohen's d).
- **Significance Level**: $\alpha = 0.05$.
- **Power Analysis**: N=5 runs is a feasibility constraint (6-hour CI limit). While low power (<0.8) is expected for binary metrics, bootstrapping continuous metrics maximizes resolution. Results will be reported with CIs and effect sizes, acknowledging the limitation.
- **Paired Analysis**: For Constitution VII validation, Baseline trajectories are replayed through the Student-Only agent to enable Pearson correlation on identical data points.

### Compute Strategy
- **Primary**: CPU-only execution on GitHub Actions (2 vCPU, 7GB RAM).
- **Fallback**: Kaggle GPU (T4) if CPU quantization fails.
- **Data Handling**: Environments are downloaded once and cached. No large external datasets required (synthetic agent tasks).
- **Early Stopping**: Runs terminate immediately upon reaching a predefined reward threshold or after a fixed step cap to ensure data completeness and fit the 6-hour budget.

## Dataset Strategy

| Dataset / Resource | Source | Verification | Usage |
| :--- | :--- | :--- | :--- |
| **ALFWorld** | `pip install alfworld` | Verified via PyPI | Training environment for household tasks. |
| **WebShop** | `pip install webshop` | Verified via PyPI | Training environment for e-commerce tasks. |
| **Qwen2.5-1.7B** | Hugging Face (`Qwen/Qwen2.5-1.7B`) | Verified via HF Hub | Student model for both variants. |
| **Retriever Model** | Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`) | Verified via HF Hub | Context stability calculation. |
| **GRPO Baseline** | Internal implementation | N/A | Control group for performance comparison. |

*Note: No access-gated datasets (e.g., ADNI, HCP) are used. All resources are open and programmatic.*

## Ethical Considerations & Limitations

- **Bias**: The environments (ALFWorld/WebShop) are synthetic. Results may not generalize to real-world agent tasks without further validation.
- **Reproducibility**: All random seeds are pinned. Code and data will be versioned.
- **Limitations**:
  - **Sample Size**: N=5 runs per variant is low for robust statistical power. Results will be reported with confidence intervals and effect sizes, with explicit caveats about Type II error risk.
  - **Model Size**: A small number of parameters is small. Scaling to larger models may change the entropy-stability correlation.
  - **Hardware**: CPU-only execution may limit the complexity of the retriever or context window.
  - **Time Constraints**: The fixed CI limit necessitates early stopping, which may truncate long-tail training dynamics.

## References

1.  **SDAR Paper**: (Reference to the original Self-Distilled Agentic Reinforcement Learning paper, to be verified during implementation).
2.  **ALFWorld**: Shridhar, M., et al. "ALFWorld: Aligning Text and Embodied Environments for Interactive Learning." (Verified via PyPI).
3.  **WebShop**: Yan, Y., et al. "WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents." (Verified via PyPI).
4.  **Qwen2.5**: Qwen Team. "Qwen2.5 Technical Report." (Verified via Hugging Face).
5.  **Sentence-Transformers**: Reimers, N., & Gurevych, I. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." (Verified via Hugging Face).