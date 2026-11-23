# Research: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

## Overview

This research investigates the drivers of ingredient substitution success. **CRITICAL REFRAME**: Due to the unavailability of verified independent datasets (FlavorDB, Counterfactual Recipe Generation), the study is explicitly defined as a **"Correlational Analysis of Corpus Bias"**. The core hypothesis is that **semantic similarity** (via Recipe1M embeddings) and **functional role** (derived from ingredient position/frequency) are *associatively* linked to culinary compatibility (Recipe1M ratings) *within the same corpus*, acknowledging that the outcome variable is inherently coupled with the predictor (co-occurrence frequency). The study aims to quantify this associative strength and the degree of data leakage, not to claim causal independence.

## Dataset Strategy

| Dataset | Purpose | Verified Source / Loader | Usage in Pipeline |
|---------|---------|--------------------------|-------------------|
| **Recipe1M** | Source of ingredient co-occurrence frequencies, semantic embeddings, and ratings. | `datasets.load_dataset("AnonymousSub/recipe1m_vit_base_embeddings")` (Parquet shards). | Used to construct the global co-occurrence matrix $C$, derive "semantic_similarity" (cosine similarity of embeddings), and derive the binary `compatibility_label` (from ratings). |
| **FlavorDB** | *Unavailable*. Replaced by Recipe1M embeddings. | **NO verified source found**. | **Proxy Strategy**: Recipe1M visual/text embeddings are used as a proxy for "flavor similarity". A "Proxy Validation" step is mandated to correlate these embeddings with known chemical similarity pairs (from literature) to establish construct validity. |
| **Counterfactual Recipe Generation** | *Unavailable*. Replaced by Recipe1M ratings. | **NO verified source found**. | **Proxy Strategy**: Recipe1M ratings are used as the outcome variable. A "Schema Verification" step is performed on the Recipe1M ratings schema to ensure data integrity. |

**Dataset Strategy Rationale**:
- **Recipe1M**: Verified via Hugging Face `datasets` loader. Used for co-occurrence, embeddings, and ratings.
- **FlavorDB**: **NO verified source** in the provided block. The plan uses **Recipe1M embeddings** (verified) as the proxy for "semantic similarity", with an explicit "Proxy Validation" step.
- **Counterfactual Recipe Generation**: **NO verified source** in the provided block. The plan uses **Recipe1M ratings** (verified) as the outcome variable, with an explicit "Schema Verification" step.

## Statistical Methodology

### 1. Data Pre-processing
- **Normalization**: Ingredient names mapped to canonical IDs using Levenshtein distance (threshold ≤ 2) against the verified Recipe1M vocabulary.
- **Co-occurrence**: Log-transformed counts $C_{ij} = \log(1 + \text{count}(i, j))$.
- **Semantic Similarity**: Cosine similarity between ingredient embeddings (from Recipe1M). **Note**: This is a "semantic" proxy, not "chemical".
- **Functional Role**: Derived from ingredient position in the list and frequency, **excluding** co-occurrence counts to prevent multicollinearity (though circularity with outcome remains).
- **Proxy Validation**: A small, manually curated set of known chemical similarity pairs is used to validate the Recipe1M embeddings as a proxy. If correlation is weak, the study is halted or redefined.

### 2. Model Fitting
- **Logistic Regression**: $P(Y=1) = \sigma(\beta_0 + \beta_1 \text{Sim} + \beta_2 \text{Role} + \beta_3 \log(C))$.
  - Regularization: L2 (Ridge).
  - Validation: **Nested Model Comparison** using AIC/BIC (replacing LRT for "independence" claims) to test if semantic similarity adds predictive value *within the corpus*.
  - **Partial Correlation**: Used to control for the shared variance between frequency and ratings, estimating the unique contribution of semantic similarity.
- **Hierarchical Bayesian**: PyMC (CPU-based NUTS) on a **downsampled dataset (N=50,000 pairs)** to ensure CPU completion within 6 hours.
  - Priors: Weakly informative.
  - Convergence: R-hat ≤ 1.05, ESS ≥ 200.

### 3. Diagnostics
- **VIF**: Variance Inflation Factor for all predictors. Target: VIF < 5.
- **Data Leakage Audit**: A model is trained to predict 'frequency' from 'semantic similarity' to quantify the degree of leakage. This metric is reported in the final analysis.
- **Power Analysis**: Conducted *before* full download to determine sample size $N$ (capped at 50k) for detecting effect size $\ge 0.1$ with $\ge 80\%$ power.

## Compute Feasibility

- **CPU-First**: All models (Logistic, Bayesian) are planned for CPU execution on the downsampled dataset (N=50,000 pairs).
- **GPU Escape Hatch**: Not required for this statistical analysis.
- **Streaming**: Recipe1M parquet files are streamed (`streaming=True`) to avoid RAM overflow.

## Decision/Rationale

- **Why CPU?** The statistical models (Logistic Regression, Bayesian NUTS on N=50k) are computationally tractable on CPU.
- **Why Recipe1M Embeddings for Flavor?** Verified FlavorDB source is missing; Recipe1M embeddings are the only verified vector source. **Proxy Validation** step added to establish construct validity.
- **Why Proxy Outcome?** Verified Counterfactual source is missing; Recipe1M ratings are the only available proxy. **Constitution Exception** documented for circularity.
- **Why N=50k?** Derived from power analysis and benchmark to ensure CPU completion within 6 hours.
