# Research: Socratic Transformers (Negative Selection on Belief)

## 1. Problem Definition

The research investigates whether a language model can improve its reasoning capabilities through **negative selection on belief**. Unlike "self-teaching" (which implies internal knowledge generation), this mechanism treats the model as a population of reasoning traces subject to **evolutionary pressure**.

**Hypothesis**: Fine-tuning a model on a dataset where incorrect reasoning paths are explicitly critiqued (Selection Condition) will yield higher accuracy on held-out benchmarks compared to:
1.  **Static Condition**: Standard QA pairs (augmented to 4-turns with neutral placeholder).
2.  **Ablation Condition**: Dialogue pairs where the critique is replaced by a neutral placeholder (control for token length).

If the Selection Condition outperforms the Ablation Condition, it validates that the *content* of the adversarial critique (the negative selection signal) drives improvement, not merely the presence of additional context.

## 2. Dataset Strategy

The study relies on three verified, open-source datasets for reasoning. All are available via Hugging Face `datasets` library, ensuring programmatic download on CI.

| Dataset | Verified Source URL | Role | Variable Fit |
| :--- | :--- | :--- | :--- |
| **GSM8K** | `https://huggingface.co/datasets/openai/gsm8k` (via `datasets.load_dataset("openai/gsm8k", "main")`) | Primary training & evaluation. Contains grade-school math word problems with step-by-step solutions. | **Fit**: Contains `question` (input) and `answer` (target). The step-by-step solution allows for generating "Initial Answer" and "Critique" by splitting the reasoning path. |
| **MATH-500** | `https://huggingface.co/datasets/HuggingFaceH4/MATH-500` (via `datasets.load_dataset("HuggingFaceH4/MATH-500")`) | Secondary evaluation (held-out). Contains high-school level competition math. | **Fit**: Contains `problem` and `solution`. Used strictly for evaluation to ensure no data leakage. |
| **MMLU-STEM** | `https://huggingface.co/datasets/cais/mmlu` (via `datasets.load_dataset("cais/mmlu", "STEM")`) | Primary evaluation for generalization. Contains multiple-choice questions on STEM topics. | **Fit**: Contains `question` and `choices`. Used to test if the "negative selection" mechanism generalizes beyond math word problems. |

**Data Availability & Feasibility**:
- **GSM8K**: ~8.5k training, ~1.3k test examples. Fully downloadable.
- **MATH-500**: 500 test examples. Fully downloadable.
- **MMLU-STEM**: ~2000 test examples. Fully downloadable.
- **Constraint**: The full GSM8K dataset is small enough to fit in memory, but the *generated* dialogue tuples (3x the size) may exceed 7GB RAM if processed naively. The plan will use `streaming=True` or process in chunks to stay within the available memory limit.

**Dataset Mismatch Check**:
- The spec requires "logical contradictions" and "unsupported assumptions" as critique targets.
- **Verification**: GSM8K solutions are deterministic and logical. An adversarial model can be prompted to identify "calculation errors" or "logical leaps" in the initial reasoning. The dataset *does* contain the necessary logical structure to generate valid critiques. No variable mismatch exists.

## 3. Methodology

### 3.1 Data Generation (US1)

**Input**: GSM8K Training Set.
**Process**:
1.  **Static Tuples (Augmented)**: `(question, initial_answer, neutral_placeholder, revised_answer)`. The `neutral_placeholder` matches the token length of a typical critique, and `revised_answer` is identical to `initial_answer` (or a copy). This ensures the Static condition is also 4-turns, controlling for structure.
2.  **Dialogue Tuples (Selection)**:
    -   *Step 1*: Generate `Initial Answer` (using **Llama-3-8B-Instruct** for high-quality generation).
    -   *Step 2*: Generate `Critique` (using **Llama-3-8B-Instruct** with a specific "Critique Prompt" that instructs the model to identify **logical contradictions**, **unsupported assumptions**, and **calculation errors**).
    -   *Step 3*: Generate `Revised Answer` based on the critique.
    -   *Tuple*: `(question, Initial Answer, Critique, Revised Answer)`.
3.  **Ablation Tuples**:
    -   Same as above, but `Critique` is replaced with a **randomly shuffled** version of the critique text that has the **exact same token count** (calculated via tokenizer).
    -   *Tuple*: `(question, Initial Answer, Shuffled Critique, Revised Answer)`.

**Balanced Sampling**: The pipeline will generate a fixed target count (N=1000) for each condition. If the Selection condition yields fewer valid tuples due to quality gate filtering, it will regenerate until N is reached. This ensures equal sample sizes and quality distribution across all three conditions.

**Quality Gate**: Before writing to `data/processed`, a `quality_gate.py` script will filter out tuples where:
-   `Critique` length < 20 tokens (triviality).
-   `Critique` has a BLEU score > 0.8 with `Initial Answer` (repetition).
-   `Revised Answer` is identical to `Initial Answer` (unless the critique explicitly states "No error found").
-   If a tuple fails, it is regenerated.

**Token-Matching Algorithm (FR-007)**: For the Ablation condition, the `critique` text is tokenized using the target model's tokenizer. The token count is recorded. A neutral placeholder string (e.g., "Neutral placeholder text") is generated and padded/truncated until its token count matches the original critique exactly.

### 3.2 Training & Evaluation (US2)

**Model**: **Llama-3-1.5B-Instruct** (4-bit quantized via `bitsandbytes`). *Note: A smaller model is chosen to ensure feasibility on 7GB RAM CPU and 14GB VRAM Kaggle GPU.*
**Method**: LoRA (Low-Rank Adaptation) fine-tuning.
**Conditions**:
-   **Condition A (Selection)**: Fine-tune on Dialogue Tuples.
-   **Condition B (Ablation)**: Fine-tune on Ablation Tuples.
-   **Condition C (Static)**: Fine-tune on Augmented Static Tuples.

**Hardware Strategy**:
-   **CPU-First Attempt**: Run training on 2 CPU cores with 4-bit quantization.
-   **Hard Timeout**: A timeout is enforced per training run using Python's `signal` module. If exceeded, the process is terminated with exit code 137.
-   **GPU Escape Hatch**: If the CPU run fails with OOM (exit code indicating out-of-memory or "CUDA out of memory" string), the system will automatically re-run the same training step on a Kaggle GPU instance (16GB VRAM).
-   **Scaling**: To fit the CI time limit, the training will use a **subset** of the generated data (e.g., 500 examples per condition) if the full dataset causes timeout. This is explicitly noted as a power limitation in the analysis.
-   **Multiple Runs**: **5 independent training runs** (different random seeds) will be performed for each condition to generate a distribution of accuracies.

**Evaluation**:
-   Test on held-out GSM8K test set, MATH-500, and MMLU-STEM.
-   Metric: **Accuracy** (% of correct final answers).
-   **Primary Hypothesis**: Improvement on MMLU-STEM (generalization) is the primary test of the "negative selection" hypothesis. GSM8K and MATH-500 are secondary.

### 3.3 Statistical Analysis (US3)

**Hypothesis Test**: **Independent Samples t-test** (or ANOVA if >2 groups) comparing accuracy distributions across conditions.
-   **Unit of Analysis**: The 'n' is the number of independent runs (seeds), not the number of test samples.
-   **Null Hypothesis ($H_0$)**: No difference in mean accuracy between Selection and Ablation/Static conditions.
-   **Correction**: Bonferroni correction applied for multiple comparisons (A vs B, A vs C, B vs C).
-   **Significance**: $\alpha = 0.05$.

**Power Justification**:
-   With **5 independent runs** per condition, the study is powered to detect large effect sizes ($d > 0.8$) at $\alpha = 0.05$ (Bonferroni corrected).
-   **Limitation**: If the effect size is small, the study may be underpowered. This will be explicitly stated in the results.

**Operationalization of Negative Selection**: The model is trained to map `(Question, Critique) -> Revised Answer`. The "negative selection" is the *computational process* of filtering out incorrect beliefs via the critique, which the model learns to emulate. The model does not learn to "reject" the initial answer in a binary sense, but to generate the correct answer given the negative signal.

**Selection Bias Mitigation**: The pipeline will include "correct" initial answers in the Selection condition (where the critique notes "No error found") to ensure the model learns when *not* to revise. This balances the distribution with the Static condition.

## 4. Statistical Rigor & Constraints

-   **Multiple Comparisons**: Bonferroni correction is mandatory as per FR-006.
-   **Sample Size**: Acknowledged limitation due to CI constraints. If the full dataset cannot be processed, the subset size is fixed and reported.
-   **Causal Inference**: Claims are **associational** regarding the model's internal state. The "selection" is a computational process, not a biological one.
-   **Measurement Validity**: GSM8K, MATH, and MMLU are standard, validated benchmarks for mathematical and general reasoning.
-   **Collinearity**: The `Initial Answer` and `Revised Answer` are definitionally related. The model is trained to map `(Question, Initial, Critique) -> Revised`. The critique is the independent variable of interest.

## 5. Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **Llama-3-1.5B Base Model** | Mandatory for running on 7GB RAM (FR-003) and ensuring LoRA fine-tuning fits within 14GB VRAM (Kaggle). |
| **Llama-3-8B for Generation** | Ensures high-quality critiques (FR-002) without circular dependency (generation vs. fine-tuning). |
| **4-bit Quantization** | Mandatory for running 1.5B models on 7GB RAM (FR-003). |
| **LoRA Fine-tuning** | Efficient parameter update; avoids full model retraining which would exceed memory. |
| **Neutral Placeholder (Shuffled)** | Controls for token length and structure, isolating the semantic value of the adversarial signal (FR-007). |
| **Static Augmentation** | Ensures Static condition is also 4-turns, controlling for dialogue structure. |
| **Balanced Sampling** | Ensures equal N across conditions, preventing confounding by sample size. |
| **Multiple Runs (5 seeds)** | Enables Independent Samples t-test, resolving the "paired" vs "independent" conflict. |
| **Hard Timeout** | Ensures compliance with FR-008 and 6h CI limit. |
| **Kaggle GPU Offload** | If CPU training OOMs, the real computation (not a synthetic stand-in) runs on Kaggle. |