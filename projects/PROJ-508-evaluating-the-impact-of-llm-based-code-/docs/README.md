# Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Project Overview

This research project investigates the association between LLM-based code completion adoption (e.g., GitHub Copilot, Cursor) and developer cognitive load, using proxy metrics derived from code review and commit history on GitHub repositories.

**Research Question**: Does the adoption of LLM-based code completion tools correlate with changes in developer cognitive load, as proxied by iteration count, review depth, and comment complexity?

**Key Methodological Updates**:
- **Signal Separation**: Controls for "AI Noise" (fixing AI-generated errors) using `diff_complexity_score`.
- **Statistical Engine**: Uses Mixed-Effects Models (GLMM) and Zero-Inflated Negative Binomial (ZINB) models instead of simple linear regression.
- **Data Scope**: Includes all push events between PR open and merge (no exclusion of "Copilot" commits).

## Prerequisites

- Python 3.11+
- A GitHub Personal Access Token (PAT) with `public_repo` scope (set via `GITHUB_TOKEN` environment variable)
- Required Python packages (see `requirements.txt`)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-508-evaluating-the-impact-of-llm-based-code-
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment variables**:
 Create a `.env` file in the project root or set the following environment variable:
 ```bash
 export GITHUB_TOKEN="your_github_personal_access_token"
 ```

## Usage

The pipeline consists of three main stages: Ingestion, Analysis, and Reporting.

### 1. Data Ingestion

Fetches repository metadata, PRs, commits, and configuration files to classify LLM adoption and calculate metrics.

```bash
python code/generate_master_dataset.py
```

**Output**:
- `data/derived/master_dataset.csv`: The primary dataset containing repo metrics and adoption flags.
- `data/manifest.json`: Metadata about the data sources and processing timestamps.

### 2. Statistical Analysis

Runs GLMM and ZINB models to test hypotheses while controlling for confounders (project size, team size, AI noise).

```bash
python code/analyze.py
```

**Output**:
- `data/derived/analysis_results.json`: Model coefficients, standard errors, and p-values.
- `data/derived/sensitivity_analysis.json`: Results from threshold sweeps.
- `data/derived/stratified_analysis.json`: Results splitting data by "AI Noise" levels.

### 3. Report Generation

Generates publication-ready visualizations (Forest Plots, Sensitivity Plots) and the final PDF report.

```bash
python code/report.py
```

**Output**:
- `docs/output/final_report.pdf`: The comprehensive research report.
- `docs/output/forest_plot.png`: Visualization of effect sizes.
- `docs/output/data_flow.svg`: Mermaid diagram of the data pipeline.

## Project Structure

```text
projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/
├── code/
│ ├── ingest.py # Data ingestion logic
│ ├── analyze.py # Statistical modeling (GLMM, ZINB)
│ ├── report.py # Visualization and PDF generation
│ ├── generate_master_dataset.py # Orchestration for dataset creation
│ ├── utils/
│ │ ├── github_client.py # GitHub API client with retry logic
│ │ ├── metrics.py # Cognitive load proxy calculations
│ │ └── data_validation.py # PII scanning and schema validation
├── data/
│ ├── raw/ # Raw API responses (if cached)
│ └── derived/ # Processed datasets and analysis results
├── docs/
│ ├── output/ # Final reports and figures
│ └── README.md # This file
├── specs/
│ └── 001-evaluating-the-impact-of-llm-based-code-completion/
│ ├── plan.md # Research plan and methodology
│ └── spec.md # Functional requirements
├── tests/ # Test suite (pytest)
├── requirements.txt # Python dependencies
└── README.md
```

## Key Metrics Defined

- **`llm_adoption_flag`**: Boolean indicating if a repository uses LLM tools (based on `.cursorrules`, commit message frequency, or README mentions).
- **`iteration_count`**: Total number of push events between PR open and merge (no exclusions).
- **`diff_complexity_score`**: `(lines_added + lines_deleted) / total_lines` for commits with deletions. Used to flag "AI Noise".
- **`avg_comment_length`**: Average length of comments in review threads.
- **`review_thread_depth`**: Average depth of nested comments in review threads.

## Limitations & Theoretical Grounding

- **Proxy Metrics**: This study uses code repository metrics as proxies for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.
- **Observational Design**: Findings are associational, not causal.
- **Signal Separation**: The analysis attempts to distinguish between "solving the problem" load and "fixing AI's mess" load using `diff_complexity_score`.

## License

This research project is intended for academic use. Please refer to the repository license for details.
