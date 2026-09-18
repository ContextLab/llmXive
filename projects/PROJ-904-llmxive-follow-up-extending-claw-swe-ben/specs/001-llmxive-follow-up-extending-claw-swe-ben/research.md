# Research: Context Fidelity vs. Model Scaling Trade-offs

## 1. Research Question & Hypotheses

**Primary Question**: Can high-fidelity context compression strategies (retrieval, summarization) substitute for model parameter scaling in resolving complex software engineering tasks under strict CPU constraints?

**Hypotheses**:
- **H1 (Fidelity Effect)**: High-fidelity context strategies (TF-IDF, Heuristic Keyword-Proxy, Summarization) will yield significantly higher Pass@1 scores than naive truncation for both 1B and 7B models.
- **H2 (Scaling Effect)**: The 7B model will outperform the 1B model across all context strategies.
- **H3 (Interaction)**: We will estimate the magnitude of the interaction effect between model size and context strategy. **Note**: Due to sample size constraints, the study is **Exploratory** regarding H3 if N < 800. We will report the **Odds Ratio (OR) with 95% Confidence Interval** for the interaction term. A null result does not prove the absence of an effect; it indicates insufficient power to detect it. If N >= 800, we will attempt a confirmatory test. **Crucially, given the likely sample size (N < 400) for binary outcomes, the study is underpowered to detect significant interaction effects. The primary claim will be the effect magnitude (OR) rather than statistical significance.**

## 2. Dataset Strategy

### 2.1 Source Selection
The experiment utilizes the **Claw-SWE-Bench** dataset as the primary source.
- **Primary Source URL**: (Use the verified URL from the "# Verified datasets" block for Claw-SWE-Bench).
- **Verification**: This URL is listed in the "# Verified datasets" block. It is a direct Parquet download, suitable for programmatic fetching via `datasets.load_dataset`.
- **Access**: Open access; no credentials required.
- **Fallback**: If Claw-SWE-Bench is unavailable, **SWE-bench Verified** will be used as a fallback, with explicit schema adaptation notes (mapping `problem_statement` to `issue_description`).

### 2.2 Filtering & Complexity Definition (FR-001)
To satisfy the requirement for "context-bound complexity," the dataset will be filtered programmatically using a **Hybrid IR-Seeding** approach to avoid circularity with the test strategies:
1. **Keyword Extraction**: Parse the `issue_description` (or `problem_statement`) via regex to extract file paths (e.g., `.*\.[py|js|ts]`).
2. **Hybrid IR-Seeding**: If no paths are found, use a **frozen generic CodeBERT-base** model to embed the issue description and retrieve the **top-5 files** from the repo based on code similarity. This model is **independent** of the TF-IDF/Diff-Aware strategies.
3. **Graph Traversal**: For each identified file, load the file and count lines. Traverse the import graph (if available) to include direct dependencies, summing their line counts.
4. **Threshold**: Retain only instances where the sum of relevant file lines > 500.
5. **Fallback**: If no instances meet the threshold, the system logs an error and halts (as per Edge Case handling).
6. **Independence Check**: Verify that the correlation between the generic retriever's scores and the experimental strategies is low (<0.3) to ensure the complexity metric is not a function of the strategy.
7. **Representativeness Validation**: Compare the distribution of `Task_Difficulty` (files in patch) and `Issue_Length` between the filtered subset (N>=800) and the full dataset using **Kolmogorov-Smirnov tests**. If p < 0.05, the study will report the selection bias magnitude and include `Task_Difficulty` as a mandatory covariate in the GLM to adjust for the bias.

### 2.3 Data Hygiene
- **Checksumming**: All raw and filtered Parquet files, intermediate JSONL logs, and final aggregated CSVs will be checksummed (SHA256).
- **State Recording**: Checksums and artifact paths will be recorded in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml`.
- **No Modification**: Raw data is preserved; filtered data is written to a new file (`data/filtered_swe_bench_v1.parquet`). **No data may be modified in place; every transformation MUST produce a new file.**

## 3. Methodology & Statistical Rigor

### 3.1 Experimental Design
A 2x4 factorial design:
- **Factor A (Model Size)**: 1B (e.g., `Llama-3.1-1B` or similar CPU-runnable), 7B (Quantized `Q4_K_M`).
- **Factor B (Context Strategy)**:
  1. **Baseline**: First-N-lines truncation (N = 4096 tokens or 8000 lines).
  2. **TF-IDF/BM25**: Relevance-ranked snippets.
  3. **Heuristic Keyword-Proxy**: Identify lines in "relevant files" containing keywords ('fix', 'bug', 'error', 'TODO') and include a 10-line window around them. **Note**: This is a construct validity limitation; the plan acknowledges this is a lower-bound proxy for "diff-aware" retrieval.
  4. **Summarization**: Rule-based (first sentence of paragraph, last sentence of function).

### 3.2 Statistical Analysis (FR-006, SC-003)
- **Model**: Generalized Linear Model (GLM) with Binomial link function.
- **Formula**: `Pass ~ Model_Size + Context_Strategy + Model_Size:Context_Strategy + Task_Difficulty + Quantization_Penalty`
- **Outcome**: Binary Pass/Fail (Pass@1).
- **Predictors**: `Model_Size`, `Context_Strategy`, `Task_Difficulty` (covariate), `Quantization_Penalty` (if needed), and interaction `Model_Size:Context_Strategy`.
- **Correction**: **Firth's Penalized Likelihood** will be used to handle sparse data (separation issues) common in small sample sizes (n < 50 per cell). This is critical for convergence and unbiased coefficient estimation. If `statsmodels` does not support Firth, the system will fallback to `firth-logistic` (Python) or `logistf` via `rpy2`.
- **Multiple Comparisons**: Post-hoc pairwise comparisons will use Bonferroni correction to control Family-Wise Error Rate (FWER).
- **Power Limitation**: If the filtered dataset yields < 800 instances, the study is **underpowered** for detecting interaction effects with >0.80 power. The primary claim will be the **Effect Size** (Odds Ratio with 95% CI) of the interaction term. A null result (p > 0.05) will be interpreted as "insufficient evidence to detect an effect" rather than "no effect". **Given the likely sample size (N < 400), the study is explicitly underpowered for detecting significant interaction effects in binary outcomes. The primary claim is the magnitude of the effect (OR), not statistical significance.**
- **Power Calculation**: 
  - For N=400 (n=50/cell), power to detect a medium interaction effect (Cohen's h=0.3) is ~0.35.
  - For N=800 (n=100/cell), power increases to ~0.80.
  - For N=1200, power reaches ~0.90.
  - The study will proceed with N>=800 for confirmatory claims. If N < 800, the study is strictly Exploratory.

### 3.3 Failure Mode Analysis (FR-008)
- **Classifier**: Deterministic rule-based classifier.
- **Rules**:
  - "Missing Context": Output contains "file not found", "cannot locate", or references file not in input.
  - "Reasoning Error": File exists in context, but logic fails.
- **Metric**: Distribution of failure modes across strategies to validate H1.

## 4. Compute Feasibility & Hardware Strategy

### 4.1 CPU-First Approach
- **Hardware**: GitHub Actions Free Tier (2 vCPU, 7GB RAM, ~14GB Disk).
- **Model Loading**:
  - **1B Model**: Runs natively in default precision.
  - **7B Model**: Must use **Q4_K_M** quantization (GGUF format) to fit within 7GB RAM. The `models/quantization.py` module will handle loading via `llama-cpp-python` or `transformers` with `load_in_8bit` fallback if GGUF is unavailable.
- **Inference**: Batched execution with strict timeout (60 min/instance).
- **Quantization Calibration**: **Mandatory Phase 0 step**. A [deferred] stratified sample of instances will be run with both FP16 (if RAM permits) and Q4_K_M. If the performance drop > 5%, the 'Quantization Penalty' is calculated and added as a confounding factor in the GLM. The 7B results are explicitly labeled as "Quantized-7B".

### 4.2 GPU Escape Hatch
- **Condition**: If CPU inference for 7B model fails due to OOM despite Q4_K_M.
- **Action**: The execution runner will detect the error and re-run the specific instance on a **Kaggle Free GPU** (T4/P100, ~16GB VRAM).
- **Scaling**: On GPU, the model will be loaded in **Q4_K_M** or **FP16** (if VRAM permits) with a reduced batch size to ensure stability.
- **Note**: No synthetic CPU approximation will be used for GPU-bound tasks.

### 4.3 Runtime Budget
- **Per Instance**: 60 minutes (timeout enforced).
- **Total**: ≤ 72 hours (parallel batching of up to 4 instances per runner).
- **Optimization**: Streaming data loading to avoid disk I/O bottlenecks.
- **Global Timeout**: If the total runtime exceeds 72 hours, the system will terminate and report a "Timeout" status for remaining instances.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Claw-SWE-Bench** | Primary dataset mandated by spec. Verified open source with ground-truth unit tests for code generation. |
| **Hybrid IR-Seeding** | Required to avoid circularity where the complexity metric depends on the test strategies. Uses a frozen generic model independent of experimental strategies. |
| **Q4_K_M Quantization** | Only method to fit 7B model in 7GB RAM without losing critical reasoning capacity. |
| **Firth GLM** | Standard GLM fails on sparse binary data; Firth correction is the statistical standard for this scenario. |
| **Exploratory Design** | N=800 is the target for confirmatory tests. If N < 800, the study is Exploratory and reports effect sizes. **Given likely N < 400, the study is underpowered for interaction significance; primary claim is effect magnitude.** |
| **Rule-Based Summarization** | Spec mandates "first sentence of paragraph, last sentence of function"; LLM-based summarization is too costly for this phase. |
| **Heuristic Keyword-Proxy** | Ground-truth diff is unavailable in zero-shot; keyword-based heuristic is the only viable proxy. Acknowledged as a construct validity limitation. |
| **Quantization Calibration** | Mandatory to verify Q4_K_M performance and adjust for any 'Quantization Penalty' in the GLM. |
| **Representativeness Validation** | KS-test comparison of filtered vs. full dataset to ensure external validity. |