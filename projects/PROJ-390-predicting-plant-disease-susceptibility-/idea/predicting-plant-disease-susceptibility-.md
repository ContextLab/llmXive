---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data

**Field**: biology

## Research question

To what extent do genomic signatures of crop varieties and environmental conditions jointly influence susceptibility to common plant pathogens across agricultural species?

## Motivation

Plant disease outbreaks cause substantial crop losses globally, yet predictive models that integrate both host genetics and environmental context remain underdeveloped. Understanding how genomic vulnerability interacts with environmental modulators would enable earlier intervention strategies and more targeted breeding programs. This question addresses a gap between molecular plant pathology (which often studies mechanisms in isolation) and epidemiological modeling (which often lacks genomic resolution).

## Related work

- [Predicting the resistance of basil entries to downy mildew based on their genetics, pathogen race, growth stage, and environmental conditions (2025)](https://www.semanticscholar.org/paper/064dd81cacb242fbf67f0e7fee79a57799e83eeb) — Demonstrates a predictive model for plant disease resistance incorporating genetics and environmental conditions, providing a methodological precedent for this work.
- [Unravelling Updates in Deciphering Plant Defence Mechanisms with Insights from Functional Genomics and Proteomics (2025)](https://www.semanticscholar.org/paper/a59f6b76514e506df44d9873934793c43f92689d) — Reviews functional genomics approaches to plant immunity, establishing the molecular basis for genomic susceptibility markers.

## Expected results

We expect to find that genomic markers explain a moderate proportion of variance in disease susceptibility (R² ≈ 0.2–0.4), with environmental conditions adding significant predictive power when combined with genomic data. A null result (genomic and environmental features showing no joint predictive signal) would suggest that unmeasured factors (e.g., microbial community composition or pathogen strain diversity) dominate susceptibility, which would be equally informative for redirecting future research.

## Methodology sketch

- Download publicly available plant genomic data from NCBI SRA for 3–5 major crop species (wheat, rice, maize, tomato, soybean) using `wget` or NCBI E-utilities.
- Extract pathogen infection status labels from associated metadata or linked phenotypic datasets (e.g., CropScape, Plant Phenome Database).
- Collect environmental variables (temperature, precipitation, humidity) for sample collection locations from public weather APIs (NOAA, ERA5) using `curl`.
- Preprocess genomic data: align reads to reference genomes using minimap2, call SNPs with bcftools, and summarize as variant frequency vectors.
- Normalize and merge genomic and environmental features into a single feature matrix, handling missing values via k-nearest-neighbor imputation.
- Split data into training (70%), validation (15%), and test (15%) sets stratified by crop species.
- Train random forest and support vector machine models using scikit-learn, with hyperparameter tuning via grid search (≤50 combinations).
- Evaluate performance using AUC-ROC, precision-recall curves, and feature importance rankings to assess relative contributions of genomic vs. environmental predictors.
- Perform statistical significance testing via permutation tests (1000 permutations) to validate that model performance exceeds random baseline.
- Generate visualization outputs (feature importance plots, ROC curves) using matplotlib and save all intermediate files to a results directory.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate

## Literature gap analysis

### What we searched

Search queries included "plant disease prediction genomic environmental" and "plant susceptibility machine learning genomics" on Semantic Scholar and arXiv. The literature block returned 8 papers, of which only 2 were directly on-topic for plant disease prediction combining genetics and environment.

### What is known

- [Predicting the resistance of basil entries to downy mildew based on their genetics, pathogen race, growth stage, and environmental conditions (2025)](https://www.semanticscholar.org/paper/064dd81cacb242fbf67f0e7fee79a57799e83eeb) — Establishes that integrated genetic-environmental models can predict resistance in basil, demonstrating feasibility for this approach.
- [Unravelling Updates in Deciphering Plant Defence Mechanisms with Insights from Functional Genomics and Proteomics (2025)](https://www.semanticscholar.org/paper/a59f6b76514e506df44d9873934793c43f92689d) — Documents functional genomics insights into plant immunity mechanisms but does not address predictive modeling across species.

### What is NOT known

No published work has systematically evaluated whether publicly available multi-species genomic datasets (NCBI SRA) combined with environmental data can predict disease susceptibility across different crop species. Existing studies focus on single crop-pathogen pairs (e.g., basil-downy mildew) without generalization to broader agricultural contexts.

### Why this gap matters

A multi-species predictive framework would enable cost-effective disease risk assessment for crops lacking extensive phenotypic databases, supporting resource-limited agricultural systems and guiding breeding priorities. Filling this gap could provide a scalable benchmark for future plant disease prediction research.

### How this project addresses the gap

The methodology explicitly uses NCBI SRA genomic data and public environmental databases across 3–5 crop species, directly testing whether joint genomic-environmental models generalize beyond single crop-pathogen systems. The feature importance analysis quantifies relative contributions of each data type, producing evidence previously unavailable for multi-species contexts.
