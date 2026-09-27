# Quickstart Guide

This guide walks you through running the full pipeline to predict plant drought tolerance from Root System Architecture (RSA) data.

## Prerequisites

- Python 3.11+
- `TRY_API_KEY` environment variable set for trait data access.
- Sufficient disk space (~14GB recommended for full dataset).

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd PROJ-464-predicting-plant-drought-tolerance-from-
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Ensure the `config.py` file in the `code/` directory reflects your desired paths and seeds. By default, it uses `random_seed=42`.

## Running the Pipeline

The pipeline is executed in stages. Each stage produces artifacts required for the next.

### Step 1: Setup & Data Download

Download root images and physiological traits.

```bash
python code/download_images.py
python code/download_traits.py
```

*Note: If the NPPN dataset or TRY API is unreachable, the script will halt with a critical error.*

### Step 2: Feature Extraction

Process images to extract RSA metrics (depth, branching density, surface area).

```bash
python code/preprocess_images.py
```

**Output**: `data/derived/rsametrics.csv`

### Step 3: Phylogeny & Merging

Fetch the phylogenetic tree and merge all data sources.

```bash
python code/fetch_phylogeny.py
python code/merge_data.py
```

**Output**: `data/derived/merged_data.csv`, `data/derived/phylogenetic_tree.newick`

### Step 4: Modeling & Analysis

Run statistical models (OLS, Ridge, Lasso, RF, PGLS) and sensitivity analysis.

```bash
python code/models.py
python code/analysis.py
```

**Output**: `data/derived/model_results.csv`, `state/vif_compliance_check.yaml`

### Step 5: Report Generation

Generate the final scientific report with VIF compliance checks.

```bash
python code/generate_report.py
python code/generate_sensitivity_report.py
```

**Output**: `data/derived/report_framing.md`, `data/derived/sensitivity_report.md`

## Verifying Results

All generated artifacts are validated against JSON schemas defined in `contracts/`.
To run validation manually:

```bash
python code/validate_schemas.py
```

## Troubleshooting

- **Missing Data**: Ensure `TRY_API_KEY` is set and the HuggingFace token has access to `nppn/root-phenotyping`.
- **Phylogeny Errors**: The pipeline requires a valid Newick tree. If `fetch_phylogeny.py` fails, the pipeline stops as PGLS cannot proceed without a tree.
- **Memory Issues**: If processing large images, consider profiling memory usage via `code/profile_memory.py` (if available) or reducing batch sizes.