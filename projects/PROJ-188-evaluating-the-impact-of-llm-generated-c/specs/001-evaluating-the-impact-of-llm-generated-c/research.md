# Research: Evaluating the Impact of LLM-Generated Code Explanations

## Summary

This research phase validates the feasibility of the study design, confirms dataset availability, and defines the statistical approach. The study compares three conditions: Code Only, Code+LLM Explanation, and Code+Docstring. The primary outcome is comprehension accuracy (simulated). **This phase uses mock data to validate the pipeline; real human subject data collection is a future phase.**

## Dataset Strategy

### Verified Datasets

The study requires a dataset of code snippets with varying complexity. We will use **HumanEval** (HuggingFace `openai_humaneval`), which provides code snippets and docstrings.

| Dataset Name | Source/URL | Variables Available | Suitability |
| :--- | :--- | :--- | :--- |
| **HumanEval** | `openai_humaneval` (HuggingFace) | `prompt` (code), `docstring`, `entry_point` | **High**. Contains code and docstrings. Complexity is synthetic (see below). |

**Decision**: Use **HumanEval** (subset of 100 snippets).
*   **Download Method**: `datasets.load_dataset("openai_humaneval", split="test", streaming=True)`.
*   **Complexity Labeling**: Since HumanEval lacks explicit "complexity" scores, we assign a **categorical** complexity label (Low, Med, High) based on line count and cyclomatic complexity. **Limitation**: This is a synthetic proxy and may not correlate with human-perceived comprehension difficulty.

### Data Availability & Feasibility

- **Open Access**: HumanEval is open and downloadable via HuggingFace `datasets` library.
- **Size**: The full dataset is small (<100MB), fitting within 7GB RAM / 14GB disk.
- **Streaming**: Used to demonstrate best practices.

### Dataset Limitations

1.  **Synthetic Complexity**: The "complexity" labels are derived from code metrics, not human ratings. This threatens construct validity regarding "comprehension difficulty."
2.  **Docstring Nature**: HumanEval docstrings are functional descriptions, not pedagogical explanations. The study evaluates "LLM-generated text" vs. "functional docstring," not necessarily "pedagogical explanation."

## Statistical Methodology

### Linear Mixed Model (LMM)

Per **FR-005**, the analysis will use an LMM with **participant-only random intercepts**.
- **Formula**: `is_correct ~ condition + C(complexity) + (1 | participant_id)`
- **Justification**: Participants are expected to have different baseline comprehension abilities. A random intercept accounts for this correlation.
- **Fixed Effects**: `condition` (categorical: CodeOnly, CodeLLM, CodeDoc), `complexity` (categorical: Low, Med, High).
- **Interaction**: We will test for `condition * C(complexity)` to see if the benefit of explanations varies by complexity level.
- **Limitation**: The model ignores snippet-level random effects (per FR-005), which may inflate Type I error rates if snippet difficulty varies significantly.

### Multiple Comparison Correction

- **Method**: Tukey's HSD (Honest Significant Difference) for pairwise comparisons of `condition`.
- **Justification**: Controls Family-Wise Error Rate (FWER) when making all pairwise comparisons among 3 groups.

### BLEU Descriptive Analysis (FR-009)

- **Method**: Calculate BLEU score between LLM-generated explanations and the original Docstrings.
- **Reporting**: Report the distribution of BLEU scores.
- **Limitation Statement (FR-009)**: Explicitly state that BLEU measures similarity to the docstring (baseline), not necessarily the *quality* or *pedagogical value* of the explanation. A high BLEU score does not guarantee better comprehension. This is a descriptive statistic, not a validation of quality.

## Power Analysis & Sample Size

- **Current Scope**: 50 mock participants, 100 snippets, 3 conditions.
- **Power Limitation**: This sample size is likely underpowered to detect small-to-medium effect sizes in a mixed model with 100 items.
- **Framing**: This study is a **pilot** to estimate effect sizes and validate the pipeline. Definitive hypothesis testing requires a larger sample size (N > 200) in a future phase.

## Compute Feasibility

- **CPU-First**:
    - **Generation**: CodeLlama is too large for full precision inference on CPU due to high memory requirements. **TinyLlama-1.1B** is selected as the primary model for CPU execution (fits in <4GB RAM). CodeLlama-7B (4-bit quantized) is the fallback if a GPU escape hatch is triggered.
    - **Fallback**: If TinyLlama fails or OOM, fallback to CodeLlama-7B (4-bit) if GPU available, or halt.
    - **Analysis**: `statsmodels` and `pandas` are CPU-optimized and will run instantly.
- **GPU Escape Hatch**: If the CPU run fails due to model size, the execution stage will auto-offload to Kaggle GPU. The plan supports this via `device="cuda"` in the generation script.

## Ethics & PII

- **Anonymization**: `participant_id` will be a random UUID. No names, emails, or IPs will be stored.
- **Filtering**: Responses with `latency_ms < 30000` (30 seconds) will be excluded as "speeders".
- **Consent**: Mock data generation simulates the survey; no real human subjects are involved in this pipeline validation phase.