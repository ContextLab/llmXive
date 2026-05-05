---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Field**: biology

## Research question

Can machine learning models integrating single nucleotide polymorphisms (SNPs) and mobile genetic element (MGE) context predict phenotypic antibiotic resistance more accurately than gene-presence-only models using public genomic data?

## Motivation

Current genomic surveillance relies heavily on the presence of known resistance genes, which often fails to predict phenotypic resistance accurately due to regulatory mutations or structural variants. Incorporating sequence-level variations and genomic context may reveal novel markers and improve the reliability of in-silico susceptibility testing for public health surveillance.

## Related work

- [CARD 2023: expanded curation, support for machine learning, and resistome prediction at the Comprehensive Antibiotic Resistance Database (2022)](https://doi.org/10.1093/nar/gkac920) — Provides the curated ontology and machine learning support infrastructure for identifying resistance determinants.
- [ResFinder 4.0 for predictions of phenotypes from genotypes (2020)](https://doi.org/10.1093/jac/dkaa345) — Establishes baseline methods for predicting phenotypes from genotypes using known resistance genes.
- [Sequence-based modelling of bacterial genomes enables accurate antibiotic resistance prediction (2024)](https://www.semanticscholar.org/paper/006a51ffa223a24606007ac6e9b96dfabadc4efe) — Demonstrates the potential of sequence-based deep learning approaches for resistance detection.
- [Using genomic data and machine learning to predict antibiotic resistance: A tutorial paper (2024)](https://www.semanticscholar.org/paper/13344dac2ada27398f972c16bf0af089c8c2fc6c) — Outlines standard workflows and challenges in applying ML to genomic resistance data.
- [Predicting Antimicrobial Resistance (AMR) in Campylobacter, a Foodborne Pathogen, and Cost Burden Analysis Using Machine Learning (2025)](https://www.semanticscholar.org/paper/0e25fc54e15d4292deb764e60725004b83dac551) — Applies machine learning to specific foodborne pathogens to link genomic features with resistance costs.
- [Zoonomix: A Pipeline for Assessing Zoonotic Potential and Antibiotic Resistance in Bacterial Genomes (2025)](https://www.semanticscholar.org/paper/6ba6d63655872953c468e117a37bf2b821e87c66) — Offers a pipeline framework for assessing resistance potential in bacterial genomes alongside zoonotic risk.

## Expected results

The model will achieve higher F1-scores (target >0.85) for resistance prediction compared to baseline gene-presence models on held-out test sets. Specific SNPs in housekeeping genes and MGE proximity scores will be identified as significant predictors of phenotypic resistance where gene presence alone is insufficient.

## Methodology sketch

- **Data Acquisition**: Download pre-assembled *E. coli* and *S. aureus* genomes with associated phenotypic AST data from the NCBI Pathogen Genome Browser (https://www.ncbi.nlm.nih.gov/pathogens/) and CARD (https://card.mcmaster.ca/). Limit dataset to 1,000 isolates to fit within 7 GB RAM.
- **Feature Extraction**: Use `snp-sites` to call SNPs against a core genome reference (low memory footprint). Extract ARG presence/absence using CARD's API. Calculate distance of ARGs to known transposon insertion sites using annotation files.
- **Data Encoding**: Convert genomic features into a binary/numeric matrix (ARG presence, SNP counts per gene, MGE distance bins). Normalize numerical features using scikit-learn `StandardScaler`.
- **Model Training**: Train a Random Forest classifier (scikit-learn) and an XGBoost model on CPU. Perform 5-fold cross-validation to prevent overfitting within the 6-hour job limit.
- **Statistical Testing**: Apply Mann-Whitney U tests to compare feature distributions between resistant and sensitive phenotypes to validate significance of novel markers.
- **Evaluation**: Compute Precision, Recall, F1-score, and AUC-ROC. Compare performance against a baseline model using only ARG presence features.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
