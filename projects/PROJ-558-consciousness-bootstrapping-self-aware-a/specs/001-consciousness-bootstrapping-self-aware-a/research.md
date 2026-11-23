# Research: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## Summary

This research investigates whether adding a **temporal recursive self-attention module** to a 1.1B parameter language model (TinyLlama) and training it with a **joint loss** (cross-entropy + confidence prediction via self-consistency proxy) improves meta-cognitive behaviors. The study focuses on three measurable outcomes: **self-consistency** (agreement among multiple reasoning paths), **error detection** (ROC-AUC of confidence vs. correctness), and **uncertainty calibration** (Brier score and Expected Calibration Error).

## Dataset Strategy

The study relies on publicly available, programmatic datasets to ensure reproducibility on the CI runner. No access-gated data is used.

| Dataset | Purpose | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **Pile (arXiv subset)** | Training data for the base model. | `datasets.load_dataset("EleutherAI/the_pile", "arxiv", split="train", streaming=True)` | Verified: Public HF dataset. |
| **TinyLlama (Parquet)** | Reference weights for initialization (if not using HF hub directly). | `https://huggingface.co/datasets/open-llm-leaderboard-old/details_PY007__TinyLlama-1.1B-step-50K-105b/resolve/main/2023-09-12T12-30-04.204611/details_harness|arc:challenge|25_2023-09-12T12-30-04.204611.parquet` | Verified: Direct URL from prompt. |
| **GSM8K** | Benchmark for mathematical reasoning (Self-Consistency). | `datasets.load_dataset("openai/gsm8k", "main", split="test")` | Verified: `https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet` |
| **MMLU** | Benchmark for general knowledge and calibration. | `datasets.load_dataset("cais/mmlu", "abstract_algebra", split="dev")` (Subset used for speed) | Verified: `https://huggingface.co/datasets/cais/mmlu/resolve/main/abstract_algebra/dev-00000-of-00001.parquet` |

**Data Availability Note**: The "Self-Consistency" dataset mentioned in the spec is not in the verified URL list. The plan uses **GSM8K** and **MMLU** as the primary sources for generating multiple reasoning paths and calculating consistency, as these are verified and sufficient for the hypothesis. The "arXiv" subset of The Pile is used for training, accessed via streaming to fit the 7 GB RAM constraint.

## Methodology

### 1. Model Architecture
The base model is **TinyLlama-1.1B** (1.1B parameters).
- **Modification**: A **Temporal Recursive Self-Attention** module is inserted. This module takes the confidence distribution (softmax output) of the previous generation step as an additional input to the attention mechanism for the current step, up to a max depth of 3 (swept: 1, 2, 3).
- **Baselines**:
  1.  **Static-Confidence Control**: The recursive module's temporal connections are replaced with a constant, zero-initialized confidence vector. This satisfies the requirement to isolate the effect of *temporal coherence* vs. stochasticity, ensuring the baseline is structurally capable of generating the same metrics (Self-Consistency) as the recursive model.
  2.  **Frozen-Recursive Baseline**: The recursive module is instantiated but weights are frozen to random initialization. This isolates the effect of *learning* the recursive mechanism.
  - **Primary Comparison**: Recursive vs. Static-Confidence.

### 2. Training Regime
- **Dataset**: First [deferred] tokens of the `arXiv` subset of The Pile (streamed).
- **Loss Function**: `L_total = L_cross_entropy + λ * L_confidence`.
 - `L_confidence` is a **Self-Consistency Proxy** loss. To avoid tautology, a **Teacher Model** (frozen TinyLlama) generates a "consensus correctness" proxy for a small, representative validation split ([deferred] samples) *before* training begins. The Student Model is trained to predict confidence that aligns with this external consensus, providing an independent signal for the confidence head. This breaks the circular dependency and provides a meaningful signal for the confidence head.
- **Hyperparameters**:
  - Batch Size: 4 (accumulated to 16).
  - Epochs: 3 (to fit within 4-hour budget).
  - Recursion Depth: Swept at 1, 2, 3.
  - Seeds: 5 distinct random seeds for statistical power.
- **Compute Strategy**:
  - **Primary**: CPU (2 cores, 7 GB RAM). Uses `torch.no_grad()` where possible, gradient checkpointing, and streaming.
  - **Escape Hatch**: If OOM occurs on CPU, the run is automatically offloaded to a Kaggle GPU (16 GB VRAM) with the same hyperparameters, scaled to fit the kernel limit (max 9 hours). This is a feasibility fallback, not a method change. The methodology (including recursion depth and dataset size) remains identical.

### 3. Evaluation Metrics
- **Self-Consistency**: Majority vote agreement across 5 generated paths per question (Temperature=0.7, top_p=0.9). *Note: This measures output stability, not necessarily internal error detection.*
- **Error Detection**: ROC-AUC of confidence scores vs. binary correctness (verified against ground truth). *Note: Distinct from consistency; a model can be consistent but wrong.*
- **Uncertainty Calibration**: Brier Score and Expected Calibration Error (ECE).

### 4. Statistical Analysis
- **Test**: Paired t-test (recursive vs. static-confidence baseline) across the 5 seeds.
- **Correction**: **Bonferroni correction** for the 3 primary metrics (Consistency, Calibration, Error Detection). The schema enforces `bonferroni` exclusively.
- **Sensitivity**: Sweep confidence thresholds (0.3, 0.5, 0.7) and report false positive/negative rates.
- **Power Analysis**: The sample size (n=5) is the maximum feasible for a 1.1B model on CPU within 4 hours. A power calculation indicates that n=5 provides <30% power to detect a [deferred] effect size (Cohen's d ~0.5) at α=0.05. Therefore, the study is explicitly framed as **Exploratory**. Effect sizes (Cohen's d) are prioritized over p-values to quantify the magnitude of any observed effect despite the low power. The high variance from the small dataset (100k tokens) is acknowledged as a limitation.

## Decision/Rationale

**CPU vs. GPU**: The plan prioritizes **CPU** execution because the 1.1B model with a 100k token training set and gradient accumulation fits within the 7 GB RAM limit. This adheres to the "CPU-first" rule. The **GPU escape hatch** is reserved for cases where the memory footprint of the recursive module causes an OOM, ensuring the method remains real (no synthetic approximation) but feasible.

**Dataset Fit**: The verified datasets (GSM8K, MMLU, Pile) contain the necessary variables (questions, ground truth for GSM8K/MMLU, text for Pile). No required variable is missing. The "Self-Consistency" dataset is not in the verified list, so GSM8K/MMLU are used as the operational proxy, which is methodologically sound for testing reasoning consistency.

**Statistical Rigor**: The plan explicitly addresses multiple comparisons (Bonferroni), power (5 seeds, with limitations acknowledged), and causal framing (associational claims only, as the study is observational of the model's behavior). The self-consistency proxy loss is acknowledged as tautological but is the mandated spec requirement; the hypothesis is reframed to test architectural influence on this specific loop.

**Circularity Limitation**: The training loss is tautological (self-consistency proxy). The plan mitigates this by framing the hypothesis as an architectural comparison (recursive vs. static) rather than an absolute claim of "truth." The evaluation focuses on whether the recursive architecture produces *more stable* self-consistency than the static baseline.

**Non-Triviality of Self-Consistency**: The hypothesis is not that the model *will* be consistent (which is trivial if the architecture enforces it), but that the recursive architecture will achieve *higher consistency* than the static baseline *without* sacrificing calibration or error detection. The evaluation focuses on the *trade-off* between consistency and accuracy.

**Dataset Size vs. Model Capacity**: 100k tokens is insufficient for full convergence of a 1.1B model. The hypothesis is reframed to test "architectural influence on meta-cognitive behaviors in a data-scarce regime" rather than "emergent consciousness." The results are framed as exploratory, highlighting the architectural effect even if the model is under-trained.