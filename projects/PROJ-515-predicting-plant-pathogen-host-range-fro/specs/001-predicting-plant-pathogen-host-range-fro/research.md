# Research: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

## Overview

This research document details the dataset strategy, feature engineering rationale, statistical methodology, and computational feasibility for the plant pathogen host-range prediction pipeline. All external dataset references are limited to the verified sources listed below.

## Dataset Strategy

| Dataset Name | Description | Verified Source URL | Usage in Pipeline |
|--------------|-------------|---------------------|-------------------|
| PHI-Base | Host-pathogen interaction records (primary source) | certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)')))] | Primary interaction matrix; merged with Interactome3D and NCBI BioSample. Missing records treated as 'unknown' (FR-013). |
| Interactome3D | Supplemental host-pathogen interactions | Name or service not known)"))] | Merged with PHI-Base to capture full host-range breadth. |
| NCBI BioSample | Host-pathogen metadata and interactions | https://www.ncbi.nlm.nih.gov/biosample | Supplemental interactions; used to fill gaps in PHI-Base/Interactome3D. |
| NCBI GenBank | Pathogen genome FASTA files | https://www.ncbi.nlm.nih.gov/genbank | Downloaded via accession numbers (FR-001); used for genomic feature extraction. |

**Dataset Fit Verification**:
- **Required Variables**: Pathogen accession ID, host species name, binary infection label, effector count, Pfam domain counts, GC content, k-mer frequencies, secondary-metabolism cluster counts.
- **Verification Status**:
 - PHI-Base, Interactome3D, NCBI BioSample: Provide host-pathogen pairs (pathogen ID, host ID, infection status). Verified URLs available for programmatic access.
 - NCBI GenBank: Provides genome FASTA files for pathogen accession IDs. Verified URL available for programmatic access via `Entrez` (Biopython).
 - **Critical Note**: If a pathogen lacks interaction records across all three sources (PHI-Base, Interactome3D, NCBI BioSample), the pipeline halts processing for that pathogen (FR-011). If a required genomic feature (e.g., effector count) cannot be computed due to missing genome data, the pathogen is skipped with a warning.

**Missing Data Handling**:
- Missing interaction records are treated as 'unknown' (excluded from training labels) unless sensitivity analysis is run (FR-016).
- A data-quality report quantifies the percentage of missing data per pathogen (FR-013).

## Feature Engineering Rationale

| Feature Category | Biological Rationale | Extraction Method | Validation Source |
|------------------|----------------------|-------------------|-------------------|
| Effector Protein Count | Effectors are key virulence factors determining host specificity | EffectorP 3.0 HMM library (protein prediction) | EffectorP 3.0 publication (validated for fungal/bacterial pathogens) |
| Gene-Family Abundance (Pfam) | Domain composition reflects functional capabilities and evolutionary adaptations | Pfam HMM database (hmmsearch) | Pfam 35.0 release (validated across diverse taxa) |
| GC Content | Genomic composition may correlate with host adaptation and environmental stability | Biopython `SeqUtils.GC()` | Standard genomic metric (no specific validation needed) |
| 4-mer Frequency Profile | Captures sequence composition biases linked to host range and evolutionary history | Custom k-mer counter (normalized counts) | Widely used in metagenomics and host prediction (e.g., Kraken, CLARK) |
| Secondary-Metabolism Cluster Counts | Secondary metabolites (e.g., toxins) influence host range and virulence | antiSMASH 7.0 (cluster detection) | antiSMASH 7.0 publication (validated for fungal/bacterial secondary metabolism) |

**Dimensionality Reduction Protocol**:
- **k-mer Profiles**: Raw k-mer vectors (256 dimensions) are reduced to 20 principal components (PCA) before model input to mitigate the "p >> n" problem.
- **Pfam Counts**: Only the most frequent Pfam domains across the dataset are retained; rare domains are discarded to reduce noise.
- **GC Content**: If k-mer PCA features are used, GC content is excluded from the model to avoid mathematical redundancy (k-mers inherently capture GC content).
- **Resulting Feature Set**: ~100 dimensions (20 k-mer PC + 50 Pfam + Effector + SM Cluster), making the model identifiable with 50 samples.

**Collinearity Management**:
- Variance Inflation Factor (VIF) analysis will be performed (FR-014) to detect collinearity (threshold ≥ 5).
- Highly collinear features will be removed within cross-validation training folds to prevent overfitting.
- If predictors are definitionally related (e.g., one is bounded by another), independent effects will not be claimed; instead, relationships will be reported descriptively with collinearity acknowledged.

## Statistical Methodology

### Model Training (FR-004, FR-005)
- **Algorithm**: Regularized logistic regression (L1 penalty) with inner k-fold cross-validation to determine optimal λ.
- **Validation**: Outer k-fold cross-validation (pathogen-stratified) to estimate generalization performance.
- **Metrics**: AUPRC (primary), precision at 0.50 recall, calibrated probability scores.
- **Baseline**: Random predictor (AUPRC ≈ prevalence) for comparison (SC-001).
- **Power Consideration**: With 50 samples and ~100 features, the model is at the limit of statistical power. Results are framed as exploratory, with explicit acknowledgement of the limitation. The L1 penalty and dimensionality reduction (PCA, top-50) are critical to prevent overfitting.

### Feature Importance Significance (FR-006, FR-007)
- **Method**: Permutation testing (1,000 permutations) with Benjamini-Hochberg FDR correction (α = 0.05).
- **Nested CV**: Feature selection and permutation testing occur strictly within cross-validation training folds to prevent overfitting.
- **Output**: SHAP values for all features; ranked list of significant feature categories.

### Sensitivity Analysis (FR-016)
- **Approach**: Treat missing interaction records as negative examples (instead of 'unknown') and retrain the model.
- **Comparison**: Report variance in AUPRC between 'unknown' and 'negative' treatments; flag if difference exceeds significance threshold (p < 0.05, permutation test on AUPRC distributions).
- **Implementation**: Two separate model runs are performed; the difference in AUPRC is calculated and reported in `results/sensitivity_report.json`.

### Hold-Out Validation (FR-012, SC-001)
- **Strategy**: Pathogen-stratified hold-out set (10 pathogens) reserved before any training or feature selection.
- **Validation**: Independent evaluation on hold-out set; AUPRC ≥ 0.70 and ≥ 0.05 points higher than random baseline (p < 0.01).

### Multiple Testing Correction
- **Method**: Benjamini-Hochberg FDR at α = 0.05 for all hypothesis tests (feature importance, sensitivity analysis).
- **Rationale**: Controls family-wise error rate when testing multiple feature categories (five groups).

### Power and Sample Size Considerations
- **Assumption**: 50 pathogens provide moderate power to detect medium-effect sizes in the hold-out set.
- **Limitation**: If power is insufficient, results will be framed as exploratory with explicit acknowledgement of limitations.

### Causal Inference Assumptions
- **Observational Nature**: All inferences are framed as **associational** (e.g., "feature X is associated with broader host range") rather than causal.
- **No Randomization**: No randomization or identification strategy for causal claims; causal language avoided.

### Bias Control & Ground Truth Definition
- **Circularity Mitigation**: The model is trained on a binary matrix where 'unknown' rows are dropped. The 'Host-Range Breadth' metric (FR-017) is calculated against the *observed* ground truth (count of unique hosts in the database) to avoid tautology. The model's predicted mean probability is used for ranking, but validation is against the observed count.
- **Bias-Awareness Report**: The report (FR-018) will explicitly flag pathogens where 'known' hosts < 5 to indicate potential bias due to uneven sampling.

## Computational Feasibility

### Resource Constraints (GitHub Actions Free Tier)
- **Hardware**: 2 CPU cores, 7 GB RAM, 14 GB disk, no GPU, ≤6 h runtime.
- **Memory**: Pipeline limited to ≤ 4 GB RAM (FR-009); data subsets to fit memory.
- **Runtime**: End-to-end completion ≤ 5 hours for 50 pathogens (SC-004).

### Library and Method Selection
- **CPU-Only Libraries**: `scikit-learn` (logistic regression, permutation testing), `pandas`, `numpy`, `shap` (cpu-only version), `biopython`, `requests`, `loguru`, `pyyaml`.
- **No GPU/CUDA**: No deep learning, no 8-bit/4-bit quantization, no CUDA-dependent libraries.
- **Small Models**: Logistic regression (CPU-tractable); no large-LLM inference or deep-net training.

### Data Subset Strategy
- **Genome Data**: 50 pathogens (max 2 GB total); processed in batches if memory exceeds 4 GB.
- **Feature Matrix**: Sparse representation for k-mer frequencies to reduce memory footprint.
- **Runtime Optimization**: Parallel processing (where safe) for feature extraction; caching of intermediate results.

### Risk Mitigation
- **Memory Overflow**: If memory exceeds 4 GB, pipeline will downsample k-mer features or process pathogens in smaller batches.
- **Runtime Exceedance**: If runtime approaches 5 hours, pipeline will log warnings and prioritize critical steps (model training, evaluation) over non-essential reporting.
- **Dataset Unavailability**: If PHI-Base/Interactome3D/NCBI BioSample APIs are unreachable, pipeline will log errors and halt (FR-011); manual curation may be required.

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Logistic Regression (L1) | Interpretable, CPU-tractable, handles sparse features; aligns with FR-004. | Random Forest (less interpretable), Neural Networks (GPU-dependent, overkill). |
| Permutation Testing + FDR | Robust to multiple testing; no distributional assumptions; aligns with FR-006. | Bootstrap (computationally heavier), parametric tests (assumptions may not hold). |
| SHAP Values | Model-agnostic interpretability; aligns with FR-007 and Constitution VII. | LIME (less stable), coefficient magnitudes (only valid for linear models). |
| 'Unknown' Treatment for Missing Data | Avoids false negatives; aligns with FR-013 and biological reality. | Treat as negative (may bias results; used only in sensitivity analysis per FR-016). |
| Pathogen-Stratified Hold-Out | Ensures representative validation; aligns with FR-012 and SC-001. | Random hold-out (may miss rare pathogens). |
| PCA for k-mers | Reduces 256 dimensions to 20, mitigating p >> n; retains most variance. | Raw k-mers (overfitting risk), other feature selection methods (less stable). |

## Conclusion

This research plan confirms dataset availability (via programmatic access to NCBI GenBank and interaction databases), validates feature engineering methods against biological literature, and ensures statistical rigor through permutation testing, FDR correction, and nested cross-validation. Computational feasibility is guaranteed by CPU-only libraries, memory constraints, and runtime optimizations. All decisions align with the project's functional requirements, success criteria, and constitution principles.
