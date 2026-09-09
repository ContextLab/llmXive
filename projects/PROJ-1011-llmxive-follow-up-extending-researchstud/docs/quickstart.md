# llmXive Quickstart Guide

## Overview

This guide provides a complete walkthrough of the llmXive research pipeline, from data acquisition to statistical analysis. The pipeline implements a two-group experimental design to evaluate the effectiveness of pattern-guided research proposal generation.

## Prerequisites

- Python 3.11+
- 7GB+ available RAM
- pip-installed dependencies (see `requirements.txt`)
- Access to arXiv API (no authentication required)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-1011-llmxive-follow-up-extending-researchstud

# Install dependencies
pip install -r requirements.txt

# Initialize project structure
python code/setup_project_structure.py
python code/setup_data_dirs.py
```

## Quick Start

### 1. Data Acquisition (Phase 3)

Download and preprocess abstracts from ML and non-ML domains:

```bash
python code/01_data_acquisition.py
```

This produces:
- `data/raw/corpus_raw.jsonl` - Raw fetched data
- `data/processed/corpus.jsonl` - Preprocessed, normalized data

**Expected runtime**: 5-10 minutes

### 2. Pattern Mapping (Phase 4)

Map problem statements to ideation patterns:

```bash
python code/02_pattern_mapping.py
```

This produces:
- `data/processed/pattern_map.json` - Pattern similarity mappings
- `data/processed/holdout_patterns.json` - Hold-out validation set

**Expected runtime**: 2-5 minutes

### 3. Proposal Generation (Phase 4)

Generate paired research proposals (pattern-guided vs baseline):

```bash
python code/03_proposal_generation.py
```

This produces:
- `data/results/generated_proposals.jsonl` - Generated proposals with metadata

**Expected runtime**: 30-60 minutes (depending on LLM API latency)

### 4. Evaluation Setup (Phase 5)

Generate recruitment materials:

```bash
python code/04_evaluation_recruitment.py --mode generate
```

This produces:
- `data/results/recruitment_payload.json` - Job posting payload
- `data/results/recruitment_instructions.md` - Manual posting guide
- `data/results/ratings_template.csv` - Blinded rating template

**Note**: Expert recruitment is a manual process. Follow the instructions to post the job and collect ratings.

### 5. Statistical Analysis (Phase 5)

After collecting expert ratings in `data/results/ratings_filled.csv`:

```bash
python code/05_statistical_analysis.py
```

This produces:
- `data/results/analysis_report.md` - Final statistical report
- `data/results/validity_metrics.json` - Quantitative metrics
- `data/results/sensitivity_analysis_report.md` - Robustness analysis

**Expected runtime**: 1-5 minutes

## Validation

Run the integration test suite to verify the entire pipeline:

```bash
python code/99_run_quickstart_validation.py
```

This validates:
- All artifacts exist and have correct structure
- Checksums match the manifest
- Memory constraints are met
- Two-group design is enforced
- Required rhetorical constraints are present

## Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw Corpus | `data/raw/corpus_raw.jsonl` | Fetched abstracts |
| Processed Corpus | `data/processed/corpus.jsonl` | Normalized data |
| Pattern Map | `data/processed/pattern_map.json` | Similarity mappings |
| Generated Proposals | `data/results/generated_proposals.jsonl` | Proposal pairs |
| Expert Ratings | `data/results/ratings_filled.csv` | Collected ratings |
| Analysis Report | `data/results/analysis_report.md` | Final results |
| Validity Metrics | `data/results/validity_metrics.json` | Quantitative summary |

## Troubleshooting

### Memory Errors

If you encounter memory errors:
1. Ensure you have at least 7GB free RAM
2. The pipeline uses streaming/chunking by default
3. Check logs in `logs/data_acquisition.log` for specific errors

### API Errors

If arXiv API fails:
1. Check network connectivity
2. Verify `data-sources.yaml` configuration
3. The pipeline will fail loudly with a clear error message

### Missing Artifacts

If artifacts are missing:
1. Check `state/manifest.yaml` for expected files
2. Re-run the failed phase
3. Verify checksums with `python code/99_run_quickstart_validation.py`

## Next Steps

After completing the quickstart:
1. Review `data/results/analysis_report.md` for findings
2. Examine `data/results/validity_metrics.json` for effect sizes
3. Consider extending the study with additional domains or larger samples
4. Read the full documentation in `docs/` for detailed methodology

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review error messages in console output
- Consult the API documentation in `code/` module docstrings
