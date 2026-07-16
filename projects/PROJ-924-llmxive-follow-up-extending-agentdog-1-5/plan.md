# Project Plan: llmXive Follow-up - Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview
This project extends the AgentDoG 1.5 framework with zero-shot drift detection capabilities.
The system will analyze LLM interaction logs to detect novel attack patterns by measuring
semantic distance from known benign taxonomy centroids.

## Objectives
1. Implement zero-shot drift scoring using cosine distance to taxonomy centroids
2. Create human-in-the-loop validation pipeline for stratified log analysis
3. Compare drift-based detection against zero-shot LLM classifier baselines
4. Ensure all processing respects memory constraints (<7GB RAM) and reproducibility

## Project Structure
```
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/
│ ├── config.py # Configuration management
│ ├── data_loader.py # Data fetching and validation
│ ├── drift_scoring.py # Core drift scoring logic
│ ├── taxonomy_builder.py # Centroid generation
│ ├── validation.py # Statistical validation
│ ├── annotator_interface.py # Human annotation workflow
│ ├── comparison.py # Baseline comparison
│ ├── utils.py # Utility functions
│ └── main.py # Orchestration script
├── data/
│ ├── raw/ # Raw downloaded data
│ │ ├── taxonomy.json # AgentDoG taxonomy definition
│ │ └── logs/ # Raw log data
│ ├── processed/ # Processed output files
│ │ ├── drift_scores.csv # Drift scores per log
│ │ ├── merged_annotations.csv
│ │ ├── simulated_ground_truth.csv
│ │ └── validation_stats.json
│ ├── test_static_logs.json # Static test fixtures
│ └── checksums.json # Data integrity tracking
├── tests/
│ ├── unit/ # Unit tests
│ │ ├── test_contracts.py
│ │ ├── test_drift_scoring.py
│ │ ├── test_validation.py
│ │ └── test_comparison.py
│ └── integration/ # Integration tests
│ └── test_end_to_end.py
├── contracts/
│ ├── drift_result.schema.yaml
│ └── safety_prompt_v1.txt
├── specs/
│ └── 001-llmxive-drift-detection/
│ ├── spec.md
│ └── data-model.md
├── docs/
│ ├── quickstart.md
│ └── api.md
├── requirements.txt
├── pyproject.toml # Tooling config (ruff, black)
├──.ruff.toml # Linting rules
└──.pre-commit-config.yaml # Pre-commit hooks
```

## Dependencies
- Python 3.11+
- sentence-transformers (embeddings)
- scikit-learn (metrics, clustering)
- pandas, numpy (data processing)
- datasets (Hugging Face data loading)
- statsmodels (statistical tests)
- jsonschema (contract validation)
- pytest (testing)
- ruff, black (code quality)

## Constraints
- Memory: Max 7GB RAM during batch processing
- Compute: CPU-first (all-MiniLM-L6-v2), GPU fallback only if necessary
- Data: Real data only, no synthetic fallbacks
- Reproducibility: Deterministic seeds, cached responses

## Milestones
1. **Foundation**: Project structure, data loading, taxonomy building
2. **US1 MVP**: Drift scoring pipeline with statistical validation
3. **US2**: Human-in-the-loop annotation workflow
4. **US3**: Baseline comparison and performance metrics
5. **Polish**: Documentation, benchmarks, CI integration

## Success Criteria
- Drift scores distinguish benign vs novel attacks (p < 0.05, Cohen's d ≥ 0.5)
- Inter-annotator agreement (Kappa) > 0.6
- |AUC_drift - AUC_llm| ≤ 0.10 for efficient alternative claim
- All tests pass, code passes linting/formatting
- Full pipeline reproducible on clean environment
