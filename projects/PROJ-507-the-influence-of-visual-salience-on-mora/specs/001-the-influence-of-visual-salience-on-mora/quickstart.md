# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview

This guide walks you through setting up and running the project on a CPU-only environment (e.g., GitHub Actions free-tier). The pipeline includes data ingestion, human coding, stimulus generation, survey deployment (simulated), data cleaning, and statistical analysis using Linear Mixed-Effects Models (LMM).

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git (for cloning the repository)
- ~14 GB disk space (for dataset and processing)
- Internet access (to download datasets and CLIP model)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   **requirements.txt** (pinned versions):
   ```text
   numpy==1.26.0
   pandas==2.1.0
   scikit-learn==1.3.0
   scipy==1.11.0
   torch==2.1.0+cpu  # CPU-only wheel
   transformers==4.35.0
   opencv-python==4.8.0
   pillow==10.0.0
   statsmodels==0.14.0
   pingouin==0.5.3
   pyyaml==6.0.1
   pytest==7.4.0
   ```

## Data Preparation

1. **Download Visual Genome Subset**:
   - Manually download a subset of Visual Genome images (social/conflict scenarios) from https://visualgenome.org/ or use a script (if available).
   - Place images in `data/raw/visual_genome_subset/`.
   - Download metadata (annotations) and place in `data/raw/visual_genome_subset/metadata/`.
   - Verify checksums against the official source.

2. **Run Data Ingestion Script**:
   ```bash
   python code/01_data_ingestion.py
   ```
   This filters images by metadata and saves candidates to `data/interim/scenarios.csv`.

## Human Coding

1. **Run Human Coding Script**:
   ```bash
   python code/02_human_coding.py
   ```
   This calculates Cohen's κ and identifies ambiguous scenarios based on human coder inputs.

## Manipulation Check (Pilot)

1. **Run Manipulation Check Script**:
   ```bash
   python code/03_manipulation_check.py
   ```
   This verifies that the intended salience levels are perceptually distinct before full generation.

## Stimulus Generation

1. **Run Salience Manipulation Script**:
   ```bash
   python code/04_salience_manipulation.py
   ```
   Generates low/medium/high salience variants for each scenario.

2. **Run Semantic Validation Script**:
   ```bash
   python code/05_semantic_validation.py
   ```
   Validates semantic preservation via CLIP and SSIM; excludes variants with similarity <0.95 or SSIM <0.90.

## Survey Deployment (Simulated)

For real deployment, integrate with a survey platform (e.g., Prolific, Qualtrics). For testing, run the simulated survey:

```bash
python code/06_survey_deployment.py
```

This generates synthetic responses for testing the pipeline.

## Data Cleaning

1. **Run Data Cleaning Script**:
   ```bash
   python code/07_data_cleaning.py
   ```
   Detects and excludes straight-lining participants.

## Statistical Analysis

1. **Run Analysis Script**:
   ```bash
   python code/08_statistical_analysis.py
   ```
   Performs Linear Mixed-Effects Model (LMM) analysis, corrections, and generates results.

2. **View Results**:
   - Check `data/processed/analysis_results.json` for statistical outputs.
   - Review console output for LMM coefficients and effect sizes.

## Versioning Update

1. **Run Versioning Script**:
   ```bash
   python code/09_versioning_update.py
   ```
   Updates the project state file with content hashes and timestamps.

## Testing

1. **Run Unit Tests**:
   ```bash
   pytest tests/unit/ -v
   ```

2. **Run Integration Tests**:
   ```bash
   pytest tests/integration/ -v
   ```

3. **Run Contract Tests**:
   ```bash
   pytest tests/contract/ -v
   ```

## Troubleshooting

- **CLIP Inference Slow**: Reduce batch size or process images in smaller chunks.
- **Memory Error**: Subset the dataset further; process images in batches.
- **Missing Dependencies**: Ensure virtual environment is activated; reinstall `requirements.txt`.
- **Data Not Found**: Verify paths in `data/raw/`; check checksums in `state/projects/...yaml`.
- **LMM Convergence Failure**: Check data structure; try simplifying random effects or using robust standard errors.

## Next Steps

- **Real Survey Deployment**: Integrate with a survey platform; collect real participant data.
- **Power Analysis**: Refine sample size estimates based on pilot data.
- **Paper Writing**: Use `data/processed/analysis_results.json` to draft the research paper.

## Support

- **Documentation**: See `plan.md`, `research.md`, `data-model.md`.
- **Issues**: Open a GitHub issue for bugs or questions.
- **Contributions**: Follow the project's contribution guidelines.