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

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using the following distinct queries: (1) "gut microbiome Parkinson's disease longitudinal progression taxa correlation" and (2) "microbiome biomarkers PD severity UPDRS change". The search returned a limited set of results, primarily focusing on cross-sectional classification or general associations rather than longitudinal trajectory modeling.

### What is known

- [BDPM: A Machine Learning-Based Feature Extractor for Parkinson's Disease Classification via Gut Microbiota Analysis](https://arxiv.org/abs/2509.07723) — Establishes that microbiome data can distinguish PD patients from controls using machine learning, but does not address longitudinal progression or specific taxa trajectories over time.

### What is NOT known

No published work has systematically identified specific microbial taxa whose abundance changes are statistically correlated with the *rate* of motor symptom worsening (UPDRS Part III slope) in a longitudinal cohort while controlling for medication dosage. Existing literature largely treats PD as a static binary state (case vs. control) rather than a dynamic process with variable progression speeds.

### Why this gap matters

Filling this gap is critical for developing prognostic biomarkers that can stratify patients into "rapid" vs. "slow" progressors, a distinction that is currently difficult to make early in the disease course. Such stratification would significantly improve the power of clinical trials by reducing variance in outcome measures and enabling targeted therapeutic interventions for specific progression phenotypes.

### How this project addresses the gap

This project directly addresses the gap by applying Linear Mixed Effects Models to longitudinal 16S rRNA data from the PPMI cohort to model the interaction between time and specific taxa abundances against clinical progression slopes. The methodology explicitly tests for taxa that predict the *change* in severity over time, rather than just the baseline state.

## Expected results

We expect to identify 2–3 microbial taxa (e.g., specific genera within *Lachnospiraceae* or *Ruminococcaceae*) that show significant negative or positive correlation with UPDRS score increases over a 12-month period. Evidence will be considered robust if associations remain significant (p < 0.05) after multiple hypothesis correction and confounder adjustment, and if the identified taxa replicate directionality in a held-out temporal split of the dataset.

## Methodology sketch

- **Data Acquisition**: Download pre-processed 16S rRNA ASV tables and associated longitudinal clinical metadata (MDS-UPDRS Part III, medication status, demographics) from the Parkinson’s Progression Markers Initiative (PPMI) database (https://www.ppmi-info.org/access-data-specimens).
- **Cohort Selection**: Filter samples to include only PD patients with at least two timepoints (baseline and follow-up) within a 12-month window to calculate individual progression slopes.
- **Data Preprocessing**: Apply centered log-ratio (CLR) transformation to ASV tables to handle compositional data bias; impute missing clinical values using k-nearest neighbors (k=5) if <5% missing.
- **Progression Metric Calculation**: Compute the slope of MDS-UPDRS Part III scores for each patient (change in score / time in years) to serve as the dependent variable.
- **Primary Analysis**: Fit Linear Mixed Effects Models (LMM) for each taxon: `Slope ~ Taxon_Abundance + Age + Sex + Levodopa_Dose + (1|Patient_ID)`, treating the taxon abundance as a fixed effect and patient ID as a random intercept.
- **Multiple Testing Correction**: Apply Benjamini-Hochberg (BH) correction to the p-values of all tested taxa to control the False Discovery Rate (FDR).
- **Independent Validation (Non-Circular)**: To address the circularity concern regarding success criteria, split the cohort temporally (e.g., 70% training on earliest cohorts, 30% testing on later cohorts). The "success" of the study is defined by the *replication* of the sign and significance of the top 2-3 taxa in the held-out temporal test set, rather than solely by the p-value in the full dataset.
- **Stability Check**: Perform a non-parametric permutation test (1,000 iterations) on the final LMM coefficients to ensure the observed correlations are not driven by outliers or specific sample configurations.
- **Scope Check**: Ensure all computations (R/Python scripts) run within the 7GB RAM and 6-hour limit of the GitHub Actions runner by subsampling to the top 100 most abundant taxa if the full feature set causes memory errors.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: BDPM (2025) (similarity sketch: Both utilize microbiome data for PD analysis, but this project focuses on longitudinal progression rates and independent temporal validation, whereas BDPM focuses on cross-sectional classification).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-17T04:11:21Z
**Outcome**: exhausted
**Original term**: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression biology
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression biology | 0 |
| 1 | Gut-brain axis in Parkinson's disease | 2 |
| 2 | Microbiota-gut-brain axis and neurodegeneration | 0 |
| 3 | Intestinal microbiome alterations in Parkinson's | 0 |
| 4 | Dysbiosis and Parkinson's disease progression | 0 |
| 5 | Fecal microbiota transplantation for Parkinson's disease | 0 |
| 6 | Gut microbiome biomarkers for Parkinson's disease | 0 |
| 7 | Alpha-synuclein propagation via the vagus nerve | 0 |
| 8 | Enteric nervous system and Parkinson's pathology | 0 |
| 9 | Short-chain fatty acids and neuroinflammation in Parkinson's | 0 |
| 10 | Gut microbiome metabolites in Parkinson's disease | 0 |
| 11 | Bacterial diversity indices in Parkinson's patients | 0 |
| 12 | Specific gut bacteria strains associated with Parkinson's | 0 |
| 13 | Probiotics and Parkinson's disease symptom management | 0 |
| 14 | Microbiome composition changes preceding Parkinson's onset | 0 |
| 15 | Vagus nerve-mediated gut-brain signaling in neurodegeneration | 0 |
| 16 | Gut permeability and alpha-synuclein aggregation | 0 |
| 17 | Microbiome-targeted therapies for Parkinson's disease | 0 |
| 18 | Comparative analysis of gut flora in Parkinson's vs controls | 0 |
| 19 | Inflammation markers linked to gut microbiome in Parkinson's | 0 |
| 20 | Metagenomic analysis of Parkinson's disease stool samples | 0 |

### Verified citations

1. **BDPM: A Machine Learning-Based Feature Extractor for Parkinson's Disease Classification via Gut Microbiota Analysis** (2025). Bo Yu, Zhixiu Hua, Bo Zhao. arXiv. [2509.07723](https://arxiv.org/abs/2509.07723). PDF-sampled: No.
