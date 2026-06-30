# Research: Reproduce & Validate EffOPD On-Policy Distillation

## 1. Methodology & Feasibility Analysis

### 1.1 Compute Constraints & Strategy
The target environment is a GitHub Actions free-tier runner (limited vCPU, constrained RAM, no GPU, time-limited execution). The original paper likely utilizes GPU clusters for full training.
*   **Strategy**: The validation will focus on **mechanism verification** rather than full performance replication.
    *   **Simulated On-Policy Step**: To validate the "low-rank concentration" of *updates* (not static weights), we will perform a **single training step** (forward + backward pass) on a small batch of data using the `Qwen2.5-0.5B` model. This generates a non-zero update matrix (Delta W = W_new - W_old). SVD is then performed on Delta W. This is a *proxy* for the full on-policy loop; it validates the update mechanism but acknowledges that full loop dynamics cannot be simulated in this environment.
    *   **SFT Baseline Generation**: To validate the "efficiency" claim, we will generate a second update matrix using standard Supervised Fine-Tuning (SFT) on the same data (same learning rate, batch size) but without the EffOPD "Foreseeing" mechanism. This provides a comparative baseline for rank concentration.
    *   **Null Baseline Generation**: To ensure the "concentration" claim is not tautological, we will generate a random Gaussian weight matrix of the same shape and compute its SVD. This establishes the expected energy distribution for a random matrix.
    *   **SVD & Rank Analysis**: These are linear algebra operations on the Delta W matrix. With `scikit-learn` and `numpy`, these can run efficiently on CPU if the matrix size is managed.
    *   **Inference**: We will use a small, CPU-tractable model (`Qwen2.5-0.5B-Instruct`) to generate solutions for `reasoning_eval.py`. This avoids the memory overhead of large models while validating the *format* of the output and the *logic* of the grader.
    *   **Training**: Full training is excluded. The plan validates the *pipeline* and *evaluation scripts* (US-3) on a subset, confirming the code structure works, but does not attempt to reproduce the "3x acceleration" via training.
    *   **Theoretical Efficiency**: Since runtime acceleration cannot be validated on CPU vs GPU, we will calculate theoretical **FLOPs/step** using the formula $2 \times N \times M \times K$ (where $N, M, K$ are matrix dimensions) and compare the **effective rank** of the EffOPD update vs. the SFT and Null baselines. A lower effective rank for the same loss reduction implies higher theoretical efficiency (fewer steps to convergence).

### 1.2 Dataset Variable Fit
*   **Required Variables**: Problem statement (text), Ground Truth (solution), Metadata (difficulty).
*   **Datasets**:
    *   `gsm8k`: Contains math word problems and step-by-step solutions. **Fit**: High. Used for `svd.py` and `upd_rank.py` logic validation. **Keys**: `question`, `answer`.
    *   `aime24`: Contains high-difficulty math problems. **Fit**: High. Used for `reasoning_eval.py` to test the grader's ability to handle complex outputs. **Keys**: `problem`, `solution`.
*   **Verification**: The `EffOPD` codebase must be checked for hardcoded dataset paths. If it expects `data/gsm8k/test.jsonl`, we must generate this file from the Hugging Face `gsm8k` dataset (via `datasets` library) and place it in the expected directory. A data adapter will map HF keys to the internal schema.

### 1.3 Statistical & Measurement Rigor
*   **SVD**: We will compute singular values $\sigma_i$ of the **Delta W** matrix. The "low-rank concentration" claim implies that a small number of singular values capture most of the update energy. We will calculate the cumulative energy ratio $\frac{\sum_{i=1}^k \sigma_i^2}{\sum_{all} \sigma_i^2}$.
*   **Baseline Comparison**: To validate the claim, we will compare the EffOPD update's concentration against two baselines:
    1.  **Null Model**: A random Gaussian weight matrix of the same shape (expected uniform energy distribution).
    2.  **SFT Baseline**: A standard SFT update (computed via a single step on the same data without the "Foreseeing" mechanism) to compare the rank concentration.
*   **Rank Concentration**: The `upd_rank.py` script calculates a concentration score. We will verify the output is in $[0, 1]$ (SC-002).
*   **Pass@k**: For `reasoning_eval.py`, we will generate $k$ solutions per problem (where $k \in \{1, 5, 10\}$) and compute the fraction of problems where at least one solution is correct.
    *   **Baseline for Efficiency**: The Pass@k results will be compared against **Literature Baselines** (expected performance of Qwen2.5-0.5B on GSM8K/AIME24 from public benchmarks) and a **Random Guess Baseline** (1/number_of_options for multiple choice, or exact match for generation). This contextualizes the "efficiency" claim (e.g., "Does this method achieve comparable Pass@k to standard SFT with fewer parameters/steps?").
*   **Collinearity**: N/A for this specific validation (no regression analysis of predictors).
*   **Multiple Comparisons**: N/A (descriptive validation of existing scripts).

## 2. Dataset Strategy

| Dataset | Source (Verified) | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **gsm8k** | `openai/gsm8k` (Hugging Face) | SVD, Rank Analysis | Downloaded via `datasets.load_dataset("openai/gsm8k", "main")`. Subset to a representative sample size. Keys: `question`, `answer`. |
| **aime24** | `HuggingFaceH4/aime24` (Hugging Face) | Reasoning Eval | Downloaded via `datasets.load_dataset("HuggingFaceH4/aime24")`. Subset to a representative sample of manageable size. Keys: `problem`, `solution`. |
| **EffOPD Code** | `NO verified source found` (Vendored Submodule) | Execution | Loaded from `external/EffOPD`. |

*Note: The "Verified datasets" block provided in the prompt does not contain standard academic benchmarks like `gsm8k` or `aime24`. Since these are standard, public datasets available via the Hugging Face `datasets` library, we will use the library to fetch them programmatically using the specific repo IDs listed above. These IDs serve as the formal data resources.*

## 3. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `Qwen2.5-0.5B-Instruct`** | Fits within 7 GB RAM on CPU. Larger models (B+) would OOM. Validates the *grader* logic without needing full-scale inference. |
| **Sample a representative subset of items for SVD** | SVD on full dataset matrices is memory intensive. A sufficient number of samples will provide the necessary statistical signal for the "low-rank" claim verification while staying under RAM limits. |
| **Exclude Full Training** | Full training of LLMs on limited CPU and RAM resources is infeasible (would take days/weeks). The goal is *validation of the code*, not *reproduction of the result*. |
| **CPU-Only PyTorch** | Explicitly install `torch` without CUDA flags to prevent `ImportError` or `RuntimeError`. |
| **Simulated Single Step** | A single step is the minimal unit to generate a non-zero Delta W for SVD, serving as a proxy for the on-policy update mechanism. |
| **Theoretical Efficiency** | Replaces invalid runtime acceleration claims with FLOPs/step analysis and effective rank comparison, which is hardware-agnostic. |
| **SFT Baseline** | Required to validate the "efficiency" claim. Generated by running a standard SFT step on the same data. |
| **Null Baseline** | Required to validate that "concentration" is not a property of random matrices. |

## 4. Limitations

*   **Static Data**: The use of static datasets (`gsm8k`, `aime24`) prevents validation of the dynamic "on-policy" loop (where the model generates data, is trained, and generates new data). The validation is limited to the *mechanism* of update generation and analysis.
*   **Hardware Mismatch**: The "3x acceleration" claim cannot be empirically validated on a 2-vCPU free-tier runner against a paper likely run on multi-GPU clusters. The plan validates the *theoretical* efficiency (FLOPs, rank concentration) instead.
*   **Model Size**: The use of a small model (`Qwen2.5-0.5B`) may not fully capture the dynamics of larger models used in the original paper.

## 5. Risk Assessment

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **OOM on Model Load** | High | Blocking | Use `torch_dtype=torch.float16` and `device_map="cpu"`. If OOM, switch to `TinyLlama-1.1B` or smaller. |
| **Dataset Mismatch** | Medium | Blocking | Pre-flight check: Verify `gsm8k` and `aime24` have `question`/`answer` and `problem`/`solution` keys before running scripts. |
| **Script Dependencies** | Medium | Blocking | Pin all dependencies in `requirements.txt` to CPU-compatible versions. Remove `bitsandbytes`. |
| **Timeout (>6h)** | Medium | Blocking | Enforce strict sample limits (for SVD, a reduced subset for Eval). Add timeout wrappers to scripts. |
| **Invalid Delta W** | Medium | Blocking | Ensure the training step is non-zero by using a learning rate > 0 and a small batch size. |