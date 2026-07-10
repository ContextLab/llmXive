# Research: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Summary of Research

This research phase identifies the specific datasets, tools, and methodological strategies required to implement the plan within the constraints of a CPU-only GitHub Actions runner. It addresses the critical feasibility gap regarding antiSMASH execution, the availability of matched genomic/metabolomic data, and the statistical challenges of small sample sizes (N < 50).

## Dataset Strategy

The study requires a matched set of plant species with both high-quality genome assemblies and quantitative metabolite abundance profiles. No pre-matched dataset exists. The strategy is to construct a matched set by intersecting a curated list of species with available data.

| Dataset | Role | Source / URL (Verified) | Feasibility & Notes |
| :--- | :--- | :--- | :--- |
| **Genomic Assemblies** | Source of BGC features | **NO verified source found** for a pre-matched plant genome/metabolome dataset. | We will programmatically fetch genomes from **NCBI RefSeq** using `biopython` or `ncbi-genome-download`. A curated list of species (e.g., from the 1000 Plants initiative) will be used as input. **Constraint**: Skip species with genome > 500MB to ensure antiSMASH runs within 6 hours. |
| **Metabolite Profiles** | Source of targets | **NO verified source found** for a pre-matched plant genome/metabolome dataset. | We will fetch from **MetaboLights** (via API/bulk) or **PMDB** (pathway maps, not quantitative). We will prioritize MetaboLights studies that provide quantitative tables. If no quantitative data is found for a species, it is excluded. |
| **BGC Prediction Tool** | Feature extraction | **NO verified source found** for a pre-trained model. | **antiSMASH 7.0** is the standard. **Decision**: Commit to antiSMASH for the entire dataset. If antiSMASH fails for a species (timeout/OOM), that species is excluded. **No fallback to different tools** to avoid confounding. |
| **Phylogenetic Tree** | Stratification / PGLS | **NO verified source found** for a pre-built plant tree. | We will use the **1KP (1000 Plants) phylogeny** as the source. The plan will include a step to prune this tree to the exact species in the final dataset using `dendropy`, ensuring topology and branch lengths match. |

**Data Alignment Strategy**:
1.  **Species List**: A user-defined list of species (e.g., `config/species_list.yaml`) anchored to the 1000 Plants list.
2.  **Download**:
    *   Genomes: Fetch FASTA/GFF from NCBI RefSeq. Skip if > 500MB.
    *   Metabolites: Fetch abundance tables from MetaboLights.
3.  **Processing**:
    *   **BGCs**: Run antiSMASH on FASTA. Parse JSON output for BGC types and counts. Map to MIBiG ontology. **Fallback**: If no MIBiG match, use Pfam HMMs for plant-specific clusters (e.g., Terpene Synthases). If no match, label 'unknown'.
    *   **Metabolites**: Harmonize identifiers to InChIKey. Add pseudo-count (1) and log-transform.
4.  **Alignment**: Inner join on Species Name. Exclude species missing either data type (log warning).
5.  **Output**: Aligned matrix (Species x [BGC Types, Metabolites]).

**Critical Feasibility Note**: The spec assumes "publicly available genomic data" and "metabolite profiles" are easily matched. In reality, few species have *both* high-quality assemblies and quantitative metabolomics. The pipeline must handle a high rate of "missing data" (species with only one modality) gracefully, as per the Edge Cases in the spec.

## Methodological Rigor

### Statistical Approach
1.  **Models**:
    *   **Random Forest**: Non-linear, robust to collinearity.
    *   **Elastic Net**: Handles high-dimensional features (many BGC types) and performs feature selection.
    *   **Gradient Boosting**: Added to satisfy FR-005 (CPU-optimized `scikit-learn`).
    *   **PGLS (Phylogenetic Generalized Least Squares)**: The primary model to account for phylogenetic non-independence (FR-010). Implemented via `statsmodels` with custom phylogenetic covariance (using `dendropy`).
2.  **Validation**:
    *   **Cross-Validation**: **Leave-One-Out (LOO)** instead of 5-fold CV. With N < 20, 5-fold CV yields test sets < 4, making R² unstable. LOO maximizes data usage.
    *   **Bootstrap**: 1000 bootstrap resamples to estimate confidence intervals for R².
    *   **Baseline**: **Phylogenetic Permutation**. If clades are small, perform **global permutation with phylogenetic correction** (shuffling both predictors and targets simultaneously or using phylogenetic eigenvectors) to break shared phylogenetic signal while preserving structure. A sufficient number of iterations will be performed to ensure convergence.
3.  **Metrics**:
    *   **R²**: Variance explained.
    *   **Pearson Correlation**: Linear association.
    *   **p-value**: Significance of R² against the null distribution.
    *   **SC-002**: Variation in R² across threshold sweep must be ≤ 0.05.

### Statistical Rigor Checklist
- **Multiple Comparisons**: If testing multiple metabolite classes, apply Bonferroni or FDR correction to p-values.
- **Power Justification**: Acknowledge that with N < 20 (likely due to data scarcity), power will be low. Results will be framed as "exploratory" or "associational" rather than definitive causal claims.
- **Causal Inference**: The study is observational. Claims will be limited to "predictive association" and "genomic potential," not causality.
- **Collinearity**: BGC types (e.g., terpenoid) and metabolite classes (e.g., terpenes) are definitionally related. The model will report feature importance but explicitly acknowledge that independent effects cannot be disentangled due to this biological coupling. **Quantitative Focus**: The model predicts *abundance* (continuous) from *copy number* (continuous), not presence/absence, to avoid tautology.
- **Measurement Validity**: Rely on MIBiG 3.0 ontology for BGC classification and InChIKey for metabolite identity. **Fallback**: Use Pfam for plant-specific clusters if MIBiG fails.
- **Dimensionality Reduction**: Apply PCA to BGC features before multivariate modeling to address N < 50 vs. high-feature count.

## Compute Feasibility Analysis

- **Constraint**: 2 CPU, 7 GB RAM, 6 hours.
- **Risk**: antiSMASH 7.0 is computationally intensive.
- **Mitigation**:
    1.  **Genome Size Filter**: Skip species with genome > 500MB.
    2.  **Single Tool Commit**: Use antiSMASH only. If it fails, exclude species (do not switch tools).
    3.  **Sampling**: Limit the full pipeline to a maximum of 20 species for the "research" run.
    4.  **Data Subsetting**: If the metabolite matrix is too large, filter for top N most abundant metabolites.
- **Library Pins**: Use `scikit-learn` (CPU only), `pandas`, `numpy`, `statsmodels`, `dendropy`. Avoid GPU-specific torch versions.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use NCBI RefSeq for Genomes** | Most reliable source for high-quality plant assemblies with GFF annotations. |
| **Skip Large Genomes (>500MB)** | Ensures antiSMASH completes within 6h on GitHub Actions free-tier. |
| **LOO Cross-Validation** | Essential for N < 20 where 5-fold CV is unstable. |
| **Phylogenetic Permutation (Global/Co-evolution)** | Essential to break shared phylogenetic signal in both predictors and targets. |
| **Log-transform + Pseudo-count** | Standard practice for metabolite abundance to normalize distributions and handle zeros. |
| **Inner Join for Alignment** | Strict requirement for paired analysis; partial data is biologically uninformative for this specific regression. |
| **PCA Dimensionality Reduction** | Required to prevent overfitting with N < 50 and >100 features. |
| **Quantitative Prediction Focus** | Avoids tautology by predicting abundance from copy number, not presence/absence. |
| **Pfam Fallback for BGC Mapping** | Addresses MIBiG bias against plant-specific clusters. |