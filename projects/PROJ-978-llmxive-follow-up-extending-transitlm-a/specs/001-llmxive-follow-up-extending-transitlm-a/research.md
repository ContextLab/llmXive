# Research: llmXive follow-up: extending "TransitLM"

## 1. Problem Statement & Scientific Hypothesis

**Hypothesis**: There exists a specific "cognitive horizon" (route length $L^*$) where local adjacency statistics (sufficient for $L < L^*$) become statistically insufficient to uniquely determine valid global transit paths, causing a sharp divergence in route validity between a deterministic, local-statistics-based model and an autoregressive LLM baseline.

**Key Question**: At what route length and topological complexity does the performance of the lightweight model degrade significantly (≥15% absolute drop in validity, p<0.05) compared to the global LLM baseline?

## 2. Dataset Strategy

### Verified Datasets
The primary data source is the **TransitLM** dataset.
*   **Source**: `XYZAILab/TransitLM` (Hugging Face).
*   **Access**: Programmatic download via `datasets.load_dataset`.
*   **Content**: SFT (Supervised Fine-Tuning) data containing transit routes, station sequences, and metadata.
*   **Verification**: The dataset is publicly available on Hugging Face.

### Data Strategy & City Identification
The dataset does not contain a direct `city` column. The plan implements a **City Identification** step:
1.  **Mapping**: A verified mapping file (derived from station name patterns or a small external lookup) will be used to map station names to cities (Beijing, Shanghai, Guangzhou, Shenzhen).
2.  **Filter**: Select records corresponding to these four cities.
3.  **Vocabulary Restriction**: Apply a top-N station vocabulary restriction (N deferred, default a high-frequency threshold). Map out-of-vocabulary stations to `<UNKNOWN>`.
4.  **Stratification**: Split the test set into three strata: Short-haul (<15 stops), Medium-haul (15-30 stops), Long-haul (>30 stops).
5.  **Sampling**: To ensure feasibility within the 6-hour CI window, a stratified random sample (e.g., 500 routes per stratum per city) will be used for the baseline LLM inference. The lightweight model will run on the full filtered set if feasible, or the same sample.

### Dataset Fit & Limitations
*   **Fit**: The dataset contains the required variables: `route_sequence`, `start_station`, `end_station`, `stop_count`.
*   **Limitation**: If the Chinese city subset is too small for stratified analysis, the power of the survival analysis may be low. This will be reported as a limitation.
*   **Power Constraint**: The use of a sampled dataset for the baseline is a power limitation that will be explicitly stated.

## 3. Methodology & Statistical Rigor

### 3.1 Model Architectures
*   **Lightweight Model (Fixed Lookup)**: A deterministic mechanism that, given a current station and local adjacency context (retrieved from a pre-indexed graph), selects the next station with the **highest historical transition frequency** from the training data. This satisfies Constitution Principle VII ("fixed lookup strategy"). No neural network training is performed.
*   **Baseline Model**: An autoregressive LLM (Qwen-1.5-1.8B, quantized to 4-bit/8-bit).
    *   *Constraint*: Must run on CPU. If the model exceeds the 6-hour runtime or 7GB RAM limit, the result is recorded as "timeout/infeasible" to preserve reproducibility. The feasibility is a hypothesis to be tested, not a guaranteed fact.
    *   *Sampling*: Due to computational cost, the baseline will only be run on the stratified sample (500 routes/stratum/city).

### 3.2 Validity Metric (Addressing Uniqueness)
To address the "uniqueness" tautology:
1.  **Valid Path Space Generation**: For each start/end pair, the system computes the set of all geographically valid paths (using **Breadth-First Search (BFS)** on the adjacency graph) to serve as the ground truth set. **This set is generated from the graph structure, independent of the dataset's single ground-truth sequence.**
2.  **Validity Definition**: A prediction is "valid" if it matches **ANY** path in the valid path set. If the ground truth is a single path, the set contains one element, but if multiple valid paths exist, the set contains multiple elements.
3.  **Metric**: Validity rate = (Count of valid predictions) / (Total predictions).
4.  **Hop-Level Validity**: For survival analysis, validity is tracked per hop. A route "survives" as long as the predicted next station is in the valid path set. The first hop where it deviates is the "event".

### 3.3 Statistical Analysis Plan
The analysis uses a **dual-method approach**:

1.  **Survival Analysis (Kaplan-Meier & Cox PH)**:
    *   **Purpose**: To model the cumulative probability of route validity decay (hazard of failure) as route length increases.
    *   **Event**: First hop where the prediction deviates from the *valid path set*.
    *   **Censoring**: Routes that complete successfully or are truncated.
    *   **Test**: Log-rank test to compare global survival curves (Lightweight vs. Baseline). Cox Proportional Hazards model to estimate the hazard ratio of failure per unit of route length, treating route length as a time-dependent covariate to address sequential independence.

2.  **Inflection Point Detection (Point-wise Chi-Squared Scan)**:
    *   **Purpose**: To identify the specific route length $L$ where the validity gap exceeds the 15% threshold (as required by User Story 1).
    *   **Method**: Perform a **Chi-squared test** (or logistic regression) comparing the validity proportions of the two models **at every individual route length L** (e.g., L=1, L=2, ... L=max), not just broad strata.
    *   **Inflection Criteria**: The shortest $L$ where:
        *   $Validity_{lightweight}(L) < Validity_{baseline}(L) - 15\%$ (Absolute margin).
        *   AND the difference is statistically significant (p < 0.05) after correction.
    *   **Effect Size**: Cohen's h will be reported for the proportion differences.
    *   **Multiple Comparison Correction**: Since tests are run across 4 cities and potentially 30+ lengths, apply **Benjamini-Hochberg (FDR)** correction as the primary method to control the false discovery rate, as it is more appropriate for exploratory research with correlated strata than Bonferroni. Bonferroni will be reported as a sensitivity analysis.

### 3.4 Rigor Checks
*   **Collinearity**: Route length and topological complexity may be correlated. The analysis will report the correlation and avoid claiming independent causal effects without further modeling.
*   **Power**: Sample size is limited by the sampling strategy. Power limitations will be explicitly stated.
*   **Assumptions**: The proportional hazards assumption for Cox models will be tested. If violated, a non-parametric fallback (median survival comparison) will be used.

### 3.5 Missing Baseline Protocol
If the empirical baseline run fails (timeout/OOM) for a specific city or stratum:
*   The analysis for that subset will rely on the lightweight model's absolute performance or literature values.
*   The "divergence" claim (inflection point) will be marked as **"inconclusive"** for that subset.
*   The final report will explicitly state that the baseline data is missing, preventing a direct comparison.

## 4. Compute Feasibility

*   **CPU-First**: The lightweight model (lookup) and data preprocessing are designed to run on a minimal core configuration, constrained by limited RAM resources.
*   **Baseline Feasibility**: The Qwen-1.5-1.8B baseline is a **hypothesis to be tested**. The pipeline will attempt to run it on the CPU runner.
    *   *Scenario A*: If it completes within 6 hours, results are recorded.
    *   *Scenario B*: If it times out or OOMs, the result is recorded as "timeout/infeasible".
    *   *No Offload*: No Kaggle GPU offload is permitted to maintain the "single source of truth" reproducibility principle.
*   **Data Streaming**: The dataset will be streamed to avoid loading the full corpus into RAM.
*   **Sampling**: A stratified sample (e.g., 500 routes/stratum/city) is used for the baseline to ensure feasibility.

## 5. Risk Mitigation

*   **Data Sparsity**: If a specific city has insufficient long-haul routes, the stratification for that city will be merged or the analysis will be limited to the aggregate.
*   **Graph Completeness**: The local adjacency graph will be validated against the ground truth (FR-008). If edge overlap <95%, the graph construction method will be adjusted.
*   **Baseline Infeasibility**: If the baseline fails, the study will report the failure and rely on the lightweight model's performance relative to the *theoretical* baseline (if available in literature) or simply report the lightweight model's absolute performance. The divergence claim will be marked as inconclusive.