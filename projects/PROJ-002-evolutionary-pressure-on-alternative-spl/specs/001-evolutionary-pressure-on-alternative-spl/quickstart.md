# Quickstart: Evolutionary Pressure on Alternative Splicing in Primates

## Prerequisites

-   **Python**: 3.11+
-   **R**: 4.3+ (with packages `caper`, `ape`, `ggplot2`, `phylolm`)
-   **External Tools**: `STAR`, `SUPPA2`, `bedtools` (installed in PATH)
-   **Git**: For repository cloning

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/PROJ-002-evolutionary-pressure.git
    cd PROJ-002-evolutionary-pressure-on-alternative-spl
    ```

2.  **Set up Python environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

3.  **Set up R packages**:
    ```bash
    R -e "install.packages(c('caper', 'ape', 'ggplot2', 'dplyr', 'phylolm'), repos='https://cloud.r-project.org')"
    ```

4.  **Verify External Tools**:
    Ensure `star`, `suppa`, and `bedtools` are in your PATH.
    ```bash
    star --version
    suppa.py --version
    bedtools --version
    ```

## Running the Pipeline

### Option A: Full Run (Requires Real Data)
*Note: Requires valid SRA accessions and sufficient disk space.*

1.  **Prepare Configuration**: Edit `config/species.yaml` with real SRA IDs and genome paths.
2.  **Execute**:
    ```bash
    python code/download.py --config config/species.yaml
    python code/align.py --config config/species.yaml
    python code/quantify.py --config config/species.yaml
    python code/annotate.py --config config/species.yaml
    python code/stats.py --config config/species.yaml
    python code/plot.py --config config/species.yaml
    ```

### Option B: CI/Synthetic Run (Recommended for Validation)
*Uses synthetic data to validate logic without downloading large files.*

1.  **Generate Synthetic Data**:
    ```bash
    python code/download.py --synthetic --config config/species.yaml
    ```
    *This creates `data/raw/synthetic/` with mock FASTQs.*

2.  **Run Full Pipeline**:
    ```bash
    python code/align.py --synthetic --config config/species.yaml
    python code/quantify.py --synthetic --config config/species.yaml
    python code/annotate.py --synthetic --config config/species.yaml
    python code/stats.py --synthetic --config config/species.yaml
    python code/plot.py --synthetic --config config/species.yaml
    ```

3.  **Validate Output**:
    ```bash
    python code/validate_plot.py --input data/processed/manhattan.png
    ```
    *Expected: "Validation Passed: Dimensions >= 1200x800, axes labeled, threshold line present."*

## Expected Outputs

-   `data/processed/lineage_specific_events.tsv`: Filtered splicing events.
-   `data/processed/annotation_table.csv`: Flanking regions and phyloP scores.
-   `data/processed/enrichment_results.csv`: Statistical tests and PGLS adjustments.
-   `data/processed/manhattan.png`: Visualization of results.
-   `pipeline.log`: Timestamped log of all steps.

## Troubleshooting

-   **STAR Memory Error**: Reduce `--max-mem` in `config/species.yaml` or sample fewer reads.
-   **Missing phyloP**: If using real data, ensure UCSC Table Browser access. For synthetic, check `annotate.py` simulation logic.
-   **PGLS Failure**: Ensure `primate_tree.nwk` is valid Newick format and matches species names exactly.