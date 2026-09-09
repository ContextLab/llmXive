# llmXive: Automated Scientific Research Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**llmXive** is an automated pipeline for extending existing research ideas into new, pattern-guided proposals. It ingests academic abstracts, maps them to ideation patterns, generates paired research proposals (pattern-guided vs. baseline), and facilitates expert evaluation to determine if pattern-guided proposals differ significantly from baseline.

## 🎯 Project Goal

Extend the "ResearchStudio-Idea" framework by:
1. Ingesting and preprocessing abstracts from ML and non-ML domains
2. Mapping problem statements to ML-derived ideation patterns
3. Generating paired research proposals (pattern-guided vs. baseline)
4. Facilitating expert evaluation with statistical validation

**Key Constraint**: All conclusions are "associational, not causal."

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- 7 GB+ available RAM (for CPU-based embedding)
- Internet access for data fetching
- ORCID credentials (for expert recruitment)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-1011-llmxive-follow-up-extending-researchstud

# Install dependencies
pip install -r requirements.txt

# Setup project structure
python code/setup_project_structure.py
python code/setup_data_dirs.py
```

### Running the Pipeline

```bash
# 1. Data Acquisition
python code/01_data_acquisition.py

# 2. Pattern Mapping
python code/02_pattern_mapping.py

# 3. Proposal Generation
python code/03_proposal_generation.py

# 4. Evaluation (Manual recruitment step required)
python code/04_evaluation_recruitment.py

# 5. Statistical Analysis
python code/05_statistical_analysis.py

# 6. Validation
python code/utils/benchmark_validator.py
```

### Testing

```bash
pytest tests/unit/ -v
```

## 📊 Data Flow

```
arXiv/DOI Sources
 ↓
[Acquisition] data/raw/corpus_raw.jsonl
 ↓
[Preprocessing] data/processed/corpus.jsonl
 ↓
[Pattern Mapping] data/processed/holdout_patterns.json
 ↓
[Proposal Generation] data/results/generated_proposals.jsonl
 ↓
[Expert Evaluation] data/results/ratings_filled.csv
 ↓
[Statistical Analysis] data/results/analysis_report.md
```

## 🔑 Key Features

### 1. Fail-Loudly Data Fetching
- Strict validation on 403/404/paywall errors
- No synthetic data fallbacks
- Clear error messages with venue context

### 2. Memory-Efficient Processing
- Streaming data loading (Hugging Face `datasets`)
- Quantized embeddings (CPU-tractable)
- Batch processing with generator-based loaders
- 6-hour runtime constraint enforcement

### 3. Two-Group Design Integrity
- Explicit validation against 'random-pattern' references
- Static analysis to reject third-arm logic
- All outputs strictly labeled as 'pattern-guided' or 'baseline'

### 4. Reproducibility
- Seed pinning for numpy, torch, python
- Checksum manifest for all artifacts
- Versioned state tracking

## 🧪 User Stories

### US1: Corpus Acquisition and Pre-processing (P1)
- Ingest abstracts from arXiv (cs.LG, q-bio.QM) and curated DOI lists
- Validate fetch status and preprocess text
- Output: Balanced sample of ML, Non-ML Accepted, Non-ML Rejected records

### US2: Pattern Mapping and Proposal Generation (P2)
- Map problem statements to ML-derived ideation patterns
- Generate paired proposals (pattern-guided vs. baseline)
- Enforce two-group design constraints

### US3: Expert Evaluation and Statistical Analysis (P3)
- Recruit domain experts (≥5 years experience)
- Aggregate ratings and perform statistical tests
- Output: Final report with p-values, effect sizes, and validity metrics

## 📁 Project Structure

```
PROJ-1011-llmxive-follow-up-extending-researchstud/
├── code/ # Core implementation
│ ├── 01_data_acquisition.py
│ ├── 02_pattern_mapping.py
│ ├── 03_proposal_generation.py
│ ├── 04_evaluation_recruitment.py
│ ├── 05_statistical_analysis.py
│ ├── models/ # Data models
│ └── utils/ # Shared utilities
├── data/ # Data storage
│ ├── raw/
│ ├── processed/
│ └── results/
├── tests/ # Unit tests
├── docs/ # Documentation
├── state/ # Artifact versioning
├── logs/ # Execution logs
├── data-sources.yaml # External data sources
├── plan.md # Project plan
├── spec.md # Feature specifications
└── README.md # This file
```

## ⚙️ Configuration

### data-sources.yaml
Define API endpoints and DOI lists:
```yaml
arxiv:
 categories:
 - cs.LG
 - q-bio.QM
 max_results: 500
 acceptance_filter: true

nature_climate_change:
 doi_list: [...]
 acceptance_status: true

health_affairs:
 doi_list: [...]
 acceptance_status: true
```

### config.py
Configure seeds, models, and fallbacks:
```python
SEED = 42
FALLBACK_EMBEDDING_MODEL = "all-MiniLM-L6-v2-quantized"
MAX_MEMORY_MB = 7000
```

## 🛡️ Safety & Constraints

- **No Synthetic Data**: Pipeline fails loudly on real source errors
- **PII Sanitization**: All outputs checked for personally identifiable information
- **Memory Limits**: 7 GB RAM constraint enforced with streaming and batching
- **Runtime Limit**: 6-hour maximum pipeline execution time
- **Two-Group Design**: No 'random-pattern' or third-arm logic allowed

## 📈 Statistical Methodology

- **Sample Size**: n=50 pairs, 3 raters (power analysis: d≈0.5, α=0.05, power≥0.8)
- **IRR Gate**: Krippendorff's α ≥ 0.6 (fail if lower)
- **Test Selection**: Paired t-test (normal) or Wilcoxon signed-rank (non-normal)
- **Sensitivity Analysis**: Remove entire pairs if one member is an outlier (IQR method)
- **Multiple Comparison Correction**: Bonferroni or Benjamini-Hochberg
- **Validity Statement**: All conclusions are "associational, not causal"

## 🧪 Testing

Unit tests cover:
- Data parsing and validation
- Memory usage constraints
- Preprocessing validation
- Pattern mapping logic
- Proposal generation pairing
- Statistical normality checks
- Multiple comparison correction
- IRR gate enforcement
- Sensitivity analysis logic

Run tests:
```bash
pytest tests/unit/ -v --cov=code
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Workflow Guide](docs/WORKFLOW.md)
- [API Reference](docs/API.md) (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Based on the "ResearchStudio-Idea" framework. Extended by the llmXive team.

## 📞 Contact

For questions or support, please open an issue in the repository.