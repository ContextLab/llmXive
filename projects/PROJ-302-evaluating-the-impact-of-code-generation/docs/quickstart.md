# Quickstart Guide: Evaluating the Impact of Code Generation on Code Review Time

This guide provides step-by-step instructions to set up, run, and validate the research pipeline for evaluating the impact of LLM-generated code on code review times.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- A GitHub Personal Access Token (with `repo` scope) for API access
- At least 16GB RAM recommended for full dataset processing

## 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-302-evaluating-the-impact-of-code-generation

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Create a `.env` file in the project root with your GitHub token:

```bash
GITHUB_TOKEN=your_github_personal_access_token
RANDOM_SEED=42
```

Alternatively, set these as environment variables.

## 3. Directory Structure

The project uses the following directory structure:

```
.
├── code/
│ ├── data_acquisition/
│ ├── feature_extraction/
│ ├── analysis/
│ └── utils/
├── data/
│ ├── raw/
│ └── processed/
├── tests/
│ ├── contract/
│ ├── integration/
│ └── unit/
├── docs/
└── specs/
```

## 4. Running the Pipeline

### Phase 1: Data Acquisition (US1)

Fetch GitHub PR metadata and generate synthetic LLM code snippets:

```bash
# Fetch PR data from repositories with >= 1000 stars
python code/data_acquisition/github_scraper.py

# Generate synthetic LLM code snippets
python code/data_acquisition/synthetic_generator.py

# Classify code snippets (diagnostic only)
python code/data_acquisition/classifier_runner.py
```

**Output**: `data/processed/generated_snippets.parquet`

### Phase 2: Feature Extraction (US1)

Extract complexity, timestamps, style features, and semantic similarity:

```bash
# Calculate code complexity metrics
python code/feature_extraction/complexity.py

# Extract review timestamps
python code/feature_extraction/timestamps.py

# Compute style features
python code/feature_extraction/style_features.py

# Calculate semantic similarity scores (diagnostic only)
python code/feature_extraction/semantic_similarity.py
```

**Output**: `data/processed/diagnostic_scores.parquet`

### Phase 3: Propensity Score Matching & Analysis (US2)

Match LLM-like and human commits, perform statistical testing:

```bash
# Run propensity score matching
python code/analysis/matching.py

# Run statistical tests
python code/analysis/statistical_test.py

# Generate deviation report (documents exclusion of semantic similarity)
python code/analysis/deviation_report_generator.py
```

**Output**:
- `data/processed/matching_results.parquet`
- `data/processed/statistical_results.json`
- `data/processed/deviation_report.md`

### Phase 4: Sensitivity Analysis & Visualization (US3)

Perform sensitivity analysis across star-count quartiles and generate plots:

```bash
# Run sensitivity analysis
python code/analysis/sensitivity.py

# Generate visualizations
python code/analysis/visualization.py
```

**Output**:
- `data/processed/sensitivity_summary.json`
- `figures/` (box plots, CDF curves, sensitivity plots)

### Phase 5: Prompt-Based Cohort Validation (US4)

Generate and validate prompt-based LLM code cohort:

```bash
# Generate prompt-based cohort
python code/data_acquisition/prompt_cohort_generator.py

# Validate syntax of generated snippets
python code/feature_extraction/prompt_cohort_validator.py

# Run matching for prompt-based cohort
python code/analysis/prompt_cohort_matching.py
```

**Output**: `data/processed/prompt_based_cohort.parquet`

## 5. Validation

Run the complete validation suite:

```bash
# Contract tests
python -m pytest tests/contract/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Unit tests
python -m pytest tests/unit/ -v
```

## 6. Generating the Final Report

Combine all analysis results into a comprehensive HTML/PDF report:

```bash
python code/analysis/report_generator.py
```

**Output**: `docs/final_report.html`, `docs/final_report.pdf`

## 7. Troubleshooting

### GitHub API Rate Limiting
If you encounter rate limiting, the pipeline automatically implements exponential backoff. Ensure your token has sufficient permissions.

### Memory Issues
For large datasets, consider processing in chunks or using streaming mode:
```python
# In your data loading code
dataset = load_dataset("github_prs", split="train", streaming=True)
```

### Generation Failures
If LLM generation fails (T014b or T033), the pipeline will halt and generate `spec_amendment_request.md` with details about the failure.

### Matching Imbalance
If propensity score matching fails to achieve balance (SMD > 0.1), check `data/processed/matching_failure_report.json` for diagnostic information.

## 8. Expected Outputs

After successful execution, you should have:

- `data/processed/generated_snippets.parquet` - Synthetic LLM code snippets
- `data/processed/diagnostic_scores.parquet` - Semantic similarity scores
- `data/processed/matching_results.parquet` - Matched pairs
- `data/processed/statistical_results.json` - P-values and effect sizes
- `data/processed/sensitivity_summary.json` - Sensitivity analysis results
- `data/processed/deviation_report.md` - Documentation of methodological choices
- `figures/` - Visualization plots
- `docs/final_report.html` - Comprehensive analysis report

## 9. Next Steps

- Review the `specs/` directory for detailed feature requirements
- Check `tasks.md` for implementation status
- Read `docs/research_methodology.md` for scientific rationale
- Examine `docs/data_dictionary.md` for field definitions

## Support

For issues or questions, please refer to the project's issue tracker or contact the research team.
