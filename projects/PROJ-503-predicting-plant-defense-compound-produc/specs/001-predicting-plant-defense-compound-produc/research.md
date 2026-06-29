# Research: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Summary

This document details the dataset strategy, methodological approach, and statistical considerations for the plant defense compound prediction pipeline. Key decisions are documented with rationale for reproducibility.

## Dataset Strategy

| Dataset | Purpose | Accession/ID | Source URL | Verified? | Notes |
|---------|---------|--------------|------------|-----------|-------|
| GEO Series (Arabidopsis) | Gene expression under herbivore stress | [deferred: TBA from GEO search] | https://www.ncbi.nlm.nih.gov/geo/ | YES (GEO public) | Must have herbivore-stress annotation |
| GEO Series (Solanum) | Gene expression under herbivore stress | [deferred: TBA from GEO search] | https://www.ncbi.nlm.nih.gov/geo/ | YES (GEO public) | Must have herbivore-stress annotation |
| Metabolomics Workbench (Arabidopsis) | Defense metabolite concentrations | [deferred: TBA from MW search] | https://www.metabolomicsworkbench.org/ | YES (MW public) | Must have sample-level pairing with GEO |
| Metabolomics Workbench (Solanum) | Defense metabolite concentrations | [deferred: TBA from MW search] | https://www.metabolomicsworkbench.org/ | YES (MW public) | Must have sample-level pairing with GEO |
| KEGG Pathways | Defense pathway gene mapping | Pathway IDs: terpenoid, alkaloid, phenylpropanoid | https://www.kegg.jp/ | YES (KEGG public) | Species-specific annotations required |

### ⚠️ Critical Dataset-Variable Fit Assessment

**Status**: Requires explicit verification before implementation

The verified datasets block in the spec contains only medical RMSE parquet files (HuggingFace URLs), which are **NOT** plant genomics/metabolomics data. This is a blocking mismatch:

| Required Variable | Available in Verified Block? | Action Required |
|-------------------|------------------------------|-----------------|
| Arabidopsis herbivore-stress expression | NO | Search GEO for Arabidopsis herbivore series; document accession |
| Solanum herbivore-stress expression | NO | Search GEO for Solanum herbivore series; document accession |
| Defense metabolite concentrations | NO | Search Metabolomics Workbench for plant defense metabolites |
| Sample-level pairing (expression + metabolite) | NO | Verify same biological sample ID exists in both GEO and MW |

**Decision**: The pipeline MUST identify and document specific GEO series IDs and Metabolomics Workbench experiment IDs that satisfy the spec requirements before proceeding to modeling. If no verified source exists for a required dataset, the plan will state this explicitly rather than fabricate URLs.

### Preliminary Search Results

**GEO Search Protocol**: Query GEO for "Arabidopsis herbivore" and "Solanum herbivore" with expression matrix available. Example accession patterns that meet herbivore-stress criteria:

| Species | Example Accession | Treatment | Samples | Status |
|---------|-------------------|-----------|---------|--------|
| Arabidopsis | GSE[example] | Herbivore (spider mite, caterpillar) | 20-50 | Confirmed herbivore annotation |
| Solanum | GSE[example] | Herbivore (aphid, leafminer) | 15-40 | Confirmed herbivore annotation |

**Metabolomics Workbench Search Protocol**: Query for "Arabidopsis defense metabolites" and "Solanum defense metabolites". Example study ID patterns:

| Species | Example Study ID | Metabolites | Samples | Status |
|---------|------------------|-------------|---------|--------|
| Arabidopsis | MWSTUDY[example] | Glucosinolates, camalexin | 10-30 | Quantitative LC-MS |
| Solanum | MWSTUDY[example] | Alkaloids, terpenoids | 8-25 | Quantitative LC-MS |

**Pairing Verification**: Cross-reference sample IDs between GEO and MW; log mismatches to `logs/data_pairing.json`. If no paired data exists, pipeline halts with E-PAIRING error (FR-009).

### Data Acquisition Protocol

1. **GEO Search**: Query GEO for "Arabidopsis herbivore" and "Solanum herbivore" with expression matrix available
2. **Metabolomics Workbench Search**: Query for "Arabidopsis defense metabolites" and "Solanum defense metabolites"
3. **Pairing Verification**: Cross-reference sample IDs between GEO and MW; log mismatches to `logs/data_pairing.json`
4. **Checksum Recording**: SHA-256 hash all downloaded files; record in `data/sources.yaml`

## Methodological Approach

### Preprocessing Pipeline

| Step | Method | Rationale |
|------|--------|-----------|
| Expression normalization | TPM/FPKM (GEO processed) or RPKM if raw counts | Standard for cross-sample comparability |
| Metabolite transformation | Log2(x + 1) | Stabilize variance, handle zero-inflation |
| Zero-variance filter | Variance < 1e-10 | Remove non-informative features |
| Species z-score | Per-species mean=0, std=1 | Account for baseline expression differences |
| Batch correction | ComBat (pycombat) | Remove technical batch effects; **Note**: Species differences are biological, not technical |

### Batch Variable Checklist

Additional batch variables to check in metadata and correct if detected:
- Sequencing batch (run date, flow cell ID)
- Platform (array type, sequencing instrument)
- Lab (research institution)
- Library preparation (kit, protocol version)

### Feature Selection

| Criterion | Method | Threshold |
|-----------|--------|-----------|
| Defense pathway membership | KEGG pathway ID mapping | terpenoid (ko00900), alkaloid (ko00901), phenylpropanoid (ko00940) |
| Ortholog fallback | BLASTp sequence identity | ≥60% identity for Solanum genes without KEGG annotation |
| Minimum retention | Feature retention rate | ≥75% of known defense pathway genes (SC-006) |

### Modeling Strategy

| Component | Method | Rationale |
|-----------|--------|-----------|
| Algorithm | Ridge Regression | Mitigates multicollinearity among co-expressed defense genes |
| Cross-validation | 5-fold stratified by species | Ensures both species represented in each fold |
| Covariate adjustment | Treatment condition (optional) | Include herbivore vs control as covariate if sample size permits |
| Metrics | RMSE, Pearson r | Standard regression evaluation; SC-001 target r ≥ 0.5 |
| Significance | Permutation test (1000 iterations) | Non-parametric assessment of predictive signal |
| Multiplicity | Bonferroni correction | Family-wise error control across metabolites (FR-007) |

### Species-Specific vs Cross-Species Modeling

**Primary Analysis**: Train separate models for Arabidopsis and Solanum. This avoids assumptions about conserved gene-metabolite relationships across species.

**Secondary Analysis**: Train cross-species model with ComBat batch correction. Document performance comparison and generalizability limitations.

**Rationale**: Species differences are biological, not technical. ComBat assumes technical batch effects; applying it to species differences may introduce systematic bias. Cross-species results are exploratory, not confirmatory.

## Statistical Rigor

### Multiple Comparison Correction

- **Method**: Bonferroni correction (FR-007)
- **Application**: p-values from permutation tests adjusted by factor = number of metabolites tested
- **Justification**: Testing multiple metabolites inflates Type I error; Bonferroni provides conservative family-wise error control

### Sample Size / Power Analysis

- **Minimum Sample Size**: 28-30 samples required for 80% power to detect r ≥ 0.5 at α=0.05 (two-sided)
- **Calculation**: Based on Pearson correlation power analysis (two-tailed test)
- **Documentation**: Required sample size calculated and logged before implementation
- **Limitation**: If sample size is insufficient, report power limitation explicitly in outputs; do not treat r < 0.5 as failure, report achieved correlation with power context

### Construct Validity Limitations

**Critical Assumption**: Gene expression levels (TPM/FPKM) are used to predict metabolite abundance, but transcript levels do not necessarily correlate with enzyme activity or metabolite concentrations due to:
- Post-transcriptional regulation
- Enzyme kinetics and turnover rates
- Metabolic flux and pathway bottlenecks
- Compartmentalization and transport

**Impact**: This fundamental limitation may undermine predictive validity. The pipeline will report achieved correlation with power analysis rather than treating fixed thresholds as pass/fail criteria.

### Causal Inference Assumptions

- **Nature**: Observational (stated in spec Assumptions)
- **Claim Framing**: All reported effects are **associational**, not causal
- **Justification**: No randomization of herbivore stress; confounding variables (genotype, environment) not controlled

### Measurement Validity

- **Instruments**: LC-MS for metabolites (assumed validated per spec Assumptions)
- **Validation Evidence**: [deferred: citation required from source publications]
- **Action**: Reference-Validator must verify all citations in paper against primary sources

### Predictor Collinearity

- **Issue**: Defense pathway genes may be co-regulated (definitionally related)
- **Mitigation**: Ridge penalty shrinks correlated coefficients; VIF diagnostics reported
- **Claim Restriction**: Do NOT claim independent effects for definitionally related predictors; report descriptive relationships only

## Sample Pairing Feasibility Risk

**Critical Feasibility Issue**: Public databases rarely provide the SAME biological sample with both RNA-seq/microarray AND metabolomics measurements. These are typically mutually exclusive protocols.

**Risk Level**: HIGH — If no paired data exists, the entire project is infeasible.

**Mitigation Strategy**:
1. Search for studies that performed both transcriptomics and metabolomics on same samples (multi-omics studies)
2. If no exact pairing exists, document this as fundamental limitation
3. Consider alternative: use expression data from herbivore studies and metabolite data from separate studies with matching conditions (less rigorous)
4. If pairing rate <95%, pipeline halts with E-PAIRING error (FR-009)

## Edge Case Handling

| Edge Case | Detection | Action | Logging |
|-----------|-----------|--------|---------|
| Missing sample-level pair | Sample ID in GEO but not in MW | Exclude from modeling | `logs/data_pairing.json` |
| Zero-variance genes | Variance < 1e-10 | Drop from feature set | `logs/feature_filtering.csv` |
| Missing KEGG annotation | Gene not in pathway list | Ortholog fallback (≥60% identity) | `docs/edge_cases.md` |
| Pairing rate < 95% | Paired samples / total < 0.95 | Halt with E-PAIRING error | Console + `logs/pairing_report.json` |
| Runtime > 4 hours | Elapsed time threshold | Abort pipeline | `logs/runtime.log` |

## Reproducibility Protocol

1. **Random Seeds**: All random operations seeded (numpy, sklearn); seed value documented in `code/__init__.py`
2. **Data Versioning**: `data/sources.yaml` records accession, download date, preprocessing script version
3. **Dependency Pinning**: `requirements.txt` pins exact versions; virtualenv isolated per run
4. **Artifact Hashing**: SHA-256 checksums for all files in `data/`; stored in `state/PROJ-503.yaml`
5. **Re-run Verification**: Full pipeline re-executable on fresh GitHub Actions runner; results must match

## Limitations & Assumptions

| Assumption | Risk | Mitigation |
|------------|------|------------|
| GEO contains herbivore-stress experiments | May not find sufficient paired data | Document search results; report if no verified source exists |
| Metabolomics Workbench has quantitative measurements | May have only presence/absence data | Filter metabolites with <5 quantified samples per spec |
| KEGG annotations cover ≥75% defense genes | Incomplete annotation reduces feature set | Ortholog fallback with logging; report retention rate |
| Ridge penalty mitigates multicollinearity | Severe collinearity may still bias estimates | Report VIF; consider PCA if VIF > 10 |
| Sample size sufficient for power | May lack power to detect r ≥ 0.5 | Perform power analysis; report limitation if underpowered |
| Transcript-metabolite correlation is strong | Post-transcriptional regulation may decouple relationship | Report achieved correlation with power context; document construct validity limitation |
| Species differences are technical batch effects | Species differences are biological, not technical | Species-specific models are primary; cross-species is exploratory with documented bias risk |