# llmXive Research Workflow Guide

## Overview

This document describes the end-to-end workflow for executing the llmXive pipeline, from data acquisition to final statistical analysis. The workflow is designed to be reproducible, memory-efficient, and compliant with strict data integrity constraints.

## Prerequisites

- Python 3.11+
- 7 GB+ available RAM (for CPU-based embedding)
- Internet access for data fetching
- ORCID credentials for expert recruitment (manual step)

## Step-by-Step Workflow

### 1. Project Setup

Initialize the project structure and data directories:

```bash
# Clone and setup
cd PROJ-1011-llmxive-follow-up-extending-researchstud

# Install dependencies
pip install -r requirements.txt

# Create directory structure
python code/setup_project_structure.py
python code/setup_data_dirs.py
```

**Outputs**:
- `code/`, `data/`, `tests/`, `logs/`, `state/` directories
- `data/raw/`, `data/processed/`, `data/results/` subdirectories
- `state/manifest.yaml` (initial checksum manifest)

### 2. Data Acquisition (User Story 1)

Fetch abstracts from arXiv and curated DOI sources:

```bash
python code/01_data_acquisition.py
```

**Configuration**:
- Edit `data-sources.yaml` to specify arXiv categories and DOI lists
- Target: Balanced sample of ML (cs.LG, q-bio.QM), Non-ML Accepted, Non-ML Rejected

**Process**:
1. Validate `data-sources.yaml` (T009a)
2. Stream arXiv API results (paginated, acceptance status filtered)
3. Stream DOI entries from *Nature Climate Change* and *Health Affairs*
4. Apply strict fetch validation (T012): fail on 403/404/paywall
5. Stream and sample to `n=500` (T014) with domain balance check (T014a)
6. Preprocess: normalize text, filter malformed entries (T013)
7. Save to `data/raw/corpus_raw.jsonl` and `data/processed/corpus.jsonl`

**Outputs**:
- `data/raw/corpus_raw.jsonl`: Raw fetched data
- `data/processed/corpus.jsonl`: Cleaned, normalized data with metadata

**Validation**:
- Unit tests: `tests/unit/test_data_parsing.py`, `test_preprocessing_validation.py`
- Memory constraint test: `tests/unit/test_memory_usage_constraint.py`

### 3. Pattern Mapping (User Story 2 - Part 1)

Extract and map ideation patterns from the corpus:

```bash
python code/02_pattern_mapping.py
```

**Configuration**:
- Model: `all-MiniLM-L6-v2` (quantized for CPU)
- Fallback model: Configurable via `FALLBACK_EMBEDDING_MODEL` in `config.py` (T008a)
- Similarity threshold: 0.6
- Top-k patterns: 3

**Process**:
1. Load `data/processed/corpus.jsonl`
2. Encode abstracts using quantized sentence-transformer
3. Compute cosine similarity matrix
4. Retrieve top-k patterns for each abstract
5. Generate hold-out set for validation (T020b)

**Outputs**:
- `data/processed/holdout_patterns.json`: Hold-out pattern set
- Pattern mappings stored in memory or cache

**Validation**:
- Unit test: `tests/unit/test_pattern_mapping_validation.py`

### 4. Proposal Generation (User Story 2 - Part 2)

Generate pattern-guided and baseline proposals:

```bash
python code/03_proposal_generation.py
```

**Configuration**:
- Sample size: Read from `data/results/power_analysis_report.md` (T024a)
- Batch size: Configurable via `utils/batch_config.py`
- Two-group design: Strict enforcement (T023, T023b)

**Process**:
1. Run power analysis (T024a): Justify n=50 pairs, 3 raters, d≈0.5
2. Load processed corpus and pattern mappings
3. Generate pattern-guided proposals (injected pattern cards) (T021)
4. Generate baseline proposals (generic prompts) (T022)
5. Validate two-group design (no 'random-pattern' references) (T023)
6. Pair proposals and strip metadata for evaluation
7. Save to `data/results/generated_proposals.jsonl`

**Outputs**:
- `data/results/power_analysis_report.md`: Sample size justification
- `data/results/generated_proposals.jsonl`: Paired proposals (pattern-guided + baseline)

**Validation**:
- Unit test: `tests/unit/test_proposal_generation_logic.py`
- Static analysis: `code/utils/validate_design.py` (T023b)

### 5. Evaluation Recruitment (User Story 3 - Part 1)

Prepare and execute expert recruitment (manual workflow):

```bash
# Generate recruitment payload and instructions
python code/04_evaluation_recruitment.py --mode=payload
```

**Process**:
1. Load `data/results/generated_proposals.jsonl`
2. Generate blinded `ratings_template.csv` (T030c-manual)
3. Create `recruitment_payload.json` and `recruitment_instructions.md` (T030a-manual)
4. **Manual Step**: Post job on crowdsourcing platform (e.g., Prolific)
5. **Manual Step**: Verify ORCIDs and experience (≥5 years)
6. Populate `data/results/expert_roster.csv` with verified experts (T030a-execute)
7. **Manual Step**: Distribute blinded template to experts
8. **Manual Step**: Collect filled `ratings_filled.csv`

**Outputs**:
- `data/results/recruitment_payload.json`: API payload for job posting
- `data/results/recruitment_instructions.md`: Manual posting guide
- `data/results/expert_roster.csv`: Verified expert list
- `data/results/ratings_template.csv`: Blinded rating template
- `data/results/ratings_filled.csv`: Collected expert ratings

**Validation**:
- Input validation: `validate_expert_inputs()` (T030b)
- Schema check: Row count and column validation (T030)

### 6. Statistical Analysis (User Story 3 - Part 2)

Analyze expert ratings and generate final report:

```bash
python code/05_statistical_analysis.py
```

**Process**:
1. Load `ratings_filled.csv` (blinded, ORCID verified)
2. Calculate Krippendorff's alpha (IRR gate: α ≥ 0.6) (T032)
 - **Fail** if α < 0.6
3. Perform normality check on mean scores (T033)
4. Select test: Paired t-test (normal) or Wilcoxon signed-rank (non-normal) (T034)
5. Sensitivity analysis:
 - Identify outliers using IQR method (T035a)
 - Remove entire pairs if one member is an outlier
 - Re-run statistical test on cleaned data
 - Check power: Flag if n < 30 or power < 0.8 (T035b)
6. Apply multiple-comparison correction (Bonferroni or BH) (T035)
7. Calculate validity improvement (contextual alignment) (T036)
8. Generate final report with "associational, not causal" phrase (T037, T037a)

**Outputs**:
- `data/results/sensitivity_analysis_report.md`: Pre/post p-values, effect sizes
- `data/results/validity_metrics.json`: Mean difference in alignment scores
- `data/results/analysis_report.md`: Final statistical report

**Validation**:
- Unit tests: `test_statistical_normality_check.py`, `test_multiple_comparison_correction.py`, `test_inter_rater_reliability_gate.py`, `test_sensitivity_analysis.py`

### 7. Benchmarking and Validation

Verify runtime and memory constraints:

```bash
# Profile runtime and memory
python code/utils/benchmark_profiler.py

# Validate 6-hour constraint
python code/utils/benchmark_validator.py
```

**Process**:
1. Profile each phase (data, generation, analysis)
2. Log results to `data/results/benchmark_log.json` (T045a)
3. Assert total runtime < 6 hours (T045c)
4. **Fail** build if threshold exceeded

**Outputs**:
- `data/results/benchmark_log.json`: Runtime/memory metrics
- Exit code 1 if constraint violated

## Error Handling

### Data Fetch Failures
- **403/404/Paywall**: `DataFetchError` raised with venue name and URL
- **Action**: Check `data-sources.yaml`, verify API access, halt pipeline

### Memory Constraints
- **Model fallback**: Switch to `FALLBACK_EMBEDDING_MODEL` (T008a)
- **Streaming**: Use chunked loading to stay within 7 GB RAM
- **Logging**: Model switch events logged to `logs/data_acquisition.log`

### IRR Gate Failure
- **Krippendorff's α < 0.6**: Pipeline halts, report insufficient rater agreement
- **Action**: Recruit additional experts, re-collect ratings

### Power Analysis Failure
- **n < 30 or power < 0.8**: Flag result as 'underpowered' (T035b)
- **Action**: Note limitation in final report, do not proceed to conclusion

## Troubleshooting

### "DataFetchError: Venue X returned 403"
- Check `data-sources.yaml` for correct endpoint
- Verify API key/authentication if required
- Contact venue administrator for access

### "MemoryError during embedding"
- Ensure quantized model is used (`all-MiniLM-L6-v2`)
- Check `FALLBACK_EMBEDDING_MODEL` configuration
- Reduce batch size in `utils/batch_config.py`

### "Krippendorff's alpha < 0.6"
- Recruit more experts (aim for ≥5)
- Check rating template clarity
- Verify rater training/instructions

### "Power analysis: n reduced below 30"
- Review sensitivity analysis outliers
- Consider relaxing outlier threshold (k*IQR)
- Note 'underpowered' flag in final report

## Best Practices

1. **Reproducibility**: Always run `set_seed(42)` before data loading
2. **Checksums**: Verify `state/manifest.yaml` after each phase
3. **Logging**: Check `logs/data_acquisition.log` for model switches and errors
4. **Manual Steps**: Document expert recruitment process in `recruitment_instructions.md`
5. **Validation**: Run unit tests after each major change
6. **Caching**: Use `utils/caching.py` to avoid redundant computation

## Next Steps

- Extend to additional domains (e.g., social sciences)
- Automate expert recruitment workflow
- Integrate with LLM for automated proposal refinement
- Deploy as a web service for collaborative research
