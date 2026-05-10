---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Field**: statistics

## Research question

How do common data transformation techniques (Box-Cox, Yeo-Johnson, rank-based) alter the Type I error rate and statistical power of parametric tests (t-test, ANOVA) when applied to non-normal data from real-world distributions?

## Motivation

Researchers routinely apply transformations to satisfy normality assumptions before running parametric tests, yet the empirical consequences for error rates remain under-characterized in the literature. This gap creates a risk of either inflated false positives (if transformations fail to normalize) or unnecessary loss of power (if transformations are applied when not needed). Systematic evidence would guide transformation selection in applied research across biology, social science, and engineering.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex with the following query terms: "data transformation statistical test power", "Box-Cox transformation Type I error", "normalization impact hypothesis testing", and "Yeo-Johnson transformation ANOVA sensitivity". The search returned 8 papers total, all from applied domains (genetics, neuroimaging, RNA-Seq) rather than methodological evaluation of transformation effects on error rates.

### What is known

- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Discusses the broader philosophical context of statistical inference but does not address transformation-specific effects on test properties.
- [The Statistical Analysis of fMRI Data (2009)](http://arxiv.org/abs/0906.3662v1) — Mentions preprocessing and normalization in neuroimaging but does not quantify how transformations affect t-test or ANOVA error rates.

### What is NOT known

No published work has systematically measured how Box-Cox, Yeo-Johnson, or rank transformations change Type I error and power across a range of non-normal distributions. Existing literature applies transformations in domain-specific contexts (e.g., RNA-Seq, fMRI) without isolating their statistical properties. There is no benchmark dataset or protocol for comparing transformation effects on parametric vs. non-parametric test sensitivity.

### Why this gap matters

Applied researchers need evidence-based guidance on when transformations improve inference reliability versus when they introduce artifacts. Without this evidence, the field risks either over-transforming (reducing power) or under-transforming (inflating false positives), with downstream impacts on reproducibility across disciplines.

### How this project addresses the gap

This project will download public datasets from UCI and OpenML, apply standardized transformations, run t-tests/ANOVA/Mann-Whitney U tests, and directly compare error rates and power across conditions. The methodology produces the first systematic benchmark of transformation effects on test sensitivity using real-world non-normal data.

## Expected results

We expect to observe that transformations reduce Type I error for highly skewed distributions but may reduce power for moderately non-normal data. We will confirm this by measuring false positive rates under null conditions and power under alternative conditions across 50+ datasets, with statistical significance assessed via bootstrap confidence intervals.

## Methodology sketch

- Download 50+ public datasets from UCI Machine Learning Repository and OpenML with continuous variables and known group labels (use `wget`/`curl` with explicit dataset URLs).
- Filter for datasets with non-normal distributions (Shapiro-Wilk p < 0.05) and sample sizes N ≥ 30.
- Apply three transformations to each continuous variable: Box-Cox (λ optimized per dataset), Yeo-Johnson (λ optimized per dataset), and rank-based inverse normal transformation.
- For each dataset and transformation, simulate null conditions (shuffle group labels 1000 times) and compute t-test/ANOVA p-values to estimate Type I error rate.
- For each dataset and transformation, compute statistical power by testing known group differences (original labels) and comparing to a baseline non-parametric test (Mann-Whitney U).
- Aggregate results across datasets; compute mean Type I error and power for each transformation-test combination with 95% bootstrap confidence intervals.
- Perform Friedman test (non-parametric repeated measures ANOVA) to assess whether transformation type significantly affects error rates, followed by post-hoc pairwise comparisons with Bonferroni correction.
- Produce summary tables and bar plots (matplotlib/seaborn) showing error rates and power by transformation and test type.

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate

## Scope compliance

- All datasets from public sources (UCI, OpenML) with direct download URLs.
- Computation: 50 datasets × 3 transformations × 3 tests × 1000 null simulations ≈ 150,000 test runs; feasible within 6h on 2 CPU cores using vectorized operations.
- Memory: Each dataset loaded individually; peak RAM usage < 4GB.
- No GPU, no wet-lab, no proprietary data.
