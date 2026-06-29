# Research: 001-soil-microbiome-diversity-disease-resistance

## Summary

This research plan addresses the spec's core hypothesis: soil microbiome alpha-diversity is associatively related to plant disease incidence using observational data. **Construct Validity Note**: Spec title uses "Disease Resistance" but measures "disease incidence" (observational, not controlled inoculation). All analyses framed as associational per FR-009. The methodology involves downloading 16S rRNA amplicon data and disease incidence records, computing diversity metrics, fitting beta regression/GLMM models, and performing ANCOM/co-occurrence network analysis. **BLOCKING GATE**: No verified dataset sources exist for required data (see Dataset Strategy).

## Dataset Strategy

| Dataset | Required Variables | Verified Source | Fit Assessment |
|---------|-------------------|-----------------|----------------|
| EMP agricultural subset | OTU/ASV tables, plant species, GPS, soil type, sequencing depth | NO verified source found | **MISMATCH**: Spec requires EMP agricultural data; verified datasets block contains no Earth Microbiome Project agricultural subset URLs. The EMP URLs in verified block are unrelated (MiniMax-M3, Empathetic counseling, global censorship). |
| MG-RAST soil microbiome | OTU/ASV tables, metadata | NO verified source found | **MISMATCH**: Spec requires MG-RAST soil microbiome repository; verified datasets block explicitly states "NO verified source found". |
| Plant disease incidence records | sample ID, disease type, incidence rate (0-100%), measurement date | NO verified source found | **MISMATCH**: Spec requires disease incidence records with matched metadata; verified datasets block contains no plant disease database URLs. |
| GPS (csv) | N/A | https://huggingface.co/datasets/Nazarko/D_GPS_Accelerometer/resolve/main/GPS_Accelerometer_data_100000_entries.csv | **NOT APPLICABLE**: Contains GPS/accelerometer data, not soil microbiome or disease records. |
| OTU (parquet) | N/A | | **NOT APPLICABLE**: Contains Turkish Lloyd data, not 16S rRNA OTU tables. |
| ASV (json) | N/A | https://huggingface.co/datasets/LanceaKing/asvspoof2019/resolve/main/dataset_infos.json | **NOT APPLICABLE**: Contains ASV spoof detection data, not soil microbiome ASVs. |

### Dataset Fit Conclusion

**FATAL MISMATCH**: The spec's required datasets (EMP agricultural subset, MG-RAST soil microbiome, plant disease incidence records) have NO verified sources in the provided verified datasets block. Per FR-008, the system must record `[MISSING_VARIABLE: <variable-name>]` for any missing variables. However, since entire datasets are unavailable, this represents a blocking gap that requires either:

1. **Option A**: Locate and verify alternative datasets containing the required variables (soil microbiome OTU/ASV tables with plant species, GPS, soil type, sequencing depth; disease incidence records with sample ID, disease type, incidence rate, measurement date), OR
2. **Option B**: Amend the spec to reference available datasets that contain subset of required variables, OR
3. **Option C**: Flag as blocking gap requiring spec revision before implementation proceeds.

**Recommendation**: Implementers should pause and flag this as a blocking dataset-variable fit issue per the planning instructions. Do NOT proceed with analysis planning as if the datasets fit when they do not.

## Statistical Methods

### Alpha-Diversity Computation (FR-003)

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Shannon | H = -Σ p_i × ln(p_i) | Diversity considering richness and evenness |
| Simpson | D = 1 - Σ p_i² | Probability two random reads are different taxa |
| Faith's PD | Sum of branch lengths in phylogenetic tree | Phylogenetic diversity |

**Implementation**: QIIME 2 `diversity alpha` plugin via subprocess. If QIIME 2 containerization fails on CPU-only runner, fall back to scikit-bio diversity calculations.

**Collinearity Note (FR-012)**: Three alpha-diversity metrics are mathematically correlated from same OTU table. Plan addresses FR-012 by: (a) computing Variance Inflation Factor (VIF) for each metric when used together; (b) if VIF >5, either model metrics separately with collinearity warning, or use PCA to create orthogonal composite diversity score; (c) report all relationships descriptively without claiming independent effects for definitionally related predictors.

### Beta Regression / GLMM (FR-004)

| Component | Specification |
|-----------|---------------|
| Response | Disease incidence (proportion 0-100%, transformed to (0,1)) |
| Fixed Effects | Alpha-diversity metric (Shannon/Simpson/Faith's PD), soil_type (covariate per concern methodology-79e5b1ed) |
| Random Effects | Plant species (intercept), Geographic region (intercept) |
| Link Function | Logit (for beta regression) |
| Distribution | Beta (for continuous proportions) or Binomial (for count data) |

**Implementation**: statsmodels `GLM` with Beta family or `lme4` equivalent in Python (statsmodels MixedLM). Check for singular fit; if boundary issues occur, report as model convergence warning per edge cases. **Soil Type**: Added as fixed effect covariate to control for confounding (soil type influences both microbiome composition and disease susceptibility).

### Permutation Tests (FR-005)

| Parameter | Value |
|-----------|-------|
| Permutations | a sufficient number (per spec) |
| Null Hypothesis | No association between diversity and disease incidence |
| Alternative | Observed correlation exceeds random expectations |
| p-value Calculation | (count of permuted statistics ≥ observed + 1) / (permutations + 1) |
| Stratification | **Maintained during permutation** by plant species and geographic region to preserve hierarchical data structure per GLMM assumptions (per concern scientific_soundness-934443ea) |

**Implementation**: Custom permutation function with random seed pinning. Verify stability across multiple independent runs per SC-004.

### Multiple-Comparison Correction (FR-010)

| Method | Application |
|--------|-------------|
| Benjamini-Hochberg FDR | Applied when >1 hypothesis test is run |
| Test Count Accounting | **Explicit enumeration**: 3 diversity metrics × N crop subsets + ANCOM across all taxa (potentially hundreds) + network centrality tests |
| Coverage Requirement | ≥100% correction coverage per SC-005 |

**Implementation**: statsmodels `multipletests` with method='fdr_bh'. Track all hypothesis tests in results log; verify ≥100% correction coverage. **Test Count Tracking**: Results output includes total hypothesis test count for SC-005 measurement.

### ANCOM Differential Abundance (FR-006)

| Parameter | Specification |
|-----------|---------------|
| Groups | High-disease vs. Low-disease sites (stratified by median or threshold) |
| Test | ANCOM (Analysis of Composition of Microbiomes) |
| Significance Threshold | q < 0.1 (FDR-corrected) |
| Output | Taxa enriched in disease-suppressed soils |
| Analysis Type | **Exploratory/Hypothesis-Generating** (distinct from confirmatory beta regression/GLMM per concern scientific_soundness-f26f791b) |

**Implementation**: scikit-bio or ancom-BC implementation. If ANCOM fails to converge, report as edge case per spec. **Note**: ANCOM stratification by disease incidence should not be circularly interpreted with main model outcomes; results are hypothesis-generating for keystone taxa identification.

### Co-occurrence Networks (FR-007)

| Parameter | Specification |
|-----------|---------------|
| Tool | CoNet or networkx-based implementation |
| Centrality Metrics | Betweenness, degree |
| Keystone Threshold | High betweenness/degree nodes |
| Output | ≥2 taxa flagged as putative keystones |

**Implementation**: networkx for graph construction and centrality computation. CoNet via subprocess if containerized.

### Power Analysis (FR-015)

| Parameter | Specification |
|-----------|---------------|
| Target Power | ≥0.8 |
| Effect Size | **≥0.1 requires literature justification from soil microbiome-disease meta-analyses per SC-001** (concerns methodology-722f9a81, scientific_soundness-36e0a132). If no meta-analysis exists, flag as spec-root cause requiring FR-015 amendment. |
| Method | A priori sample size calculation for beta regression/GLMM |
| Output | Minimum N required; report if actual N < minimum |

**Implementation**: statsmodels `power` module or G*Power equivalent. If actual sample size < minimum, acknowledge power limitation in results. **Literature Justification**: Effect size threshold must be derived from SC-001 meta-analysis source (see Success Metrics Alignment below).

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| CPU-only methods | GitHub Actions free-tier runner has no GPU; all methods must run on a limited number of CPU cores and memory resources |
| Default precision | No 8-bit/4-bit quantization; avoid CUDA dependencies |
| Sampled datasets if needed | If raw data exceeds 7 GB RAM, sample to fit constraints; document sampling rate |
| Beta regression over GLMM | Disease incidence is proportion data; beta distribution better handles (0,1) bounded outcomes |
| Associational framing | Observational design precludes causal claims per FR-009 |
| Dataset mismatch flag | Per planning instructions, do NOT plan as if datasets fit when verified sources do not exist |
| Soil type as covariate | Controls for confounding; soil type influences both microbiome and disease (concern methodology-79e5b1ed) |
| Stratified permutation | Maintains hierarchical data structure per GLMM assumptions (concern scientific_soundness-934443ea) |
| Collinearity diagnosis | VIF calculation and descriptive framing for alpha-diversity metrics (concern scientific_soundness-d0cfbecd, FR-012) |
| Confirmatory vs exploratory | ANCOM distinct from beta regression/GLMM to avoid circular interpretation (concern scientific_soundness-f26f791b) |
| Dataset mismatch flag | Per planning instructions, do NOT plan as if datasets fit when verified sources do not exist |

## Edge Case Handling

| Edge Case | Handling Strategy |
|-----------|-------------------|
| <30 matched samples | Report as data acquisition failure; cannot proceed with statistical power requirements |
| Sequencing depth variation >10x | Rarefaction discards >50% reads: document as data quality issue; consider alternative normalization (e.g., CSS, TSS) |
| Model convergence failure | Report singular fit/boundary issues; try alternative model specifications; if persistent, report as analysis limitation |
| ANCOM yields no significant taxa | Report as null result (q≥0.1 for all); do NOT fabricate significant findings |
| Dataset variables missing | Record [MISSING_VARIABLE: <variable-name>] per FR-008; count affected samples |
| Model overfitting (N too small) | Acknowledge in results; report power analysis from FR-015 |
| Alpha-diversity collinearity | VIF >5 triggers either separate modeling with warning or PCA composite (FR-012 compliance) |

## Success Metrics Alignment

| Success Criteria | Measurement | Source |
|------------------|-------------|--------|
| SC-001: Correlation coefficient | Compare against published meta-analysis values from soil microbiome-disease literature | **Meta-analysis source must be identified and cited during research phase** (concern scientific_soundness-a36203a1); if no meta-analysis exists, flag as blocking gap |
| SC-002: Model fit (R², AIC) | Compare against null model baseline | Model output |
| SC-003: Keystone taxa count | Count taxa with q<0.1 from ANCOM | ANCOM output |
| SC-004: Permutation p-value stability | Measure across multiple independent runs | Permutation test output |
| SC-005: Multiple-comparison correction | Track all hypothesis tests; verify ≥100% coverage; include total test count in results log | Test execution log |
| SC-006: Data acquisition quality | Matched sample count, variable completeness | Data acquisition output |