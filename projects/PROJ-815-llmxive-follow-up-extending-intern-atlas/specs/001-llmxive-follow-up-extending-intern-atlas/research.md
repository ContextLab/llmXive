# Research: llmXive follow-up: extending "Intern-Atlas"

## Dataset Strategy

### Primary Dataset: Intern-Atlas Graph
- **Description**: A methodological evolution graph containing nodes (papers/methods) and edges (relationships like `improves`, `replaces`).
- **Source Status**: **NOT VERIFIED** in the provided "Verified datasets" block.
- **Action**: The pipeline requires this dataset to be present at `data/raw/intern-atlas-snapshot.graphml`. **If missing, the pipeline triggers the Synthetic Fallback Protocol** to generate a reproducible synthetic graph for code validation. **Scientific analysis of real data is aborted** if the file is missing.
- **Verification**: The user must provide the graph file for scientific discovery. The plan assumes the file contains human-annotated edge types. **Synthetic data is generated ONLY for code validation if real data is missing.**

### Secondary Dataset: Retraction Watch Database
- **Description**: External database of retractions with reasons (fraud, error, irreproducibility).
- **Source Status**: **NOT VERIFIED** in the provided "Verified datasets" block.
- **Action**: Pipeline expects a CSV at `data/raw/retraction-watch-dump.csv`. **If missing, the pipeline triggers the Synthetic Fallback Protocol** to generate synthetic labels. **Scientific analysis is aborted** if the file is missing.
- **Note**: The provided "Verified datasets" block only lists `vifactcheck` (fact-checking dataset), which is **not** suitable for this study. The plan proceeds assuming the user will supply the correct retraction data for scientific discovery, but explicitly notes the lack of a verified URL in this block.

### Verified Dataset (Available but Irrelevant)
- **URL**: `
- **Relevance**: This dataset is for fact-checking (VIF) and does **not** contain methodological evolution graphs or retraction labels for the 2010-2018 window. It is **not** used in this analysis.

## Methodological Approach

### 1. Data Extraction & Feature Engineering
- **Filter**: Nodes published between 2010-01-01 and 2018-12-31.
- **Circularity Audit**: **Explicitly verify** that edge types ('improves', 'replaces') are derived from methodological relationships and NOT from retraction outcomes. Exclude any edge types semantically linked to retraction (e.g., 'retracted', 'invalidated') to prevent label leakage.
- **Feature 1: Bottleneck Resolution Ratio (BRR)**
 - Formula: `count(outgoing edges where type in ['improves', 'replaces']) / count(total outgoing edges)`.
 - Edge Case: If total outgoing edges = 0, BRR = 0.0.
 - Constraint: Untyped edges and LLM-inferred edges are excluded from the denominator.
- **Feature 2: Branching Entropy (BE)**
 - Formula: Shannon entropy of the distribution of downstream method types.
 - $H(X) = -\sum p(x) \log p(x)$.
- **Label Mapping**:
 - `1` (Fragile): Retraction due to methodological error/irreproducibility.
 - `2` (Retraction-Only): Fraud/Plagiarism.
 - `0` (Robust): No retraction or other reasons.
 - **Duplicate Handling**: Earliest publication date; if tie, alphabetical by journal.
- **Matching Logic (FR-011)**:
 1. Exact DOI match.
 2. **If DOI fails, use Levenshtein ratio >= 0.85 on title/author.**

### 2. Model Training
- **Model A (Topological)**: Logistic Regression using `[BRR, BE]`.
- **Model B (Baseline)**: Logistic Regression using `[citation_count, publication_year]`.
- **Validation**: **Stratified Time-Based Split** (Train: 2010-2015, Validate: 2016-2018) to ensure temporal independence and **guarantee a minimum of 10 positive cases** in the validation set.
- **Metrics**: AUC-ROC, Precision, Recall, F1.
- **Note**: The target is the *event* of retraction (proxy for fragility). Citation count is a confounder (popular papers get more citations and may be more likely to be retracted if flawed). The model isolates topological signal independent of citation volume. **The analysis is strictly associational, not causal.** The model predicts the *event* of retraction, not the abstract quality of reproducibility, and results are interpreted as such.

### 3. Robustness & Sensitivity
- **Permutation Test**: Shuffle labels **n=1000** times. **Stratified by `field_of_study` and `publication_venue`** to control for confounding. Check if Observed AUC > Mean(Permuted) + 2*Std(Permuted). **Interpretation**: This tests the null hypothesis that the association exists *within* fields/venues, not globally.
- **Threshold Sweep**: Evaluate FPR/FNR at 0.3, 0.5, 0.7.
- **Collinearity Check**:
 - VIF for BRR and BE. Flag if VIF > 5.
 - Mutual Information (MI). Flag if MI > 0.1.
 - **Structural Coupling**: If BRR and BE are highly correlated (due to mathematical coupling), **re-run model using only 'branching_entropy' or a composite metric** and report as sensitivity analysis.
- **Confounding Control**: Stratified permutation with specific keys `field_of_study` and `publication_venue`. **Covariate Adjustment**: Run logistic regression with `field_of_study` and `publication_venue` as controls as a confirmatory step.

## Statistical Rigor & Assumptions
- **Observational Nature**: Claims are strictly associational. No causal inference is made regarding topology causing retraction.
- **Multiple Comparisons**: The permutation test (n=1,000) controls for family-wise error rate.
- **Sample Size**: Power analysis is deferred to the implementation phase. If the dataset is small (<1000 nodes), the study will report this as a limitation.
- **Measurement Validity**: Relies on the accuracy of the Intern-Atlas edge types and Retraction Watch labels.
- **Data Availability**: The study is **infeasible** for scientific discovery if the primary datasets (Intern-Atlas, Retraction Watch) are not provided, as no verified sources exist. The pipeline will run in **Code Validation Mode** using synthetic data if real data is missing.

## Compute Feasibility
- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
 - Use `pandas` for data manipulation (memory efficient).
 - Use `networkx` for graph metrics (CPU only).
 - Use `scikit-learn` for logistic regression (CPU only).
 - No GPU libraries.
 - If graph > 100k nodes, random sample to fit memory.