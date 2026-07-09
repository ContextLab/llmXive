# Research: Evaluating the Impact of Code Complexity on LLM Code Understanding

## 1. Problem Statement & Hypothesis

**Hypothesis**: There is a negative monotonic relationship between code complexity metrics (Cyclomatic Complexity, Halstead Volume, Maintainability Index) and LLM performance on **Code Summarization** tasks.
**Null Hypothesis**: No significant correlation exists between complexity and performance.

**Scope Clarification**: The original specification included "Bug Detection" and "Code Completion" tasks. These tasks were removed from the research design because they require synthetic ground truths (injected bugs, truncated code) that introduce severe construct validity threats. Specifically:
- Synthetic bugs (e.g., off-by-one) do not naturally correlate with code complexity metrics, meaning the model's ability to detect them is not a valid proxy for "understanding" complex code.
- Code completion tasks risk measuring memorization of training data rather than logical understanding, and the "correctness" metric is often trivially determined by syntax.
- **Decision**: The project now focuses exclusively on **Code Summarization**, which uses the native `docstring` ground truth in CodeSearchNet, providing a valid measure of code understanding.

## 2. Dataset Strategy

The primary dataset is **CodeSearchNet (Python subset)**. It is verified and reachable via the following canonical HuggingFace source. We will apply a **stratified sampling** strategy to ensure sufficient representation of high-complexity functions.

| Dataset Name | Source URL | Usage |
| :--- | :--- | :--- |
| CodeSearchNet Python (Raw corpus)

The research question and method remain unchanged as per the planning document requirements. References: CodeSearchNet (Raw corpus). | `https://huggingface.co/datasets/kejian/codesearchnet-python-raw-457k` | Primary source for code snippets. |

**Note on Source Selection**: The `kejian/codesearchnet-python-raw-457k` dataset is selected as the primary source because it provides the most comprehensive raw Python code with docstrings, avoiding the ambiguity of multiple resolve links.

**Dataset Fit Verification**:
- **Required Variables**: `code` (source), `docstring` (ground truth for summarization), `func_name` (for context).
- **Availability**: CodeSearchNet provides `code` and `docstring`.
- **Gap Handling**: No synthetic bugs or truncations are used. The study relies solely on the native `code` -> `docstring` relationship.

**Sampling Strategy (Stratified by Complexity)**:
- **Problem**: CodeSearchNet has a highly skewed distribution of complexity (mostly simple functions), which reduces statistical power to detect correlations.
- **Solution**: We will compute complexity metrics on a larger initial sample, then **stratify** the final dataset into three tertiles: **Low**, **Medium**, and **High** complexity. We will oversample from the High complexity bin to ensure balanced representation (e.g., [deferred] Low, [deferred] Medium, [deferred] High).
- **Target Size**: [deferred] functions (actual count depends on the number of valid snippets in each tertile).

## 3. Model Strategy

**Model**: `microsoft/Phi-3-mini-4k-instruct`
**Source**: HuggingFace (Model Hub).
**Feasibility Check**:
- **Hardware Constraint**: GB RAM (GitHub Actions Free Tier).
- **Original Spec Model**: `CodeLlama-7b-Instruct` (~14 GB in FP16) is **physically impossible** to run on 7 GB RAM.
- **Selected Model**: `Phi-3-mini-4k-instruct` (A large-scale language model with billions of parameters).
- **Quantization**: To strictly fit within 7 GB RAM (including OS overhead and context window), the model will be loaded in **4-bit quantization** (`load_in_4bit=True` via `bitsandbytes`).
  - **Estimated Memory**: Significant memory allocation for weights + ~1 GB for runtime/context = ~3.5 GB total. This leaves ~3.5 GB headroom for the Python interpreter and data processing, satisfying SC-003.
- **Constraint**: No GPU. Inference must be batched with batch size 1 and monitored via `memory_guard.py`.

**Task Prompts**:
1.  **Summarization**: "Summarize the functionality of the following Python code in one sentence:\n{code}"

## 4. Statistical Analysis Plan

**Metrics**:
- **Performance**: BLEU-4, ROUGE-L (comparing model output to `docstring`).
- **Complexity**: Cyclomatic Complexity, Halstead Volume, Maintainability Index (computed via `radon`).

**Methods**:
1.  **Multicollinearity Check**:
    -   Compute Variance Inflation Factor (VIF) for the three complexity metrics.
    -   **Decision Rule**: If VIF > 5 for any metric, the analysis will **fall back to Principal Component Analysis (PCA)**. The first principal component (capturing the majority of variance in complexity) will be used as the predictor in the GLM instead of individual metrics.
2.  **Spearman Correlation**: Compute $\rho$ and p-values between the complexity metric (or PCA component) and performance scores.
3.  **Generalized Linear Model (GLM)**:
    -   Family: Gaussian (for continuous scores like BLEU/ROUGE).
    -   Link: Identity.
    -   Formula: `Performance ~ Complexity + Complexity^2` (to test non-linearity).
4.  **Multiple Comparison Correction**: Apply Benjamini-Hochberg procedure to p-values across all tests to control False Discovery Rate (FDR).
5.  **Power Analysis**: Acknowledge that sample size is limited by CI constraints. Report observed effect sizes with confidence intervals. The stratified sampling strategy is designed to maximize power for detecting non-linear effects.

**Assumptions**:
- Errors in code parsing (radon failures) are random and do not bias the complexity distribution significantly.
- The `Phi-3-mini` model is a valid proxy for "LLM code understanding" despite being smaller than CodeLlama-7B.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| OOM (Out of Memory) on CI | Job failure | Use 4-bit quantization (Phi-3-mini); implement `memory_guard.py` to abort/downsample. |
| Radon parse errors | Data loss | Log and exclude; ensure >95% validity (SC-004). |
| Multicollinearity | Unstable coefficients | Implement VIF check; fallback to PCA if VIF > 5. |
| Model hallucination | Invalid metrics | Use strict regex parsing for outputs; fallback to "failed" on parse error. |
| Validity of Summarization | Proxy for "understanding" | Acknowledge in report that summarization is a valid but limited proxy; scope is restricted to avoid invalid synthetic tasks. |