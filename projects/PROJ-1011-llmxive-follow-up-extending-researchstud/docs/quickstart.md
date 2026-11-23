# Quick Start Guide

This guide walks you through setting up and running the llmXive automated research pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 8 GB RAM (7 GB minimum for pipeline execution) [UNRESOLVED-CLAIM: c_87b919dd — status=not_enough_info]
- Internet connection for data fetching

## Step 1: Clone and Setup

```bash
# Navigate to project root
cd PROJ-1011-llmxive-follow-up-extending-researchstud

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Initialize Project Structure

Create required directories and manifest:

```bash
python code/setup_data_dirs.py
```

This creates:
- `data/raw/`
- `data/processed/`
- `data/results/`
- `logs/`
- `state/`

## Step 3: Configure Data Sources

Edit `data-sources.yaml` to specify:
- arXiv categories (`cat:cs.LG`, `cat:q-bio.QM`)
- Non-ML DOI lists or API endpoints
- Acceptance status filters

Example configuration:

```yaml
sources:
 arxiv:
 endpoint: ""
 categories:
 - "cs.LG"
 - "q-bio.QM"
 max_results: 1000
 nature_climate:
 endpoint: " Connection refused"))]"
 doi_list: [""]
 health_affairs:
 endpoint: "https://www.healthaffairs.org/do/"
 doi_list: [""]
```

## Step 4: Run Data Acquisition (US1)

```bash
python code/01_data_acquisition.py
```

**What this does**:
- Fetches abstracts from arXiv and non-ML sources
- Validates acceptance status
- Streams and samples to ~500 records (balanced domains) [UNRESOLVED-CLAIM: c_d85ee05f — status=not_enough_info]
- Saves to `data/processed/corpus.jsonl`

**Expected output**:
- `data/raw/corpus_raw.jsonl`: Raw fetched data
- `data/processed/corpus.jsonl`: Cleaned corpus with metadata
- `logs/data_acquisition.log`: Execution logs

**Validation**:
```bash
pytest tests/unit/test_data_parsing.py -v
pytest tests/unit/test_memory_usage_constraint.py -v
pytest tests/unit/test_preprocessing_validation.py -v
pytest tests/unit/test_data_sources_config.py -v
```

## Step 5: Pattern Mapping (US2 - Part 1)

```bash
python code/02_pattern_mapping.py
```

**What this does**:
- Loads pattern cards
- Generates embeddings using quantized `all-MiniLM-L6-v2`
- Retrieves top-3 patterns for each problem statement [UNRESOLVED-CLAIM: c_a71ff94d — status=not_enough_info]
- Validates two-group design

**Expected output**:
- Pattern mappings in memory (or cached)
- `data/processed/holdout_patterns.json`: Hold-out validation set

**Validation**:
```bash
pytest tests/unit/test_pattern_mapping_validation.py -v
```

## Step 6: Generate Power Analysis Report (US2 - Prerequisite)

```bash
python code/utils/power_analysis.py
```

**What this does**:
- Calculates required sample size for medium effect size (d=0.5) [UNRESOLVED-CLAIM: c_d5d46106 — status=not_enough_info]
- Justifies n=50 pairs with 3 raters [UNRESOLVED-CLAIM: c_4cb0839c — status=not_enough_info]
- Outputs to `data/results/power_analysis_report.md`

**Expected output**:
- `data/results/power_analysis_report.md`: Sample size justification

## Step 7: Proposal Generation (US2 - Part 2)

```bash
python code/03_proposal_generation.py
```

**What this does**:
- Reads sample size `n` from power analysis report
- Generates pattern-guided proposals
- Generates baseline proposals
- Pairs and saves results

**Expected output**:
- `data/results/generated_proposals.jsonl`: Paired proposals (stripped metadata)

**Validation**:
```bash
pytest tests/unit/test_proposal_generation_logic.py -v
```

## Step 8: Evaluation Setup (US3 - Part 1)

```bash
python code/04_evaluation_recruitment.py
```

**What this does**:
- Generates recruitment job payload
- Creates blinded ratings template
- Validates expert roster

**Expected output**:
- `data/results/recruitment_payload.json`: Job posting data
- `data/results/recruitment_instructions.md`: Manual posting guide
- `data/results/ratings_template.csv`: Blinded evaluation template

**Manual Step**:
- Post recruitment job using generated payload
- Distribute `ratings_template.csv` to verified experts
- Collect filled ratings to `data/results/ratings_filled.csv`

## Step 9: Statistical Analysis (US3 - Part 2)

```bash
python code/05_statistical_analysis.py
```

**What this does**:
- Loads expert ratings
- Calculates Krippendorff's alpha (gate: ≥0.6) [UNRESOLVED-CLAIM: c_45062b51 — status=not_enough_info]
- Performs normality check
- Runs paired t-test or Wilcoxon signed-rank
- Conducts sensitivity analysis (outlier removal)
- Applies multiple comparison correction
- Generates final report

**Expected output**:
- `data/results/validity_metrics.json`: Effect sizes and p-values
- `data/results/sensitivity_analysis_report.md`: Robustness analysis
- `data/results/analysis_report.md`: Final report with "associational, not causal"

**Validation**:
```bash
pytest tests/unit/test_inter_rater_reliability_gate.py -v
pytest tests/unit/test_statistical_normality_check.py -v
pytest tests/unit/test_multiple_comparison_correction.py -v
pytest tests/unit/test_sensitivity_analysis.py -v
```

## Step 10: Benchmarking and Validation

```bash
# Profile runtime and memory
python code/utils/benchmark_profiler.py

# Validate against 6-hour constraint
python code/utils/benchmark_validator.py
```

**Expected output**:
- `data/results/benchmark_log.json`: Performance metrics
- Exit code 0 if <6 hours, 1 if exceeded [UNRESOLVED-CLAIM: c_c58542bb — status=not_enough_info]

## Step 11: Final Manifest Update

```bash
python code/utils/manifest_updater.py
```

**What this does**:
- Scans all artifacts
- Calculates checksums
- Updates `state/manifest.yaml`

**Expected output**:
- `state/manifest.yaml`: Final artifact checksums

## Troubleshooting

### Memory Errors

If you encounter memory errors:
1. Ensure `streaming=True` is used in data loading
2. Check that `all-MiniLM-L6-v2` is quantized
3. Verify batch sizes in `code/utils/batch_config.py`

### Data Fetch Failures

If data fetching fails:
1. Check `data-sources.yaml` for correct endpoints
2. Verify network connectivity
3. Review `logs/data_acquisition.log` for specific error context

### IRR Gate Failure

If Krippendorff's alpha < 0.6:
1. Check expert roster for verified status
2. Ensure ratings are collected for all pairs
3. Consider recruiting additional raters

### Power Constraint Violation

If n drops below 30 after outlier removal [UNRESOLVED-CLAIM: c_d26ee18b — status=not_enough_info]:
1. Review `data/results/sensitivity_analysis_report.md`
2. Flag results as "underpowered" in final report
3. Do not proceed to conclusions without flag

## Next Steps

- Review `data/results/analysis_report.md` for findings
- Share `state/manifest.yaml` for reproducibility
- Consider extending with additional domains or patterns

## Support

For issues or questions:
1. Check `docs/README.md` for architecture overview
2. Review `docs/pipeline_architecture.md` for component details
3. Inspect `logs/` for execution traces
