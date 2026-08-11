# Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

This project analyzes the relationship between gut microbiome diversity (Shannon Index) and cognitive performance (Fluid Intelligence) using UK Biobank data.

## Research Question
What is the correlation between gut microbiome diversity and cognitive performance?

## Method
Correlation analysis using Spearman rank correlation on processed data, followed by multivariate regression adjusting for covariates (Age, Sex, BMI, Diet Quality Score).

## Project Structure

```
PROJ-077-investigating-the-correlation-between-gu/
├── code/ # Pipeline implementation
│ ├── main.py # Orchestrator
│ ├── config.py # Configuration and paths
│ ├── data_fetcher.py # Data acquisition utilities
│ ├── data_ingestion.py # Cleaning and preprocessing
│ ├── diversity.py # Shannon Index calculation
│ ├── analysis.py # Correlation and regression
│ ├── visualization.py # Plot generation
│ └──...
├── data/
│ ├── raw/ # **RAW DATA MUST BE PLACED HERE**
│ └── processed/ # Cleaned data and analysis outputs
├── tests/ # Unit and integration tests
├── docs/ # Documentation and spec overrides
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Data Access Instructions

### 1. Obtain UK Biobank Data

This project requires access to specific fields from the UK Biobank. You must apply for access through the official UK Biobank portal (https://www.ukbiobank.ac.uk/) if you do not already have credentials.

**Required Data Fields:**

The pipeline expects the following columns to be present in the raw data files. Ensure your extracted dataset includes these:

**Microbiome Data (`data/raw/microbiome_data.csv`):**
- `participant_id`: Unique identifier for the participant.
- `OTU_1`, `OTU_2`,..., `OTU_N` (or specific taxonomic columns): Raw count data for Operational Taxonomic Units (OTUs) or Amplicon Sequence Variants (ASVs). **Do not provide CLR-transformed data here.**
- *Note: If the data is in a wide format where rows are participants and columns are taxa, this is the expected format.*

**Cognitive Data (`data/raw/cognitive_data.csv`):**
- `participant_id`: Unique identifier (must match microbiome data).
- `fluid_intelligence_score`: The primary cognitive outcome variable.
- `age`: Participant age at assessment.
- `sex`: Participant sex (M/F).
- `bmi`: Body Mass Index.

**Dietary Data (`data/raw/dietary_data.csv`):**
- `participant_id`: Unique identifier.
- `fruit_intake`: Frequency or amount of fruit consumption.
- `vegetable_intake`: Frequency or amount of vegetable consumption.
- `grain_intake`: Frequency or amount of grain consumption.
- `dairy_intake`: Frequency or amount of dairy consumption.
- `protein_intake`: Frequency or amount of protein consumption.
- *Note: These fields are used to calculate the Diet Quality Score (DQS) using the HEI-2015 standard if pre-calculated DQS is not available.*

### 2. Data Placement

Once you have downloaded the necessary files from the UK Biobank (or the `ukbiobank/microbiome-cognitive` dataset if using the verified streaming source), place them in the `data/raw/` directory.

The directory structure must look like this:

```
data/
└── raw/
 ├── microbiome_data.csv
 ├── cognitive_data.csv
 └── dietary_data.csv
```

**Important:** The pipeline is configured to fail loudly if these files are missing or empty. It will **not** generate synthetic data as a fallback.

### 3. Alternative: Verified Streaming Source

If you have access to the verified Hugging Face dataset `ukbiobank/microbiome-cognitive`, the `code/data_fetcher.py` module can attempt to stream this data directly. However, for local development and reproducibility, placing the data in `data/raw/` is the recommended approach.

## Installation

1. **Clone the repository:**
 ```bash
 git clone <repository-url>
 cd PROJ-077-investigating-the-correlation-between-gu
 ```

2. **Create a virtual environment:**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies:**
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Ensure that `data/raw/` contains the required CSV files as described above.

1. **Run the full pipeline:**
 ```bash
 python code/main.py
 ```

2. **Run specific stages:**
 - Data Ingestion: `python code/data_ingestion.py`
 - Diversity Analysis: `python code/diversity.py`
 - Correlation/Regression: `python code/analysis.py`
 - Visualization: `python code/visualization.py`

3. **Validation:**
 - Run `python code/validate_sc001.py` to verify correlation results.
 - Run `python code/validate_sc002.py` to verify regression results.

## Expected Outputs

Upon successful completion, the following files will be generated in `data/processed/`:

- `cleaned_data.csv`: Filtered and imputed dataset.
- `correlation_results.csv`: Spearman correlation coefficients and p-values.
- `regression_results.csv`: Multivariate regression coefficients and statistics.
- `plots/`: Directory containing scatter plots and histograms.

## Configuration

Edit `code/config.py` to adjust:
- `INPUT_PATHS`: Paths to raw data files.
- `SAMPLE_LIMIT`: Maximum number of samples to process (default: 50,000 for CI safety).
- `RANDOM_SEED`: Seed for reproducibility.

## Troubleshooting

- **FileNotFoundError: Input files missing**: Ensure `data/raw/` contains `microbiome_data.csv`, `cognitive_data.csv`, and `dietary_data.csv`.
- **ImportError**: Ensure all dependencies in `requirements.txt` are installed.
- **Memory Error**: Reduce `SAMPLE_LIMIT` in `code/config.py`.

## References

- Spec Override FR-002: System MUST compute alpha diversity (Shannon index) using `scikit-bio` on raw counts.
- Spec Override SC-001: The correlation coefficient and p-value between Raw Shannon Index and fluid intelligence are measured against the Spearman rank correlation test results.
- Spec Override FR-007: System MUST impute missing categorical values (sex) using the mode.