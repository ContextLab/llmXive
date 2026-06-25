---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Statistical Validity of Publicly Available A/B Test Summaries  

**Field**: statistics  

## Research question  

To what extent do publicly available A/B test summaries report statistically consistent results—specifically, do the reported p‑values, effect sizes, and sample sizes align under standard hypothesis‑testing assumptions when evaluated at a 95 % confidence level?

## Motivation  

A/B testing underpins product decisions across many online services, yet the way experiment results are reported is often informal and unstandardized. Inconsistent statistics can mislead stakeholders and propagate erroneous conclusions. Quantifying the prevalence of such inconsistencies will reveal the reliability of publicly shared experiment claims and motivate clearer, community‑adopted reporting guidelines.

## Related work  

- [Preferred Reporting Items for Systematic Reviews and Meta‑Analyses: The PRISMA Statement (2009)](https://doi.org/10.7326/0003-4819-151-4-200908180-00135) — Provides a well‑known checklist for reporting standards; demonstrates that systematic reporting improves reproducibility, although it does not address individual A/B tests.  
- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Audits statistical reporting consistency in publicly released healthcare quality reports, offering a methodological precedent for systematic validity checks of released statistics.

## Expected results  

We anticipate that 20 %–40 % of the sampled public A/B test summaries will contain at least one statistical inconsistency (e.g., a reported p‑value that cannot be reproduced from the disclosed effect size and sample size). The observed inconsistency proportion will be compared to a baseline error rate of 5 % (derived from prior studies of reporting mistakes). A binomial test will determine whether the observed proportion exceeds this baseline with statistical significance (α = 0.05). Additionally, a **95 % Wilson confidence interval** for the inconsistency proportion will be reported.

## Methodology sketch  

- **User stories & functional requirements (traceability)**  
  1. **US‑1**: As a researcher, I need to supply a list of URLs containing A/B test summaries. → **FR‑001** (accept list of URLs).  
  2. **US‑2**: As a system, I must automatically extract the reported statistics and reconstruct significance. → **FR‑002** (automatic extraction), **FR‑003** (reconstruct p‑value), **FR‑004** (detect inconsistencies), **FR‑005** (basic aggregate analyses).  
  3. **US‑3**: As a user, I want a reproducible research package that can be re‑run to obtain the same results. → **FR‑006** (export reproducible package).  
  4. **US‑4**: As a CI engineer, I require the pipeline to run on CPU‑only GitHub Actions runners within the free‑tier limits. → **FR‑009** (CPU‑only execution constraints).  

- **Success criteria (linked to FR/US)**  
  - **SC‑001** (US‑1, FR‑001): The system accepts ≥ 100 valid URLs and reports any unreachable or non‑HTML resources.  
  - **SC‑002** (US‑2, FR‑004): Inconsistency‑detection precision ≥ 90 % on an independent validation set.  
  - **SC‑003** (US‑2, FR‑002/FR‑003): All statistical calculations are performed with SciPy (v1.14+).  
  - **SC‑004** (US‑3, FR‑006): The exported Docker image builds in ≤ 5 minutes and reproduces the full analysis with identical numeric outputs (hash‑matched result files).  
  - **SC‑005** (US‑4, FR‑009): End‑to‑end runtime ≤ 4 hours and peak RAM ≤ 6 GB on a GitHub Actions free‑tier runner.  

- **Corpus construction**  
  1. Compile a curated list of ≥ 100 URLs that host publicly posted A/B test summaries (e.g., company engineering blogs, GitHub “ab‑test” repositories, OpenML experiment records).  
  2. For each entry record: URL, publication date, source type, and licensing information.  

- **Automatic extraction of reported statistics (FR‑002)**  
  3. Run a lightweight Python script (regex + spaCy) on each HTML/Markdown page to extract:  
     - Sample sizes for control and variant (n₁, n₂)  
     - Reported effect size (difference in conversion rates or lift %)  
     - Reported significance metric (p‑value, test statistic, or 95 % confidence interval).  
  4. Flag entries with missing fields for manual review (these are excluded from quantitative analysis).  

- **Re‑computation of significance (FR‑003)**  
  5. Using the extracted n₁, n₂, and effect size, compute a two‑proportion z‑test (or Welch’s two‑sample t‑test for continuous metrics) via **SciPy** to obtain a *reconstructed* p‑value.  
  6. Derive a **95 % confidence interval** for the effect size from the reconstructed test (this fixes the previously deferred “[deferred]” level).  

- **Inconsistency detection (FR‑004)** – concrete thresholds  
  7. Flag a summary as **inconsistent** when either:  
     - |p_reported − p_reconstructed| > 0.05 **or**  
     - reported sample‑size discrepancy > 5 % of the larger of n₁ or n₂ (i.e., |n_reported − n_extracted| / max(n₁,n₂) > 0.05) **or**  
     - a reported 95 % confidence interval does **not** contain the effect size implied by the reconstructed test.  

- **Independent validation set (removes circularity)**  
  8. Generate a synthetic validation dataset of 1,000 simulated A/B experiments with known ground‑truth parameters (sample sizes, true effect sizes).  
  9. For each simulated experiment, compute the *true* p‑value using SciPy (the same statistical model as FR‑003) and then deliberately introduce reporting errors (randomly perturb p‑values, effect sizes, or sample sizes) at controlled rates (5 % error, 10 % error, etc.).  
  10. Apply the full extraction + reconstruction + inconsistency‑detection pipeline to the *perturbed* reports. Because the ground‑truth truth values are known a priori, precision and recall can be measured **independently** of the pipeline’s own reconstruction logic, satisfying SC‑002.  

- **Aggregate analysis (FR‑005)**  
  11. Let *k* be the number of inconsistent summaries out of *N* total examined.  
  12. Perform an exact binomial test of H₀: π = 0.05 vs H₁: π > 0.05, where π = k/N, using α = 0.05.  
  13. Compute a 95 % Wilson confidence interval for π.  

- **Subgroup exploration (optional, bounded scope)**  
  14. Summarize inconsistency rates by source type (blog, repository, benchmark) and by year; apply Fisher’s exact test only when a subgroup contains ≥ 10 entries.  

- **Reproducible research package (FR‑006)**  
  15. Package all extracted data, analysis scripts, the synthetic validation generator, and a **Dockerfile** (Python 3.11, pandas, SciPy, statsmodels, spaCy) in a public GitHub repository.  
  16. Provide a single command (`docker build -t ab‑audit . && docker run --rm ab‑audit`) that runs the complete pipeline end‑to‑end, satisfying SC‑004 and FR‑009.  

- **CI‑friendly execution (FR‑009)**  
  17. The pipeline is split into ≤ 10 atomic steps, each ≤ 30 minutes on a 2‑core, 7 GB RAM runner.  
  18. All intermediate artefacts are streamed to disk and deleted after use to keep peak RAM ≤ 6 GB.  

## Duplicate-check  

- Reviewed existing ideas: PRISMA reporting standards audit, hospital outcomes profiling consistency, digital experimentation transparency.  
- Closest match: Hospital Outcomes Profiling (2007) — similar statistical auditing methodology but applied to healthcare rather than digital A/B testing; different domain constructs and data sources.  
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-25T05:05:43Z
**Outcome**: exhausted
**Original term**: Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics
**Verified citation count**: 0

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Statistical Validity of Publicly Available A/B Test Summaries statistics | 0 |

### Verified citations

(none)
