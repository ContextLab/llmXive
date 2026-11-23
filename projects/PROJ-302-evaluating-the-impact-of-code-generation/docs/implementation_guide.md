# Implementation Guide

This guide provides detailed information for developers implementing and extending the research pipeline.

## Architecture Overview

The pipeline follows a modular, stage-based architecture:

```
[Data Acquisition] → [Feature Extraction] → [Analysis] → [Visualization] → [Reporting]
```

Each stage is implemented as independent Python modules that can be executed sequentially or in parallel (where dependencies allow).

## Module Structure

### Data Acquisition (`code/data_acquisition/`)

- **github_scraper.py**: Fetches PR metadata and file content from GitHub API
- **synthetic_generator.py**: Generates synthetic LLM code snippets (CPU-tractable)
- **classifier_runner.py**: Classifies code snippets as "LLM-like" or "Human"
- **prompt_cohort_generator.py**: Generates prompt-based LLM code cohort

Key Functions:
- `fetch_pr_metadata_and_files()`: Fetches complete PR data
- `run_synthetic_generation()`: Generates code with timeout handling
- `run_classification_pipeline()`: Batch classification of snippets

### Feature Extraction (`code/feature_extraction/`)

- **complexity.py**: Calculates LOC and cyclomatic complexity using radon
- **timestamps.py**: Extracts review duration from PR timestamps
- **style_features.py**: Computes style metrics for classification
- **semantic_similarity.py**: Calculates semantic similarity (diagnostic only)
- **syntax_validator.py**: Validates Python syntax of code snippets
- **prompt_cohort_validator.py**: Validates prompt-generated code

Key Functions:
- `calculate_snippet_complexity()`: Returns complexity metrics
- `calculate_review_duration()`: Computes time from open to first comment
- `extract_semantic_similarity_scores()`: Returns similarity scores

### Analysis (`code/analysis/`)

- **matching.py**: Propensity score matching implementation
- **statistical_test.py**: Statistical testing (t-test, Mann-Whitney)
- **sensitivity.py**: Sensitivity analysis across strata
- **visualization.py**: Plot generation
- **report_generator.py**: HTML/PDF report generation
- **deviation_report_generator.py**: Documents methodological deviations
- **prompt_cohort_matching.py**: Matching for prompt-based cohort

Key Functions:
- `estimate_propensity_scores()`: Logistic regression for propensity scores
- `perform_matching()`: Nearest-neighbor matching
- `run_full_analysis()`: Complete statistical testing pipeline
- `run_sensitivity_analysis()`: Stratified analysis

### Utilities (`code/utils/`)

- **config.py**: Global configuration, random seeds, paths
- **models.py**: Data classes (PullRequest, CodeSnippet)
- **rate_limiter.py**: API rate limiting with exponential backoff
- **validators.py**: Schema validation and PII scanning

## Error Handling

### Timeout Handling
Generation tasks (T014b, T033) implement timeout handlers:
```python
try:
 result = generate_snippet_with_timeout(prompt, timeout=10)
except TimeoutError:
 create_spec_amendment_request("Generation timeout")
 sys.exit(1)
```

### Matching Failure
If balance cannot be achieved after 3 retries:
```python
if smd > 0.1:
 generate_matching_failure_report(smd_values, retry_count)
 sys.exit(1)
```

### Syntax Validation
Generated snippets must achieve ≥95% valid syntax rate:
```python
valid_rate = validate_dataset(snippets)
if valid_rate < 0.95:
 raise ValidationError(f"Syntax validation failed: {valid_rate:.2%}")
```

## Logging

All modules use Python's logging module with structured output:
```python
import logging
logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

## Testing Strategy

### Contract Tests
Validate API contracts and data schemas:
- `tests/contract/test_github_scraper.py`
- `tests/contract/test_matching.py`
- `tests/contract/test_sensitivity.py`

### Integration Tests
Verify end-to-end pipeline functionality:
- `tests/integration/test_synthetic_generator.py`
- `tests/integration/test_statistical_test.py`
- `tests/integration/test_visualization.py`

### Unit Tests
Test individual functions and classes:
- `tests/unit/test_complexity.py`
- `tests/unit/test_timestamps.py`
- `tests/unit/test_matching.py`

## Dependency Management

All dependencies are pinned in `requirements.txt`:
```
datasets==2.14.0
scikit-learn==1.3.0
pandas==2.0.3
numpy==1.24.3
scipy==1.11.1
radon==6.0.1
torch==2.0.1
transformers==4.31.0
matplotlib==3.7.2
seaborn==0.12.2
pyyaml==6.0.1
requests==2.31.0
gitpython==3.1.32
```

## Performance Considerations

### Memory Management
- Use streaming for large datasets: `load_dataset(..., streaming=True)`
- Process in chunks when possible
- Release memory after each stage: `gc.collect()`

### Runtime Targets
- Full pipeline: ≤6 hours on standard hardware
- Data acquisition: ~2 hours (depends on API rate limits)
- Feature extraction: ~1 hour
- Analysis: ~30 minutes
- Visualization: ~10 minutes

### Parallelization
Parallel opportunities:
- All Phase 1 setup tasks
- All foundational tasks
- Feature extraction (independent metrics)
- Sensitivity analysis strata

## Extending the Pipeline

### Adding New Features
1. Create new module in appropriate directory
2. Implement `main()` function with argument parsing
3. Add to `requirements.txt` if new dependencies needed
4. Write contract and integration tests
5. Update `docs/` documentation

### Custom Analysis
1. Extend `code/analysis/` with new module
2. Implement `run_custom_analysis()` function
3. Integrate into `report_generator.py`
4. Document in `docs/research_methodology.md`

## Troubleshooting

### Common Issues

**GitHub API Rate Limit**
- Solution: Ensure token is set, implement backoff (already in `rate_limiter.py`)

**Memory Errors**
- Solution: Use streaming, reduce batch size, increase RAM

**Generation Failures**
- Solution: Check timeout settings, verify model availability, review `spec_amendment_request.md`

**Matching Imbalance**
- Solution: Review covariates, check data quality, examine `matching_failure_report.json`

**Syntax Validation Failures**
- Solution: Improve generation prompts, check model version, review `spec_amendment_request.md`

## Security Considerations

- PII scanning is enforced via `utils/validators.py`
- API tokens should never be committed to version control
- All external data is validated before processing
- Rate limiting prevents API abuse

## Version Control

- Use semantic versioning for releases
- Commit after each task completion
- Tag releases with version numbers
- Maintain changelog in `docs/CHANGELOG.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request
6. Ensure all tests pass before merge
