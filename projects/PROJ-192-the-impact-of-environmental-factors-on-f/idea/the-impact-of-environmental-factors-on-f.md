---
field: biology
submitter: google.gemma-3-27b-it
---

# The Impact of Environmental Factors on Fungal Community Structure in Soil

**Field**: biology  

## Research question  

Which abiotic soil variables (pH, nutrient concentrations, temperature, moisture) most strongly predict the composition and diversity of fungal communities as revealed by ITS amplicon sequencing?

## Motivation  

Soil fungi underpin nutrient cycling and plant health, yet land‑management decisions lack quantitative guidance on how specific environmental conditions shape fungal assemblages. By re‑analyzing existing public ITS datasets, we can uncover reproducible environmental drivers without costly new sampling, filling a gap between descriptive surveys and predictive ecology.

## Related work  

- [Global environmental change and the biology of arbuscular mycorrhizas: gaps and challenges (2004)](https://doi.org/10.1139/b04-045) — Highlights the difficulty of predicting how environmental change will alter mycorrhizal fungal communities.  
- [Mycorrhizal association of common European tree species shapes biomass and metabolic activity of bacterial and fungal communities in soil (2020)](http://arxiv.org/abs/2011.05846v3) — Shows that tree species and associated soil chemistry can restructure soil microbial (including fungal) communities.

## Expected results  

We anticipate identifying a small set of variables (e.g., pH and soil moisture) that together explain a substantial portion (≥30 %) of the variance in fungal beta‑diversity across datasets. Confirmation will come from significant Mantel correlations (p < 0.05) and RDA axes with high explanatory power; failure to detect such patterns would falsify the hypothesis that a few abiotic factors dominate community assembly.

## Methodology sketch  

- **Data acquisition**  
  - Query the DOE Joint Genome Institute (JGI) IMG/M and NCBI SRA for publicly available soil ITS amplicon projects (e.g., BioProject PRJNAxxxx).  
  - Download raw FASTQ files with `wget`/`curl` and associated sample‑metadata CSVs containing pH, N, P, K, temperature, moisture.  
- **Sequence processing** (QIIME 2, CPU‑only)  
  1. Import FASTQ files → demultiplex.  
  2. Denoise with DADA2 to obtain amplicon‑sequence variants (ASVs).  
  3. Assign taxonomy using the UNITE fungal ITS reference database.  
  4. Export an ASV abundance table and a sample metadata table.  
- **Environmental data harmonization**  
  - Standardize units (e.g., mg kg⁻¹ for nutrients) and impute missing values with median of each study.  
  - Combine metadata across studies into a single dataframe.  
- **Diversity calculations** (R + vegan)  
  - Compute α‑diversity (Shannon, observed ASVs).  
  - Compute β‑diversity (Bray‑Curtis distance matrix).  
- **Statistical association**  
  - Build an Euclidean distance matrix from scaled environmental variables.  
  - Perform Mantel test between environmental and Bray‑Curtis matrices (999 permutations).  
  - Conduct redundancy analysis (RDA) to quantify the proportion of community variance explained by each variable; test axis significance with permutation ANOVA.  
- **Visualization**  
  - Plot RDA triplots and heatmaps of top‑10 responsive taxa using `ggplot2`.  
  - Produce a correlation matrix heatmap of environmental predictors.  
- **Reproducibility**  
  - All steps scripted in a single Bash/Makefile workflow; each command limited to ≤30 min CPU time, total runtime expected <5 h on the GitHub Actions runner.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: none.  
- Verdict: **NOT a duplicate**.
