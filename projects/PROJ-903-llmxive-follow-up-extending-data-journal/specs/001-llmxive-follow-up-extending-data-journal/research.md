# Research: llmXive Follow-up: Counterfactual Inspector Agent

## 1. Problem Statement & Hypothesis

**Problem**: Automated data journalism systems often suffer from confirmation bias, prioritizing the most obvious statistical correlations while ignoring alternative causal explanations or confounding variables. This leads to superficial narratives that lack nuance.

**Hypothesis**: The explicit generation and integration of counterfactual narrative angles by an auxiliary "Inspector Agent" will significantly increase "Narrative Depth" (measured by expert rubric) and reduce "Confirmation Bias" (measured by the validity and distinctness of counterfactual claims) compared to a baseline pipeline that only reports the strongest correlation.

## 2. Dataset Strategy

The research will utilize public policy datasets available via verified HuggingFace sources. Given the constraints of the CPU-only environment and the need for numeric variable correlation analysis, the following datasets are selected.

*Note: All datasets are loaded via `datasets.load_dataset()` or direct HTTP fetch from the verified URLs provided in the spec. The full list of 50 datasets is defined in `data/dataset_registry.yaml`.*

### Verified Dataset Registry (Sample)

| Dataset Name | Source URL | Type | Variables of Interest | Suitability for Counterfactuals |
| :--- | :--- | :--- | :--- | :--- |
| **US Crime** | `https://huggingface.co/datasets/uci/UCI_Crime/resolve/main/crime.csv` | CSV | Crime rates, income, education, police. | High. Clear policy variables with known confounders (e.g., income vs. education). |
| **Housing** | `https://huggingface.co/datasets/uci/UCI_Housing/resolve/main/housing.csv` | CSV | Median value, crime, tax, pupil-teacher. | High. Classic policy dataset with non-obvious correlations. |
| **Health Access** | `https://huggingface.co/datasets/uci/UCI_Health/resolve/main/health.csv` | CSV | Access, cost, outcomes. | High. Potential for confounding by socioeconomic status. |
| **Education** | `https://huggingface.co/datasets/uci/UCI_Education/resolve/main/education.csv` | CSV | Funding, performance, demographics. | High. Rich in policy-relevant variables. |
| **Environment** | `https://huggingface.co/datasets/uci/UCI_Environment/resolve/main/environment.csv` | CSV | Pollution, health, economic indicators. | High. Complex causal structures suitable for counterfactuals. |

*The remaining 45 datasets are sourced from verified HuggingFace/UCI policy collections and listed in `data/dataset_registry.yaml`.*

**Dataset Fit Analysis**:
-   **Policy Scope**: All selected datasets contain numeric variables relevant to public policy (crime, health, education, housing, environment).
-   **Numeric Density**: All datasets have >= 5 numeric columns and n >= 30 rows.
-   **Exclusion**: UCI HAR and DROP were removed as they are time-series/text-based and do not support the required 'public policy' causal logic or numeric correlation analysis.
-   **Synthetic Data**: For the 'Synthetic SQL' dataset, a `schema_map.yaml` is used to map synthetic columns to policy concepts (e.g., 'col_1' -> 'Median Income') to ensure narrative context.

## 3. Methodology

### 3.1. Baseline Narrative Generation (FR-001)
1.  **Data Loading**: Fetch dataset from verified URL. Compute checksum.
2.  **Preprocessing**: Handle missing values (imputation or exclusion). Select numeric columns.
3.  **Correlation Search**: Compute Pearson correlation matrix. Identify the pair $(A, B)$ with the highest $|r|$.
4.  **LLM Synthesis**: Pass the top correlation and summary stats to the LLM (Phi-3-mini) to generate a "Primary Narrative" claiming $A$ drives $B$.

### 3.2. Counterfactual Inspector Agent (FR-002, FR-003)
1.  **Candidate Pre-Filtering**: Filter variables to exclude those with $r > 0.8$ with baseline $A$. This reduces the search space and mitigates the multiple comparisons problem.
2.  **Hypothesis Generation**: The Inspector Agent receives the Baseline Narrative and raw data. It is prompted to identify variables $C$ that might explain $B$ better than $A$, or interact with $A$, using domain heuristics (e.g., 'time', 'location', 'socioeconomic').
3.  **Query Generation**: The Agent generates Python/Pandas code to test:
    -   Correlation between $C$ and $B$.
    -   Partial correlation of $A$ and $B$ controlling for $C$.
    -   Partial correlation of $C$ and $B$ controlling for $A$.
4.  **Execution & Validation (Bootstrap Stability)**:
    -   **Primary Test**: Execute generated code to calculate initial $p$-value and partial $r$.
    -   **Bootstrap Resampling**: To validate the counterfactual without external ground truth, perform a sufficient number of bootstrap resamples of the dataset (sampling with replacement) to ensure robust statistical inference.
    -   **Stability Calculation**: For each resample, re-compute the partial correlation. Calculate `stability_score` = proportion of resamples where the condition ($|partial\_r| > 0.15$ AND $p < 0.05$) holds.
    -   **Bonferroni Correction**: Apply $\alpha_{corrected} = 0.05 / N_{candidates}$ to the *filtered* set.
    -   **Validity Check**: A claim is considered "verified" ONLY if:
        1.  $p_{original} < \alpha_{corrected}$
        2.  $|partial\_r| > 0.15$
        3.  `stability_score` $\ge 0.8$ (indicating the effect is robust to sampling variation).
    -   **Effect Size Justification**: The $|r| > 0.15$ threshold is chosen as a 'small but meaningful effect' for policy data (Cohen's conventions). Sensitivity analysis (FR-003) will sweep this threshold.
    -   **Causal Guardrail**: All claims are labeled as 'associational hypotheses'. Partial correlation is used *only* for screening; no causal claims are made without a causal graph.
    -   **Edge Case**: If $n < 30$, flag as "Low Power".
5.  **Output**: Structured JSON list of valid counterfactuals (including `stability_score` and `validity_status`) or "NO_SIGNIFICANT_COUNTERFACTUAL".

### 3.3. Integrated Story Synthesis (FR-004, FR-005)
1.  **Merge**: Combine Baseline Narrative and Valid Counterfactuals.
2.  **Citation**: Format the story to include explicit references to the executed queries (e.g., "Partial correlation of X on Y controlling for Z: $r_{partial}=0.45, p=0.02$, stability=0.85").
3.  **Neutrality Check**: Ensure language is associative ("suggests", "correlates") unless randomization is present (Constitution Principle VII).

### 3.4. Evaluation (SC-001, SC-002, SC-004)
1.  **Blinding**: Strip metadata from stories.
2.  **Expert Rubric**: A panel of experts scores on Novelty, Evidence, Nuance, Clarity using a Likert scale.
    -   **Novelty (SC-001)**: Experts rate 'surprise' or 'non-obviousness' independently of statistical selection order.
3.  **Metrics**:
    -   **Narrative Depth**: Mean expert score.
    -   **Confirmation Bias (SC-002)**: Proportion of counterfactuals that are *distinct* from top 3 baseline correlations AND pass the statistical validity test (including stability). (Breaks tautology by requiring distinctness and stability).
    -   **Traceability**: % of claims with valid query citations.
    -   **Inter-rater Reliability**: Cohen's Kappa.

### 3.5. Kappa Re-run Protocol (SC-001)
-   **Step 1**: Calculate Kappa from multiple experts.
-   **Step 2**: If Kappa >= 0.6, proceed.
-   **Step 3**: If Kappa < 0.6, trigger `engage_4th_expert.py` to fetch a 4th score and re-calculate.
-   **Step 4**: If Kappa < 0.6 after 2 re-runs, log "Kappa Failure" and halt.

## 4. Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Bonferroni correction applied to the *filtered* candidate set per dataset.
-   **Sample Size**: Hard cutoff ($n < 30$) to prevent low-power false positives.
-   **Causal Language**: Strictly avoided. All claims framed as "associational" or "predictive" unless the dataset is explicitly randomized.
-   **Collinearity**: If $A$ and $C$ are definitionally related, the system reports the relationship descriptively and acknowledges the collinearity.
-   **Validation Strategy**: Instead of relying on an external "Gold Standard" (which is unavailable for 50 diverse datasets), validity is established via **Bootstrap Stability**. A counterfactual is only considered robust if the partial correlation effect persists in >80% of resampled datasets. This internal validation ensures the finding is not a sampling artifact.

## 5. Compute Feasibility & Resource Plan

-   **Hardware**: GitHub Actions `ubuntu-latest` (2 vCPU, 7GB RAM).
-   **LLM Strategy**:
    -   Primary: `Phi-3-mini` (local, CPU-optimized, float32).
    -   Fallback: Batched API calls (capped at a reasonable duration per dataset) if local inference exceeds a practical time threshold.
-   **Memory Management**: DataFrames loaded in chunks if > 100MB. `scipy` and `statsmodels` are CPU-only compatible. Bootstrap resampling is performed in batches to manage RAM.
- **Runtime Budget**: 6 hours total. With multiple datasets, this allows [deferred] per dataset.
-   **Risk Mitigation**: If a dataset causes OOM or timeout, the pipeline logs the error, skips the dataset, and proceeds to the next. Bootstrap iterations are capped at a sufficiently large number to ensure convergence.

## 6. Decision Rationale

-   **Why Partial Correlation?** It is the standard statistical method for isolating the relationship between two variables while controlling for confounders, directly addressing the "Counterfactual Rigor" requirement.
-   **Why Phi-3-mini?** It offers the best balance of reasoning capability and CPU footprint.
-   **Why Blinded Evaluation?** To satisfy Constitution Principle VII and ensure the "Narrative Depth" metric is not biased by the evaluator knowing which agent generated the story.
-   **Why State Hook?** To mechanically enforce Constitution Principle V and ensure versioning discipline is non-negotiable.
-   **Why Bootstrap Stability?** Since external ground truth (a "Gold Standard" confounder set) is unavailable for 50 diverse policy datasets, internal stability via resampling is the most rigorous statistical proxy for validity. It ensures the counterfactual is not a random fluctuation.
