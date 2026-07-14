# Assessing the Impact of Code Style Consistency on LLM Code Understanding

This project investigates whether code style consistency (e.g., indentation, naming conventions, line length) significantly impacts Large Language Model (LLM) performance in code understanding tasks such as summarization and bug localization.

## Project Structure

```
.
├── code/ # Implementation scripts and utilities
│ ├── utils/ # Reusable helper modules
│ ├── 00_validate_urls.py
│ ├── 00_hash_artifacts.py
│ ├── 00_extract_metadata.py
│ ├── 01_style_scoring.py
│ ├── 02_stratification.py
│ ├── 03_sensitivity_analysis.py
│ ├── 03_inference.py
│ ├── 04_evaluation.py
│ ├── 05_statistical_analysis.py
│ ├── 06_ablation_analysis.py
│ └── 06_robustness_check.py
├── data/ # Data storage
│ ├── raw/ # Original dataset files
│ ├── processed/ # Processed data and results
│ ├── metadata/ # File metadata and style scores
│ └──.gitkeep
├── tests/ # Unit and integration tests
│ ├── unit/
│ └── integration/
├── specs/ # Design documents and specifications
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.10+
- Git (for file age extraction)
- CPU-only environment (no GPU required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Set up project directories**:
 ```bash
 python code/create_directories.py
 ```

5. **Configure linting and formatting**:
 ```bash
 python code/setup_linting.py
 ```

## Usage

The pipeline is executed in sequential phases. Run each script from the `code/` directory.

### Phase 1: Setup & Validation

- **Validate Dataset URLs**:
 ```bash
 python code/00_validate_urls.py
 ```
 Checks accessibility of CodeSearchNet and Defects4J dataset URLs.

- **Extract File Metadata**:
 ```bash
 python code/00_extract_metadata.py
 ```
 Generates `data/metadata/file_metadata.csv` containing `file_age`, `file_size`, and `cyclomatic_complexity`.

- **Generate Artifact Hashes**:
 ```bash
 python code/00_hash_artifacts.py
 ```
 Creates content hashes for data artifacts and updates `state/*.yaml`.

### Phase 2: Style Scoring & Stratification (User Story 1)

- **Compute Style Consistency Scores**:
 ```bash
 python code/01_style_scoring.py
 ```
 Outputs `data/metadata/style_scores_raw.csv` with pylint and radon metrics.

- **Stratify Data by Style Score**:
 ```bash
 python code/02_stratification.py --low-threshold 0.25 --high-threshold 0.75
 ```
 Assigns files to Low, Medium, or High style consistency groups.

- **Sensitivity Analysis**:
 ```bash
 python code/03_sensitivity_analysis.py
 ```
 Tests multiple threshold sets to determine optimal stratification.

### Phase 3: LLM Inference (User Story 2)

- **Run Inference on Stratified Samples**:
 ```bash
 python code/03_inference.py
 ```
 Uses StarCoder (CPU mode) to generate summaries and bug predictions.
 Outputs: `data/processed/inference_results.jsonl`.

- **Evaluate Inference Results**:
 ```bash
 python code/04_evaluation.py
 ```
 Computes BLEU-4 for summaries and Precision/Recall/F1 for bug localization.

### Phase 4: Statistical Analysis (User Story 3)

- **Perform Statistical Analysis**:
 ```bash
 python code/05_statistical_analysis.py
 ```
 Runs ANCOVA (controlling for file size/age) and t-tests.
 Outputs: `data/processed/statistical_report.json`.

- **Ablation Analysis**:
 ```bash
 python code/06_ablation_analysis.py
 ```
 Verifies style score independence from code complexity.

- **Robustness Check**:
 ```bash
 python code/06_robustness_check.py
 ```
 Attempts secondary model validation or fallback to CPU-feasible alternatives.

## Statistical Results

Upon completion of the full pipeline, the primary results are stored in `data/processed/statistical_report.json`. This file contains:

- **ANCOVA Results**: F-statistic, p-values, and covariate coefficients for file size and file age.
- **Effect Sizes**: Cohen's d values for pairwise group comparisons (High vs. Low, etc.).
- **Confidence Intervals**: 95% CIs for effect sizes.
- **Group Separation Verification**: Confirmation that effect sizes meet the >0.5 threshold.
- **Statistical Power**: Estimated power of the tests given the sample size.

Key findings regarding the impact of code style consistency on LLM accuracy will be summarized here after execution.

## Testing

Run unit and integration tests to verify pipeline integrity:

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

## License

This project is part of the llmXive automated science pipeline.