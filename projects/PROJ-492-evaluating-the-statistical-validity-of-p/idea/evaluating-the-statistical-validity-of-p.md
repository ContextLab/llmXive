---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Statistical Validity of Publicly Available A/B Test Summaries  

**Field**: statistics  

## Research question  

To what extent do publicly available A/B test summaries report statistically consistent results—specifically, do the reported p‑values, effect sizes, and sample sizes align with those recomputed from the original raw outcome counts under standard hypothesis‑testing assumptions at a 95 % confidence level?

## Motivation  

A/B testing drives product decisions across many online services, yet the way experiment results are reported is often informal and unstandardized. Inconsistent statistics can mislead stakeholders and propagate erroneous conclusions. Quantifying the prevalence of such inconsistencies will reveal the reliability of publicly shared experiment claims and motivate clearer, community‑adopted reporting guidelines.

## Related work  

- [Preferred Reporting Items for Systematic Reviews and Meta‑Analyses: The PRISMA Statement (2009)](https://doi.org/10.7326/0003-4819-151-4-200908180-00135) — Provides a widely‑adopted checklist for transparent reporting; demonstrates that systematic reporting improves reproducibility, though it does not address individual A/B tests.  
- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Audits statistical reporting consistency in publicly released healthcare quality reports, offering a methodological precedent for systematic validity checks of released statistics.

## Expected results  

We anticipate that 20 %–40 % of the sampled public A/B test summaries will contain at least one statistical inconsistency (e.g., a reported p‑value that cannot be reproduced from the disclosed raw counts). The observed inconsistency proportion will be compared to a baseline error rate of 5 % (derived from prior studies of reporting mistakes). A binomial test (α = 0.05) will assess whether the observed proportion exceeds this baseline, and a 95 % Wilson confidence interval will be reported for the inconsistency proportion.

## Methodology sketch  

- **1. Corpus construction**  
  1.1. Compile a curated list of ≥ 100 URLs that host publicly posted A/B test summaries (company engineering blogs, GitHub “ab‑test” repositories, OpenML experiment records). Record for each URL: publication date, source type, licensing information.  
  1.2. From this list, randomly select 30 summaries for **manual annotation** (human verification of extracted raw counts, effect sizes, and p‑values). These annotated cases will serve as a gold‑standard benchmark.  

- **2. Automatic extraction of reported statistics**  
  2.1. Run a lightweight Python script (regex + spaCy) on each HTML/Markdown page to extract:  
     - Reported raw outcome counts for control and variant (e.g., conversions / impressions).  
     - Reported effect size (difference in conversion rates or lift %).  
     - Reported significance metric (p‑value, test statistic, or 95 % confidence interval).  
  2.2. Flag entries missing any of the three raw‑count fields for manual review; exclude them from the quantitative inconsistency analysis.  

- **3. Re‑computation of significance (independent of reported effect size)**  
  3.1. Using the extracted raw counts *(c₁, n₁)* for control and *(c₂, n₂)* for variant, compute:  
     - Two‑proportion z‑test p‑value via **SciPy** (`stats.proportions_ztest`).  
     - Effect size as the difference in observed proportions (Δ̂ = c₂/n₂ − c₁/n₁).  
     - 95 % confidence interval for Δ̂ using the Wilson method (`statsmodels.stats.proportion.proportion_confint`).  
  3.2. Perform the same calculations with **statsmodels** as an *independent library* to obtain a second set of ground‑truth p‑values; any discrepancy > 1 % between the two libraries triggers a warning but does not affect the main inconsistency check.  

- **4. Inconsistency detection (concrete, operational rule)**  
  A summary is flagged **inconsistent** when **any** of the following holds:  
  - **P‑value discrepancy**: \|p_reported − p_recomputed\| > 0.05 (absolute difference).  
  - **Sample‑size discrepancy**: \|n_reported − max(n₁,n₂)\| / max(n₁,n₂) > 0.05 (i.e., > 5 % relative difference from the larger extracted count).  
  - **Effect‑size discrepancy**: \|effect_reported − Δ̂\| > 0.05 × |Δ̂| (i.e., > 5 % relative tolerance).  
  - **Confidence‑interval mismatch**: the reported 95 % CI does **not** contain the recomputed Δ̂.  

- **5. Synthetic validation dataset (independent ground truth)**  
  5.1. Generate 1,000 simulated A/B experiments with known parameters (n₁, n₂, true conversion rates).  
  5.2. Compute *true* p‑values using **statsmodels** (`statsmodels.stats.proportion.proportions_ztest`).  
  5.3. Introduce reporting errors at controlled rates (5 % and 10 %) by perturbing one of: raw counts, reported p‑value, or reported effect size.  
  5.4. Apply the full extraction + re‑computation + inconsistency‑detection pipeline to the *perturbed* reports. Because the true parameters are known, compute precision, recall, and F1 of the detector.  

- **6. Aggregate analysis**  
  6.1. Let *k* be the number of inconsistent summaries out of *N* total examined (excluding those flagged for missing raw counts).  
  6.2. Perform an exact binomial test of H₀: π = 0.05 vs H₁: π > 0.05, where π = k/N, using α = 0.05.  
  6.3. Report a 95 % Wilson confidence interval for π.  

- **7. Subgroup exploration (bounded scope)**  
  7.1. Summarize inconsistency rates by source type (blog, repository, benchmark) and by publication year.  
  7.2. Apply Fisher’s exact test only when a subgroup contains ≥ 10 entries; otherwise report descriptive rates.  

- **8. Reproducible research package**  
  8.1. Package all extracted data, analysis scripts, the synthetic‑validation generator, and a **Dockerfile** (Python 3.11, pandas, SciPy, statsmodels, spaCy) in a public GitHub repository.  
  8.2. Provide a single command (`docker build -t ab‑audit . && docker run --rm ab‑audit`) that runs the complete pipeline end‑to‑end.  

- **9. CI‑friendly execution**  
  9.1. The pipeline is split into ≤ 10 atomic steps, each ≤ 30 minutes on a 2‑core, 7 GB RAM GitHub Actions free‑tier runner.  
  9.2. All intermediate artefacts are streamed to disk and deleted after use to keep peak RAM ≤ 6 GB and total runtime ≤ 4 hours.  

## Duplicate-check  

- Reviewed existing ideas: PRISMA reporting standards audit, hospital outcomes profiling consistency, digital experimentation transparency.  
- Closest match: Hospital Outcomes Profiling (2007) — similar statistical auditing methodology but applied to healthcare rather than digital A/B testing; different domain constructs and data sources.  
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-25T05:49:33Z
**Outcome**: exhausted
**Original term**: Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics
**Verified citation count**: 0

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics | 0 |

### Verified citations

(none)
