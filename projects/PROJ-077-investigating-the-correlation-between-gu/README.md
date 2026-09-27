# Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

**Project ID**: PROJ-077-investigating-the-correlation-between-gu
**Research Question**: What is the correlation between gut microbiome diversity and cognitive performance?
**Method**: Correlation analysis using processed UK Biobank data (Spearman rank correlation, Multivariate Linear Regression, Lasso Regression).

## Getting Started

This project analyzes the relationship between gut microbiome alpha diversity (Shannon Index) and fluid intelligence scores using data from the UK Biobank.

### Prerequisites

- Python 3.11+
- pip
- Access to UK Biobank data (see below)

### Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Access Instructions

**CRITICAL**: This analysis requires real data from the UK Biobank. The pipeline is configured to **fail loudly** if the required data is missing. Do not attempt to run this pipeline without obtaining the dataset.

### Step 1: Apply for Access

To access UK Biobank data, you must:
1. Register at [https://www.ukbiobank.ac.uk/](https://www.ukbiobank.ac.uk/)
2. Submit a research proposal detailing your intended use of the data.
3. Await approval and receive your application ID.

**Required Application ID**: [INSERT YOUR UK BIOBANK APPLICATION ID HERE]
*(Note: Replace the placeholder above with your actual approved Application ID when submitting a proposal.)*

### Step 2: Request Specific Fields

Upon approval, request the following specific fields (Data Fields) via the UK Biobank Access Management System:

**Microbiome Data (OTU/ASV Counts):**
- Field ID: 19900 (Bacterial taxa relative abundance counts / OTU tables)
- *Note: Specific field IDs for microbiome OTU/ASV counts may vary based on the specific release. Ensure you request the "16S rRNA sequencing data" or "Metagenomics" dataset.*

**Cognitive Performance:**
- Field ID: 20016 (Fluid intelligence score)
- Field ID: 20002 (Date of birth - for age calculation if not directly provided)

**Demographic Covariates:**
- Field ID: 31 (Sex)
- Field ID: 21001 (Age at recruitment)
- Field ID: 21002 (Body Mass Index - BMI)

**Dietary Data (for HEI-2015 DQS Calculation):**
- Field ID: 100001 (Total Fruits)
- Field ID: 100002 (Whole Fruits)
- Field ID: 100003 (Total Vegetables)
- Field ID: 100004 (Greens and Beans)
- Field ID: 100005 (Whole Grains)
- Field ID: 100006 (Dairy)
- Field ID: 100007 (Total Protein Foods)
- Field ID: 100008 (Seafood and Plant Proteins)
- Field ID: 100009 (Refined Grains)
- Field ID: 100010 (Sodium)
- Field ID: 100011 (Empty Calories)
*(Note: Verify exact field IDs in the UK Biobank Showcase as dietary field mappings can be updated.)*

### Step 3: Download and Place Data

1. Download the requested data files from the UK Biobank Data Showcase.
2. **Place files in `data/raw/`** directory at the project root.
3. Ensure files are named consistently with the expected input schema (e.g., `microbiome_otu.csv`, `cognitive_data.csv`, `demographics.csv`, `dietary_data.csv`).
 - If using the standard UK Biobank bulk download, you may need to rename or merge files to match the expected schema defined in `code/data_ingestion.py`.

**Directory Structure Requirement:**
```
data/
└── raw/
 ├── microbiome_otu.csv # (or equivalent OTU/ASV count matrix)
 ├── cognitive_data.csv # (fluid_intelligence scores)
 ├── demographics.csv # (age, sex, bmi)
 └── dietary_data.csv # (components for HEI-2015)
```

**Warning**: The pipeline script `code/verify_data_source.py` and `code/main.py` will raise a `FileNotFoundError` if these files are not found in `data/raw/`. Do not use synthetic data for the final analysis.

## Running the Pipeline

Once data is in place, run the full analysis:

```bash
python code/main.py
```

This will execute:
1. Data Ingestion & Preprocessing
2. Diversity Calculation (Shannon Index)
3. Correlation & Regression Analysis
4. Visualization & Reporting

### Expected Outputs

- `data/processed/cleaned_data.csv`: Preprocessed dataset
- `data/processed/correlation_results.csv`: Spearman correlation results
- `data/processed/regression_results.csv`: Regression coefficients
- `data/processed/plots/`: Generated visualization PNGs
- `data/processed/analysis_warnings.log`: Runtime warnings

## Configuration

Edit `code/config.py` to adjust:
- `SAMPLE_LIMIT`: Maximum number of rows to process (default: 50,000)
- `DQS_REQUIRED`: Set to `True` to enforce Dietary Quality Score calculation (default: `False`)
- `INPUT_PATHS`: Paths to raw data files

## License

This project is for research purposes. Data usage must comply with UK Biobank terms of service.