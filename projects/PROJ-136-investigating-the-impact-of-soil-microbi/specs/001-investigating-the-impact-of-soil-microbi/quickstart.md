# Quickstart: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Access to the internet (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-136-investigating-the-impact-of-soil-microbi
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs `pandas`, `scikit-learn`, `statsmodels`, `biom-format`, `networkx`, `datasets`, `ancombc`.*

## Running the Pipeline

The pipeline is designed to halt gracefully if data is missing.

### Step 1: Data Acquisition
Download the available OTU data. The system will attempt to find disease data but will halt if missing.
```bash
python code/data_acquisition.py
```
*Output*: `data/raw/otu_table.tsv`, or `data/raw/verification_report.json` if disease data is missing.

### Step 2: Check Feasibility
If `verification_report.json` exists, the pipeline has halted. Review the report for missing variables. No further steps should be taken.
```bash
cat data/raw/verification_report.json
```

### Step 3: Preprocessing (Only if data available)
Rarefy the OTU table and compute alpha diversity.
```bash
python code/preprocessing.py
```
*Output*: `data/processed/rarefied-table.qza`, `data/processed/alpha-diversity.tsv`.

### Step 4: Matching (Only if data available)
Attempt to join data.
```bash
python code/matching.py
```
*Output*: `data/processed/matched_samples.csv`.

### Step 5: Statistical Analysis (Only if data available)
Run GLMM, permutation tests, and network analysis.
```bash
python code/analysis/models.py
python code/analysis/network.py
```
*Output*: `data/processed/model_results.json`, `data/processed/network_nodes.csv`.

### Step 6: Report Generation
Generate the final summary.
```bash
python code/generate_report.py
```

## Troubleshooting

-   **"No verified source found"**: This is expected. The pipeline will halt and generate `verification_report.json`. Check `data/raw/verification_report.json` for details.
-   **"GLMM failed to converge"**: This may happen with small sample sizes. The pipeline will log a warning and report the result as "Unstable".
-   **Memory Error**: If the OTU table is too large, the script will automatically sample the first 1000 rows.