# Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

This project implements an automated research pipeline to analyze the correlation between gut microbiome diversity (Shannon Index) and cognitive performance (Fluid Intelligence) using data from the UK Biobank.

## Research Question

What is the correlation between gut microbiome diversity and cognitive performance?

## Method

Correlation analysis using processed data, specifically:
- Calculation of Shannon Index (alpha diversity) from raw microbiome counts.
- Spearman rank correlation between Raw Shannon Index and Fluid Intelligence.
- Multivariate linear regression controlling for Age, Sex, BMI, and Dietary Quality Score (DQS).

## Prerequisites

- Python 3.11+
- Required packages listed in `requirements.txt`

## Data Access and Setup (CRITICAL)

This pipeline requires real data from the **UK Biobank**. The data is **not** included in this repository due to size and access restrictions. You must obtain the data and place it in the `data/raw/` directory.

### 1. Obtain UK Biobank Data

Access to UK Biobank data requires an approved application. Once approved, you can download the relevant fields via the UK Biobank Access Management Portal or the `ukb` command-line tool.

**Required Fields:**
You must download and merge the following datasets:

1. **Microbiome Data (OTU/ASV Tables)**
 - **Source**: UK Biobank Microbiome Study (Field 20002 or specific microbiome release).
 - **Format**: Wide-format matrix (Rows: `participant_id`, Columns: Taxa/Species counts).
 - **Required Columns**: `participant_id`, and columns for each OTU/ASV (e.g., `Taxa_001`, `Taxa_002`...).
 - **File Name**: `data/raw/microbiome_counts.csv`

2. **Cognitive Performance Data**
 - **Source**: UK Biobank Cognitive Assessment (Field 20002).
 - **Required Fields**:
 - `participant_id`: Unique identifier.
 - `fluid_intelligence`: Fluid Intelligence Score (Field 20016 or equivalent).
 - `age`: Age at assessment.
 - `sex`: Biological sex (1: Male, 0: Female).
 - `bmi`: Body Mass Index.
 - **File Name**: `data/raw/cognitive_data.csv`

3. **Dietary Data (for DQS Calculation)**
 - **Source**: UK Biobank Dietary Assessment (Field 100000 series or similar).
 - **Required Fields**:
 - `participant_id`
 - `fruit`: Daily fruit intake (servings/day).
 - `vegetable`: Daily vegetable intake (servings/day).
 - `whole_grain`: Whole grain intake.
 - `dairy`: Dairy product intake.
 - `protein_foods`: Protein food intake.
 - `seafood_plant_protein`: Seafood and plant protein intake.
 - `refined_grains`: Refined grain intake.
 - `sodium`: Sodium intake (mg/day).
 - `empty_calories`: Empty calorie intake.
 - **File Name**: `data/raw/dietary_data.csv`

### 2. Place Data in Directory

Ensure the downloaded files are placed in the `data/raw/` directory with the exact filenames specified above:

```bash
data/
└── raw/
 ├── microbiome_counts.csv
 ├── cognitive_data.csv
 └── dietary_data.csv
```

**Note**: If `dietary_data.csv` is missing, the pipeline will halt with a fatal error as per the Dietary Quality Score (DQS) requirement (FR-008).

### 3. Verify Data Integrity

Before running the pipeline, ensure:
- All files are non-empty.
- `participant_id` is consistent across all three files.
- No required columns are missing.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

## Running the Pipeline

The full pipeline can be executed via the main entry point:

```bash
python code/main.py
```

This will:
1. Validate configuration and input files.
2. Ingest and clean data (filtering, imputation).
3. Calculate Shannon Index and perform correlation/regression analysis.
4. Apply statistical corrections and generate visualizations.

**Output Files**:
- `data/processed/cleaned_data.csv`: Cleaned dataset.
- `data/processed/correlation_results.csv`: Spearman correlation results.
- `data/processed/regression_results.csv`: Regression coefficients.
- `data/processed/plots/`: Generated visualization images.

## Project Structure

```text
.
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── data_fetcher.py # Data loading utilities
│ ├── data_ingestion.py # Data cleaning and imputation
│ ├── diversity.py # Shannon Index calculation
│ ├── analysis.py # Correlation and regression
│ ├── visualization.py # Plot generation
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Input data (YOU MUST PLACE FILES HERE)
│ └── processed/ # Output data and plots
├── tests/ # Unit and integration tests
├── requirements.txt # Dependencies
└── README.md # This file
```

## License

This project is for research purposes only. The UK Biobank data is subject to their terms of use.

## References

- UK Biobank: https://www.ukbiobank.ac.uk/
- Plan: `specs/001-gene-regulation/` (Project Internal)
- Spec Overrides: `docs/spec_override_*.md`