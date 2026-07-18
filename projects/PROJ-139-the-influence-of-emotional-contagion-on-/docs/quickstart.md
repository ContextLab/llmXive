# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

This guide provides step-by-step instructions to set up the environment, download data, run the full analysis pipeline, and verify results for the emotional contagion research project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Access to the internet (for data fetching)
- At least 15GB of free disk space for raw and processed data

## 1. Environment Setup

### Clone and Install Dependencies

```bash
# Navigate to the project root
cd PROJ-139-the-influence-of-emotional-contagion-on-

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure API Keys (Optional)

If you intend to use the Reddit Official API as a fallback, create a `.env` file in the project root:

```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
```

The pipeline will attempt to use Pushshift first, then Reddit API, then HuggingFace/Internet Archive as fallbacks.

## 2. Data Collection and Extraction

Run the data download and extraction pipeline. This step fetches Reddit data (Pushshift -> Reddit API -> Archives), extracts threads with decision points, and identifies seed posts.

```bash
python -m code.data.download
python -m code.data.extract
```

**Outputs:**
- `data/raw/downloaded_data.json` (Raw fetch results)
- `data/processed/extracted_threads.csv` (Thread data with seed posts)
- `data/processed/exclusions.log` (Threads excluded due to insufficient seed posts)

*Note: If the download step fails due to network issues, it will automatically attempt the next fallback source.*

## 3. Sentiment Analysis and Validation

### 3.1 Annotate Corpus (Optional/Manual Step)
If human annotation is required for validation (as per T007a), run:
```bash
python -m code.data.annotate_corpus
```

### 3.2 Calculate Inter-Rater Reliability
```bash
python -m code.data.calculate_reliability
```
**Output:** `data/processed/vader_validation_report.json`

### 3.3 Apply Sentiment Analysis
Run the sentiment analysis pipeline which applies VADER and validates against the annotated corpus if available.
```bash
python -m code.data.sentiment
```

## 4. Metrics Computation and Modeling

### 4.1 Compute Metrics and Contagion Index
Calculate sentiment slopes, contagion indices, agreement proportions, and entropy.
```bash
python -m code.data.metrics
```
**Outputs:**
- `data/processed/metrics.csv` (Per-thread metrics)
- `data/processed/valid_threads.csv` (Threads with ground truth validation)
- `data/processed/validity_failure_report.json` (If valid threads < 30%)

### 4.2 Statistical Modeling
Fit GLMMs, run Wald tests, apply multiple-comparison corrections, and perform sensitivity analysis.
```bash
python -m code.data.modeling
```
**Outputs:**
- `data/processed/model_results.json` (GLMM coefficients, p-values)
- `data/processed/sensitivity_analysis.csv` (Results across agreement/entropy thresholds)
- `data/processed/sensitivity_fp_fn.csv` (False Positive/Negative rates)

## 5. Reproducibility and Verification

### Record Artifact Checksums
Generate checksums for all generated artifacts to ensure reproducibility.
```bash
python -m code.utils.artifact_checksums
```
**Output:** `state/projects/PROJ-139-...yaml`

### Verify Reproducibility
Re-run the pipeline (or specific stages) and compare checksums.
```bash
python -m code.tests.test_reproducibility
```

## 6. Full Pipeline Execution

To run the entire pipeline sequentially (recommended for a clean run):

```bash
# 1. Data
python -m code.data.download
python -m code.data.extract

# 2. Sentiment
python -m code.data.annotate_corpus # If manual annotation needed
python -m code.data.calculate_reliability
python -m code.data.sentiment

# 3. Metrics & Modeling
python -m code.data.metrics
python -m code.data.modeling

# 4. Verification
python -m code.utils.artifact_checksums
```

## 7. Generating the Final Report

Once the pipeline completes, the final research report is generated at:
`docs/paper.md`

This report includes:
- SC-006 pass/fail status
- Ground truth percentage
- GLMM model results
- Sensitivity analysis summaries

## Troubleshooting

- **Data Fetching Errors**: If all data sources fail, check your internet connection and firewall settings. The pipeline logs the origin type used.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Memory Errors**: For large datasets, ensure you have sufficient RAM (min 8GB recommended). The pipeline streams data where possible.
- **Validation Failures**: If the validation report indicates low Kappa scores, review the `data/processed/vader_validation_report.json` for details.

## Next Steps

- Review the generated `docs/paper.md` for research findings.
- Analyze the `data/processed/sensitivity_analysis.csv` to understand robustness.
- Share the `state/projects/PROJ-139-...yaml` checksum file for audit purposes.