# Research: Statistical Analysis of Topic Drift in Academic Abstracts

## 1. Problem Statement & Methodology

The objective is to quantify the evolution of research themes (topic drift) in statistics and machine learning literature over the past several decades. The methodology involves:
1. **Data Acquisition**: Fetching abstracts from arXiv and PubMed APIs (primary) with checksummed storage.
2. **Preprocessing**: Tokenization, lemmatization, and filtering (min 20 tokens) with **window-specific stopword lists** to mitigate language drift.
3. **Topic Modeling**: Fitting LDA (k=10) per 5-year window, with **validation** to ensure k=10 is optimal.
4. **Topic Alignment**: Aligning topic indices across windows via cosine similarity of topic-word distributions.
5. **Drift Measurement**: Computing Jensen-Shannon (JS) divergence between **aligned** topic distributions.
6. **Significance Testing**: Permutation testing (n=1000) with **LDA refitting on shuffled data** to generate a null distribution, using **MaxT procedure** for Family-Wise Error Rate (FWER) control.
7. **Confidence Intervals**: Bootstrapping to generate 95% CIs for divergence values.
8. **Sensitivity Analysis**: Sweeping coherence thresholds {0.35, 0.40, 0.45} to report inconsistency rates.

## 2. Dataset Strategy

The plan relies on the following verified sources. Note: The spec requests arXiv and PubMed data. While verified HuggingFace datasets exist for PubMed, they may lack granular `publication_year` metadata required for strict 5-year windows. Therefore, the primary strategy is **API Fetch** (which guarantees year metadata), with static datasets as secondary.

### Verified Datasets

| Source | Description | Verified URL | Usage Plan |
|:--- |:--- |:--- |:--- |
| **arXiv API** | Academic abstracts (XML) | `http://export.arxiv.org/oai2` | **Primary Source**. Fetches abstracts with explicit `publication_year` metadata. |
| **PubMed API** | Medical abstracts (XML/JSON) | ` | **Primary Source**. Fetches abstracts with explicit `publication_year` metadata. |
| **PubMed (HF)** | Medical abstracts (JSONL) | ` | **Secondary**. Used only if API fails or for validation; year metadata must be verified. |
| **PubMed QA (HF)** | PubMed abstracts with Q&A | ` | **Secondary**. Used only if API fails; year metadata must be verified. |
| **LDA (HF)** | Pre-computed LDA topics | ` | **Not used** for training. |
| **Obelisc (HF)** | Large corpus with LDA topics | ` | **Not used**. |

### Dataset Fit Analysis & Mismatch Handling

* **API Primary Strategy**: The plan prioritizes the arXiv and PubMed APIs because they guarantee `publication_year` metadata, which is essential for the strict 5-year non-overlapping windows (FR-004, FR-014).
* **Static Dataset Limitation**: If static datasets (e.g., MedRAG) are used, we will verify the presence of `publication_year`. If missing, we will exclude them or use a proxy (e.g., title year) with a warning in `manifest.json`.
* **arXiv Fallback**: If the arXiv API fails, the study proceeds with PubMed only. This is documented in the `manifest.json` and the final report.
* **Data Freeze**: To ensure reproducibility (Constitution Principle I), fetched data is immediately checksummed and stored in `data/raw/`. Subsequent runs check the checksum before re-fetching.

### Sample Size & Power Justification

* **Target**: [deferred] abstracts per source.
* **Per Window**: 5 windows (2000-2004, 2005-2009, 2010-2014, 2015-2019, 2020-2024).
* **Minimum per Window**: 500 abstracts (per Assumptions).
* **Power**: With n=500 per window, LDA stability is generally acceptable for k=10. The permutation test (n=1000) provides a robust non-parametric p-value estimation without assuming normality.
* **Permutation Sampling**: To ensure n=1000 permutations are feasible within 6 hours on CPU, we will use a **stratified sample** of 2000 abstracts per window for the permutation refits. This maintains representativeness while reducing computational load.

## 3. Statistical Rigor & Methodological Decisions

### 3.1 Multiple Comparison Correction (MaxT)
* **Requirement**: FR-008 requires correction for >1 hypothesis test.
* **Plan**: We perform tests (divergence between Window 1-2, 2-3, 3-4, 4-5). These tests are dependent (share windows).
* **Method**: **MaxT Procedure** (Permutation-based FWER control).
 1. Shuffle window labels across the entire dataset.
 2. Refit LDA models on the shuffled data.
 3. Compute all 4 divergence values for this permutation.
 4. Record the **maximum** divergence value among the 4 pairs.
 5. Repeat the procedure a sufficient number of times to build a null distribution of the maximum divergence.
 6. Compare observed divergences to this null distribution to compute adjusted p-values.
* **Rationale**: This accounts for the correlation between overlapping windows, unlike Benjamini-Hochberg which assumes independence.

### 3.2 Causal Inference & Observational Nature
* **Assumption**: The study is observational. No randomization of time windows.
* **Claim Framing**: Findings will be framed as **associational** ("Topic distributions changed over time") rather than causal ("New technology *caused* topic drift"). No causal claims will be made.

### 3.3 Measurement Validity & Topic Alignment
* **Issue**: "Label Switching" - Topic 0 in Window 1 is not necessarily Topic 0 in Window 2.
* **Solution**: **Topic Alignment Protocol**.
 1. Compute the topic-word distribution matrix for each window.
 2. Calculate cosine similarity between topic vectors of consecutive windows.
 3. Reorder topic indices in Window 2 to maximize the similarity with Window 1.
 4. Propagate this alignment across all windows.
* **Validity**: JS divergence is then computed on **aligned** topic vectors, measuring true semantic drift rather than arbitrary index distance.
* **Language Drift Control**: Window-specific stopword lists are used to mitigate vocabulary drift, but alignment is required for semantic consistency.

### 3.4 Predictor Collinearity
* **Issue**: Topic proportions sum to 1.0 (compositional data).
* **Handling**: We do not treat topics as independent predictors. We treat the *vector* of proportions as a single state. Drift is measured by the distance between these vectors. No "independent effect" claims are made for individual topics.

### 3.5 Computational Feasibility (CPU-Only)
* **Constraint**: 2 CPU cores, 7GB RAM, 6 hours.
* **Strategy**:
 * **LDA**: Use `scikit-learn`'s `LatentDirichletAllocation` with `n_jobs=1` (or 2) and `max_iter=20`.
 * **Permutation Sampling**: For the permutation test (n=1000), we will use a **stratified sample** of 2000 abstracts per window. This reduces the cost of 1000 LDA refits while maintaining statistical power.
 * **Early Stopping**: If runtime exceeds 5 hours, we will log the status but **not** reduce n=1000 (to preserve power). Instead, we will optimize code (e.g., vectorized operations) or reduce the sample size further if absolutely necessary, documenting the trade-off.
 * **Memory Management**: Process windows sequentially; discard intermediate sparse matrices immediately.

### 3.6 Model Quality Gate
* **Requirement**: FR-006 mandates coherence >= 0.4.
* **Plan**: If a window's coherence is < 0.4, the result is flagged as "Unreliable". The permutation test is **not** run for pairs involving this window. The divergence is reported as "Invalid" rather than "Significant/Not Significant". This decouples model quality validation from the drift measurement.

## 4. Risk Management

| Risk | Impact | Mitigation Strategy |
|:--- |:--- |:--- |
| **arXiv API Failure** | High (Loss of half the data) | Proceed with PubMed only; document in `manifest.json`. |
| **Missing Year Metadata** | High (Cannot enforce 5-year windows) | Use API (guarantees year); if static data used, verify year or exclude. |
| **Coherence < 0.4** | Medium (Model invalid) | Flag as "Unreliable"; skip significance test for that pair. Run sensitivity analysis (FR-009). |
| **Runtime > 6h** | High (CI Failure) | Use stratified sampling (2000 abstracts/window) for permutation refits. Optimize code. |
| **Memory > 7GB** | High (CI Failure) | Process windows sequentially; discard intermediate sparse matrices immediately. |
