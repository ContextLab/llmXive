# Specification: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## 1. Introduction

This project aims to develop a statistical analysis pipeline to detect cognitive decline using publicly available textual data from speech transcripts. The primary objective is to identify linguistic markers associated with Alzheimer's Disease (AD) and Mild Cognitive Impairment (MCI) compared to healthy controls.

## 2. Functional Requirements

### FR-001: Data Ingestion Scope (See US1)

**Requirement**: The system shall ingest raw text transcripts and associated cognitive status labels (Control, MCI, AD) from the ADReSS (Alzheimer's Disease Recognition System for Speech) Challenge dataset.  
**Optional**: The system may also ingest pre‑computed sentence embeddings (e.g., `all‑MiniLM‑L6‑v2`) when available to accelerate downstream processing.

**Scope Definition**:
- **Primary Source**: ADReSS Challenge Dataset (2019/2020 editions).
- **Excluded Sources**: DementiaBank is explicitly excluded from this project scope per the Implementation Plan. No code paths shall attempt to fetch or process data from DementiaBank unless a verified source URL and access method are provided in a future spec amendment.
- **Data Format**: Raw text transcripts and associated cognitive status labels; optional embedding files (`.npy` or `.pt`) may be accepted.

**Edge Cases**:
- Records with missing cognitive status labels **are omitted from the output CSV** and logged in `data/interim/exclusions.log`.
- Transcripts with insufficient length (< 50 words) **are omitted from the output CSV** and logged in `data/interim/exclusions.log`.
- Non‑verbal annotations (e.g., `<laughter>`, `<pause>`) shall be removed during preprocessing.

### FR-002: Linguistic Feature Extraction & Statistical Testing (See US2)

**Requirement**: The system MUST extract the lexical, syntactic, and semantic features listed in US2, adjust for known confounding variables (age, education), and perform appropriate statistical tests with non‑parametric effect‑size reporting.

### FR-003: Statistical Reporting (See US3)

**Requirement**: The system MUST generate a comprehensive report containing:
- Corrected p‑values (Bonferroni) for each feature comparison.
- Non‑parametric effect sizes (rank‑biserial correlation) with 95 % confidence intervals.
- Summary tables and visualizations suitable for manuscript inclusion.

### FR-004: Covariate Adjustment

**Requirement**: When testing group differences, the system MUST adjust for age and education level as covariates (e.g., via ANCOVA or regression‑based residualization) to control for confounding.

### FR-005: Privacy & Data Anonymization (See Non‑Functional Requirements)

**Requirement**: The pipeline MUST ensure that no Personally Identifiable Information (PII) – defined as any name, email address, phone number, or physical address – is logged or stored. An automated regex‑based audit step shall scan all intermediate files; any detection triggers a pipeline abort and a logged error.

### FR-006: Embedding Ingestion (Optional)

**Requirement**: When pre‑computed sentence embeddings (`all‑MiniLM‑L6‑v2`) are provided, the system shall load them alongside raw transcripts to enable downstream semantic similarity calculations without re‑encoding. The presence of embeddings does **not** replace the need for raw transcripts for lexical and syntactic feature extraction.

## 3. User Stories

### US1: Data Ingestion and Preprocessing

**As a** data scientist,  
**I want** to ingest and clean the ADReSS dataset (raw transcripts and optional embeddings),  
**So that** I have a structured, labeled dataset ready for feature extraction.

**Acceptance Criteria**:
1. The system downloads the ADReSS dataset from the canonical GitHub repository.
2. The system validates the downloaded data integrity using SHA‑256 checksums.
3. The system loads raw transcripts; if embedding files are present, they are also loaded.
4. The system cleans transcripts by removing non‑verbal annotations and normalizing text.
5. The system filters out records with missing labels or insufficient text length (< 50 words) and logs exclusions.
6. The system outputs a cleaned CSV file (`data/interim/cleaned_adress.csv`) and a metadata report (`data/results/metadata.json`).
7. **Exclusion**: The system does NOT attempt to access DementiaBank.

### US2: Linguistic Feature Extraction, Covariate Adjustment, and Statistical Testing

**As a** researcher,  
**I want** to extract linguistic features, adjust for confounders, and perform statistical tests,  
**So that** I can identify significant differences between cognitive groups.

**Acceptance Criteria**:
1. Extract lexical features (Type‑Token Ratio, MTLD, Noun/Verb ratio) and adjust each for age and education.
2. Extract syntactic features (Mean Clause Length, T‑unit Count) and adjust for age and education.
3. Extract semantic features (Sentence Embedding Cosine Similarity) using the `all‑MiniLM‑L6‑v2` model (or loaded embeddings) and adjust for age and education.
4. Perform Mann‑Whitney U tests between Control vs. AD and Control vs. MCI for each feature.
5. Report effect sizes using **rank‑biserial correlation** with 95 % confidence intervals, applying Bonferroni correction for multiple comparisons.

### US3: Statistical Reporting and Interpretation

**As a** researcher,  
**I want** a reproducible statistical report,  
**So that** I can interpret the significance and effect magnitude of linguistic markers across groups.

**Acceptance Criteria**:
1. Generate a PDF/HTML report summarizing all statistical test results, corrected p‑values, and rank‑biserial effect sizes.
2. Provide visualizations (boxplots) for each feature.
3. Archive the report at `data/results/statistical_report.pdf`.

## 4. Non-Functional Requirements

- **Reproducibility**: All random seeds must be fixed, and data sources must be versioned via checksums. An optional benchmark note: on an Intel Xeon E5‑2670 v3 (12 cores, 64 GB RAM) the full pipeline completes in ≤ 4 hours.
- **Privacy**: No PII (name, email, phone, address) shall be logged or stored; an automated regex audit must verify this condition (see FR‑005).
- **Robustness**: The pipeline shall log all exclusion reasons to `data/interim/exclusions.log` and continue processing remaining records.
- **Memory**: Peak RAM usage must not exceed 16 GB, measured by monitoring the process RSS during execution.

## 5. Data Model

(See `data-model.md` for detailed entity definitions)

## 6. Contracts

(See `contracts/` directory for API and data schemas)

## 7. Implementation Plan

The project follows a phased approach:
1. **Phase 0**: Spec Amendment (T000) – Resolve scope contradictions.
2. **Phase 1**: Setup – Project structure and dependencies.
3. **Phase 2**: Foundational – Logging, config, validation.
4. **Phase 3**: US1 – Ingestion and cleaning.
5. **Phase 4**: US2 – Feature extraction, covariate adjustment, and statistical testing.
6. **Phase 5**: US3 – Reporting and interpretation.
7. **Phase N**: Polish and documentation.

## 8. Success Criteria

- **SC-001**: At least one linguistic feature shows a statistically significant difference (Bonferroni‑adjusted *p* ≤ 0.05) between Control and AD or Control and MCI groups.
- **SC-002**: The cleaned dataset (`cleaned_adress.csv`) contains ≥ 1000 records after exclusions, and the metadata report lists exact counts per group.
- **SC-003**: The final statistical report (`data/results/statistical_report.pdf`) is generated without errors, includes all required visualizations, and passes the automated PII audit.
