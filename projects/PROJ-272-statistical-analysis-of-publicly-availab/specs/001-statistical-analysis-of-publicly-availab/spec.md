# Specification: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## 1. Introduction

This project aims to develop a statistical analysis pipeline to detect cognitive decline using publicly available textual data from speech transcripts. The primary objective is to identify linguistic markers associated with Alzheimer's Disease (AD) and Mild Cognitive Impairment (MCI) compared to healthy controls.

## 2. Functional Requirements

### FR-001: Data Ingestion Scope

**Requirement**: The system shall ingest data from the ADReSS (Alzheimer's Disease Recognition System for Speech) Challenge dataset.

**Scope Definition**:
- **Primary Source**: ADReSS Challenge Dataset (2019/2020 editions).
- **Excluded Sources**: DementiaBank is explicitly excluded from this project scope per the Implementation Plan. No code paths shall attempt to fetch or process data from DementiaBank unless a verified source URL and access method are provided in a future spec amendment.
- **Data Format**: Raw text transcripts and associated cognitive status labels (Control, MCI, AD).

**Edge Cases**:
- Transcripts with missing cognitive status labels shall be excluded.
- Transcripts with insufficient length shall be excluded.
- Non-verbal annotations (e.g., `<laughter>`, `<pause>`) shall be removed during preprocessing.

## 3. User Stories

### US1: Data Ingestion and Preprocessing

**As a** data scientist,
**I want** to ingest and clean the ADReSS dataset,
**So that** I have a structured, labeled dataset ready for feature extraction.

**Acceptance Criteria**:
1. The system downloads the ADReSS dataset from the canonical GitHub repository.
2. The system validates the downloaded data integrity using SHA-256 checksums.
3. The system cleans transcripts by removing non-verbal annotations and normalizing text.
4. The system filters out records with missing labels or insufficient text length (< 50 words).
5. The system outputs a cleaned CSV file (`data/interim/cleaned_adress.csv`) and a metadata report (`data/results/metadata.json`).
6. **Exclusion**: The system does NOT attempt to access DementiaBank.

### US2: Linguistic Feature Extraction and Statistical Testing

**As a** researcher,
**I want** to extract linguistic features and perform statistical tests,
**So that** I can identify significant differences between cognitive groups.

**Acceptance Criteria**:
1. Extract lexical features (TTR, MTLD, Noun/Verb ratio).
2. Extract syntactic features (Mean Clause Length, T-unit Count).
3. Extract semantic features (Sentence Embedding Cosine Similarity).
4. Perform Mann-Whitney U tests between Control vs. AD and Control vs. MCI.
5. Apply Bonferroni correction and report effect sizes (Cohen's d).

### US3: Predictive Modeling and Validation

**As a** data scientist,
**I want** to train and validate predictive models,
**So that** I can assess the predictive power of the extracted features.

**Acceptance Criteria**:
1. Split data into distinct train, validation, and test sets.
2. Train Logistic Regression and Random Forest models.
3. Perform nested k-fold cross-validation (adaptive if dataset is small).
4. Report mean AUC and standard deviation across outer folds.

## 4. Non-Functional Requirements

- **Performance**: The pipeline must complete within 6 hours on a standard CPU environment.
- **Memory**: Peak RAM usage must not exceed a moderate threshold.
- **Reproducibility**: All random seeds must be fixed, and data sources must be versioned via checksums.
- **Privacy**: No PII should be logged or stored; transcripts must be anonymized.

## 5. Data Model

(See `data-model.md` for detailed entity definitions)

## 6. Contracts

(See `contracts/` directory for API and data schemas)

## 7. Implementation Plan

The project follows a phased approach:
1. **Phase 0**: Spec Amendment (T000) - Resolve scope contradictions.
2. **Phase 1**: Setup - Project structure and dependencies.
3. **Phase 2**: Foundational - Logging, config, validation.
4. **Phase 3**: US1 - Ingestion and cleaning.
5. **Phase 4**: US2 - Feature extraction and stats.
6. **Phase 5**: US3 - Modeling and validation.
7. **Phase N**: Polish and documentation.