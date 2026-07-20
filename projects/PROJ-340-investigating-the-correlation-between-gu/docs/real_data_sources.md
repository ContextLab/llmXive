# Real Data Sources for Gut Microbiome and Sleep Architecture Study

## Overview
This document details the search and evaluation of real-world datasets containing paired gut metagenomics and sleep architecture data.

## Search Methodology
- **Databases Searched**: NCBI SRA, EBI ENA, HuggingFace Datasets, Kaggle, GitHub.
- **Keywords**: "gut microbiome sleep", "metagenomics polysomnography", "microbiome actigraphy", "sleep gut bacteria".
- **Filters**: Human subjects, paired data, public access.

## Findings

### Single Dataset Search
- **Result**: No single public dataset was found that contains both high-quality metagenomic sequencing data and detailed sleep architecture metrics (PSG or actigraphy) for the same subjects.
- **Reasons**:
 - Most microbiome studies do not include detailed sleep phenotyping.
 - Most sleep studies do not include metagenomic sequencing.
 - Privacy and data sharing constraints often prevent the release of combined sensitive health data.

### Potential Proxies / Multi-Cohort Strategy
- **Cohort A (Microbiome)**: [Example: American Gut Project] - Contains extensive microbiome data but no sleep data.
- **Cohort B (Sleep)**: [Example: Sleep Heart Health Study] - Contains detailed sleep data but no microbiome data.
- **Strategy**: Harmonize metadata (e.g., age, BMI, diet) to create a synthetic paired dataset for hypothesis generation, acknowledging the limitations.

## Conclusion
Due to the lack of a single verified dataset, the project will proceed with a **Multi-Cohort Integration Strategy** (see `docs/multi_cohort_integration_plan.md`). The T051 task is contingent on the successful identification of a single dataset, which has not been achieved.

## Next Steps
- Implement multi-cohort data harmonization pipeline.
- Re-evaluate research question to account for data limitations.
- Update `plan.md` and `spec.md` accordingly.
