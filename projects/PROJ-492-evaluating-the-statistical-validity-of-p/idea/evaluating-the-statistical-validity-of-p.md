---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Statistical Validity of Publicly Available A/B Test Summaries  

**Field**: statistics  

## Research question  

To what extent do publicly available A/B test summaries report statistically consistent results—specifically, do the reported p‑values, effect sizes, and sample sizes align under standard hypothesis‑testing assumptions when evaluated at a 95 % confidence level?

## Motivation  

A/B testing drives product decisions across many online services, yet the way experiment results are reported is often informal and unstandardized. Inconsistent statistics can mislead stakeholders and propagate erroneous conclusions. Quantifying the prevalence of such inconsistencies will reveal the reliability of publicly shared experiment claims and motivate clearer, community‑adopted reporting guidelines.

## Related work  

- [Preferred Reporting Items for Systematic Reviews and Meta‑Analyses: The PRISMA Statement (2009)](https://doi.org/10.7326/0003-4819-151-4-200908180-00135) — Provides a widely‑adopted checklist for transparent reporting; demonstrates that systematic reporting improves reproducibility, though it does not address individual A/B tests.  
- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Audits statistical reporting consistency in publicly released healthcare quality reports, offering a methodological precedent for systematic validity checks of released statistics.

## Expected results  

We anticipate that 20 %–40 % of the sampled public A/B test summaries will contain at least one statistical inconsistency (e.g., a reported p‑value that cannot be reproduced from the disclosed effect size and sample size). The observed inconsistency proportion will be compared to a baseline error rate of 5 % (derived from prior studies of reporting mistakes). A binomial test (α = 0.05) will assess whether the observed proportion exceeds this baseline, and a 95 % Wilson confidence interval will be reported for the inconsistency proportion.

## Methodology sketch  

- **Corpus construction**  
  1. Compile a curated list of ≥ 100 URLs that host publicly posted A/B test summaries (company engineering blogs, GitHub “ab‑test” repositories, OpenML experiment records). Record for each URL: publication date, source type, and licensing information.  
- **Automatic extraction of reported statistics**  
  2. Run a lightweight Python script (regex + spaCy) on each HTML/Markdown page to extract:  
     - Sample sizes for control and variant (n₁, n₂)  
     - Reported effect size (difference in conversion rates or lift %)  
     - Reported significance metric (p‑value, test statistic, or 95 % confidence interval).  
  3. Flag entries with missing fields for manual review; these are excluded from quantitative analysis.  
- **Re‑computation of significance**  
  4. Using the extracted n₁, n₂, and effect size, compute a two‑proportion z‑test (or Welch’s two‑sample t‑test for continuous metrics) via **SciPy** to obtain a *reconstructed* p‑value and a 95 % confidence interval for the effect size.  
- **Inconsistency detection (single coherent rule)**  
  5. Flag a summary as **inconsistent** when **any** of the following holds:  
     - |p_reported − p_reconstructed| > 0.05 (absolute p‑value difference)  
     - Relative sample‑size discrepancy > 5 % of the larger count, i.e.,  
       \|n_reported − n_extracted\| / max(n₁, n₂) > 0.05  
     - The reported 95 % confidence interval does **not** contain the effect size implied by the reconstructed test.  
- **Independent validation set (removes circularity)**  
  6. Generate a synthetic validation dataset of 1,000 simulated A/B experiments with known ground‑truth parameters (sample sizes, true effect sizes).  
  7. For each simulated experiment, compute the *true* p‑value using SciPy, then deliberately introduce reporting errors (randomly perturb p‑values, effect sizes, or sample sizes) at controlled rates (5 % and 10 %).  
  8. Apply the full extraction + reconstruction + inconsistency‑detection pipeline to the *perturbed* reports. Because the ground‑truth values are known, precision and recall of the inconsistency detector can be measured independently of the pipeline’s own reconstruction logic.  
- **Aggregate analysis**  
  9. Let *k* be the number of inconsistent summaries out of *N* total examined.  
  10. Perform an exact binomial test of H₀: π = 0.05 vs H₁: π > 0.05, where π = k/N, using α = 0.05.  
  11. Compute a 95 % Wilson confidence interval for π.  
- **Subgroup exploration (bounded scope)**  
  12. Summarize inconsistency rates by source type (blog, repository, benchmark) and by year; apply Fisher’s exact test only when a subgroup contains ≥ 10 entries.  
- **Reproducible research package**  
  13. Package all extracted data, analysis scripts, the synthetic validation generator, and a **Dockerfile** (Python 3.11, pandas, SciPy, statsmodels, spaCy) in a public GitHub repository.  
  14. Provide a single command (`docker build -t ab‑audit . && docker run --rm ab‑audit`) that runs the complete pipeline end‑to‑end.  
- **CI‑friendly execution**  
  15. The pipeline is split into ≤ 10 atomic steps, each ≤ 30 minutes on a 2‑core, 7 GB RAM GitHub Actions free‑tier runner.  
  16. All intermediate artefacts are streamed to disk and deleted after use to keep peak RAM ≤ 6 GB and total runtime ≤ 4 hours.  

## Duplicate-check  

- Reviewed existing ideas: PRISMA reporting standards audit, hospital outcomes profiling consistency, digital experimentation transparency.  
- Closest match: Hospital Outcomes Profiling (2007) — similar statistical auditing methodology but applied to healthcare rather than digital A/B testing; different domain constructs and data sources.  
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-25T05:31:29Z
**Outcome**: exhausted
**Original term**: Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics
**Verified citation count**: 0

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics | 0 |

### Verified citations

(none)
