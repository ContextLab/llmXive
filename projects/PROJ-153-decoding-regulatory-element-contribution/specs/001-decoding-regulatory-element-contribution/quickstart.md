# Quickstart: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Prerequisites

- **System**: Linux (Ubuntu 22.04+), 2+ CPU cores, 8GB+ RAM, 20GB+ disk.
- **Tools**: Python 3.11, R 4.3.1, Git, Docker (optional).
- **Dependencies**: `fastp`, `bowtie2`, `MACS2`, `bedtools`, `deepTools`, `samtools`, `SRA Toolkit`.

## Installation

### 1. Clone Repository

```bash
git clone
cd yeast-cre-analysis
```

### 2. Install Dependencies

```bash
# Python
pip install -r requirements.txt

# R
Rscript -e 'install.packages(c("lme4", "clusterProfiler", "ggplot2", "dplyr"))'

# CLI Tools (if not installed)
# Ubuntu/Debian
sudo apt-get install fastp bowtie2 macs2 bedtools deeptools samtools sratoolkit
```

### 3. Set Up Environment

```bash
# Create virtualenv
python -m venv venv
source venv/bin/activate

# Set random seeds
export PYTHONHASHSEED=42
export RNG_SEED=42
```

## Data Setup

### 1. Download Raw Data

The pipeline expects the following data in `data/raw/`:

- **ChIP-seq FASTQ**: For Hsf1, Msn2/4, Hog1 under control and stress conditions (from GEO/SRA).
- **eQTL Parquet**: 1002 Yeast Genomes eQTL summary statistics.
- **Hi-C BED/Cool**: Yeast 3D Genome Atlas data.

If using placeholder GEO IDs (e.g., `GSE####`), update `config.yaml` with real IDs and run:

```bash
bash code/01_download.sh
```

This script will:
- Download data from GEO/SRA.
- Verify MD5 checksums.
- Abort if data is missing or checksums fail.

### 2. Verify Data Integrity

```bash
md5sum data/raw/*.fastq.gz > data/raw/checksums.md5
```

## Running the Pipeline

### 1. Preprocessing (Trim, Align, Peak Calling)

```bash
bash code/02_preprocess.sh
```

This will:
- Trim adapters with `fastp`.
- Align with `bowtie2` (≤2 threads).
- Filter for MAPQ >= 30 (`samtools view -q 30`).
- Call peaks with `MACS2` (FDR ≤ 0.01, with sensitivity sweep).

### 2. Annotation and Filtering

```bash
python code/03_annotate.py
python code/04_filter.py
```

- Annotate peaks (promoter/distal, context).
- Apply FR-011, FR-012, FR-014 filters.
- Generate `vif_flags.tsv`.

### 3. Weight Calculation

```bash
python code/05_weights.py
```

- Compute weights for valid CREs (motif/Hi-C based).

### 4. Statistical Analysis (LMM, LRT, Permutation)

```bash
Rscript code/06_lmm.R
```

- Fit LMM for each stress condition (with weights).
- Perform LRT and permutation testing.
- Apply FDR correction.

### 5. Report Generation

```bash
Rscript code/07_report.R
```

- Generate `results/Statistical_summary.pdf` (includes LRT, FDR, ΔR², GO, Null Plot, Causal Limitation).
- Create ranked CRE tables (`results/CRE_ranked_<stress>.md`).
- Generate `fdr_sweep_summary.tsv` and `selection_bias_comparison.tsv`.

### 6. Visualization (bigWig Tracks)

```bash
python code/08_visualize.py
```

- Generate `results/tracks/<stress>_CRE_signal.bw` using `deepTools bamCoverage`.

## Output Files

- `results/CRE_ranked_heat.md`: Ranked CREs for heat-shock (no artificial limit, q<=0.05).
- `results/CRE_ranked_osmotic.md`: Ranked CREs for osmotic stress.
- `results/CRE_ranked_oxidative.md`: Ranked CREs for oxidative stress.
- `results/Statistical_summary.pdf`: Statistical report (includes Causal Limitation).
- `results/fdr_sweep_summary.tsv`: FDR sensitivity analysis.
- `results/selection_bias_comparison.tsv`: Selection bias analysis.
- `results/tracks/*.bw`: Genome browser tracks.

## Troubleshooting

- **Missing Data**: If `code/01_download.sh` fails, check GEO IDs and network.
- **Memory Error**: Use streaming for large files; reduce batch size.
- **No Peaks**: Relax MACS2 FDR threshold (edit `code/02_preprocess.sh`).
- **Collinearity**: Check VIF flags in `data/processed/vif_flags.tsv`.

## Next Steps

- Validate top CREs with ATAC-seq (if data available).
- Plan follow-up functional assays based on ranked CREs.
- Extend to additional stress conditions or TFs.