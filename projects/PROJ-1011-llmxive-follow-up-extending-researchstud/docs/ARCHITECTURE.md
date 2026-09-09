# llmXive Pipeline Architecture

## Overview

The llmXive pipeline is an automated scientific research system designed to extend research ideas from existing literature (specifically "ResearchStudio-Idea") into new, pattern-guided proposals. The system ingests academic abstracts, maps them to ideation patterns, generates new research proposals, and facilitates expert evaluation.

## System Architecture

```
PROJ-1011-llmxive-follow-up-extending-researchstud/
├── code/ # Core implementation
│ ├── 01_data_acquisition.py # Corpus ingestion (arXiv, DOI sources)
│ ├── 02_pattern_mapping.py # Pattern extraction and mapping
│ ├── 02_pattern_validation.py # Two-group design enforcement
│ ├── 03_proposal_generation.py # Proposal generation (pattern vs baseline)
│ ├── 04_evaluation_recruitment.py # Expert rating management
│ ├── 04_pairing_and_output.py # Proposal pairing and metadata stripping
│ ├── models/ # Data models (Abstract, PatternCard, Proposal, Rating)
│ ├── utils/ # Shared utilities
│ │ ├── config.py # Seed pinning, model selection, fallback logic
│ │ ├── data_manifest.py # Checksum tracking and artifact versioning
│ │ ├── data_sources_validator.py # Configuration validation
│ │ ├── error_handling.py # Strict failure on data fetch errors
│ │ ├── logging_config.py # Centralized logging with PII filtering
│ │ ├── memory_optimizer.py # Memory profiling and constraints
│ │ ├── pii_sanitizer.py # PII detection and removal
│ │ ├── update_state.py # Artifact state management
│ │ ├── power_analysis.py # Statistical power justification
│ │ ├── batch_config.py # Batch processing configuration
│ │ ├── benchmark_profiler.py # Runtime/memory profiling
│ │ ├── caching.py # Intermediate result caching
│ │ └── benchmark_validator.py # 6-hour runtime constraint check
│ └── 05_statistical_analysis.py # IRR, hypothesis testing, sensitivity analysis
├── data/ # Data storage
│ ├── raw/ # Raw fetched data (corpus_raw.jsonl)
│ ├── processed/ # Preprocessed data (corpus.jsonl, holdout_patterns.json)
│ └── results/ # Analysis outputs (proposals, ratings, reports)
├── tests/ # Unit and integration tests
├── logs/ # Pipeline execution logs
├── state/ # Artifact versioning manifest
├── docs/ # Documentation
├── data-sources.yaml # External data source configuration
├── plan.md # Project plan and requirements
├── spec.md # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # Project overview
```

## Data Flow

1. **Acquisition (T011-T016)**:
 - Fetch abstracts from arXiv (cs.LG, q-bio.QM) and curated DOI lists
 - Validate fetch status (fail loudly on 403/404/paywall)
 - Stream and sample to manage memory (n=500 target, balanced domains)
 - Output: `data/raw/corpus_raw.jsonl` → `data/processed/corpus.jsonl`

2. **Pattern Mapping (T020-T023)**:
 - Encode abstracts using quantized `all-MiniLM-L6-v2`
 - Retrieve top-k patterns (cosine similarity ≥ 0.6)
 - Enforce two-group design (pattern-guided vs baseline)
 - Output: Pattern mappings and hold-out set

3. **Proposal Generation (T021-T024)**:
 - Generate pattern-guided proposals (injected pattern cards)
 - Generate baseline proposals (generic prompts)
 - Batch processing to stay within 7 GB RAM
 - Output: `data/results/generated_proposals.jsonl`

4. **Evaluation (T030-T038)**:
 - Recruit experts (manual workflow, ORCID verified)
 - Load blinded ratings from `ratings_filled.csv`
 - Calculate IRR (Krippendorff's α ≥ 0.6 gate)
 - Perform statistical tests (t-test/Wilcoxon, sensitivity analysis)
 - Output: `data/results/analysis_report.md`, `validity_metrics.json`

## Key Design Principles

### 1. Fail Loudly (Constitution Principle V)
- Data fetch errors (403, 404, paywall) raise `DataFetchError` with venue context
- No synthetic data fallbacks; pipeline halts on real source failure
- Memory constraints trigger explicit model fallbacks (configurable)

### 2. Reproducibility
- Seed pinning for numpy, torch, and python
- Checksum manifest for all artifacts (`state/manifest.yaml`)
- Versioned state tracking for intermediate results

### 3. Memory Efficiency
- Streaming data loading (`datasets.load_dataset(..., streaming=True)`)
- Batch processing with generator-based loaders
- Quantized embeddings (CPU-tractable)
- 6-hour runtime constraint enforced by `benchmark_validator.py`

### 4. Two-Group Design Integrity
- Explicit validation against 'random-pattern' references (T023, T023b)
- Static analysis to reject third-arm logic
- All generation outputs strictly labeled as 'pattern-guided' or 'baseline'

## Dependencies

- Python 3.11+
- `sentence-transformers` (quantized models)
- `datasets` (Hugging Face, streaming support)
- `statsmodels` (power analysis, statistical tests)
- `scipy` (statistical functions)
- `requests` (API interactions)
- `pyyaml` (configuration parsing)

## Execution

```bash
# Setup
python code/setup_project_structure.py
python code/setup_data_dirs.py

# Data Acquisition
python code/01_data_acquisition.py

# Pattern Mapping
python code/02_pattern_mapping.py

# Proposal Generation
python code/03_proposal_generation.py

# Evaluation (Manual recruitment step required)
python code/04_evaluation_recruitment.py

# Statistical Analysis
python code/05_statistical_analysis.py

# Validation
python code/utils/benchmark_validator.py
```

## Testing

Unit tests cover:
- Data parsing and validation (T017, T018a)
- Memory usage constraints (T018)
- Preprocessing validation (T019)
- Pattern mapping logic (T028)
- Proposal generation pairing (T029)
- Statistical normality checks (T039)
- Multiple comparison correction (T040)
- IRR gate enforcement (T041)
- Sensitivity analysis logic (T042)

Run tests:
```bash
pytest tests/unit/ -v
```

## Limitations

- Evaluation requires manual expert recruitment (not automated)
- Statistical conclusions are "associational, not causal"
- Power analysis assumes n=50 pairs, 3 raters, medium effect size (d≈0.5)
- Sensitivity analysis removes entire pairs if one member is an outlier
