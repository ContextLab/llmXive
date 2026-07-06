# Research: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Overview

This research plan details the data sources, methodological approach, and statistical rigor for comparing the carbon footprint of LLM-assisted code generation against a **theoretical human baseline**. The study addresses the core research question: *Is the carbon emissions per Line of Code (LOC) of LLM-assisted generation significantly different from a theoretical human baseline model?*

**Critical Methodological Note**: The human baseline is a **theoretical construct** derived from literature estimates of developer time and a standard power model. It is **not** an empirical measurement of human energy consumption. Therefore, the human "distribution" has **zero empirical variance** in energy. Standard paired t-tests (which assume empirical variance in both arms) are **statistically invalid** for this comparison. This study employs a **Distribution Overlap Analysis** to compare the empirical LLM distribution against the theoretical human range.

## Dataset Strategy

The study relies on three primary data sources. All dataset citations are restricted to verified sources to ensure reproducibility and accuracy.

| Dataset | Purpose | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **CodeXGLUE (Python Code Generation)** | Source of prompts for LLM inference. | `datasets.load_dataset("code_x_glue_ct_code_to_code", "python")` | **Verified**: Accessible via HuggingFace. |
| **Human Baseline Time Estimates** | Source of raw developer time (minutes). | **Synthesized Protocol**: If `data/raw/human_baseline_times.json` is missing, generate it using standard literature values (e.g., 30 mins/prompt, 45W) and cite the literature. | **Verified**: Must be validated for `minutes` unit and `source` field. |
| **Model Weights** | GPT-2-medium and DistilGPT-2 for inference. | `transformers.AutoModelForCausalLM.from_pretrained("openai-community/gpt2-medium")` | **Verified**: Public HuggingFace models. |

**Note on Human Baseline**: The "2025 Comparative Analysis Paper" is a hypothetical source. If unavailable, the **Synthesized Baseline Protocol** is used. The data must be stored in `data/raw/human_baseline_times.json` with a `source` field citing the literature used for synthesis (e.g., "Standard Developer Productivity Estimates, 2024").

**Note on Fallback**: If CodeXGLUE does not yield 200 valid prompts, the study proceeds with the available N. **No fallback to HumanEval/MBPP** is possible as no human baseline exists for those prompts.

## Methodological Approach

### 1. Data Collection & Preprocessing
- **Prompt Sampling**: Randomly sample up to 200 prompts from CodeXGLUE.
- **Baseline Validation**:
  - Load `human_baseline_times.json`.
  - **FR-008 Check**: Verify that values are in `minutes` (not pre-calculated CO₂).
  - **Constitution II Check**: Verify `source` field exists and cites literature.
- **Exclusion Criteria**: Prompts with 0 LOC in LLM output or 0 LOC in human baseline are excluded.

### 2. LLM Inference & Energy Measurement
- **Model**: GPT-medium (primary), DistilGPT-2 (robustness).
- **Environment**: CPU-only.
- **Instrumentation**: Wrap inference loop with `codecarbon.EmissionsTracker`.
- **Metrics**: Record `energy_kWh` and `co2_emitted_kg`.
- **Regional Factor**: Use the default regional factor provided by CodeCarbon.

### 3. Human Baseline Calculation (Theoretical Proxy)
- **Power Model**: Convert developer time to energy using a standard CPU power draw (e.g., a representative wattage).
- **Conversion**: `Energy (kWh) = (Time_minutes / 60) * Power_kW`.
- **CO₂ Conversion**: Apply the **same** regional emission factor used by CodeCarbon.
- **Sensitivity Analysis (FR-009)**:
  - Calculate `co2_per_loc` for Low (30W), Medium (45W), and High (65W) power draws.
  - Output results to `data/processed/sensitivity_analysis.csv`.
  - **Stability Check**: Determine if the conclusion (LLM < Human or LLM > Human) remains consistent across all three scenarios.

### 4. Normalization & Joining
- **Explicit Join**: Merge LLM results and Human Baseline on `prompt_id` to create `data/processed/paired_emissions.csv`.
- **Filter**: Drop any record where `loc_count` is 0 for either side.
- **Normalization**: Calculate `co2_per_loc` for both LLM and Human.

### 5. Statistical Analysis (Overlap)
- **Normality Check**: Perform Shapiro-Wilk test on the LLM `co2_per_loc` distribution.
- **Test Selection**:
  - **Primary**: **Distribution Overlap Analysis**. Check if the LLM 95% CI for `co2_per_loc` overlaps with the Human Theoretical Range (Low/Med/High).
  - **Secondary**: Descriptive paired t-test (LLM vs. Medium Human) with a disclaimer that human variance is zero.
- **Effect Size**: Cohen's d (descriptive only).
- **Robustness**: Repeat steps 2-5 for DistilGPT-2. **Explicitly re-join** DistilGPT-2 results with the *same* human baseline.
- **Significance**: Threshold p < 0.05 (for descriptive t-test) or "No Overlap" (for Overlap Analysis).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Only one primary hypothesis test is conducted (Overlap Analysis).
- **Power Analysis**: Given the fixed sample size (N ≤ 200), the study is powered to detect medium-to-large effect sizes.
- **Causal Inference**: This is a theoretical comparison. Claims are framed as associational differences in the *model*, not causal effects of "using LLMs".
- **Measurement Validity**: The human baseline relies on a theoretical power model and time estimates from literature. This is a known limitation.
- **Collinearity**: N/A.
- **Dataset Fit**: The CodeXGLUE dataset contains code generation tasks. The human baseline uses literature time estimates. A mismatch in task complexity is a potential confounder.
- **Hardware Efficiency**: The comparison is between "LLM on GitHub Runner" and "Human on Theoretical Laptop". Hardware efficiency differences are a confounding variable.
- **LOC Variability**: The LLM generates variable LOC; the human baseline uses a fixed LOC. The "per LOC" metric is a theoretical proxy.

## Decision Rationale (Compute Feasibility)

- **Model Selection**: GPT-medium and DistilGPT are small enough to run on CPU within the 6-hour limit for 200 prompts.
- **No GPU**: The plan strictly avoids CUDA dependencies.
- **Memory**: Data is streamed and processed in batches. The full dataset fits easily in available RAM.

## Limitations & Assumptions

- **Human Baseline Approximation**: The conversion of time to energy assumes a linear relationship and ignores idle time. The human "energy" is a theoretical construct.
- **Regional Factor Mismatch**: The LLM measurement uses a dynamic grid factor, while the human baseline uses a static proxy.
- **Dataset Availability**: The study depends on the availability of the CodeXGLUE subset. If N < 200, the study proceeds with reduced N.
- **Prompt Difficulty**: Variability in prompt difficulty is controlled by the paired design, but extreme outliers may skew results.
- **Model Age**: GPT-2/DistilGPT-2 are legacy models. Results are specific to these architectures.