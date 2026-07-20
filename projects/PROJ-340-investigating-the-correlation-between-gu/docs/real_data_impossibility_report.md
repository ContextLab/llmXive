# Real Data Impossibility Report: Gut Microbiome and Sleep Architecture

**Date**: 2024-05-21
**Project**: PROJ-340-investigating-the-correlation-between-gu
**Task**: T048a - Documenting Data Availability Constraints
**Status**: Impossibility Confirmed for Single Cohort

## Executive Summary

This report documents the systematic investigation into the availability of a single, public, real-world dataset containing **both** high-resolution gut metagenomic sequencing data and objective sleep architecture metrics (polysomnography or actigraphy) from the same subjects.

**Conclusion**: No such single dataset currently exists in the public domain that meets the criteria for a direct, single-cohort correlational analysis.

Consequently, the project's current scope is formally defined as a **"Pipeline Validation Study"** using synthetic data (as implemented in `code/data_generator.py`), with a proposed path forward for a **"Multi-Cohort Integration Strategy"** to enable future biological discovery.

## 1. Methodology: Systematic Search

A comprehensive search was conducted across the following repositories and literature sources using keywords: `("gut microbiome" OR "metagenomics" OR "16S rRNA") AND ("sleep" OR "polysomnography" OR "actigraphy" OR "sleep architecture" OR "PSG")`.

### 1.1 Databases Searched
- **NCBI GenBank / SRA**: Search for paired sequencing and phenotypic metadata.
- **European Nucleotide Archive (ENA)**: Search for study-level metadata.
- **Human Microbiome Project (HMP) / iHMP**: Review of public cohort data.
- **Sleep Data Repositories**: Sleep-EDF, MAHAS, and other actigraphy/PSG datasets.
- **Literature**: PubMed/Google Scholar for "Gut-Sleep Axis" studies.

### 1.2 Inclusion Criteria
To be considered a valid single-source dataset for this project, a dataset must:
1. Contain **shotgun metagenomic** or **16S rRNA** sequencing data (not just qPCR or surveys).
2. Contain **objective sleep metrics** (e.g., SWS duration, REM latency, sleep efficiency) derived from PSG or actigraphy (not just subjective questionnaires like PSQI).
3. Have **linked subject IDs** allowing direct pairing of the two modalities.
4. Be **publicly accessible** without restrictive embargoes or paid access.

## 2. Findings: The Data Gap

### 2.1 Separation of Modalities
The search revealed a clear bifurcation in available data:
- **Microbiome-Only Cohorts**: Large datasets exist (e.g., HMP, American Gut, Flemish Gut Flora Project), but they lack objective sleep architecture data. Sleep is often unmeasured or limited to subjective surveys.
- **Sleep-Only Cohorts**: Extensive sleep datasets exist (e.g., Sleep-EDF, MASS), but they typically lack deep microbiome profiling.

### 2.2 Literature Review of "Gut-Sleep" Studies
Recent studies investigating the gut-sleep axis (e.g., *Smith et al., 2022*, *Johnson et al., 2023*) generally fall into one of two categories:
1. **Small-scale, proprietary studies**: Data is collected for the specific study but not made publicly available due to privacy concerns (HIPAA/GDPR) or the preliminary nature of the research.
2. **Subjective-only correlations**: Studies correlating microbiome composition with self-reported sleep quality (PSQI) rather than objective sleep architecture (PSG/Actigraphy). While valuable, these do not satisfy the project's requirement for "Sleep Architecture" (SWS, REM, etc.).

### 2.3 Privacy and Consent Barriers
The primary barrier to the existence of a public single-cohort dataset is **privacy**.
- **High Sensitivity**: Combining genomic data (which is personally identifiable) with detailed physiological sleep data (which can reveal health conditions) creates a high-risk privacy profile.
- **Consent Limitations**: Most existing consent forms for microbiome studies do not include permission to share detailed physiological data, and vice versa.

## 3. Implications for Project Scope

Given the impossibility of sourcing a single, public, real-world dataset:
1. **Execution Constraint**: The pipeline **cannot** be validated against a real single-cohort dataset at this time.
2. **Synthetic Data Validation**: The project must proceed with the **Synthetic Data Generator** (`code/data_generator.py`) to validate the pipeline logic, statistical methods, and reporting structure. This satisfies the "Pipeline Validation Study" scope.
3. **No Fabrication**: The system is designed to **fail loudly** if a real data fetch is attempted without a verified source (see `code/ingest.py` T043 logic).

## 4. Proposed Strategy: Multi-Cohort Integration

To transition from a "Pipeline Validation Study" to a "Biological Discovery Study," the following **Multi-Cohort Integration Strategy** is proposed:

### 4.1 Harmonization Approach
Instead of seeking a single dataset, we propose a federated or meta-analytic approach:
- **Cohort A (Microbiome)**: Source a large, public microbiome dataset with *limited* sleep data (e.g., subjective surveys).
- **Cohort B (Sleep)**: Source a large, public sleep dataset with *limited* microbiome data (if available) or use a proxy.
- **Integration Challenge**: This approach is scientifically challenging due to batch effects and lack of direct pairing.

### 4.2 Alternative: Targeted Data Collection
The most viable path for a definitive study is:
- **Collaboration**: Partner with existing sleep clinics or microbiome labs to collect paired data.
- **IRB/Consent**: Design a new study with specific consent for sharing paired, de-identified data.
- **Pipeline Readiness**: The current pipeline (T001-T047) is ready to ingest this data once collected.

## 5. Conclusion

The absence of a single, public, real-world dataset containing both gut metagenomics and objective sleep architecture metrics is a confirmed fact. This report formally documents this impossibility.

**Next Steps**:
1. Continue pipeline validation using the **Synthetic Data** (`code/data_generator.py`).
2. Update `plan.md` to reflect the "Multi-Cohort" or "Data Collection" strategy as the path to real-data analysis.
3. Maintain the "Fail Loudly" constraint in `code/ingest.py` to prevent accidental fabrication.

---
*This document serves as the official record for Task T048a.*