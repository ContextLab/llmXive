# Quickstart: Predicting PPIs from Plant Co‑expression Networks

**Prerequisites**
- Python 3.11 (available on GitHub Actions runners)
- R 4.2 with Bioconductor packages (`DESeq2`, `org.At.tair.db`, `sva`, `limma`)
- Internet access (to download GEO and STRING data)

**Step‑by‑Step**

1. **Clone the repository and enter the project root**
   ```bash
   git clone https://github.com/yourorg/PROJ-185-predict-ppi-coexpression.git
   cd PROJ-185-predict-ppi-coexpression
   ```

2. **Create a fresh virtual environment and install pinned dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   # Install Bioconductor packages (run once)
   Rscript -e 'if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager"); \
               BiocManager::install(c("DESeq2","org.At.tair.db","sva","limma"), version="3.18")'
   ```

3. **Configure the species you wish to analyse**
   Edit `src/config/species_config.yaml`. Example entry for *Arabidopsis*:
   ```yaml
   Arabidopsis_thaliana:
     geo_series:
       - GSE12345
       - GSE67890
     normalization: "vst"   # or "tpm"
     correlation_threshold: high
   ```

4. **Run the full pipeline (default settings)**
   ```bash
   make all SEED=42
   ```
   - Downloads GEO data, normalizes, filters, corrects batch effects, computes correlations, maps to STRING, writes `predicted_ppi_Arabidopsis_thaliana.tsv` (columns `protein_id_1`, `protein_id_2`, `correlation`, `method`), evaluates against STRING, performs GO enrichment, and produces `summary_Arabidopsis_thaliana.txt`.  
   - All intermediate files are stored under `data/` and `results/`.

5. **Optional flags**
   - `NORMALIZATION=TPM` – use TPM (log2‑transformed) instead of DESeq2 VST.  
   - `CORR_METHOD=Spearman` – compute Spearman correlations in addition to Pearson.  
   - `BOOTSTRAP=1` – enable bootstrap confidence intervals for the top 10 000 edges.  
   - `THRESHOLDS=0.75,0.80,0.85` – run threshold sensitivity analysis (default already does).  

6. **Inspect results**
   ```bash
   # Predicted edges
   head results/predicted_ppi_Arabidopsis_thaliana.tsv

   # Evaluation metrics (JSON)
   cat results/evaluation_metrics.json | jq .

   # GO enrichment
   head results/go_enrichment_Arabidopsis_thaliana.tsv

   # Summary report
   cat results/summary_Arabidopsis_thaliana.txt
   ```

7. **Verification**
   After any Make target, the verification script runs automatically. To run it manually:
   ```bash
   make verify
   ```

8. **Cleaning up**
   ```bash
   make clean
   ```
   This removes intermediate files while preserving raw GEO downloads and final artifacts.

**Reproducibility Tips**
- Keep the same `SEED` value across runs to obtain identical outputs (FR‑012).  
- The pipeline logs every step in `pipeline.log`; use this file to audit provenance.  

**Troubleshooting**
- **Insufficient samples**: If a species aborts with `Insufficient sample count (<50)`, add more GEO series to `species_config.yaml`.  
- **Mapping warnings**: Check `mapping_warnings_<species>.log` for unmapped genes; these are omitted from the edge list.  
- **Memory errors**: Reduce the number of genes considered by editing `MAX_GENES` in `src/config/constants.py` (default set to a high threshold).  

Happy reproducible research!

---



