# Research: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Overview

This research phase validates the feasibility of the proposed pipeline, confirms dataset availability against the strict "Verified datasets" list, and outlines the statistical strategy for addressing the small-n, large-p problem inherent in cross-species transcriptomics.

## Dataset Strategy

### Verified Datasets Analysis

The project specification requires plant-specific RNA-seq data (chewing vs. piercing-sucking herbivores) and defense trait data (TRY database).

**Constraint Check**: The provided "Verified datasets" block contains:
- **RNA-seq**: `recount3-RNA-seq` (human/mouse GTEx), `rnabert_small` (generic), `Paul_RNA_Sequence` (generic). **None** are explicitly identified as *plant herbivory* datasets.
- **NCBI/SRA**: `ncbi_disease` (human disease), `HERCULES` (roadseq), `pandaset` (autonomous driving), `geometry3k`. **None** match the domain.
- **GBIF**: `gbif_ca_h3`, `gbif_genus_species`, `gbif_coleoptera_eu`. These are biodiversity occurrence records, **not** transcriptomic data.
- **TRY**: `Try-Any-Bench`, `Meti_try`, `VITON-HD-IMAGE`. These appear to be generic or unrelated to plant defense traits (VITON is fashion).

**Critical Mismatch**: The "Verified datasets" block **does not contain** any verified URL for:
1. Plant RNA-seq data with herbivory treatment metadata (chewing vs. piercing-sucking).
2. Plant defense trait data (Glucosinolates, Trichome Density, etc.) from the TRY database.

**Decision**:
1.  **No Data Acquisition**: The pipeline **cannot** download the required raw FASTQ files or defense traits from the provided verified list.
2.  **Simulated Data Path (Structural Prototype)**: To allow the code structure and statistical logic to be implemented and tested (Unit/Integration tests), the plan will utilize **synthetic/simulated data** that mimics the expected schema (plant species, tissue, treatment, TPM counts, traits).
3.  **Runtime Flag**: The pipeline will include a `--mode synthetic` flag. When enabled, it generates data with a **known ground truth** correlation to validate the pipeline's ability to recover a signal.
4.  **Data Availability Blocker**: The project is currently in **Prototype Validation** status. It cannot proceed to `research_complete` or validate the biological hypothesis until verified real data is provided.

### Simulation Ground Truth vs. Biological Validation

-   **Structural Validation**: Synthetic data is used to verify that the pipeline correctly implements LOSO CV, PGLS, Power Analysis, and schema validation.
-   **Biological Validation**: Synthetic data **cannot** validate construct validity or biological signal. The correlation in synthetic data is defined by the generator, not biological reality.
-   **Interpretation**: Results from synthetic runs are interpreted as "Code Correctness" only. Any claim of biological prediction is invalid until real data is processed.

## Statistical Methodology & Rigor

### 1. Multiple Comparison Correction (FR-010)
-   **Method**: Holm-Bonferroni correction.
-   **Application**: Applied to all hypothesis tests (e.g., significance of model R², tissue-specific effects).
-   **Implementation**: `statsmodels.stats.multitest.multipletests` with method `'holm'`.

### 2. Power Analysis (FR-016)
-   **Method**: A priori power analysis for linear regression.
-   **Parameters**: Target $R^2$ sensitivity analysis: low, moderate, and high thresholds. $\alpha = 0.05$, Power ($1-\beta$) = 0.80.
-   **Threshold**: Minimum $N = 15$ species (for R²=0.3). If R²=0.1, N may need to be >50.
-   **Action**: If available N < 15 (or required N for expected effect size), the pipeline halts and reports "Insufficient statistical power".
-   **Sensitivity**: The plan will report the power estimate for a range of effect sizes to acknowledge uncertainty in cross-species genomics.

### 3. Phylogenetic Non-Independence (FR-007, FR-017)
-   **Problem**: Species share evolutionary history; standard regression assumes independence.
-   **Solution**:
    1.  **PGLS**: Fit Phylogenetic Generalized Least Squares model as a baseline.
    2.  **Phylogenetic Null Model**:
        -   **Method**: Permute the *outcome* (Defense Allocation Index) labels across the phylogenetic tree while preserving the phylogenetic structure of the predictors (X), OR use a phylogenetic permutation of residuals.
        -   **Iterations**: N=10,000.
        -   **Goal**: Generate a null distribution of R² values that accounts for shared evolutionary history in the predictors.
        -   **Validation**: Observed R² must exceed a high percentile of this null distribution to be considered significant *beyond* phylogenetic inertia.
-   **Interpretation**: If the null model is not rejected, it suggests the observed signal may be due to shared phylogeny rather than a specific transcriptomic-phenotypic link.

### 4. Small-n, Large-p Problem (FR-012)
-   **Problem**: Many genes (features) vs. ~15 species (samples).
-   **Solution**:
    1.  **Pathway Aggregation**: Map DE genes to KEGG/GO pathways. Reduce features to ≤50 pathway-level scores.
    2.  **Robustness Check**: Filter pathways to those with ≥3 mapped genes in *all* target species to avoid model organism bias.
    3.  **Regularization**: Elastic Net ($\alpha, l1\_ratio$) and Random Forest (max_depth, min_samples_leaf).
    4.  **LOSO CV**: Leave-One-Species-Out Cross-Validation to ensure no data leakage.

### 5. Data Leakage Prevention (FR-006, FR-007)
-   **Problem**: Predicting defense allocation from transcriptomics may be tautological if the transcriptome includes genes that *synthesize* the measured traits.
-   **Solution**: Explicitly exclude genes known to be involved in the synthesis of the measured defense traits (e.g., CYP79D16 for glucosinolates, genes for trichome development) from the predictor set.

### 6. Causal vs. Associational Claims
-   **Statement**: Findings are explicitly framed as **associational**. The design is observational; herbivore treatments are not randomized across species. No causal claims of "herbivory *causes* defense allocation" will be made without randomization or instrumental variables.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Dataset Mismatch** | High ([deferred] with current list) | Critical | Use synthetic data for pipeline validation; flag `human_input_needed` for real data. |
| **RAM Overflow** | Medium | High | Sample to 15 species; stream data processing; use sparse matrices where possible. |
| **Power Failure** | High (if N<15 or R²<0.1) | Critical | Explicit power analysis step; halt if N < 15 or power < 0.8 for expected effect size. |
| **Phylogeny Missing** | Medium | Medium | Generate synthetic tree if real tree unavailable; document limitation. |
| **Circular Validation** | High | Critical | Exclude trait-synthesis genes; use residual permutation for null model. |

## Decision Rationale

The decision to use synthetic data is driven by the **fatal dataset mismatch** in the "Verified datasets" block. The spec requires plant herbivory RNA-seq and TRY traits, but the provided list contains only human, disease, or non-biological datasets. Implementing a pipeline that attempts to fetch from these URLs would fail immediately. Using synthetic data allows the **statistical rigor** (LOSO, PGLS, Power Analysis) and **code structure** to be validated, ensuring the system works correctly when the correct datasets are eventually provided.

**Note**: This is a **Structural Prototype**. The biological hypothesis remains untested until verified real data is available.