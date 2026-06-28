# Quickstart: 001-code-review-quality

## Prerequisites

- Python 3.11+
- GitHub Actions Runner (Free Tier)
- Access to HuggingFace Hub (public datasets)

## Installation

1. Clone the repository.
2. Navigate to the project directory.
3. Install dependencies:
   ```bash
   pip install -r projects/PROJ-488-evaluating-the-impact-of-code-generation/code/requirements.txt
   ```

## Execution

1. **Run Data Ingestion**:
   ```bash
   python projects/PROJ-488-evaluating-the-impact-of-code-generation/code/data_ingestion.py
   ```
   *Downloads and filters datasets. Checks checksums.*

2. **Run Metric Extraction**:
   ```bash
   python projects/PROJ-488-evaluating-the-impact-of-code-generation/code/metric_extraction.py
   ```
   *Extracts radon/pylint scores.*

3. **Run Statistical Analysis**:
   ```bash
   python projects/PROJ-488-evaluating-the-impact-of-code-generation/code/statistical_analysis.py
   ```
   *Runs Mann-Whitney U, Cliff's Delta, generates boxplots.*

4. **View Results**:
   - Statistics: `results/stats.csv`
   - Figures: `results/figures/`
   - Guidelines: `results/guidelines.md`

## Validation

- **Checksums**: Verify `data/checksums.json` matches downloaded files.
- **Seeds**: Ensure `code/seeds.py` sets random seed to 42.
- **Runtime**: Ensure total execution ≤6 hours.

## Constitutional Amendment Status

**IMPORTANT**: Before running the pipeline, verify that Constitutional Amendments for Principles VI and VII have been approved OR the spec has been revised. Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` for amendment status.

- If Amendment VI (Dataset Provenance) is PENDING: Do NOT proceed. Open amendment PR or revise spec.
- If Amendment VII (Metric Transparency) is PENDING: Do NOT proceed. Open amendment PR or revise spec.