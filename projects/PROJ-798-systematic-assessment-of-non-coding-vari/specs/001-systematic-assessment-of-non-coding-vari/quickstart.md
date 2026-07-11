# Quickstart: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Prerequisites

- **Python**: 3.11+
- **System Tools**: `bedtools` (must be installed in PATH), `wget`/`curl`
- **Memory**: 7 GB+ RAM recommended (required for full dataset processing)
- **Disk**: 20 GB+ free space (for raw and derived data)

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-798-systematic-assessment-of-non-coding-vari
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify `bedtools`**:
    ```bash
    bedtools --version
    ```

## 3. Data Preparation

The pipeline will automatically download data on the first run if `data/raw/` is empty. To manually trigger download:

```bash
python code/main.py --stage download
```

This will fetch:
- dbSNP Common VCF (GRCh38, Chrom 1-22)
- JASPAR 2024 PWMs
- ENCODE/Roadmap BED files (wgEncodeRegTssV4, wgEncodeRegEnhancerV4)
- Reference Genome (hg38)

*Note: Download times may vary (1-3 hours) due to large file sizes. Checksums (MD5) are verified after download against the primary source.*

## 4. Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py --stage full
```

This performs:
1.  **Filtering**: Intersects SNPs with regulatory regions and generates non-regulatory baseline and matched null cohort.
2.  **Scoring**: Calculates $\Delta Score$ for all SNP-TF pairs (dynamic window).
3.  **Permutation**: Generates null distributions (2-stage: 100 + 1000).
4.  **Enrichment**: Tests GWAS overlap and applies FDR correction (West-Stephens).

*Estimated runtime: 2-6 hours on a 2-core CPU runner, depending on chromosome count, permutation load, and number of candidate TFs.*

## 5. Inspecting Results

- **Filtered SNPs**: `data/derived/filtered_snps.parquet`
- **Scores**: `data/derived/scores.parquet`
- **Final Results**: `data/derived/enrichment_results.csv`

To view the top enriched TFs:
```bash
python code/main.py --stage report --top 10
```

## 6. Unit Testing

Run the test suite to verify logic:

```bash
pytest tests/ -v
```

## 7. Troubleshooting

- **OOM Error**: The pipeline processes data in batches (Chromosome 1-22). If you encounter OOM, reduce `BATCH_SIZE` in `code/config.py`.
- **bedtools missing**: Install via `conda install -c bioconda bedtools` or `apt-get install bedtools`.
- **Network Timeout**: If downloads fail, retry. The pipeline is idempotent.