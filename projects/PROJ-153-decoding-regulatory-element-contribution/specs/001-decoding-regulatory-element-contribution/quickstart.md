# Quickstart: Yeast CRE Analysis Pipeline

## Prerequisites

* **Python**: 3.11+
* **R**: 4.3+ (with `lme4`, `data.table`, `ggplot2`, `clusterProfiler`)
* **Bioconda Tools**: `fastp`, `bowtie2`, `macs2`, `bedtools`, `deepTools`
* **System**: Linux (Ubuntu recommended).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-153-decoding-regulatory-element-contribution
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

3. **Install R dependencies**:
   ```bash
   R -e "install.packages(c('lme4', 'data.table', 'ggplot2', 'clusterProfiler'), repos='https://cloud.r-project.org')"
   ```

4. **Install Bioconda tools** (if not using conda):
   ```bash
   conda install -c bioconda fastp bowtie2 macs2 bedtools deepTools
   ```

## Data Setup

> **Note**: The required GEO ChIP‑seq series and 1002 Yeast Genomes eQTL dataset are *not* included in the verified dataset list. You must obtain them manually and place them as described below. For CI testing, a synthetic mode is provided.

### Option A: Synthetic Mode (CI / Test)
```bash
python code/main.py --generate-synthetic --sample-size 500
```
This generates mock FASTQs and a synthetic eQTL table that conform to `contracts/dataset.schema.yaml`. **Synthetic data only validates pipeline logic; it does not support biological conclusions.** All downstream results will be marked as *synthetic* in the PDF.

### Option B: Null Synthetic Mode (False‑Positive Check)
```bash
python code/main.py --null-synthetic --sample-size 500
```
Generates mock data with **no true correlation** between ΔPeakSignal and log₂FC. Running the full pipeline on this data should yield non‑significant β₁ (adjusted p > 0.05), confirming the pipeline's type I error control.

### Option C: Real Data Mode
1. **Download** the raw ChIP‑seq FASTQ files for **Hsf1, Msn2/4, Hog1** under **control** and each stress condition (heat‑shock, osmotic, oxidative) from the appropriate GEO series (e.g., GSE####). Place them in `data/raw/` preserving the naming convention `SRRxxxx_TF_condition.fastq.gz`.
2. **Obtain** the 1002 Yeast Genomes eQTL summary CSV containing stress‑specific log₂FC columns (`log2fc_heat`, `log2fc_osmotic`, `log2fc_oxidative`) and promoter binding scores. Place it at `data/external/eqtl_summary.csv`.
3. (Optional) **Provide** a yeast ATAC‑seq narrowPeak file for the same conditions and place it in `data/external/atac_peaks.narrowPeak`. If omitted, the pipeline will run in **ATAC-Deferred Mode** and flag all results as unvalidated.
4. Run the full pipeline:
   ```bash
   ./run_pipeline.sh
   ```

## Execution

`run_pipeline.sh` sequentially executes:

1. **01_download.sh** – MD5 verification (FR‑001).  
2. **02_preprocess.py** – trimming & alignment (FR‑002).  
3. **03_peak_calling.py** – MACS2 sweep (FR‑003).  
4. **04_merge_annotate.py** – merge & context annotation (FR‑004).  
5. **05_atac_validation.py** – ATAC validation (skipped if missing; sets `validated_by_atac = False`).  
6. **06_me_error_correction.py** – SIMEX measurement‑error correction (Poisson-based).  
7. **07_summit_match.py** – summit‑match metric (SC‑005).  
8. **08_visualize.py** – bigWig generation (FR‑009).  
9. **09_stats.py** – LMM, permutation, BH correction, variance explained, GO enrichment (FR‑005‑FR‑008).  
10. **generate_pdf.py** – summary report (FR‑010) – includes ATAC status and causal limitation disclaimer.

## Output

* `results/CRE_ranked_<stress>.md` – full ranked table (all significant CREs).  
* `results/Statistical_summary.pdf` – includes peak counts, ΔR², GO enrichment, measurement‑error stats, summit‑match %, ATAC status, and causal limitation disclaimer.  
* `results/tracks/<stress>_CRE_signal.bw` – IGV‑compatible tracks.

## Troubleshooting

* **No peaks survive MACS2 q < 0.01** – Pipeline aborts; edit `code/utils/config.py` to relax the threshold (e.g., 0.05) and re‑run.  
* **Missing eQTL columns** – Verify that the CSV contains `log2fc_heat`, `log2fc_osmotic`, `log2fc_oxidative`, and `promoter_binding_score`. Pipeline will abort with a detailed missing‑column report (FR‑011).  
* **Memory error** – Reduce `--sample-size` or ensure you are running in real‑data mode with sufficient resources.  
* **ATAC data missing** – Pipeline runs in "ATAC-Deferred Mode" and flags results as unvalidated. No error is raised.  
* **Synthetic mode warnings** – All results will be labeled as synthetic; they are not suitable for biological conclusions.  