# Quickstart: Predicting Plant PPIs from Co‑expression

## Prerequisites
- Git ≥ 2.30
- Python 3.11
- R 4.2 with Bioconductor packages (`DESeq2`, `org.At.tair.db`, `limma`, `BiocManager`)
- GNU Make
- Internet access (to download GEO and STRING data)

## Step‑by‑Step

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/PROJ-185-predict-ppi-coexpression.git
   cd PROJ-185-predict-ppi-coexpression
   ```

2. **Create a clean Python environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install required Bioconductor packages (run once)**
   ```R
   if (!requireNamespace("BiocManager", quietly=TRUE))
       install.packages("BiocManager")
   BiocManager::install(c("DESeq2", "org.At.tair.db", "limma"))
   ```

4. **Configure species and GEO accessions**  
   Edit `src/config/species_config.yaml`. Example for *Arabidopsis*:
   ```yaml
   Arabidopsis_thaliana:
     geo_accessions:
       - GSE12345
       - GSE67890
     norm_method: "vst"      # or "tpm"
     correlation: "pearson"  # or "spearman"
   ```

5. **Run the full pipeline**
   ```bash
   make all SEED=42
   ```
   - `SEED` sets the global random seed (FR‑012).  
   - The pipeline will download data, process it, generate predictions, evaluate them, run GO enrichment, and create per‑species summary files.

6. **Inspect results**
   - Predicted edges: `results/predicted_ppi_Arabidopsis_thaliana.tsv`
   - Evaluation metrics: `results/evaluation_metrics.json` (contains `baseline_p`)
   - GO enrichment: `results/go_enrichment_Arabidopsis_thaliana.tsv`
   - Summary report: `results/summary_Arabidopsis_thaliana.txt`
   - Full log: `logs/pipeline.log`

7. **Optional targets**
   - `make evaluate` – only run the evaluation step (requires previous `make all` or existing intermediate files). Validation of `evaluation_metrics.json` against its schema is performed automatically.
   - `make enrich` – run GO enrichment only.
   - `make summary` – regenerate summary reports.
   - `make clean` – remove intermediate files while keeping raw data and final results.

8. **Reproducibility check**
   Re‑run with the same seed:
   ```bash
   make clean
   make all SEED=42
   ```
   All output files (`*.tsv`, `*.json`, `*.txt`) should be identical (see the relevant SC specification).

## Troubleshooting Tips
- **Insufficient samples** – If a species aborts with `Insufficient sample count (<50)`, add more GEO accessions to `species_config.yaml` or remove that species from the config.
- **Mapping warnings** – Unmapped genes are logged in `mapping_warnings_<species>.log`; they are simply omitted from the edge list (FR‑005).
- **Memory errors** – For extremely large gene sets, consider limiting the analysis to a manageable subset of the most variable genes (modify `correlate.py` accordingly). This still satisfies FR‑004 because the threshold remains ≥ 0.8.

Enjoy exploring plant protein‑protein interaction predictions!

---

