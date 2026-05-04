---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing Statistical Power in Reproducible Research with Public Datasets

**Field**: statistics

## Research question

What proportion of studies utilizing public datasets (e.g., OpenML) report statistically significant findings that were achieved with inadequate statistical power (<80%) given their reported sample sizes and effect sizes?

## Motivation

Underpowered studies contribute significantly to the reproducibility crisis by inflating false positive rates and effect size estimates. Public datasets offer a unique opportunity to audit historical power calculations retrospectively without collecting new experimental data, thereby identifying systemic weaknesses in how statistical evidence is generated from shared resources.

## Related work

- [Analyzing complex functional brain networks: fusing statistics and network science to understand the brain (2013)](http://arxiv.org/abs/1302.5721v3) — Highlights the necessity of rigorous statistical validation when applying network science to complex public data, though focused on neuroimaging rather than general tabular repositories.

## Expected results

We expect to find that a significant fraction of re-analyzed tests in associated publications exhibit post-hoc power below the conventional 0.8 threshold. This would confirm that many significant findings in public-data-driven research are potentially fragile or subject to winner's curse bias.

## Methodology sketch

- Access the OpenML API (https://www.openml.org/api/v1/) to retrieve metadata for the top 50 most-downloaded classification datasets.
- Filter datasets that have associated task IDs or publication links stored in their metadata schema.
- Extract sample size (N) and reported effect sizes (e.g., Cohen's d, F-statistic) from the associated publication abstracts or metadata fields using lightweight NLP parsing.
- Compute post-hoc statistical power for the reported tests using the `statsmodels.stats.power` Python library.
- Compare calculated power values against the 0.8 standard benchmark and visualize the distribution via histograms.
- Run all scripts within a single Python environment; data download and analysis are expected to complete within 30 minutes on standard CPU hardware.

## Duplicate-check

- Reviewed existing ideas: None available in context.
- Closest match: None.
- Verdict: NOT a duplicate
