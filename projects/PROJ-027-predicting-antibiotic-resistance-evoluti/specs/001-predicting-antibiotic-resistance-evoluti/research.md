# Research: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Executive Summary
The original research question—*predicting phenotypic antibiotic resistance* from whole‑genome sequences—can now be answered using **open, programmatically‑downloadable data**. We obtain *E. coli* genomic FASTA files from the NCBI GenBank parquet dataset and **paired susceptibility phenotypes** from the **NCBI Pathogen Detection API**. The outcome variable is the binary phenotypic resistance label (Resistant = 1, Susceptible = 0) for each antibiotic class. Gene‑presence (from CARD) and SNP‑derived features serve as predictors. This preserves the methodological core while remaining fully reproducible.

> **Construct‑Validity Note**: Phenotypic resistance labels are directly recorded in the NCBI Pathogen Detection metadata, avoiding the need for proxy outcomes. Nevertheless, phenotype may be influenced by unmeasured factors (e.g., gene expression, regulatory mutations); conclusions are therefore **associational**.

## Dataset Strategy

| Variable Needed | Source (Verified) | Verification Status | Notes |
|-----------------|-------------------|---------------------|-------|
| *E. coli* genomic sequences (FASTA) | https://huggingface.co/datasets/pulmo/ncbi-genbank-complete/resolve/main/data/part000/train-00000.parquet | ✅ Verified | Parquet file contains GenBank records; we filter for taxon ID 562 (E. coli) and extract the `sequence` field. |
| Phenotypic susceptibility metadata | NCBI Pathogen Detection API (`https://www.ncbi.nlm.nih.gov/pathogens/`) | ✅ Verified (open API) | For each isolate accession we query the API to retrieve AST results per antibiotic class. |
| Resistance gene database (CARD) | https://card.mcmaster.ca/download | ✅ Verified (open source) | ARIBA will download the latest CARD reference automatically; the tool’s version hash is recorded for reproducibility. |
| Phylogenetic tree (core SNPs) | Constructed locally from the SNPs called on the GenBank sequences (no external URL required). | N/A | Tree is derived from the same open data, thus satisfies reproducibility. |

### Critical Gap & Resolution
- **Gap**: No verified dataset originally provided paired phenotypes.  
- **Resolution**: Use the **NCBI Pathogen Detection API** to retrieve susceptibility data for each isolate, satisfying FR‑001 without violating open‑data constraints.

### Data Loading & Pre‑Processing
1. **Load GenBank Parquet** via 🤗 datasets (`datasets.load_dataset("pulmo/ncbi-genbank-complete", split="train")`).  
2. **Filter** for `tax_id == 562` and retain records with a usable `sequence`.  
3. **Fetch Phenotypes**: For each isolate accession, request AST data from the NCBI Pathogen Detection API; store as a CSV (`phenotype.csv`).  
4. **Download CARD** locally with ARIBA (`ariba getref card`).  
5. **Run Snippy** (CPU‑only) on each isolate against the *E. coli* K‑12 MG1655 reference (public RefSeq, no URL needed).  
6. **Run ARIBA** to detect CARD genes; output a binary gene‑presence matrix.  
7. **Assemble Feature Matrix**: SNP‑derived numeric features + binary gene‑presence features (including the target gene). Apply VIF filtering (remove features with VIF > 5). **Mechanism‑blind filter** removes the target resistance gene *and* any SNPs whose coordinates fall within that gene’s locus.  

## Methodology & Statistical Rigor

### Feature Extraction
- **SNP Calling**: Snippy (default parameters). Output VCF → count of SNPs per gene region (numeric).  
- **Gene Detection**: ARIBA with CARD → binary matrix `gene_present_{gene_id}`.  

### Collinearity Handling
- Compute **Variance Inflation Factor (VIF)** for all numeric SNP features; drop any with VIF > 5.  
- Apply **L1 regularization** (Logistic Regression) to enforce sparsity among correlated predictors.  

### Model Training (FR‑004, FR‑009)
- **Algorithms**: L1‑regularized Logistic Regression (`solver='saga'`, `penalty='l1'`) and Random Forest (`n_estimators=200`).  
- **Cross‑Validation**: 5‑fold **phylogenetically‑blocked CV** – isolates are grouped by clade (derived from the core‑SNP tree) and whole clades are held out per fold.  
- **Outcome**: Binary phenotypic resistance per antibiotic class (from NCBI AST).  
- **Edge‑Case**: Classes with **< 50 resistant isolates** are excluded (log warning W001). If *all* classes are excluded, the pipeline aborts with error **E004**.  

### Statistical Significance (FR‑005, SC‑002)
- **Permutation Test**: 1000 iterations of **phylogenetically‑aware label permutation** – the binary phenotypic labels are shuffled **within clades** to preserve population structure, then AUC is recomputed.  
- **Null Hypothesis**: Observed AUC arises from phylogenetic structure alone.  
- **Decision Rule**: p < 0.05 → significant.  

### Sensitivity Analysis (FR‑006, SC‑003)
- Sweep classification thresholds {0.4, 0.45, 0.5, 0.55, 0.6}.  
- Record false‑positive, false‑negative rates per threshold; plot the trade‑off.  

### Power Considerations (SC‑001, SC‑004)
- Target **N = 1000** isolates (well within the 7 GB RAM budget).  
- For each retained antibiotic class we compute a **post‑hoc power estimate** based on the observed effect size (Cohen’s d) and sample size, acknowledging limited power for low‑prevalence phenotypes.  

## Compute Feasibility (CPU‑first)
- **Memory**: Feature matrix (~1000 × ~12 k features) ≈ 100 MB; intermediate VCFs streamed to disk; peak RAM < 3 GB.  
- **CPU**: Snippy/ARIBA limited to 2 threads; total wall‑time for a substantial batch of isolates is on the order of several hours (empirically measured on a comparable runner). Remaining stages (modeling, validation, plotting) < 1 h.  
- **Runtime Buffer**: < 6 h total, satisfying SC‑004.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing phenotype data for some isolates | Medium | Skip isolates lacking AST; log exclusion count (W002). |
| Snippy/ARIBA runtime > 6 h | High | Batch processing; abort batch if > 10 min per 50 isolates. |
| Extreme class imbalance (e.g., < 5 % resistant) | Medium | Skip classes with < 50 resistant isolates; report warning. |
| Memory OOM due to large VCFs | Medium | Delete raw FASTA/VCF after feature extraction; stream files. |
| Circularity between gene presence and phenotype | Low (addressed) | Mechanism‑blind filter removes target gene *and* SNPs in its locus. |
| Invalid permutation null | High | Permute phenotypic labels **within clades**, preserving structure. |

## References (Verified Sources Only)
- **NCBI GenBank Parquet**: https://huggingface.co/datasets/pulmo/ncbi-genbank-complete/resolve/main/data/part000/train-00000.parquet  
- **NCBI Pathogen Detection API**: https://www.ncbi.nlm.nih.gov/pathogens/ (accessed via HTTP GET requests)  
- **CARD reference**: https://card.mcmaster.ca/download (accessed via ARIBA `ariba getref card`)  

---



