# Research: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Research Question

Does LLM-assisted code generation (using lightweight models like GPT-2-medium) result in significantly different carbon emissions per Line of Code (LOC) compared to human-written code, when measured under standardized conditions?

## Dataset Strategy

| Dataset | Source | Access Method | Verification Status | Notes |
|---------|--------|---------------|---------------------|-------|
| **CodeXGLUE (Python Code Generation)** | HuggingFace Datasets (`code_x_glue_ct_code_to_code`) | `datasets.load_dataset("code_x_glue_ct_code_to_code", "python")` | **Verified** (Public HF) | Contains prompts and human code solutions. We will sample the Python subset. |
| **GPT-2-medium** | HuggingFace Hub (`gpt2-medium`) | `transformers.AutoModelForCausalLM.from_pretrained("gpt2-medium")` | **Verified** (Public HF) | Lightweight model suitable for CPU inference. |
| **DistilGPT-2** | HuggingFace Hub (`distilgpt2`) | `transformers.AutoModelForCausalLM.from_pretrained("distilgpt2")` | **Verified** (Public HF) | Distilled variant for robustness check. |
| **Human Baseline Time** | Verified Constant (Dhurandhar) | **Synthesized** (Constant Value) | **Verified** (214 minutes) | Based on verified fact: "hour runtime = 214 minutes" (Source: Dhurandhar, Wikipedia). This is a derived constant, not a raw dataset. |
| **CodeCarbon** | PyPI (`codecarbon`) | `pip install codecarbon` | **Verified** (PyPI) | Library for energy tracking. No external dataset URL needed. |

**Dataset Fit Confirmation**:
- **CodeXGLUE**: Verified to contain the required "prompt" and "code" fields for the Python subset (`code_x_glue_ct_code_to_code`). The human solution is code, allowing for valid LOC comparison.
- **Human Baseline**: The study does *not* require a raw dataset of human emissions per prompt. It requires a time estimate to be converted. A representative mean developer time per task is used. This is sufficient for the "Synthesized Baseline Protocol".
- **No Access-Gated Data**: All required data is either public (HF) or synthesized from public constants. No credentials are needed.

## Emission Factor Standardization

To ensure a fair comparison between LLM and Human baselines:
1. **Primary**: Use the regional emission factor reported by CodeCarbon during the LLM run.
2. **Fallback**: If CodeCarbon fails to retrieve a dynamic factor (common in CI environments), default to a static global average of **0.475 kg CO2/kWh**.
3. **Application**: This same factor (dynamic or static) MUST be applied to both the LLM energy calculation and the Human baseline calculation to eliminate grid-intensity as a confounding variable.

## Methodological Approach

### 1. Data Collection & Sampling
- **Source**: CodeXGLUE Python code-generation subset (`code_x_glue_ct_code_to_code`).
- **Sampling**: Random sample of up to 200 prompts (`random.seed(42)`).
- **Validation**: Check for non-empty prompts and existing human solutions.

### 2. LLM Inference & Energy Tracking
- **Model**: GPT-2-medium (Primary), DistilGPT-2 (Robustness).
- **Environment**: CPU-only (`device="cpu"`).
- **Tracking**: Wrap inference loop with `codecarbon.EmissionsTracker`.
- **Output**: JSON record per prompt: `prompt_id`, `energy_kWh`, `co2_kg`.

### 3. Human Baseline Calculation (Synthesized)
- **Input**: `estimated_human_time_minutes = 214` (Verified Constant, Dhurandhar).
- **Power Model**: Standard laptop power draw (typical magnitude).
- **Emission Factor**: Unified factor (from CodeCarbon or fallback 0.475).
- **Calculation**: `human_co2_kg = (time_hours * power_kw * emission_factor)`.
- **Normalization**: `human_co2_per_loc = human_co2_kg / human_loc_count` (where `human_loc_count` is from the CodeXGLUE human solution).
- **Result**: A distribution of `human_co2_per_loc` values, one per prompt, driven by the variance in `human_loc_count`.

### 4. Normalization & Filtering
- **LOC Count**: Count lines in generated code (LLM) and human code (Dataset).
- **Filtering**: Exclude pairs where `llm_loc == 0` or `human_loc == 0` (to avoid division by zero).
- **Metric**: `co2_per_loc` for both LLM and Human.
- **Metric Validity Note**: The metric `co2_per_loc` measures energy density. If the LLM generates significantly more verbose code (higher LOC), the `co2_per_loc` may be artificially low. This is acknowledged as a limitation in the final report.

### 5. Statistical Analysis (One-Sample t-test)
- **Method**: One-Sample t-test (or Wilcoxon Signed-Rank if normality fails) comparing the `llm_co2_per_loc` distribution against the `human_co2_per_loc` distribution.
- **Normality Check**: Perform Shapiro-Wilk test on the differences.
- **Outputs**:
  - Test statistic (t or W).
  - P-value.
  - Effect size (Cohen's d for t-test, rank-biserial for Wilcoxon).
  - 95% Confidence Interval for the mean difference.
  - Significance label ("significant" if p < 0.05).
- **Robustness**: Repeat analysis with DistilGPT-2 to verify direction of effect.
- **Sensitivity Analysis**: Recalculate human baseline using Low, Medium, and High power draws to assess if the statistical significance conclusion remains stable.

## Compute Feasibility

- **CPU-First**: GPT-medium is small enough for CPU inference..
- **Scaling**: A moderate number of prompts × [deferred] per prompt (CPU) ≈ several hours. Well within the -hour limit.
- **Memory**: Sufficient RAM is available for loading the model and processing data..
- **GPU Escape Hatch**: Not required for GPT-2-medium, but if the model were larger, the pipeline would detect CUDA errors and offload to Kaggle (though not needed here).

## Limitations & Assumptions

- **Human Baseline Variability**: The 214-minute estimate is an average. Individual human times vary, but the study treats this as a constant for the "ideal" human baseline. The variance in the human distribution comes solely from LOC counts.
- **Regional Factors**: CodeCarbon uses a dynamic grid factor. The human baseline uses a static factor (or the same dynamic factor if available). A unified factor is used to ensure fairness.
- **Model Capability**: GPT-2-medium may generate low-quality code, affecting LOC counts. The analysis filters 0-LOC outputs.
- **Time Estimate**: The 214-minute value is a verified constant but may not reflect the specific difficulty of every CodeXGLUE prompt.
- **LOC Normalization**: The `co2_per_loc` metric assumes that LOC is a valid proxy for effort. If LLM code is significantly more verbose, this metric may be biased. This is explicitly noted in the report.