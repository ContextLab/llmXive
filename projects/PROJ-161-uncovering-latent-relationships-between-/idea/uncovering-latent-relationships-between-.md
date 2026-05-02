---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance

**Field**: chemistry  

## Research question  

Which molecular descriptors of approved or investigational antibiotics are systematically associated with observed resistance phenotypes across bacterial isolates?

## Motivation  

Antibiotic resistance escalates worldwide, yet most efforts focus on genomic mechanisms. Understanding how physicochemical properties of drugs influence the likelihood of resistance emergence can guide the design of molecules that are less prone to selective pressure. Existing studies have catalogued resistance profiles but have not linked them to comprehensive descriptor analyses, leaving a gap in hypothesis‑driven drug design.

## Related work  

- [High-Throughput Screening of Natural Product and Synthetic Molecule Libraries for Antibacterial Drug Discovery (2023)](https://doi.org/10.3390/metabo13050625) — Demonstrates the utility of large‑scale screening pipelines for antibacterial discovery and highlights the need for chemical‑level insight into resistance trends.

## Expected results  

We anticipate identifying a subset of descriptors (e.g., logP, topological polar surface area, number of rotatable bonds) that show statistically significant differences between antibiotics with high vs. low resistance rates. Confirmation will come from (i) visual separation of resistant‑prone vs. resistant‑averse compounds in UMAP space, (ii) clusters enriched for high‑resistance phenotypes, and (iii) effect sizes (Cohen’s d or odds ratios) exceeding conventional thresholds (|d| > 0.5, OR > 2). Failure to observe such patterns would falsify the hypothesis that simple physicochemical metrics drive resistance propensity.

## Methodology sketch  

1. **Data acquisition**  
   - Download antibiotic SMILES from **ChEMBL** (release 33) via their REST API.  
   - Retrieve additional compounds from **ZINC15** (subset “drug‑like”) using the provided CSV dump URL.  
   **URL:** `https://zinc15.docking.org/substances.csv` (example).  
   - Pull phenotype‑wise resistance frequencies for each antibiotic from **NCBI Pathogen Detection** (public AMR dataset) via their FTP site.  
   **URL:** `ftp://ftp.ncbi.nlm.nih.gov/pathogen/antimicrobial_resistance/`  

2. **Descriptor computation**  
   - Use **RDKit** (Python) to calculate a standardized set of 200 molecular descriptors (e.g., MolLogP, TPSA, HBD, HBA, rotatable bonds, aromatic ring count).  
   - Store results in a CSV (`descriptors.csv`).  

3. **Data integration**  
   - Merge descriptor table with resistance frequencies on InChIKey/SMILES match.  
   - Define a binary resistance label: “high resistance” (top 25 % of isolates) vs. “low resistance” (bottom 25 %).  

4. **Dimensionality reduction & visualization**  
   - Apply **UMAP** (n_neighbors = 15, min_dist = 0.1, metric = euclidean) to the descriptor matrix (≤ 10 k compounds).  
   - Plot 2‑D embeddings colored by resistance label.  

5. **Clustering**  
   - Run **DBSCAN** on the UMAP coordinates (eps = 0.5, min_samples = 10) to discover natural groups.  
   - Evaluate cluster enrichment for high‑resistance compounds using Fisher’s exact test.  

6. **Statistical association**  
   - For each descriptor, perform a Mann‑Whitney U test between high‑ and low‑resistance groups.  
   - Adjust p‑values with Benjamini‑Hochberg FDR (α = 0.05).  

7. **Interpretation & hypothesis generation**  
   - Rank descriptors by effect size and FDR‑adjusted significance.  
   - Summarize chemical patterns (e.g., “higher logP and lower TPSA tend to co‑occur with high resistance”).  

8. **Reproducibility**  
   - All scripts packaged in a `requirements.txt` (RDKit, pandas, scikit‑learn, umap‑learn, scipy).  
   - Workflow orchestrated with a single Bash script executable within a GitHub Actions runner (≤ 6 h, ≤ 7 GB RAM).  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(none identified)*.  
- Verdict: **NOT a duplicate**.
