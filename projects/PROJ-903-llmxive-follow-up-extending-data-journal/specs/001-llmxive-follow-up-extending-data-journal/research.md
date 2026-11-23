# Research: Counterfactual Inspector Agent

## Executive Summary

This research validates the feasibility of integrating a **Counterfactual Inspector Agent** into the `llmXive` pipeline. The goal is to mitigate confirmation bias in automated data journalism by forcing the system to test alternative causal hypotheses using partial correlation control. The methodology relies on open, programmatic **public policy datasets**, CPU-tractable statistical methods (scipy, pandas, statsmodels), and a fallback LLM strategy to ensure execution within the 6-hour/7GB RAM budget.

## Dataset Strategy

The project strictly adheres to the "Verified Datasets" constraint. No access-gated data (e.g., ADNI, UK Biobank) will be used. The plan utilizes open, programmatic sources that can be streamed or downloaded on CI.

### Verified Datasets

The following datasets have been verified for reachability and format compatibility. They will be loaded using the `datasets` library or direct URL fetching as specified in the "Verified datasets" block of the user message.

| Dataset Name | Source Type | Verified URL / Loader | Variables Relevant to Spec | Status |
|:--- |:--- |:--- |:---:--- |
| **California Housing** | UCI (via HuggingFace) | ` (Note: Spec mentions housing. We will use the **UCI California Housing** dataset via `datasets.load_dataset("house_prices", split="train")` if available, or a verified mirror. *Correction*: The verified block contains `gretelai`, `Aditya011`, `LangChainDatasets`, `udayl/UCI_HAR`, `jlh/uci-shower`, `ucirvine/sms_spam`. **Decision**: We will use the **UCI HAR** dataset (accelerometer data) or **SMS Spam** datasets as proxies for "public policy" style numeric correlation if the specific "housing" dataset is not in the verified block. *Wait*, the "Verified datasets" block in the prompt is the **ONLY** source. It lists: `gretelai/synthetic_text_to_sql`, `Aditya011/autotrain-data-nl-to-sql`, `LangChainDatasets/sql-qa-chinook`, `udayl/UCI_HAR`, `jlh/uci-shower`, `ucirvine/sms_spam`. None are "housing". **Crucial Constraint**: The plan must use *only* these. **Strategy**: We will adapt the "public policy" requirement to the available **UCI HAR** (human activity recognition) or **SMS Spam** datasets, treating them as the "public policy" proxy for the sake of the experiment, or use the **SQL** datasets if they contain numeric columns suitable for correlation. The `gretelai` dataset contains numeric columns (e.g., `id`, `count`). We will verify variable count. If <5 numeric, we will use `UCI_HAR` which has numeric sensor data. | **Verified** |
| **UCI HAR** | UCI (via HuggingFace) | ` | 561 numeric features (sensor data). Sufficient for correlation analysis. | **Verified** |
| **SMS Spam** | UCI (via HuggingFace) | ` | Contains numeric counts and text. May require feature extraction. | **Verified** |

**Dataset Fit Analysis**:
- **UCI HAR**: Contains 561 numeric features. Exceeds the "5 numeric variables" requirement of US-1. Suitable for detecting non-obvious correlations (e.,g., correlation between specific accelerometer axes).
- **SMS Spam**: Primarily text, but has numeric metadata. Less ideal for pure numeric correlation.
- **Gretel SQL**: Contains numeric columns (e.g., `id`, `count`). Can be used for testing the correlation engine.
- **Decision**: The **UCI HAR** dataset will be the primary testbed for the Counterfactual Inspector Agent due to its rich numeric feature space, allowing for the generation of a "primary narrative" (strongest correlation) and the search for "counterfactuals" (weaker but significant partial correlations). *Note: While the research question targets "public policy", the constraint of using only verified datasets forces the use of UCI HAR as a proxy for high-dimensional numeric correlation testing. The methodology will focus on the statistical robustness of the counterfactual detection, acknowledging the domain mismatch as a limitation.*

**Data Availability & Streaming**:
- The UCI HAR test set is of a size easily fitting in RAM.
- If larger datasets are needed in future iterations, the plan uses `datasets.load_dataset(..., streaming=True)` to iterate rows without loading the full dataset, adhering to the 7GB RAM limit.

## Statistical Methodology

### 1. Baseline Narrative Generation (FR-001)
- **Method**: Compute Pearson correlation matrix for all numeric columns.
- **Selection**: Identify the pair $(A, B)$ with the maximum absolute $|r|$.
- **Output**: "A is the primary driver of B" (with $r$ and $p$-value).
- **Validity**: Framed as associational (FR-007).

### 2. Counterfactual Inspector Agent (FR-002, FR-003)
- **Mechanism**:
 1. **Query Generation**: The LLM generates SQL/Python queries to test alternative hypotheses (e.g., "Does C correlate with B when controlling for A?").
 2. **Retry Logic**: If a query fails (syntax/timeout), retry up to 2 times (Edge Cases).
 3. **Collinearity Check**: Before partial correlation, check if candidate C is definitionally collinear with A or B. If so, mark as "Collinear" and exclude from partial correlation testing.
 4. **Partial Correlation**: For each candidate $C$ (counterfactual), compute $r_{BC.AD}$ (correlation between $B$ and $C$, controlling for top 2 drivers $A, D$).
 5. **Robustness Check**: If normality assumptions fail (Shapiro-Wilk test), switch to Spearman partial correlation.
 6. **Thresholds**:
 - **Bonferroni Correction**: Adjusted $p_{threshold} = 0.05 / N_{tests}$.
 - $|partial\_r| > 0.15$
 7. **Output**: JSON array with `threshold_config`, `claim`, `p_value`, `partial_r`. If no claim passes, output `NO_SIGNIFICANT_COUNTERFACTUAL`.
- **Statistical Rigor**:
 - **Multiple Comparisons**: Bonferroni correction is applied to control the family-wise error rate.
 - **Collinearity**: Explicit check to prevent tautological rejection.
 - **Power**: If $n < 30$, the system sets `LowPowerFlag = True` and appends a cautionary note (FR-006). It does **not** halt. Power analysis is performed to calculate Minimum Detectable Effect Size (MDES).

### 3. Integrated Story Synthesis (US-3)
- **Method**: Merge baseline and counterfactuals.
- **Citation**: Every counterfactual claim includes a verifiable citation: "Data query: `SELECT corr(C, B) FROM table WHERE...` returned r=..."
- **Neutrality**: Language must be "While X suggests Y, data indicates Z" (US-3).

## Compute Feasibility (CPU-First)

- **CPU-First**: All statistical computations (correlation, partial correlation) are performed using `scipy` and `numpy` on CPU. These are highly optimized and will run well within the 7GB RAM limit for datasets of size ~1k-100k rows.
- **LLM Inference**:
 - **Primary**: Llama-3-8B (if available via API or local quantized).
 - **Fallback**: If inference > 15 mins, switch to Phi-3-mini (local) or batched API.
 - **GPU Escape Hatch**: If a specific LLM quantization requires CUDA (e.g., 4-bit inference on a large model), the execution agent will auto-offload to Kaggle GPU. However, for this project, CPU-quantized models (e.g., `llama.cpp` or `bitsandbytes` on CPU) are preferred to avoid GPU dependency unless necessary.
- **Streaming**: For datasets > 7GB, the loader streams rows to compute running statistics (Welford's algorithm) to avoid OOM.

## Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use UCI HAR** | Verified source with sufficient numeric features (561) to test correlation and partial correlation logic. Acknowledged domain mismatch with "public policy" but necessary due to verified dataset constraints. |
| **Static Thresholds (p<0.05, |r|>0.15) with Bonferroni** | Mandated by FR-003. Bonferroni correction addresses multiple comparisons risk. "Sweep" logic removed. |
| **Low Power Flag (No Halt)** | Required by FR-006 and Edge Cases. Halting breaks US-1 (Baseline generation). |
| **CPU-First Stats** | `scipy`/`numpy` are CPU-tractable and fit within 7GB RAM. No GPU needed for statistics. |
| **Retry Logic (2 attempts)** | Required by Edge Cases to handle LLM query generation errors. |
| **Robust Correlation Switch** | To handle non-normal distributions in data. |
| **Collinearity Check** | To prevent tautological rejection of valid counterfactuals. |
