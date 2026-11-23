# llmXive: Automated Research Pipeline

**Project ID**: PROJ-1011-llmxive-follow-up-extending-researchstud

A reproducible, automated pipeline for extending research studies by mapping non-ML problem statements to ML-derived ideation patterns and evaluating the resulting proposals.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Research Use](https://img.shields.io/badge/license-research%20use-red.svg)](LICENSE)

## Overview

This project implements a two-group experimental design to test whether pattern-guided proposal generation yields higher quality research ideas compared to a baseline. The pipeline:

1. **Ingests** abstracts from ML (arXiv) and non-ML (Nature Climate Change, Health Affairs) domains
2. **Maps** non-ML problems to ML-derived ideation patterns
3. **Generates** paired proposals (pattern-guided vs. baseline)
4. **Evaluates** proposals via expert ratings
5. **Analyzes** results with rigorous statistical methods

## Quick Start

```bash
# Clone and setup
cd PROJ-1011-llmxive-follow-up-extending-researchstud
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize directories
python code/setup_data_dirs.py

# Run pipeline
python code/01_data_acquisition.py
python code/02_pattern_mapping.py
python code/03_proposal_generation.py
python code/04_evaluation_recruitment.py
python code/05_statistical_analysis.py
```

See [`docs/quickstart.md`](docs/quickstart.md) for detailed instructions.

## Key Features

### Two-Group Design (FR-003)

Strictly enforces pattern-guided vs. baseline comparison. No "random-pattern" third arm.

### Fail-Loudly Data Fetching

Immediate halt on API errors (403/404/paywall) with venue context. No synthetic fallback.

### Memory Optimization

CPU-tractable with <7 GB RAM:
- Streaming data acquisition
- Quantized embeddings (`all-MiniLM-L6-v2`)
- Batch processing

### Statistical Rigor

- Power analysis (n=50 pairs, d=0.5)
- IRR gate (Krippendorff's α ≥ 0.6)
- Sensitivity analysis with paired removal
- Multiple comparison correction

## Project Structure

```
PROJ-1011-llmxive-follow-up-extending-researchstud/
├── code/ # Pipeline implementation
│ ├── 01_data_acquisition.py # Data ingestion (US1)
│ ├── 02_pattern_mapping.py # Pattern retrieval (US2)
│ ├── 02_pattern_validation.py # Two-group enforcement
│ ├── 03_proposal_generation.py # Proposal generation (US2)
│ ├── 04_evaluation_recruitment.py # Expert ratings (US3)
│ ├── 05_statistical_analysis.py # Statistical tests (US3)
│ ├── models/ # Data models
│ └── utils/ # Configuration, logging, benchmarking
├── data/
│ ├── raw/ # Raw fetched data
│ ├── processed/ # Cleaned corpus
│ └── results/ # Proposals, ratings, reports
├── tests/ # Unit tests
├── docs/ # Documentation
├── state/ # Pipeline state & manifest
├── logs/ # Execution logs
├── requirements.txt # Dependencies
└── plan.md # Project plan
```

## Documentation

- [`docs/README.md`](docs/README.md): Full project overview
- [`docs/quickstart.md`](docs/quickstart.md): Step-by-step guide
- [`docs/pipeline_architecture.md`](docs/pipeline_architecture.md): Component details
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md): Development guidelines

## Configuration

### Data Sources

Edit `data-sources.yaml` to configure:
- arXiv categories (`cs.LG`, `q-bio.QM`)
- Non-ML DOI lists and endpoints

### Model Fallback

Configure `FALLBACK_EMBEDDING_MODEL` in `code/utils/config.py` for memory error handling.

## Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Validate benchmark constraint
python code/utils/benchmark_validator.py
```

## Output Artifacts

| File | Description |
|------|-------------|
| `data/processed/corpus.jsonl` | Cleaned abstract corpus |
| `data/results/generated_proposals.jsonl` | Paired proposals |
| `data/results/analysis_report.md` | Final statistical report |
| `state/manifest.yaml` | Artifact checksums |

## Constraints

- **Memory**: <7 GB RAM (CPU execution)
- **Runtime**: <6 hours total
- **Sample**: n=50 pairs (power-justified)
- **Data**: Real sources only; fail loudly on fetch errors

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for guidelines.

## License

Research use only. See [LICENSE](LICENSE) for details.

## Acknowledgments

Extends the ResearchStudio-Idea framework following Constitution Principles for automated science.