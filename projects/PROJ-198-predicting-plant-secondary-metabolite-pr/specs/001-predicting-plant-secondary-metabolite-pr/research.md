# Research: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Executive Summary

This research phase validates the feasibility of predicting plant secondary metabolite abundance from BGC presence using publicly available data. The primary challenge is the "Genotype-Phenotype Gap" (Assumption in spec) and the lack of direct, verified datasets containing both high-quality plant genomes and matched metabolite profiles in a single source. The plan adopts a **hybrid data assembly strategy**: fetching genomes from RefSeq/Phytozome (via API/FTP) and metabolite data from PMDB/MetaboLights, then performing a strict species-level join. **If no real matched pairs are found, the pipeline defaults to a mock dataset for CI validation.**

## Verified Datasets

**Critical Constraint**: The "Verified datasets" block provided in the input contains **NO verified source** for plant-specific genome/metabolite pairs. The RefSeq entries provided are for viral, fungal, and archaeal genomes.

| Data Type | Source Strategy | Verified URL Reference | Status |
|-----------|-----------------|------------------------|--------|
| **Genomes (Plant)** | NCBI RefSeq Plant / Phytozome API | *None in verified block* | **Risk**: Must fetch via standard API; no pre-verified URL. |
| **Metabolites** | PMDB / MetaboLights | *None in verified block* | **Risk**: Must fetch via standard API; no pre-verified URL. |
| **BGC Annotations** | antiSMASH 7.0 (Local Execution) | *None in verified block* | **Action**: Run locally on downloaded genomes (FR-002). **Skipped on CI**. |
| **Phylogeny** | NCBI Taxonomy / Open Tree of Life | *None in verified block* | **Action**: Derive from taxonomy strings or fetch tree. |

**Dataset-Variable Fit Analysis**:
- **Required**: Species ID, Genome (FASTA/GFF), Metabolite Abundance (InChIKey), Phylogenetic Clade.
- **Gap**: The "Verified datasets" block contains *only* viral/fungal/archaea RefSeq data and a generic BGC CSV (likely human/clinical). **No plant-specific verified dataset exists in the provided block.**
- **Mitigation**: The `research.md` explicitly states that the pipeline will attempt to download plant data from standard sources (RefSeq/Phytozome) but will **not** cite a fake URL. If the specific species cannot be found, the pipeline logs a warning and excludes them (Edge Case in spec). The analysis proceeds only if ≥10 valid species pairs are found. **If <10 pairs found, the pipeline uses a mock dataset for CI validation.**

## Methodological Rigor

### Statistical Approach
1.  **Modeling**: Random Forest and Elastic Net regression with **Phylogenetic Eigenvector Regression (PVR)**.
    -   *Rationale*: PVR incorporates phylogenetic structure as covariates, controlling for non-independence without the power loss of LOCO-CV in small samples (N=10-20).
    -   *Compute*: CPU-tractable on 7GB RAM for <1000 species.
2.  **Validation**:
    -   **PVR**: Used to control for phylogeny in the regression model (replacing PIC).
    -   **Permutation Test**: 100 iterations of label shuffling to establish null distribution of R².
    -   **PIC**: **Removed**. PIC requires an ultrametric tree with branch lengths, which is not available from taxonomy strings alone. Using PIC would be methodologically invalid.
3.  **Multiple Comparison Correction**:
    -   Since the primary hypothesis is "BGC diversity predicts metabolite abundance," we test one main model.
    -   Sensitivity analysis (FR-006) involves 3 thresholds. We will apply a Bonferroni correction if treating these as independent hypothesis tests, or report them descriptively as robustness checks.

### Power & Sample Size
-   **Requirement**: ≥10 species for >80% power (US-1).
-   **Limitation**: With N=10-20 and high-dimensional features, power is **<80%** for detecting moderate effects (R²~0.3). The study is framed as an **exploratory pilot**.
-   **Action**: The `research.md` notes that power is **deferred** to the data fetch step. If the fetch yields <10, the project defaults to mock data for CI validation, not a definitive study.

### Causal Inference & Confounding
-   **Framing**: All claims are **associational**. No randomization exists.
-   **Confounding**: Phylogeny is the primary confounder. PVR addresses this.
-   **Environmental Confounding**: The "Genotype-Phenotype Gap" (regulation, environment) is a known limitation. The model predicts "genomic potential," not "observed abundance" directly. Results are framed as "correlation between potential and observed," acknowledging the gap.
-   **Collinearity**: BGC classes (e.g., Terpene subtypes) are definitionally related. VIF diagnostics (FR-007) will be run. If VIF > 5, we report descriptive correlation but avoid claiming independent effects.

## Compute Feasibility Assessment

-   **Hardware**: 2 CPU, 7GB RAM, No GPU.
-   **Memory**:
    -   Genome assembly (Plant): hundreds of megabytes to a few gigabytes per genome.
    -   antiSMASH 7.0: **Too heavy for CI**. CI uses mock BGC data.
    -   Model Training: Random Forest on <1000 samples × ~50 features is trivial (<1GB RAM).
-   **Time**:
    -   Download: Variable (network bound).
    -   antiSMASH: **Skipped on CI**.
    -   Modeling: <30 mins for 20 species.
-   **Strategy**: Limit analysis to a curated list of species. If real data not found, use mock data for CI validation.

## Tool Validation (antiSMASH)

-   **Issue**: antiSMASH is optimized for bacteria/fungi, not plants.
-   **Mitigation**: The pipeline includes a "Tool Validation" step. If real data is used, the user must manually verify antiSMASH performance on plant genomes. For CI, **mock BGC data** is used, assuming a valid BGC profile for testing the pipeline logic.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No Plant Data Found** | Fatal (No analysis possible) | Explicit error: "Insufficient species count." Abort or switch to mock data for CI. |
| **antiSMASH Timeout** | Missed CI limit | **Skip antiSMASH on CI**. Use mock data. |
| **Phylogeny Missing** | PVR fails | Use NCBI Taxonomy ID to fetch tree; fallback to simple family-level split if tree unavailable. |
| **Collinearity** | Invalid coefficients | VIF check; report descriptive stats only if VIF high. |

## Decision Log

1.  **Dataset Source**: Cannot cite non-existent verified URLs. Will use standard APIs (NCBI/Phytozome) and document the lack of a pre-verified plant dataset in the "Verified Accuracy" gate. **Default to mock data if no real data found.**
2.  **Compute Limit**: Hard cap on species count to ensure modeling fits in 6 hours. **antiSMASH skipped on CI.**
3.  **Statistical Rigor**: Strict adherence to PVR and Permutation tests as per plan. No p-hacking. **PIC removed due to data limitations.**
4.  **Spec Amendment**: FR-004 (LOCO-CV) and FR-008 (PIC) must be amended to PVR.