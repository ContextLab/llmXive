# Quickstart: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Prerequisites

- **Operating System**: Linux (Ubuntu 22.04 or later).
- **Memory**: ≥7 GB RAM (recommended 8 GB).
- **Disk**: ≥14 GB free space.
- **Tools**: `git`, `conda` (or `mamba`), `R` (≥4.3), `Python` (≥3.11).
- **Data**: Access to GEO ChIP-seq data (placeholder `GSE####`) and 1002 Yeast Genomes eQTL data (placeholder).

> **Note**: The pipeline will abort if required datasets are not found. Replace placeholder accessions with verified sources before running.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd yeast-cre-analysis
 ```

2. **Create Conda environment**:
 ```bash
 conda env create -f code/environment.yml
 conda activate yeast-cre-analysis
 ```

3. **Install Python dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify tool versions**:
 ```bash
 fastp --version
 bowtie2 --version
 macs2 --version
 R --version
 ```

## Data Setup

1. **Download ChIP-seq data** (replace `GSE####` with actual accession):
 ```bash
 bash code/01_download_data.sh GSE####
 ```
 - This script downloads FASTQ files and verifies MD5 checksums.
 - **Abort** if data missing or checksums fail.

2. **Place eQTL data** in `data/raw/`:
 - Ensure CSV/TSV contains columns: `gene_id`, `fold_change_heat`, `fold_change_osmotic`, `fold_change_oxidative`.
 - **Abort** if stress-specific fold-changes missing for entire cohort.

## Running the Pipeline

Execute the full pipeline:
```bash
bash code/run_pipeline.sh
```

This runs the following steps sequentially:
1. **Download & Verify** (FR-001)
2. **Preprocess** (FR-002: fastp, bowtie2)
3. **Peak Calling** (FR-003: MACS2 FDR sweep)
4. **Merge & Annotate** (FR-004)
5. **Validate CREs** (FR-014, FR-015)
6. **Fit Mixed Models** (FR-005, FR-012)
7. **Permutation Test** (FR-006)
8. **Generate Reports** (FR-010)
9. **Create bigWig Tracks** (FR-009)

### Running Individual Steps

- **Peak calling only**:
 ```bash
 bash code/03_call_peaks.sh
 ```
- **Mixed model fitting**:
 ```bash
 Rscript code/06_fit_mixed_models.R
 ```

## Output

After successful execution, results are in:

- `results/CRE_ranked_heatshock.md`
- `results/CRE_ranked_osmotic.md`
- `results/CRE_ranked_oxidative.md`
- `results/Statistical_summary.pdf`
- `tracks/heatshock_CRE_signal.bw`
- `tracks/osmotic_CRE_signal.bw`
- `tracks/oxidative_CRE_signal.bw`

### Viewing Results

- **Ranked CREs**: Open markdown files in any text editor.
- **Statistical Report**: Open PDF to view LRT results, FDR-corrected p-values, and GO enrichment.
- **IGV Visualization**: Load bigWig tracks into IGV. Signal intensity should correlate with log₂FC values.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Fatal: Missing ChIP-seq data` | GEO accession not found or incomplete. | Verify accession; download missing TF-condition pairs. |
| `Fatal: Missing eQTL fold-changes` | Entire stress condition missing in eQTL data. | Replace eQTL dataset with one containing all stresses. |
| `Warning: No peaks survive FDR < 0.01` | Stringent threshold; no significant peaks. | Relax threshold to 0.05 (pipeline suggests this). |
| `Error: VIF > 5 for all CREs` | High collinearity; no independent effects. | Report all CREs as collinear; no independent testing. |
| `MemoryError` | Dataset too large for 7 GB RAM. | Filter eQTL data to paired genes; sample if necessary. |

## Next Steps

- **Functional Validation**: Use ranked CREs to design CRISPRi/a experiments.
- **Literature Integration**: Cross-reference top CREs with known stress-response pathways.
- **Extension**: Apply pipeline to other stress conditions or yeast strains.
