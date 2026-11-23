# llmXive: Automated Research Pipeline

**Project ID**: PROJ-1011-llmxive-follow-up-extending-researchstud

A reproducible, automated pipeline for extending research studies by mapping non-ML problem statements to ML-derived ideation patterns and evaluating the resulting proposals.

## Overview

This project implements a two-group experimental design to test whether pattern-guided proposal generation yields higher quality research ideas compared to a baseline. The pipeline ingests abstracts from ML and non-ML domains, maps problems to patterns, generates proposals, and performs statistical analysis on expert ratings.

## Architecture

The system is organized into six phases:

1. **Setup**: Project initialization and directory structure
2. **Foundational**: Core infrastructure (data models, state management, error handling)
3. **User Story 1 (P1)**: Corpus Acquisition and Pre-processing
4. **User Story 2 (P2)**: Pattern Mapping and Proposal Generation
5. **User Story 3 (P3)**: Expert Evaluation and Statistical Analysis
6. **Polish**: Benchmarking, caching, and documentation

## Directory Structure

```
PROJ-1011-llmxive-follow-up-extending-researchstud/
├── code/
│ ├── 01_data_acquisition.py # Data ingestion and preprocessing
│ ├── 02_pattern_mapping.py # Pattern retrieval and embedding
│ ├── 02_pattern_validation.py # Two-group design validation
│ ├── 03_proposal_generation.py # Proposal generation (pattern-guided & baseline)
│ ├── 04_evaluation_recruitment.py # Expert rating infrastructure
│ ├── 05_statistical_analysis.py # IRR, hypothesis testing, sensitivity analysis
│ ├── models/ # Data models (Abstract, PatternCard, Proposal, Rating)
│ ├── utils/ # Configuration, logging, error handling, benchmarking
│ └── setup_data_dirs.py # Directory initialization
├── data/
│ ├── raw/ # Raw fetched data (corpus_raw.jsonl)
│ ├── processed/ # Cleaned and normalized data (corpus.jsonl)
│ └── results/ # Generated proposals, ratings, analysis reports
├── tests/
│ └── unit/ # Unit tests for each component
├── docs/ # Documentation
├── state/ # Pipeline state and artifact manifest
├── logs/ # Execution logs
├── requirements.txt # Python dependencies
└── plan.md # Project plan and design
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone and navigate to project
cd PROJ-1011-llmxive-follow-up-extending-researchstud

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

1. **Initialize directories**:
 ```bash
 python code/setup_data_dirs.py
 ```

2. **Acquire and preprocess data** (US1):
 ```bash
 python code/01_data_acquisition.py
 ```
 This downloads abstracts from arXiv (ML) and non-ML sources, validates them, and saves to `data/processed/corpus.jsonl`.

3. **Pattern mapping and proposal generation** (US2):
 ```bash
 python code/02_pattern_mapping.py
 python code/03_proposal_generation.py
 ```
 Generates paired proposals (pattern-guided and baseline) saved to `data/results/generated_proposals.jsonl`.

4. **Evaluation and analysis** (US3):
 ```bash
 python code/04_evaluation_recruitment.py
 python code/05_statistical_analysis.py
 ```
 Performs IRR checks, statistical tests, and generates the final report in `data/results/analysis_report.md`.

### Running Tests

```bash
pytest tests/unit/ -v
```

### Benchmarking

The pipeline includes built-in benchmarking to ensure runtime stays under 6 hours:

```bash
python code/utils/benchmark_profiler.py
python code/utils/benchmark_validator.py
```

## Key Features

### Two-Group Design (FR-003)

The system strictly enforces a two-group design:
- **Pattern-guided**: Proposals generated using retrieved ML ideation patterns
- **Baseline**: Proposals generated using generic prompts

No "random-pattern" or third-arm logic is permitted. This is validated by `code/02_pattern_validation.py` and `code/utils/validate_design.py`.

### Fail-Loudly Data Fetching

Data acquisition is configured to fail immediately on:
- HTTP 403/404 errors
- Paywall detection
- Invalid API responses

Errors are logged with venue context and halt the pipeline. No synthetic data fallback is implemented.

### Memory Constraints

The pipeline is optimized for CPU execution with <7 GB RAM:
- Streaming data acquisition (`stream_and_sample`)
- Quantized sentence-transformers (`all-MiniLM-L6-v2`)
- Batch processing for proposal generation
- Memory profiling and garbage collection

### Statistical Rigor

- **Power Analysis**: Justifies sample size (n=50 pairs, 3 raters) for medium effect size
- **Inter-Rater Reliability**: Krippendorff's alpha gate (≥0.6)
- **Sensitivity Analysis**: Outlier removal with paired-difference preservation
- **Multiple Comparison Correction**: Bonferroni/Benjamini-Hochberg applied unconditionally
- **Power Check**: Flags results if n drops below threshold

## Configuration

### Data Sources

Configure data endpoints in `data-sources.yaml`:
- arXiv API for ML abstracts (`cat:cs.LG`, `cat:q-bio.QM`)
- DOI lists/APIs for *Nature Climate Change* and *Health Affairs*

### Model Fallback

Embedding model fallback is configurable via `FALLBACK_EMBEDDING_MODEL` in `code/utils/config.py`. Memory errors trigger automatic switching with explicit logging.

## Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw corpus | `data/raw/corpus_raw.jsonl` | Fetched abstracts |
| Processed corpus | `data/processed/corpus.jsonl` | Normalized, validated data |
| Generated proposals | `data/results/generated_proposals.jsonl` | Paired proposals (stripped metadata) |
| Power analysis | `data/results/power_analysis_report.md` | Sample size justification |
| Expert ratings | `data/results/ratings_filled.csv` | Collected expert evaluations |
| Sensitivity report | `data/results/sensitivity_analysis_report.md` | Outlier analysis impact |
| Final report | `data/results/analysis_report.md` | Statistical results with "associational, not causal" |
| Benchmark log | `data/results/benchmark_log.json` | Runtime/memory profiling |
| Manifest | `state/manifest.yaml` | Artifact checksums |

## Contributing

1. Create a feature branch
2. Implement changes following the existing API surface
3. Run tests: `pytest tests/unit/ -v`
4. Validate benchmark: `python code/utils/benchmark_validator.py`
5. Submit a pull request

## License

Research use only. See LICENSE file for details.

## Acknowledgments

This project extends the ResearchStudio-Idea framework and follows the Constitution Principles for automated science pipelines.
