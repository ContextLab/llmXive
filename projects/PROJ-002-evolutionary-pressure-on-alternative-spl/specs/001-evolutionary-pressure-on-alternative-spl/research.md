# Research: Evolutionary Pressure on Alternative Splicing in Primates

**Feature**: `PROJ-002-001-evolutionary-pressure`  
**Date**: 2026‑06‑29  

## Objective
Generate a reproducible pipeline that (1) derives PSI values from cortex RNA‑seq of human, chimpanzee, macaque, and marmoset; (2) annotates ±500 bp intronic flanks with phyloP conservation and accelerated‑evolution flags; (3) tests enrichment of lineage‑specific splicing events in accelerated regions while correcting for multiple testing and phylogenetic non‑independence; and (4) visualises the results.

## Dataset Strategy

| Required Data | Source (Verified) | Access Method | Fit Check |
|---------------|-------------------|---------------|-----------|
| Primate cortex RNA‑seq (human, chimpanzee, macaque, marmoset) | **None** – no verified URL in the “Verified datasets” block matches these needs. | – | ❗ Dataset mismatch: required SRA accessions are not provided. Phase 0 will halt until a list of valid accession IDs is supplied. |
| Reference genomes (GRCh38, panTro6, rheMac10, calJac4) | Ensembl FTP (canonical, publicly accessible) | `wget`/`curl` in `download_reference.sh` | ✅ (canonical source, version‑pinned) |
| PhyloP 100‑way scores (intronic) | UCSC Table Browser (public) | HTTP GET via `requests` in `annotate_flanks.py` | ✅ |
| Primate species tree (Newick) | Ensembl Compara release 110 (public) | `wget` from Ensembl FTP | ✅ |

> **Note**: The lack of a verified primate RNA‑seq source is a *blocking* issue per the plan. The pipeline will produce a clear error message and exit before any downstream computation.

## Tool & Library Selection (CPU‑only)

| Task | Tool | Version (pinned) | Rationale |
|------|------|------------------|-----------|
| SRA metadata & download | `pysradb` | 1.3.0 | Pure Python, works on CI, no GPU |
| Alignment | `STAR` | 2.7.11a | Fast, multithreaded, CPU‑only |
| PSI quantification | `SUPPA2` | 2.3 | Command‑line, works with BAM |
| Sequence extraction | `bedtools` | 2.31.0 | Standard for FASTA retrieval |
| PhyloP query | UCSC HTTP API (custom script) | – | No extra dependency |
| Statistical tests | Python `scipy.stats.fisher_exact` | 1.14.0 | Fisher’s exact |
| Multiple testing | Python `statsmodels.stats.multitest` | 0.14.0 | BH & Bonferroni |
| Phylogenetic correction | R `caper` | 1.0.5 | Implements PGLS |
| Plotting | R `ggplot2` | 3.5.0 | Publication‑quality Manhattan plot |
| Logging | Python `logging` | builtin | Structured timestamps |
| Validation | Custom `validate_psi.py`, `validate_plot.py` | – | Enforces SC‑001 & SC‑004 |

All tools are installable via `conda` channels (`bioconda`, `conda-forge`) without CUDA.

## Statistical Rigor

- **Enrichment Test**: Fisher’s exact per lineage (binary table of accelerated vs. non‑accelerated events).  
- **Multiple‑Testing**:  
  - Across lineages (4 tests) → Benjamini‑Hochberg FDR ≤ 0.05 (FR‑012).  
  - Within each lineage → Bonferroni correction α = 0.05 / N_events (FR‑012).  
- **Phylogenetic Adjustment**: PGLS model (`caper::pgls`) regressing accelerated flag on lineage, using `primate_tree.nwk`. Adjusted p‑values replace raw Fisher p‑values before the above corrections (FR‑013).  
- **Power Considerations**: Minimum of 3 biological replicates per species enforced (FR‑011). Power ≥ 80 % to detect ΔPSI ≥ 0.1 at α = 0.05 (per Love et al., 2014). If fewer replicates are supplied, the pipeline aborts with error code 101.  
- **Collinearity**: ΔPSI and accelerated flag are distinct (ΔPSI is continuous, flag is binary) – no collinearity concerns.  
- **Measurement Validity**: PSI computed by SUPPA2 (validated in Trincado et al., 2018). PhyloP scores derived from UCSC 100‑way alignment (validated in Siepel et al., 2005).

## Assumptions Re‑checked
- Minimum 10 M paired‑end reads per sample (assumed; not verified until data are downloaded).  
- Reference genomes compatible with STAR & SUPPA2 (true).  
- PhyloP scores available for all flanking regions; missing scores recorded as `NA` and those events excluded from enrichment (per edge case).  

## Deliverables
- `data/raw/` FASTQ files (retained 90 days, then archived).  
- `data/aligned/` sorted BAMs.  
- `data/psi/` unified PSI TSV.  
- `data/events/lineage_specific_events.tsv`.  
- `data/annotations/` BED, FASTA, phyloP CSV.  
- `data/results/enrichment.tsv` (includes raw, corrected, phylo‑adjusted p‑values).  
- `data/results/manhattan.png` (≥ 1200 × 800 px).  
- `metadata.json` (DOI of Zenodo archive).  

## Timeline (CI‑friendly)
| Step | Estimated CI Runtime |
|------|-----------------------|
| Download (≤ 5 samples/species) | 30 min |
| STAR alignment (8 cores) | ≤ 2 h per sample (FR‑002) |
| SUPPA2 quantification | 10 min |
| Filtering & annotation | 5 min |
| Enrichment & corrections | 2 min |
| Plot generation | 1 min |
| Validation & archiving | 5 min |
| **Total** | **≈ 3 h** (well under 6 h limit) |

---
