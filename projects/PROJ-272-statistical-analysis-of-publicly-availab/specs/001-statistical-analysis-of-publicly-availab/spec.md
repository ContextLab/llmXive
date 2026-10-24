# Specification: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## 1. Introduction

This project aims to develop a statistical analysis pipeline to detect cognitive decline using publicly available textual data from speech transcripts. The primary objective is to identify linguistic markers associated with Alzheimer's Disease (AD) and Mild Cognitive Impairment (MCI) compared to healthy controls.

## 2. Functional Requirements

### FR-001: Data Ingestion Scope (See US1)

**Requirement**: The system shall ingest raw text transcripts and associated cognitive status labels (Control, MCI, AD) from the ADReSS (Alzheimer's Disease Recognition System for Speech) Challenge dataset.  
**Optional**: When pre‑computed sentence embeddings (`all‑MiniLM‑L6‑v2`) are provided, the system shall also ingest these embeddings to enable downstream semantic similarity calculations without re‑encoding. Raw transcripts remain required for lexical and syntactic feature extraction.

**Scope Definition**:
- **Primary Source**: ADReSS Challenge Dataset (2019/2020 editions).
- **Excluded Sources**: DementiaBank is explicitly excluded from this project scope per the Implementation Plan. No code paths shall attempt to fetch or process data from DementiaBank unless a verified source URL and access method are provided in a future spec amendment.
- **Data Format**: Raw text transcripts and associated cognitive status labels; optional embedding files (`.npy` or `.pt`) may be accepted.

**Edge Cases**:
- Records with missing cognitive status labels **are omitted from the output CSV** and logged in `data/interim/exclusions.log`.
- Transcripts with insufficient length (< 50 words) **are omitted from the output CSV** and logged in `data/interim/exclusions.log`.
- Non‑verbal annotations (e.g., `<laughter>`, `<pause>`) shall be removed during preprocessing.

### FR-002: Linguistic Feature Extraction, Covariate Adjustment, and Statistical Testing (See US2)

**Requirement**: The system MUST extract the lexical, syntactic, and semantic features listed in US2 and perform **ANCOVA** between groups (Control vs AD, Control vs MCI) for each feature, **including age and education as covariates directly in the ANCOVA model (no prior residualization)**. Results shall include **Bonferroni‑corrected p‑values** and **partial eta‑squared (η²)** effect sizes with 95 % confidence intervals.

### FR-003: Statistical Reporting (See US3)

**Requirement**: The system MUST generate a comprehensive report containing:
- Corrected p‑values (Bonferroni) for each feature comparison.
- Effect sizes reported as **partial eta‑squared (η²)** with 95 % confidence intervals.
- Summary tables and visualizations suitable for manuscript inclusion.

### FR-004: Covariate Adjustment

**Requirement**: When testing group differences, the system MUST adjust for age and education level by **including them as covariates in the ANCOVA model**, thereby controlling for confounding while using a parametric testing framework.

### FR-005: Privacy & Data Anonymization (See Non‑Functional Requirements, See US4)

**Requirement**: The pipeline MUST ensure that no Personally Identifiable Information (PII) – defined as any name, email address, phone number, or physical address – is logged or stored. An automated regex‑based audit step shall scan all intermediate files; any detection triggers a pipeline abort and a logged error.

### FR-007: Power Analysis (See US2)

**Requirement**: Prior to analysis, the system MUST perform an a priori power analysis targeting **≥ 80 % power** to detect a **medium effect size (Cohen’s d = 0.5)** for each feature after Bonferroni correction. The analysis shall determine the minimum detectable effect and confirm that the available sample size meets this criterion; results are recorded in `data/results/power_analysis.txt`.

### FR-008: ANCOVA Assumption Verification (See US2)

**Requirement**: The system MUST verify key ANCOVA assumptions for each feature:
- Normality of residuals (e.g., Shapiro‑Wilk test, α = 0.05).
- Homogeneity of regression slopes across groups.
- Linearity between covariates and the dependent variable.  
Diagnostics and any violations shall be reported in the final statistical report.

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
1. Extract lexical features (Type‑Token Ratio, MTLD, Noun/Verb ratio) and adjust for age and education **via ANCOVA covariates**.
2. Extract syntactic features (Mean Clause Length, T‑unit Count) and adjust for age and education **via ANCOVA covariates**.
3. Extract semantic features (Sentence Embedding Cosine Similarity) using the `all‑MiniLM‑L6‑v2` model (or loaded embeddings) and adjust for age and education **via ANCOVA covariates**.
4. Perform **ANCOVA** between Control vs. AD and Control vs. MCI for each feature.
5. Verify ANCOVA assumptions as specified in FR‑008; report diagnostics.
6. Report effect sizes using **partial eta‑squared (η²)** with 95 % confidence intervals, applying Bonferroni correction for multiple comparisons.
7. Conduct the a priori power analysis defined in FR‑007 and record the outcome.

### US3: Statistical Reporting and Interpretation

**As a** researcher,  
**I want** a reproducible statistical report,  
**So that** I can interpret the significance and effect magnitude of linguistic markers across groups.

**Acceptance Criteria**:
1. Generate a PDF/HTML report summarizing all statistical test results, corrected p‑values, and η² effect sizes.
2. Provide visualizations (boxplots) for each feature.
3. Archive the report at `data/results/statistical_report.pdf`.

### US4: Privacy Auditing

**As a** compliance officer,  
**I want** the pipeline to automatically audit all intermediate artifacts for personally identifiable information,  
**So that** we guarantee no PII is inadvertently stored or logged.

**Acceptance Criteria**:
1. After each processing step, run a regex‑based PII scanner over all generated files.
2. If any PII pattern is detected, abort the pipeline, emit a clear error message, and write the incident to `logs/privacy_audit.log`.
3. Verify that the final cleaned dataset (`cleaned_adress.csv`) contains no PII.

## 4. Non-Functional Requirements

- **Reproducibility**: All random seeds must be fixed, and data sources must be versioned via checksums. An optional benchmark note: on an Intel Xeon E5‑2670 v3 (12 cores, 64 GB RAM) the full pipeline completes in ≤ 4 hours.
- **Privacy**: No PII (name, email, phone, address) shall be logged or stored; an automated regex audit (see FR‑005 / US4) must verify this condition.
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
5. **Phase 4**: US2 – Feature extraction, covariate adjustment, statistical testing, and power analysis.
6. **Phase 5**: US3 – Reporting and interpretation.
7. **Phase 6**: US4 – Privacy auditing integration.
8. **Phase N**: Polish and documentation.

## 8. Success Criteria

- **SC-001**: At least one linguistic feature shows a statistically significant difference (Bonferroni‑adjusted *p* ≤ 0.05) **(See US2)**.
- **SC-002**: The cleaned dataset (`cleaned_adress.csv`) contains **≥ 120 records** after exclusions, and the metadata report lists exact counts per group (Justified by the sizable ADReSS dataset.) **(See US1)**.
- **SC-003**: The final statistical report (`data/results/statistical_report.pdf`) is generated without errors, includes all required visualizations, and passes the automated PII audit **(See US3 & US4)**.
- **SC-004**: Privacy audit reports **zero** PII detections; any detection aborts the pipeline as specified in US4.
- **SC-009**: The a priori power analysis (FR‑007) confirms **≥ 80 % power** to detect a medium effect size (Cohen’s d = 0.5) given the available sample size **(See US2)**.

## Requirements *(mandatory)*

Functional requirements are defined in the “Functional Requirements” section above. Please refer to those definitions for the authoritative specifications.

