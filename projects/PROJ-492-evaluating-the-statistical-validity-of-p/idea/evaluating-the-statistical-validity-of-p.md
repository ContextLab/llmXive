---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Statistical Validity of Publicly Available A/B Test Summaries

**Field**: statistics

## Research question

To what extent do publicly available A/B test summaries report statistically consistent results (i.e., p-values, effect sizes, and sample sizes that align with standard statistical tests)?

## Motivation

A/B testing is ubiquitous in tech and business decision-making, yet reporting standards vary widely outside peer-reviewed literature. If public summaries systematically contain statistical inconsistencies, practitioners may base critical decisions on flawed evidence. This research addresses the gap between the prevalence of A/B testing in industry and the rigor of its public documentation.

## Literature gap analysis

### What we searched

Queried Semantic Scholar, arXiv, and OpenAlex with terms including "A/B testing reporting standards," "statistical validity online experiments," "p-value consistency industry," and "experimental reporting transparency." The PRISMA statement (2009) provides reporting guidelines for systematic reviews but does not address individual A/B tests. Hospital outcomes profiling (2007) examines statistical reporting in clinical contexts, offering methodological precedent but not directly applicable to digital experimentation.

### What is known

- [Preferred Reporting Items for Systematic Reviews and Meta-Analyses: The PRISMA Statement (2009)](https://doi.org/10.7326/0003-4819-151-4-200908180-00135) — Establishes reporting standards for meta-analyses, not individual experimental summaries.
- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Examines statistical reporting consistency in healthcare report cards, providing methodological precedent for validity auditing.

### What is NOT known

No published work has systematically audited the statistical consistency of A/B test summaries in industry blogs and case studies. There is no baseline estimate of how frequently reported p-values, effect sizes, and sample sizes are mutually consistent under standard statistical assumptions. The prevalence of Type I/II error inflation due to reporting choices in public A/B test documentation remains unquantified.

### Why this gap matters

Product managers, researchers, and policymakers rely on public A/B test summaries to guide decisions about feature rollouts and experimental practices. If inconsistencies are prevalent, the industry may be overconfident in reported effects or missing genuine signals. Establishing a baseline validity rate would inform transparency standards and improve decision quality.

### How this project addresses the gap

The methodology extracts reported metrics from public A/B test summaries and reconstructs expected statistical relationships under standard assumptions. Discrepancies between reported and reconstructed values directly quantify the prevalence of statistical inconsistency, producing the first empirical estimate of this gap.

## Expected results

We expect to find that 20-40% of public A/B test summaries contain at least one statistical inconsistency (e.g., p-value incompatible with reported effect size and sample size). A chi-squared goodness-of-fit test across the corpus will confirm whether inconsistency rates exceed what random reporting error would produce. This evidence level (corpus of 100+ summaries with quantified inconsistency rates) is sufficient to publish in a methods-focused venue.

## Methodology sketch

- Compile a corpus of 100+ publicly available A/B test summaries from tech company blogs, case study repositories, and conference proceedings (sources: GitHub A/B test archives, company engineering blogs, OpenML experiment reports).
- Extract reported metrics: sample sizes per variant, observed effect sizes (conversion rate differences, lift percentages), and p-values or confidence intervals.
- Reconstruct expected p-values from reported sample sizes and effect sizes using standard two-proportion z-tests and t-tests.
- Compute consistency scores: absolute difference between reported and reconstructed p-values, flagging discrepancies exceeding 0.05 absolute threshold.
- Apply chi-squared goodness-of-fit test to determine if inconsistency rates exceed random error expectations (null: inconsistencies are uniformly distributed).
- Categorize inconsistencies by type (sample size mismatch, effect size inflation, p-value rounding errors, unreported multiple testing corrections).
- Generate summary statistics and visualization of inconsistency prevalence across sources and time periods.
- Document reproducibility: store all extracted data and analysis code in public GitHub repository with Docker environment specification.

## Duplicate-check

- Reviewed existing ideas: PRISMA reporting standards audit, hospital outcomes profiling consistency, digital experimentation transparency.
- Closest match: Hospital Outcomes Profiling (2007) — similar statistical auditing methodology but applied to healthcare rather than digital A/B testing; different domain constructs and data sources.
- Verdict: NOT a duplicate
