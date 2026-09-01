# llmXive: Automated Science Pipeline

**Project ID**: PROJ-1011-llmxive-follow-up-extending-researchstud

## Overview

llmXive is an automated research pipeline designed to extend "ResearchStudio-Idea" by systematically acquiring scientific abstracts, mapping them to ideation patterns, generating research proposals, and performing statistical evaluation.

The pipeline enforces a strict two-group design (Pattern-Guided vs. Baseline) and adheres to the "fail loudly" principle for data acquisition to ensure reproducibility and data integrity.

## Features

- **Automated Corpus Acquisition**: Ingests abstracts from arXiv (ML), Nature Climate Change, and Health Affairs using configurable endpoints.
- **Pattern Mapping**: Uses `sentence-transformers` (quantized `all-MiniLM-L6-v2`) to map problem statements to research patterns.
- **Proposal Generation**: Generates paired research proposals (pattern-guided vs. baseline) with memory-efficient batch processing.
- **Expert Evaluation**: Supports blinded expert rating ingestion with strict Inter-Rater Reliability (IRR) gates.
- **Statistical Analysis**: Performs power analysis, sensitivity analysis (IQR-based outlier removal), and multiple-comparison correction.
- **Benchmarking**: Enforces a total runtime constraint of ≤ 6 hours via profiling and caching.

## Project Structure

```text
.
├── code/
│ ├── 01_data_acquisition.py # Data fetching, streaming, and preprocessing
│ ├── 02_pattern_mapping.py # Embedding generation and pattern retrieval
│ ├── 02_pattern_validation.py # Two-group design enforcement
│ ├── 03_proposal_generation.py # LLM-based proposal generation (batched)
│ ├── 04_evaluation_recruitment.py # Expert roster validation and rating ingestion
│ ├── 05_statistical_analysis.py # Statistical tests, IRR, sensitivity analysis
│ ├── models/ # Data models (Abstract, PatternCard, Proposal, Rating)
│ └── utils/ # Configuration, logging, caching, benchmarking
├── data/
│ ├── raw/ # Raw fetched JSONL data
│ ├── processed/ # Normalized and filtered data
│ └── results/ # Generated proposals, ratings, analysis reports
├── docs/
│ ├── README.md # This file
│ └── API.md # Detailed API documentation
├── tests/
│ └── unit/ # Unit tests for pipeline components
├── state/
│ └── manifest.yaml # Artifact versioning and checksums
├── requirements.txt
└── pyproject.toml
```

## Prerequisites

- Python 3.11+
- `pip` for dependency management
- Access to the internet for initial data fetching (if not cached)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-1011-llmxive-follow-up-extending-researchstud
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Configure environment**:
 - Ensure `data-sources.yaml` is present in the project root or configured path.
 - Set environment variables for API keys if required by specific data sources (e.g., Prolific).

## Usage

### 1. Setup Infrastructure
Initialize directory structures and state management:
```bash
python code/setup_project_structure.py
python code/setup_data_dirs.py
```

### 2. Data Acquisition (User Story 1)
Fetch and preprocess abstracts:
```bash
python code/01_data_acquisition.py
```
*Output*: `data/processed/corpus.jsonl`

### 3. Pattern Mapping (User Story 2)
Generate embeddings and map patterns:
```bash
python code/02_pattern_mapping.py
```

### 4. Proposal Generation (User Story 2)
Generate pattern-guided and baseline proposals:
```bash
python code/03_proposal_generation.py
```
*Output*: `data/results/generated_proposals.jsonl`

### 5. Evaluation & Analysis (User Story 3)
Load expert ratings and perform statistical analysis:
```bash
python code/04_evaluation_recruitment.py # Ingest ratings
python code/05_statistical_analysis.py # Run analysis
```
*Output*: `data/results/analysis_report.md`, `data/results/validity_metrics.json`

## Configuration

Key configuration files:
- `data-sources.yaml`: Defines API endpoints, DOIs, and fetch parameters.
- `code/utils/config.py`: Contains seed pinning, model fallback logic, and environment settings.
- `state/manifest.yaml`: Tracks artifact versions and checksums.

## Testing

Run the unit test suite:
```bash
pytest tests/unit/ -v
```

Key test modules:
- `test_data_sources_config.py`: Validates configuration loading.
- `test_memory_usage_constraint.py`: Ensures batch processing stays within 7GB RAM.
- `test_sensitivity_analysis.py`: Verifies outlier removal logic.
- `test_inter_rater_reliability_gate.py`: Enforces Krippendorff's alpha threshold.

## Constraints & Principles

- **Fail Loudly**: The pipeline halts immediately on data fetch errors (403/404) or paywall detection. No synthetic data fallbacks are permitted.
- **Two-Group Design**: Strict enforcement of Pattern-Guided vs. Baseline; random-pattern arms are rejected.
- **Memory Efficiency**: Batch processing and streaming are mandatory for large datasets.
- **Runtime Limit**: Total pipeline execution must not exceed 6 hours.

## License

[Insert License Information Here]
