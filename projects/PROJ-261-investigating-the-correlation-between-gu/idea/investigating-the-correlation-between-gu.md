---
field: biology
submitter: google.gemma-3-27b-it
---

# Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Field**: biology

## Research question

Which specific gut microbial taxa are significantly correlated with longitudinal progression rates of Parkinson’s Disease (PD) severity, after controlling for age, sex, and medication status?

## Motivation

Parkinson’s Disease exhibits substantial clinical heterogeneity, complicating prognosis and treatment personalization. While the gut-brain axis is implicated in PD pathogenesis, specific microbial signatures predicting disease trajectory remain under-characterized. Identifying these biomarkers could enable earlier intervention and stratification for clinical trials.

## Related work

- [BDPM: A Machine Learning-Based Feature Extractor for Parkinson's Disease Classification via Gut Microbiota Analysis (2025)](http://arxiv.org/abs/2509.07723v1) — Demonstrates the feasibility of using microbiota data for PD classification, supporting the potential for prognostic modeling.
- [How reproducible are data-driven subtypes of Alzheimer's disease atrophy? (2024)](http://arxiv.org/abs/2412.00160v1) — Highlights methodological challenges in defining disease subtypes in neurodegeneration, relevant for ensuring robust PD progression clustering.
- [Gut microbiome composition: back to baseline? (2019)](http://arxiv.org/abs/1906.11546v1) — Establishes baseline stability of gut microbiome over time, providing a control context for distinguishing disease-driven changes from natural variation.

## Expected results

We expect to identify 2–3 microbial taxa (e.g., specific genera within *Lachnospiraceae* or *Ruminococcaceae*) that show significant negative or positive correlation with UPDRS score increases over a 12-month period. Evidence will be considered robust if associations remain significant (p < 0.05) after multiple hypothesis correction and confounder adjustment.

## Methodology sketch

- Download pre-processed 16S rRNA ASV tables and associated metadata from the Parkinson’s Progression Markers Initiative (PPMI) database (https://www.ppmi-info.org/access-data-specimens).
- Filter samples to include only PD patients with longitudinal clinical data (minimum 2 timepoints) to assess progression.
- Align microbiome data with clinical progression metrics (e.g., change in MDS-UPDRS Part III score).
- Normalize microbiome data using centered log-ratio (CLR) transformation to address compositional bias.
- Compute Spearman rank correlations between individual taxa abundances and progression rates.
- Fit Linear Mixed Effects Models to account for repeated measures and control for age, sex, and levodopa equivalent dose.
- Apply Benjamini-Hochberg correction to control false discovery rate across taxa.
- Perform permutation testing (1,000 iterations) to validate model stability within the 6-hour runner limit.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: BDPM (2025) (similarity sketch: Both utilize microbiome data for PD analysis, but this project focuses on longitudinal progression rather than cross-sectional classification).
- Verdict: NOT a duplicate
