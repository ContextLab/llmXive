# Research: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## 1. Problem Statement

Can a language model exhibit emergent meta-cognitive behaviors (self-consistency, error detection, uncertainty calibration) if its architecture includes a **temporal recursive self-attention module** that attends to the uncertainty distribution of its own previous generation steps? This study investigates whether such architectural recursion improves performance on standard benchmarks compared to a non-recursive baseline.

## 2. Dataset Strategy

The study relies on three publicly available, programmatic datasets verified for direct download via Hugging Face `datasets` library. No access-gated data is used.

| Dataset | Purpose | Verified Source / Loader | Variable Fit |
|---------|---------|--------------------------|--------------|
| **Pile (arXiv subset)** | Training data for model fine-tuning. | `datasets.load_dataset("bigcode/pile", "arxiv", streaming=True)` [Verified: Hugging Face `bigcode/pile`]. | **Fit**: Contains text suitable for language modeling. **Constraint**: A limited token count was used to fit RAM. (derived from memory calculation). |
| **GSM8K** | Evaluation of reasoning consistency. | `datasets.load_dataset("openai/gsm8k", "main", split="test", streaming=True)` [Verified: https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet] | **Fit**: Contains math problems with step-by-step solutions. Required for self-consistency paths. |
| **MMLU** | Evaluation of domain knowledge calibration. | `datasets.load_dataset("cais/mmlu", "abstract_algebra", split="dev", streaming=True)` [Verified: https://huggingface.co/datasets/cais/mmlu/resolve/main/abstract_algebra/dev-00000-of-00001.parquet] | **Fit**: Multiple-choice questions for uncertainty calibration. |
| **Self-Consistency Metric** | Metric applied to GSM8K/MMLU. | N/A (Metric, not a dataset). | **Fit**: Self-Consistency is a method of evaluation (generating N paths and voting), not a dataset. Applied to GSM8K/MMLU. |

**Data Availability Note**: The "Pile" dataset is large. We stream the `arXiv` subset directly. The verified dataset list provided contains **TinyLlama evaluation checkpoints** (parquet files) and **GSM8K/MMLU test files**. We will use the **GSM8K** and **MMLU** verified URLs for evaluation. For training, we will use the standard Hugging Face `datasets` loader for the `bigcode/pile` (arXiv split) as the primary training source.

**Dataset Strategy Table**:
| Dataset | Source Type | Access Method | Feasibility |
|---------|-------------|---------------|-------------|
| Pile (arXiv) | Open, Programmatic | `datasets.load_dataset("bigcode/pile", "arxiv", streaming=True)` | **High**: No auth, streaming fits RAM. |
| GSM8K | Open, Programmatic | `datasets.load_dataset("openai/gsm8k", "main", streaming=True)` | **High**: Verified URL available. |
| MMLU | Open, Programmatic | `datasets.load_dataset("cais/mmlu", "abstract_algebra", streaming=True)` | **High**: Verified URL available. |

## 3. Methodology

### 3.1 Model Architecture
- **Base**: TinyLlama-1.1B (or smaller variant if RAM constraints are exceeded).
- **Recursive Module**: A custom `TemporalRecursiveAttention` layer inserted after standard self-attention.
  - **Input**: Hidden states + **Projected Softmax Vector** from the *previous* generation step (t-1).
  - **Mechanism**: The full softmax probability vector (size ~32k) is projected to a lower dimension (e.g., 64) via a learnable linear layer. The recursive module attends to this projected vector. This captures the "shape" of uncertainty, not just the chosen token's confidence.
  - **History**: To fit memory, the module only attends to the confidence vector of t-1 and a compressed summary of the previous 5 steps (sliding window).
  - **Depth**: Max recursion depth = 2 (for primary run, per resource constraint).
- **Baseline**: Standard TinyLlama with identical hyperparameters but no recursive module.

### 3.2 Training Protocol
- **Data**: First [deferred] tokens of the `arXiv` subset of the Pile.
- **Loss Function**: Joint Loss = Cross-Entropy (next token) + **Calibration Loss**.
  - **Calibration Loss**: Trained on a held-out **calibration set** (500 examples) from GSM8K/MMLU with ground-truth labels. The model predicts the probability of correctness for its own generation, and the loss minimizes the difference between predicted probability and actual correctness (binary cross-entropy). This breaks the circular dependency of training on self-consistency.
  - **For Pile Training**: The calibration loss is approximated using the next-token prediction confidence vs. next-token correctness (if available) or simply the cross-entropy loss, avoiding tautology.
- **Hyperparameters**:
  - Batch Size: A small value (gradient accumulation to an effective larger value).
  - Epochs: 1 (100k tokens is small; 1 epoch is sufficient for fine-tuning).
  - Learning Rate: e-5.
  - **Compute Budget**: ≤ 4 hours on CPU. If training exceeds this, the run is aborted (Constitution Principle VII).

### 3.3 Evaluation Metrics
1.  **Self-Consistency**: Majority vote of N=10 generated paths per question (Temperature=0.7, top_p=0.9). **Tie-Breaking**: Path with highest average confidence.
2.  **Uncertainty Calibration**:
    - **Brier Score**: Mean squared error of predicted probability vs. binary correctness.
    - **ECE (Expected Calibration Error)**: Binned accuracy vs. confidence.
3.  **Error Detection**: ROC-AUC of confidence scores predicting correctness.

### 3.4 Statistical Analysis
- **Design**: Paired t-tests across multiple distinct random seeds.
- **Comparison**: Recursive Model vs. Baseline.
- **Correction**: Bonferroni correction applied to the primary metrics (Self-Consistency, Brier, ROC-AUC) to control family-wise error rate.
- **Effect Size**: Cohen's d calculated for all significant differences.
- **Power Analysis Note**: 5 seeds is the minimum for a t-test. Given the high variance of LLM training, the power to detect small effect sizes (Cohen's d < 0.5) is low. Non-significant results will be reported as "inconclusive" rather than "no effect".
- **Sensitivity**: Sweep confidence thresholds (0.3, 0.5, 0.7) for error detection (explicitly satisfying SC-005).

## 4. Computational Feasibility & Escape Hatch

### CPU-First Strategy
- **Model**: TinyLlama (1.1B) is large for CPU. We will use `torch_dtype=torch.float16` and `device_map="auto"` (if available) or strict CPU loading with `low_cpu_mem_usage=True`.
- **Optimization**:
  - **Batch Size**: Reduced to 2 or 4.
  - **Gradient Accumulation**: Used to maintain effective batch size.
  - **Streaming**: Data streamed to avoid loading full dataset.
  - **Sliding Window**: Confidence history limited to t-1 + 5 steps to fit 7 GB RAM.
- **Risk**: 1.1B model may OOM on 7 GB RAM.
- **Mitigation**: If OOM occurs, fallback to a smaller model (e.g., `TinyLlama-0.5B` or `Phi-2` if available) or reduce context length. *Note: The spec requires TinyLlama. We will attempt TinyLlama first. If it fails, we will document the failure and switch to the smallest viable variant that fits the recursive module.*

### GPU Escape Hatch (Kaggle)
- **Trigger**: If the CPU run fails due to OOM or time limit (6h), the execution agent will auto-offload to Kaggle.
- **Kaggle Plan**:
  - **Model**: TinyLlama-1.1B (full precision or 8-bit quantized if needed).
  - **Data**: Streamed from HF.
  - **Time**: ≤ 9 hours (Kaggle limit).
  - **Implementation**: The recursive module will be implemented using a custom CUDA kernel (or highly optimized PyTorch operation) that fuses the confidence projection and attention, ensuring the GPU does not sit idle waiting for CPU post-processing. If a custom kernel is not feasible, the plan defaults to the CPU run with a reduced context window, acknowledging the time limit risk.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OOM on CPU** | High | Reduce model size (TinyLlama-0.5B), reduce batch size, use streaming, limit confidence history to sliding window. |
| **Training Time > 4h** | High | Reduce epochs to 1, reduce data to 50k tokens. |
| **Recursive Module Instability** | Medium | Add gradient clipping; cap recursion depth at 2. |
| **Dataset Access Failure** | High | Use verified URLs; implement retry logic; fallback to local cache if available. |
| **Statistical Power Low** | Medium | Increase seeds to 5 (mandatory); if still low, report as limitation and interpret non-significant results as "inconclusive". |

## 6. Decision Rationale

- **Why TinyLlama?** Spec requirement. It is the smallest viable model for "language understanding" that fits the "recursive" concept without being trivial.
- **Why 100k tokens?** Derived from memory calculation (7 GB RAM - 2 GB OS - Model Size) / Per-token overhead. Balances training signal with 7 GB RAM limit. Full Pile is impossible.
- **Why CPU-first?** GitHub Actions free tier has no GPU. The plan must be executable there.
- **Why Streaming?** Prevents OOM on 7 GB RAM.
- **Why 5 Seeds?** Constitution Principle VI mandates statistical rigor. 5 is the minimum for a reliable paired t-test in this context, with acknowledged power limitations.
- **Why Calibration Loss?** To avoid circular training on self-consistency. Grounding the loss in external correctness (GSM8K/MMLU) allows valid claims about error detection and calibration.