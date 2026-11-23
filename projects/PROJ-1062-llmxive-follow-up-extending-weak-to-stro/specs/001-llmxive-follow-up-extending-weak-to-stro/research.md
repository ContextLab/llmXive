# Research: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

## Problem Statement

The core hypothesis is that the implicit reward signal derived from a weak teacher's policy shift (log-ratio of probabilities between post-RL and pre-RL checkpoints) retains its efficacy when transferred to a student model with a fundamentally different architectural inductive bias (e.g., Dense Transformer to MoE or State-Space Model). The research investigates whether this signal degrades due to representational misalignment or remains robust across architectural families.

## Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified data sources to ensure reproducibility and feasibility on the CI runner:

1.  **AIME 2024 Dataset**:
    *   **Source**: `MathArena/aime_2024` (HuggingFace).
    *   **URL**: `https://huggingface.co/datasets/MathArena/aime_2024`
    *   **Access Method**: `datasets.load_dataset("MathArena/aime_2024")`.
    *   **Content**: Contains ID, Year, Problem Number, Question, Answer, and Part.
    *   **Variable Fit**: The dataset provides the necessary reasoning steps (ground-truth tokens) required for FR-001 (implicit reward computation) and FR-005 (evaluation).
    *   **Human-Verified Labels**: The spec requires human-verified correctness labels (SC-006). If `HuggingFaceH4/aime_2024_verified` is unavailable, the plan will generate a 'Teacher-Verified' label by checking if the teacher's output matches the `Answer` field with 100% confidence. This proxy is explicitly documented as 'Teacher-Verified' rather than 'Human-Verified' to maintain validity.

2.  **Teacher Models (Implicit Reward Source)**:
    *   **Source**: HuggingFace Hub (Public).
    *   **Models**: Pre-RL and Post-RL checkpoints of a dense Transformer (e.g., `Qwen/Qwen2.5-1.5B-Instruct` for pre-RL and a verified RL checkpoint if available).
    *   **Constraint**: Must be publicly accessible without registration. **Halt Condition**: If no verified 'Post-RL' checkpoint exists, the experiment will halt and report the missing artifact. No SFT checkpoint will be used as a proxy for RL, as this would invalidate the core hypothesis (construct validity).

3.  **Student Models**:
    *   **MoE**: `Qwen/Qwen1.5-MoE-A2.7B` (2.7B parameters). While >1B, this is the smallest verified MoE available that fits 7GB RAM in int8 quantization. It will be loaded with `load_in_8bit=True` and `device_map="cpu"`.
    *   **SSM**: `state-spaces/mamba-1.3b` (1.3B parameters). Loaded with `load_in_8bit=True` and `device_map="cpu"`.
    *   **Loading Strategy**: `transformers` with `device_map="cpu"`, `load_in_8bit=True` (via `bitsandbytes`), and `torch_dtype=torch.float16` where possible to minimize RAM.

### Data Loading & Preprocessing
*   **Streaming**: For large datasets, `datasets.load_dataset(..., streaming=True)` will be used to avoid loading the full dataset into RAM.
*   **Filtering**: The AIME subset will be filtered to a manageable size to fit the 6-hour compute budget while maintaining statistical power (see Power Analysis).
*   **Label Generation**: If `human_verified_label` is missing, `label_generator.py` will generate a 'Teacher-Verified' label by checking if the teacher's output matches the `Answer` field. This is a valid proxy for "correctness" in math problems, but the limitation is documented.

## Methodology

### 1. Implicit Reward Computation (FR-001)
*   **Input**: AIME problem prompts and ground-truth reasoning tokens.
*   **Teacher**: Dense Transformer (Pre-RL and Post-RL checkpoints).
*   **Computation**: $R_{imp}(x, y) = \log P_{post}(y|x) - \log P_{pre}(y|x)$.
*   **Stability**: Epsilon smoothing ($\epsilon = 1e-9$) applied to probabilities before log to prevent NaNs (Edge Case handling).

### 2. Student Training (FR-002, FR-003)
*   **Architectures**:
    *   **MoE**: `Qwen/Qwen1.5-MoE-A2.7B` (int8, CPU).
    *   **SSM**: `state-spaces/mamba-1.3b` (int8, CPU).
*   **Training Loop**: On-policy distillation. The student maximizes the expected implicit reward: $\max_{\theta} \mathbb{E}_{(x,y) \sim D} [R_{imp}(x,y) \cdot \log P_{\theta}(y|x)]$.
*   **Baseline**: Standard distillation maximizing $\log P_{teacher}(y|x)$ without the reward signal.
*   **Noise Control**: A 'Random Reward' baseline is included, where the reward signal is shuffled to distinguish signal transfer from overfitting to noise.
*   **Constraints**:
    *   **Batch Size**: 1 (verified fact from RAM constraints).
    *   **Quantization**: int8 for all models.
    *   **Gradient Accumulation**: Used to simulate larger effective batches if needed.
    *   **Memory Guard**: `memory_guard.py` enforces batch size 1 as a hard floor. If OOM persists, it saves partial results and halts.

### 3. Evaluation (FR-005, FR-009)
*   **Metric**: Log-probability improvement of ground-truth reasoning steps on a held-out AIME subset.
*   **Validation**: Comparison against 'Teacher-Verified' correctness (derived from `Answer` field). The primary validation metric for SC-006 is 'Exact Match (EM) Rate' on the held-out set, which is independent of the log-prob optimization target.
*   **Data Split**: `data/processed/train_split.parquet` and `data/processed/held_out_split.parquet` are explicitly created to ensure FR-009 (held-out evaluation) is satisfied.

### 4. Statistical Analysis (FR-006)
*   **Test**: Wilcoxon signed-rank test (non-parametric) as primary, with paired t-test as secondary.
*   **Correction**: Bonferroni correction for the planned pairwise comparisons (MoE, SSM).
*   **Robustness**: `stats_utils.py` implements cluster-robust standard errors.
*   **Seeds**: 3 independent random seeds per architecture/regime to generate a distribution of performance gains.
*   **Threshold**: $\alpha = 0.05$.

## Power Analysis & Sample Size
* **Goal**: Detect a moderate effect size ($d = 0.5$) with [deferred] power.
*   **Constraint**: 6-hour time limit and 7GB RAM.
*   **Plan**: Given the computational cost of training, a sample size of 200 problems (subset of AIME) is the maximum feasible within 6 hours. If this yields low power, the limitation will be explicitly stated in the results. The plan will perform a post-hoc power analysis if the effect size is small. Non-significant results will be interpreted as 'underpowered to detect small effects' rather than 'no effect'.

## Compute Feasibility
*   **CPU-First**: All training and inference will run on CPU using `torch` and `transformers` with quantization.
*   **No GPU Offload**: The plan strictly adheres to CPU-only execution. If a model cannot run on CPU, the experiment is halted.
*   **Scaling**: If the full AIME dataset is too large, a random sample of problems will be used.

## Risks & Mitigations
*   **Risk**: No verified 1B MoE model exists on HuggingFace.
    *   **Mitigation**: Use `Qwen/Qwen1.5-MoE-A2.7B` (2.7B) with int8 quantization. If this fails, use `state-spaces/mamba-1.3b` (SSM) as the sole alternative, clearly labeling the limitation.
*   **Risk**: `HuggingFaceH4/aime_2024_verified` is unavailable.
    *   **Mitigation**: Generate 'Teacher-Verified' labels via `label_generator.py` and document the proxy nature.
*   **Risk**: Memory overflow on 7GB RAM.
    *   **Mitigation**: Enforce batch size = 1, use int8 quantization, and implement `memory_guard.py` with hard floor logic.
*   **Risk**: No verified 'Post-RL' checkpoint.
    *   **Mitigation**: Halt the experiment and report the missing artifact. No SFT proxy will be used.
