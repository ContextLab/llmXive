# Research: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Overview

This document describes the research strategy, dataset selection, and methodological approach for predicting plant defense compound production from publicly available genomic and transcriptomic data.

## ⚠️ DATA BLOCKER: Dataset Availability

**CRITICAL**: The verified datasets block contains ONLY medical RMSE parquet files from HuggingFace, NOT plant genomic or transcriptomic data required for this project.

**Current Verified Datasets Block Contents**:
- https://huggingface.co/datasets/arjunashok/medical-5day-zeroshot-freshexps-test-plot_with_rmsesort/resolve/main/data/test-00000-of-00001.parquet
- https://huggingface.co/datasets/arjunashok/medical-5day-zeroshot-freshexps-test-no-context-plot_with_rmsesort_noctx/resolve/main/data/test-00000-of-00001.parquet

**These datasets are NOT suitable because**:
1. They contain medical/clinical data, NOT plant genomic or transcriptomic data
2. They do NOT contain gene expression profiles for Arabidopsis or Solanum
3. They do NOT contain defense metabolite concentrations
4. They do NOT support herbivore stress experimental conditions

**ABORT CRITERIA**: If no verified plant omics datasets are identified during Phase 0 Data Discovery, the project halts with error code **E-DATASET**. This is a research question blocker that cannot proceed without:
- Option A: Verified plant transcriptomic/metabolomic datasets added to verified datasets block
- Option B: Spec modification to use available medical datasets (changes research question)
- Option C: Project pause until plant-specific omics datasets are verified

## Dataset Strategy

| Dataset Type | Source | Accession/Identifier | Variables Needed | Status |
|--------------|--------|---------------------|------------------|--------|
| Gene Expression (Arabidopsis) | GEO | [DEFERRED: GEO series IDs with herbivore stress annotation] | TPM/FPKM values, sample IDs, herbivore treatment labels | ⚠️ **NO VERIFIED SOURCE** |
| Gene Expression (Solanum) | GEO | [DEFERRED: GEO series IDs with herbivore stress annotation] | TPM/FPKM values, sample IDs, herbivore treatment labels | ⚠️ **NO VERIFIED SOURCE** |
| Metabolite Concentrations | Metabolomics Workbench | [DEFERRED: Experiment IDs with defense metabolite measurements] | Log-transformed concentrations, sample IDs, metabolite IDs | ⚠️ **NO VERIFIED SOURCE** |
| KEGG Pathway Annotations | KEGG API | Plant-specific pathway IDs (terpenoid, alkaloid, phenylpropanoid) | Gene-pathway mappings, species identifiers | ⚠️ **NO VERIFIED SOURCE** |

### Dataset Availability Plan (Phase 0)

**MANDATORY PHASE 0 - DATA DISCOVERY** (before any data download):

1. **Search Protocol**: Query GEO for series with herbivore-stress annotations for Arabidopsis thaliana and Solanum species
2. **Metabolomics Search**: Query Metabolomics Workbench for targeted metabolomics experiments with defense compounds
3. **Pairing Feasibility Check**: Verify ≥95% sample-level pairing between expression and metabolite datasets (FR-009)
4. **Power Analysis**: Calculate required sample size for detecting r≥0.5 with 80% power at α=0.05. **Required: n≥28-30 samples** (see Power Analysis Framework below)
5. **Abort if**: No verified plant omics datasets found OR pairing rate <95% OR sample size <28

### Power Analysis Framework

**Statistical Basis**: For Pearson correlation coefficient testing:
- Null hypothesis: r = 0
- Alternative hypothesis: r ≥ 0.5
- Power: [deferred] (β = 0.20)
- Significance level: α = 0.05

**Sample Size Calculation**: Using Fisher's z-transformation approximation:
- Required n ≈ 28-30 for r ≥ 0.5, power = 0.80, α = 0.05 (two-tailed)
- **ABORT if available samples < 28** (error code E-POWER)

**Formula Reference**:
```
z_r = 0.5 * ln((1+r)/(1-r))
n = ((z_(1-α/2) + z_(1-β)) / z_r)^2 + 3
```

**Implementation**: Power analysis will be performed during Phase 0 using scipy.stats.power module. Document sample size and power calculation in outputs/power_analysis.json.

## Methodological Approach

### Statistical Rigor Requirements

| Requirement | Method | Status |
|-------------|--------|--------|
| Multiple-comparison correction | Bonferroni correction across all metabolites tested (FR-007) | ✅ Planned |
| Sample-size / power justification | **Phase 0 mandatory**: n≥28-30 samples for r≥0.5, 80% power, α=0.05 | ✅ Phase 0 |
| Causal inference assumptions | Observational study; all claims framed as associational, not causal | ✅ Documented |
| Measurement validity | All instruments validated (LC-MS with published calibration curves) per source publications [deferred: citation required] | ⚠️ Deferred to implementation |
| Predictor collinearity | Ridge penalty mitigates multicollinearity; VIF diagnostics reported | ✅ Planned |
| Treatment condition confounds | Stratified CV; treatment as covariate in exploratory models; document in docs/edge_cases.md | ✅ Planned |

### Model Specification

**PRIMARY APPROACH**: Species-specific Ridge Regression models

| Species | Model Type | Rationale |
|---------|-----------|-----------|
| Arabidopsis thaliana | Ridge Regression (L2 regularization) | Handle multicollinearity; computationally efficient on CPU |
| Solanum species | Ridge Regression (L2 regularization) | Handle multicollinearity; computationally efficient on CPU |

**EXPLORATORY ONLY** (if sample size permits and after species-specific models complete): Cross-species model with species as covariate

**WARNING**: Cross-species modeling has significant scientific validity concerns:
- Arabidopsis and Solanum have different gene sets, pathway architectures, and metabolic profiles
- Species-level confounds may introduce systematic bias beyond batch effects
- Claims from cross-species models must be explicitly framed as exploratory
- **If spec.md FR-010 requires cross-species as primary, this contradicts scientific soundness** (flagged for kickback)

**Cross-validation**: 5-fold CV (FR-005)  
**Permutation Testing**: Sufficient iterations for p-value calculation (FR-006)  
**Family-wise Error Correction**: Bonferroni across all metabolites tested (FR-007)

### Treatment Condition Modeling

**Herbivore Stress vs Control Stratification**:

1. **Cross-validation stratification**: Ensure balanced treatment/control distribution across folds
2. **Treatment as covariate**: In exploratory models, include treatment condition as covariate
3. **Separate analysis**: If treatment effects dominate, consider modeling herbivore-stress samples separately
4. **Document confounds**: Log treatment distribution in docs/edge_cases.md
5. **If treatment confounds cannot be controlled, acknowledge in paper as limitation**

### Biological Validity Note

**Gene Expression vs Metabolite Abundance Relationship**:

The relationship between gene expression and metabolite abundance is NOT guaranteed to be strong due to:
- Post-transcriptional regulation
- Enzyme activity modulation
- Substrate availability
- Compartmentalization and degradation

**SC-001 target (r≥0.5) is an exploratory target**. Weaker correlations may be biologically realistic. All claims about prediction performance must acknowledge these biological limitations.

## FR-SC Coverage Mapping

| FR/SC ID | Description | Plan Phase |
|----------|-------------|------------|
| FR-001 | Download GEO expression matrices | Phase 1 - Data Acquisition (after Phase 0 verification) |
| FR-002 | Retrieve Metabolomics Workbench metabolite data | Phase 1 - Data Acquisition (after Phase 0 verification) |
| FR-003 | Normalize expression (TPM/FPKM), log-transform metabolites, filter zero-variance | Phase 2 - Preprocessing |
| FR-004 | Select defense pathway genes via KEGG | Phase 2 - Feature Selection |
| FR-004 Extended | Include regulatory genes, transporters, compartmentalization factors | Phase 2 - Feature Selection |
| FR-005 | Train species-specific Ridge Regression with 5-fold CV; report RMSE, Pearson r | Phase 3 - Modeling |
| FR-006 | Permutation test with 1,000 iterations | Phase 3 - Evaluation |
| FR-007 | Bonferroni correction across metabolites | Phase 3 - Evaluation |
| FR-008 | Log runtime; abort if >4 h CPU time | Phase 0 - Infrastructure |
| FR-009 | Validate sample-level pairing; halt if <95% match rate | Phase 0 - Data Discovery |
| FR-010 | Species-specific models; cross-species exploratory only | Phase 3 - Modeling |
| SC-001 | Pearson r ≥ 0.5 for best metabolite (exploratory target) | Phase 3 - Evaluation |
| SC-002 | Permutation p-value ≤ 0.05 after Bonferroni | Phase 3 - Evaluation |
| SC-003 | E2E pipeline ≤ 4 hours on GitHub Actions | Phase 0 - Infrastructure |
| SC-004 | Checksum match ≥ 99% for downloaded files | Phase 1 - Data Acquisition |
| SC-005 | ≥ 95% expression samples have matched metabolite records | Phase 0 - Data Discovery |
| SC-006 | ≥ 75% defense pathway genes retained; zero-variance filtering logged | Phase 2 - Feature Selection |

## Edge Case Handling

| Edge Case | Handling Strategy | Logging Location |
|-----------|-------------------|------------------|
| GEO sample lacks metabolite measurement | Log to logs/data_pairing.json; exclude from modeling | logs/data_pairing.json |
| Gene with zero variance across samples | Drop during preprocessing; log to logs/feature_filtering.csv | logs/feature_filtering.csv |
| KEGG pathway ID not found for species | Fallback to orthologous genes (≥60% sequence identity); document in docs/edge_cases.md | docs/edge_cases.md |
| Sample size <28 | Halt with E-POWER error; project cannot proceed | Phase 0 abort |
| No verified plant omics datasets | Halt with E-DATASET error; project cannot proceed | Phase 0 abort |
| Treatment condition imbalance | Stratified CV; document in docs/edge_cases.md; acknowledge as limitation | docs/edge_cases.md |
| Cross-species biological incompatibility | Species-specific models PRIMARY; cross-species exploratory only | research.md |

## Dependencies & Versioning

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Runtime |
| pandas | [deferred] | Data manipulation |
| numpy | [deferred] | Numerical operations |
| scikit-learn | [deferred] | Ridge Regression, cross-validation |
| scipy | [deferred] | Statistical tests, permutation testing |
| statsmodels | [deferred] | VIF diagnostics |
| requests | [deferred] | HTTP requests for data download |
| pyyaml | [deferred] | YAML configuration |
| biopython | [deferred] | Sequence identity calculations |

All dependencies pinned in code/requirements.txt for reproducibility (Constitution Principle I).

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md FR-010 still references cross-species model as primary, but this research document correctly defines species-specific models as PRIMARY. This requires spec.md revision (flagged for kickback).

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md Assumptions defers power analysis to implementation, but this research document requires explicit power analysis in Phase 0 (n≥28-30). This requires spec.md revision (flagged for kickback).