# Research: Self-improving LLM: recursive architecture refinement and re‑training

## 1. Problem Statement & Hypothesis

**Problem**: Can a language model recursively improve its own performance by proposing and applying architectural modifications, re-training on a small subset of data, and validating against held-out benchmarks?

**Hypothesis**: A GPT-2 124M model can propose valid architectural modifications that, after re-training, yield statistically significant improvements in reasoning accuracy (GSM8K, ARC) and calibration (BoolQ) for at least one cycle, though gains may plateau or degrade in subsequent cycles due to over-parameterization or catastrophic forgetting.

**Control Hypothesis**: Improvements are driven by increased parameter count (capacity) rather than the model's "intelligence" in proposing topology. A control group with random parameter increases will be used to isolate this effect.

## 2. Dataset Strategy

The project relies on four verified datasets. All are accessed via the Hugging Face `datasets` library or direct parquet URLs to ensure reproducibility and programmatic access on CI runners.

| Dataset | Purpose | Source / Verified URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **OpenWebText** | Training corpus | ` | `datasets.load_dataset(..., streaming=True)` | Used for fine-tuning. Streaming prevents RAM overflow. |
| **GSM8K** | Reasoning Benchmark | ` | `datasets.load_dataset('openai/gsm8k', 'main', split='test')` | Subset of 100 samples used for evaluation (FR-005). |
| **ARC-Challenge** | Reasoning Benchmark | ` | `datasets.load_dataset('allenai/ai2_arc', 'ARC-Challenge', split='test')` | Subset of 100 samples used for evaluation (FR-005). **Canonical Source**. |
| **BoolQ** | Calibration Benchmark | `https://huggingface.co/datasets/google-research-datasets/boolq/resolve/main/boolq-test.jsonl` | `datasets.load_dataset('google-research-datasets/boolq', split='test')` | Subset of 1000 samples used for ECE calculation (FR-005). **Increased N for power**. |

**Dataset Fit Analysis**:
- **OpenWebText**: Contains the raw text required for language modeling fine-tuning. The streaming approach ensures we can process the full corpus without exceeding the 7 GB RAM limit.
- **GSM8K/ARC/BoolQ**: These are standard OOD (Out-of-Distribution) benchmarks. They are **not** used in training, ensuring independence (Constitution VII).
- **No Access-Gated Data**: All datasets are publicly available without credentials, satisfying the feasibility constraint for GitHub Actions.

**Baseline Capability Check**:
Before starting the refinement loop, the baseline GPT-2 124M model will be evaluated. If it achieves near-random performance (<10% accuracy on GSM8K/ARC), the experiment will proceed with the caveat that "improvement" is measured against a very low baseline, or the plan will switch to a zero-shot prompting baseline for comparison.

## 3. Methodological Rigor

### 3.1 Statistical Testing (FR-006, SC-001, SC-002)
To determine if performance changes are significant, the plan employs **paired bootstrap resampling**:
- **Method**: Resample the test set (with replacement) $N$ times (where $N=1000$).
- **Statistic**: Difference in accuracy/ECE between Cycle $i$ and Cycle $i-1$.
- **Threshold**: $\alpha = 0.05$. A result is significant only if $p < 0.05$ (strictly less).
- **Correction**: Since multiple benchmarks are tested per cycle, a **Bonferroni correction** will be applied to control the Family-Wise Error Rate (FWER).
- **Reporting**: In addition to p-values, **effect sizes (Cohen's d)** and **95% confidence intervals** will be reported to address the low power of small samples (N=100).

### 3.2 Power & Sample Size
- **Training Data**: The subset size is initially [deferred] but will be capped at a manageable scale appropriate for the study. If training time exceeds 2 hours per cycle (CPU constraint), the subset will be reduced to a smaller, computationally manageable size. to ensure completion within the -hour budget.
- **Evaluation Data**:
 - GSM8K/ARC: 100 samples. **Limitation**: Power to detect a 2-5% shift is low (<40%). Results will be interpreted with caution, emphasizing confidence intervals.
 - BoolQ: [deferred] samples. Increased to improve calibration stability and statistical power for ECE.

### 3.3 Causal Inference & Validity
- **Observational Nature**: The "improvement" is correlational within the experiment. We cannot claim the model *caused* the improvement in a general sense, only that the specific modification led to a change in the specific benchmark.
- **Control Group**: A **Random Modification Control** will be implemented. In one cycle, architectural changes (parameter count increases) will be applied randomly rather than by the model's proposal. This isolates the effect of "capacity gain" from "architectural intelligence."
- **Capacity Normalization**: The linear regression analysis will include "parameter count" as a covariate to disentangle its effect from the specific architectural topology.
- **Instrument Validity**: GSM8K and ARC are widely accepted benchmarks for reasoning. BoolQ is a standard binary QA task. The plan cites validation literature for these datasets in the final paper.
- **Collinearity**: Architectural modifications (e.g., increasing hidden size) are inherently correlated with parameter count. The plan will not claim "independent effects" of architecture vs. capacity but will report the trade-off explicitly.

### 3.4 Separation of Logic (Constitution VII)
- **Generative Logic**: The model proposes a change (e.g., "increase layers").
- **Verification Logic**: An external oracle (hardcoded rules) validates the change against constraints (parameter count, distinctness).
- **Evaluation Logic**: Benchmarks run on held-out data.
- **No Circular Validation**: The evaluation data is never seen by the generative model during the proposal phase.

## 4. Compute Feasibility (CPU-First)

### 4.1 CPU Strategy & Fallback
- **Model**: GPT (a medium-scale language model).
- **Training**: 1 epoch, batch size 4, AdamW.
- **Hardware**: GitHub Actions (multi-core CPU, several GB RAM).
- **Feasibility**: GPT with a smaller parameter count fits in ~500MB VRAM/RAM.
- **Time Budget**: 12 hours total for 3 cycles.
- **Fallback Strategy**: If training a cycle exceeds 2 hours (estimated), the training subset size will be automatically reduced from the initial [deferred] value to **[deferred] samples**. This ensures the experiment completes within the time budget, even if statistical power for training is reduced.
- **Streaming**: Data is streamed to avoid loading the full large-scale OpenWebText corpus into RAM.

### 4.2 GPU Escape Hatch (Not Required)
- The plan is designed to run entirely on CPU. No CUDA or 8-bit quantization is required for GPT-2 124M. If the training time exceeds limits, the strategy is to **reduce the training subset size**, not to offload to a GPU (which is not available on the free tier).

## 5. Risk Analysis

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Training Failure** | Cycle aborts. | Retry up to 2 times (FR-012). If failed, log and proceed to next cycle (FR-007). |
| **Performance Degradation** | >5% drop from baseline. | Early termination (FR-015). |
| **API Rate Limits** | Data download fails. | Exponential backoff (FR-011). |
| **RAM Overflow** | OOM crash. | Use `streaming=True` for datasets; limit batch size. |
| **Modification Rejection** | Model proposes invalid change. | Oracle rejects and prompts for new proposal (FR-003, FR-020). |
| **Low Statistical Power** | Inconclusive results. | Report effect sizes and confidence intervals; increase BoolQ sample size to a sufficient magnitude for robust statistical analysis. |
| **Time Exceeded** | Job fails. | Reduce training subset to [deferred] samples if cycle time > 2h. |