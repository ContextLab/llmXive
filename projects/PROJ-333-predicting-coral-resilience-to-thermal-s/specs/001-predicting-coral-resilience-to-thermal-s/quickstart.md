# Quickstart: Predicting Coral Resilience to Thermal Stress

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (or local machine with sufficient RAM).
- `ncbi-sra-tools` (optional, for SRA download) or `curl`/`wget`.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-333-predicting-coral-resilience-to-thermal-s
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `biopython`, `pandas`, `scipy`, `pydeseq2`, `gseapy`, `matplotlib`, `requests`.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

1. **Download Reference & Ingest**:
   ```bash
   python code/main.py --step reference
   python code/main.py --step ingest
   ```
   *This downloads the *A. millepora* transcriptome (GCF_000163615.2), then downloads FASTQs from PRJNA292777, verifies checksums, and parses metadata.*

2. **Quantify**:
   ```bash
   python code/main.py --step quant
   ```
   *Streams FASTQs against the reference index to generate the count matrix.*

3. **Differential Expression**:
   ```bash
   python code/main.py --step dge
   ```
   *Runs `pydeseq2` and generates `data/processed/dge_results.csv`.*

4. **Enrichment & Visualization**:
   ```bash
   python code/main.py --step enrich
   python code/main.py --step viz
   ```
   *Runs GSEA via `gseapy` and generates `data/processed/gsea_report.csv` and `data/processed/volcano_plot.png`.*

## Verification

- Check `data/processed/` for output files.
- Verify `data/processed/dge_results.csv` contains `p_adj` < 0.05.
- Ensure peak memory usage (via `psutil` logs) did not exceed 7 GB.
- Confirm that the Reference-Validator Agent (or log) confirms the validity of NCBI and RefSeq citations.