---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes  

**Field**: neuroscience  

## Research question  

Do higher scores on adverse childhood experiences (ACEs) associate with reduced volumes in specific hippocampal subfields (CA3, dentate gyrus, subiculum) in adolescents, and are the inter‑subfield volume ratios systematically altered?

## Motivation  

Early life stress leaves lasting imprints on brain structure, yet most prior work treats the hippocampus as a uniform region. Disentangling subfield‑specific effects could clarify how stress shapes memory‑related circuitry and explain the heightened risk for mood and anxiety disorders observed in individuals with high ACE scores.

## Related work  

- [Incomplete hippocampal inversion and hippocampal subfield volumes: Implementation and inter‑reliability of automatic segmentation (2023)](http://arxiv.org/abs/2304.14799v1) — Provides a validated, fully automated pipeline for hippocampal subfield segmentation and demonstrates its reliability across large cohorts, establishing a methodological foundation for subfield‑level volumetric analyses.

## Expected results  

We anticipate a modest but statistically reliable negative association between ACE scores and volumes of CA3 and dentate gyrus, with the subiculum showing weaker effects. A significant shift in the CA3 : DG volume ratio would further support subfield‑specific vulnerability. Confirmation will come from regression coefficients that survive Bonferroni‑corrected thresholds (p < 0.05/3) and replication across ABCD release waves.

## Methodology sketch  

- **Data acquisition**  
  - Download the ABCD Study Release 4.0 phenotypic CSV (https://abcd-study.org/data) containing:  
    - Demographics (age, sex, scanner site)  
    - ACE questionnaire scores (parent‑reported)  
    - Freesurfer‑derived hippocampal subfield volumes (CA3, DG, subiculum) already provided in the “subcorticalSegmentationStats” files.  
- **Pre‑processing**  
  - Exclude participants with missing ACE scores or poor MRI quality flags.  
  - Normalize each subfield volume by intracranial volume (ICV) to control for head size.  
  - Log‑transform ACE scores if distribution is skewed.  
- **Statistical analysis**  
  - Fit separate linear mixed‑effects models (using `statsmodels` or `lme4` via rpy2) for each subfield:  
    `subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)`  
  - Extract standardized β coefficients and 95 % confidence intervals.  
  - Apply Bonferroni correction for the three subfields; report both corrected and uncorrected p‑values.  
  - Compute the CA3 : DG ratio and test its association with ACE scores using the same covariate set.  
- **Robustness checks**  
  - Repeat analyses using a non‑parametric permutation test (5,000 permutations) to verify linear model assumptions.  
  - Conduct a sensitivity analysis restricting to participants with ICV within one standard deviation of the sample mean.  
- **Visualization & reporting**  
  - Generate scatter plots with regression lines for each subfield (using `matplotlib`/`seaborn`).  
  - Summarize results in a table of effect sizes, standard errors, and corrected p‑values.  
  - All code will be Python‑based, executable on a GitHub Actions runner (≤ 7 GB RAM, ≤ 2 CPU cores, total runtime < 6 h).  

## Duplicate-check  

- Reviewed existing ideas: *none provided*.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
