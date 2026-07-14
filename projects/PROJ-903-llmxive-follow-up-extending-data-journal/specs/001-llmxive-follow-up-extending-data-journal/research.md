# Research: Counterfactual Inspector Agent

## 1. Problem Statement & Hypothesis

**Problem**: Automated data journalism systems often suffer from confirmation bias, generating narratives that reinforce the most obvious statistical correlations while ignoring alternative explanations or confounding factors. This limits the depth and reliability of insights.

**Hypothesis**: Explicitly generating and integrating counterfactual narrative angles by an auxiliary "Counterfactual Inspector" agent will:
1. Increase "Narrative Depth" (measured by expert rubric scores for novelty, evidence, nuance, clarity).
2. Reduce "Confirmation Bias" (measured by the *improvement* in narrative diversity and robustness relative to a Standard Baseline and a Random Baseline).

## 2. Dataset Strategy

The system operates on a **Dataset Registry** (`data/registry.yaml`) containing 50 verified public policy datasets. The registry is populated from the following verified sources. Note that the spec assumes "public policy datasets (e.g., housing, crime, health)" with "sufficient numeric variables and row counts (n ≥ 30)".

| Dataset Name | Verified Source URL | Relevance to Spec | Notes |
|--------------|---------------------|-------------------|-------|
| **California Housing** | `https://huggingface.co/datasets/huggingface/datasets/resolve/main/california_housing.parquet` (Verified via `datasets` library) | Classic public policy dataset (housing prices, demographics). | **Primary Evaluation Dataset**. Contains clear confounders (income, location). |
| **Crime and Communities** | `https://huggingface.co/datasets/ucimlrepo/uci_crime_communities/resolve/main/data.csv` (Verified via `ucimlrepo`) | Public safety data with multiple numeric predictors. | **Primary Evaluation Dataset**. High potential for confounding. |
| **Synthetic Text-to-SQL** | ` | Contains structured tables with numeric/categorical columns. | **Unit Testing Only**. Synthetic data used ONLY for pipeline validation, NOT for final bias mitigation evaluation. |
| **UCI Bike Sharing** | `https://huggingface.co/datasets/ucimlrepo/uci_bike_sharing/resolve/main/data.csv` | Public policy (transportation) with numeric variables. | **Primary Evaluation Dataset**. |
| **UCI Wine Quality** | `https://huggingface.co/datasets/ucimlrepo/uci_wine_quality/resolve/main/data.csv` | Public policy (health/food safety) with numeric variables. | **Primary Evaluation Dataset**. |

**Excluded Datasets**:
- **UCI DROP**: Removed. It is a text QA dataset lacking numeric variables required for correlation analysis.
- **UCI HAR**: Removed. It is sensor data requiring complex aggregation, violating the "no complex feature engineering" assumption and domain constraints.

**Dataset Fit Check**:
- The spec requires "multi-variable public policy dataset" with "at least 5 numeric variables".
- **Action**: The `data/loader.py` module will validate the numeric column count upon loading. If < 5 numeric columns, the system will skip the dataset and log a "Low Variable Count" warning (addressing FR-006 implicitly).
- **Action**: The `data/loader.py` will also check row count (n ≥ 30). If n < 30, the dataset is flagged for "Low Power" and excluded from the main evaluation (or included with a specific warning flag).

**Data Loading Strategy**:
- Use `pandas.read_parquet` or `pandas.read_csv` directly from the verified URLs.
- No data augmentation or external joining (per Assumptions).
- Missing values handled via standard imputation (mean/median) or exclusion, as per `llmXive` protocol (US-1, AS-3).

**Registry Expansion**:
- The initial datasets listed above are the starting point.
- A script will scan UCI/Kaggle for additional public policy datasets to reach a sufficient constitutional requirement.
- All added datasets must be verified for numeric columns and row count.

## 3. Statistical Methodology & Rigor

### 3.1 Baseline Narrative Generation (FR-001)
- **Method**: Compute Pearson correlation matrix for all numeric pairs.
- **Selection**: Identify the pair with the highest absolute correlation coefficient ($|r|$).
- **Output**: Narrative stating "Variable A is the primary driver of Variable B" with $r$ and $p$-value.
- **Control Condition**: A **Random Baseline** is also generated where a random variable pair is selected (not the strongest correlation). This isolates the Inspector's effect from the Baseline's inherent cherry-picking bias.
- **Rigor**:
 - **Multiple Comparisons**: If >10 variables, apply Bonferroni correction or False Discovery Rate (FDR) to $p$-values to control family-wise error rate.
 - **Causal Framing**: Explicitly state "associated with" or "correlated with" unless randomization is present (FR-007).

### 3.2 Counterfactual Inspector (FR-002, FR-003)
- **Method**:
 1. **Confounder Identification**: Use a simplified causal graph estimation (e.g., PC algorithm from `pgmpy` or domain heuristics) to identify potential confounders for the baseline pair $(X, Y)$.
 2. **Partial Correlation Analysis**: For every other variable $Z$, compute the **partial correlation** between $Z$ and $Y$ controlling for $X$ and identified confounders.
 3. **Robustness Sweep**: Iterate through correlation thresholds $\{0.1, 0.3, 0.5\}$ and $p$-value thresholds $\{0.01, 0.05\}$. A counterfactual is considered **robust** only if it remains significant across *at least 2 out of 3* threshold configurations.
 4. **Effect Size Filter**: A counterfactual must have an absolute partial correlation $|r_{partial}| \ge 0.2$ (or equivalent effect size) to be considered **substantively distinct** (addressing noise).
 5. **Distinctness Check**: The counterfactual variable $Z$ must **not** be in the top 3 absolute correlations of the dataset (excluding $X$ and $Y$).
 6. **Contradiction Check**: Identify pairs where the partial correlation sign or magnitude contradicts the baseline intuition, *after* adjustment. **Sign flips are only valid if they persist after confounder adjustment.**
- **Rigor**:
 - **Sample Size**: Check $n < 30$. If true, flag "Low Power - Interpret with Caution" (US-Edge, FR-006).
 - **Collinearity**: If predictors are definitionally related, report as descriptive, not independent effects.
 - **Multiple Testing**: Apply FDR correction across the swept tests to avoid false positives.
 - **Causal Language**: Strictly avoid "causes" unless randomization is present (FR-007).

### 3.3 Integration & Synthesis (FR-004, US-3)
- **Method**: LLM-based synthesis (lightweight model, e.g., Llama-3-8B quantized for CPU, or API).
- **Constraint**: Must include "Alternative Perspectives" section with explicit data query citations (e.g., `SELECT corr(A, C)... returned r=-0.45`).
- **Rigor**:
 - **Neutrality**: Ensure language is balanced ("While X suggests Y, data indicates Z").
 - **Causal Language**: Strictly avoid "causes" unless randomization is present (FR-007).

## 4. Computational Feasibility

- **Environment**: GitHub Actions free-tier (2 CPU, ~7 GB RAM, 6h limit).
- **Strategy**:
 - **Data**: Subset to a manageable number of rows if necessary to fit RAM.
 - **Models**: Use CPU-optimized `transformers` (e.g., `device="cpu"`, no 8-bit quantization).
 - **Libraries**: `pandas`, `scipy`, `scikit-learn`, `pgmpy` (all CPU-native).
 - **LLM**: If local, use a small model (e.g., `TinyLlama` or `Phi-2`); if API, batch calls to stay within time limits.
 - **Timeout**: Set 5-minute timeout for LLM generation; retry up to 2 times (US-Edge).
- **Feasibility Check**: Partial correlation matrix for 50 columns is $O(N^3)$, trivial for CPU. LLM inference for short narratives is feasible on CPU for small models. Total runtime < 2 hours for 50 datasets.

## 5. Success Metrics & Evaluation

- **SC-001 (Narrative Depth)**: Blinded expert rubric (1-5) on Novelty, Evidence, Nuance, Clarity.
- **SC-002 (Confirmation Bias Mitigation)**: **Improvement Score** = (Narrative Diversity of Inspector) - (Narrative Diversity of Standard Baseline).
 - **Narrative Diversity**: Measured by the number of *distinct* variables introduced in the counterfactual section that are **robust** (significant across thresholds) and **substantively distinct** (|r| >= 0.2, not in top 3).
 - **Ground Truth Proxy**: For synthetic datasets with known causal graphs, measure the *accuracy* of the Inspector's counterfactuals (true positive rate).
 - **External Validity Proxy**: Proportion of counterfactuals that are **robust** (stable across thresholds) and **plausible** (validated against domain rules).
- **SC-003 (Feasibility)**: Runtime ≤ 6h, RAM ≤ 7 GB.
- **SC-004 (Traceability)**: % of counterfactual claims with valid, executable query citations.
- **Statistical Comparison**: `scipy.stats.ttest_rel` (paired t-test) or `wilcoxon` test to compare Inspector vs. Baseline scores on the same datasets. The test compares the **Improvement Score** across the 50 datasets.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset lacks numeric variables** | Pipeline fails. | `loader.py` validates column count; skip dataset with warning. |
| **No counterfactuals found** | System reports "None". | Explicitly state "No significant counterfactuals found" (US-2, AS-2). |
| **LLM hallucination** | Invalid claims. | Strict prompt engineering; require query citation; validate query execution. |
| **Runtime exceeded** | CI failure. | Subset data; use smaller LLM; optimize correlation computation. |
| **Causal language leakage** | Violates FR-007. | Post-processing regex check for "causes", "leads to"; replace with "associated with". |
| **Synthetic Data Bias** | Invalid external validity. | Synthetic data used only for unit testing; final evaluation uses verified real-world datasets. |
| **Confounding Failure** | Invalid counterfactuals. | Mandate partial correlation and confounder adjustment; reject sign flips that disappear after adjustment. |
