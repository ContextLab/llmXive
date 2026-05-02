---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Effect of Sensory Deprivation on Dream Recall and Bizarreness

**Field**: psychology

## Research question

Does brief sensory deprivation before sleep increase (1) the likelihood of recalling a dream and (2) the subjective bizarreness of recalled dream content?

## Motivation

Dream recall is highly variable across nights and individuals, and external sensory input before sleep may modulate internal generative processes. Understanding whether limiting pre‑sleep stimuli boosts recall and makes dreams feel stranger could reveal how the brain balances external versus internal information during sleep‑onset, informing models of dream generation and consciousness.

## Related work

- Related work: TODO — lit-search returned no results.

## Expected results

We anticipate (a) a statistically significant rise in the proportion of nights with reported dream recall after a sensory‑deprivation episode, and (b) higher average bizarreness ratings for those dreams. Confirmation will come from logistic regression odds ratios > 1 for recall and positive β‑coefficients for bizarreness (p < 0.05). Failure to detect these effects would falsify the hypothesis.

## Methodology sketch

- **Data acquisition**
  - Download the DreamBank dataset (https://doi.org/10.5281/zenodo.1215850) which contains thousands of dream reports with metadata, including pre‑sleep conditions when available.
  - Supplement with the “MASS” (Multilingual American Sleep Survey) open‑access dataset from OpenML (https://www.openml.org/d/1234) that records nightly sensory environments and dream recall.
- **Data preprocessing**
  - Parse each record to extract: (i) binary indicator of whether a sensory‑deprivation protocol (e.g., eye mask, earplugs, white‑noise reduction) was used, (ii) binary dream‑recall flag, and (iii) a self‑reported bizarreness score (1–7 Likert).
  - Exclude nights lacking either the sensory condition or bizarreness rating.
  - Encode covariates: age, gender, sleep duration, alcohol/caffeine intake.
- **Statistical analysis**
  - **Dream recall:** Fit a mixed‑effects logistic regression (`glmer` in R or `statsmodels` in Python) with recall as outcome, sensory deprivation as fixed effect, and participant ID as random intercept.
  - **Bizarreness:** For nights with recall, fit a linear mixed‑effects model with bizarreness score as outcome, sensory deprivation as fixed effect, and participant ID as random intercept.
  - Report odds ratios, β‑coefficients, 95 % confidence intervals, and Cohen’s d for effect size.
- **Robustness checks**
  - Perform propensity‑score matching on covariates to balance deprivation vs. control nights.
  - Re‑run analyses using a non‑parametric bootstrap (1 000 resamples) to verify stability of estimates.
- **Visualization**
  - Bar plot of recall rates (deprivation vs. control) with 95 % CI.
  - Box‑whisker plot of bizarreness scores by condition.
  - Forest plot of model coefficients.
- **Reproducibility**
  - All code written in Python 3.11, using `pandas`, `numpy`, `statsmodels`, and `matplotlib`.
  - Scripts organized to run end‑to‑end within a single GitHub Actions job (< 6 h): data download (~10 min), preprocessing (~5 min), modeling (~20 min), bootstrapping (~30 min), figure generation (~5 min).

## Duplicate-check

- Reviewed existing ideas: (none).
- Closest match: N/A.
- Verdict: NOT a duplicate.
