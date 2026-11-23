# Project Plan: llmXive Follow-up - Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview
This project extends the AgentDoG 1.5 framework to include zero-shot drift detection capabilities.
The system will compute drift scores for incoming logs by comparing them against a pre-built
taxonomy of known safety patterns using cosine distance metrics.

## Goals
1. Implement a robust drift scoring mechanism based on cosine distance to taxonomy centroids.
2. Enable human-in-the-loop validation for edge cases and novel attacks.
3. Compare the drift-based detector against a standard zero-shot LLM classifier (gpt-4o-mini).
4. Ensure the system operates within strict memory limits (<7GB RAM) and completes large benchmarks in <30 minutes.

## Architecture
- **Data Layer**: Raw data fetching (AdvBench, HF4, Taxonomy), checksum verification, and preprocessing.
- **Core Logic**: Taxonomy centroid generation, drift score computation, batch processing with memory monitoring.
- **Validation**: Statistical testing (Cohen's d, p-values), human annotation ingestion, inter-annotator agreement (Kappa).
- **Comparison**: Baseline comparison with API-based LLM classifier.

## Directory Structure
```
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/
│ ├── config.py # Configuration management (seeds, paths, batch sizes)
│ ├── data_loader.py # Data fetching and integrity verification
│ ├── taxonomy_builder.py # Centroid generation and memory profiling
│ ├── drift_scoring.py # Core drift scoring logic
│ ├── annotator_interface.py # Human annotation preparation
│ ├── validation.py # Statistical validation and Kappa calculation
│ ├── comparison.py # Baseline LLM comparison
│ ├── utils.py # Schema validation and file I/O helpers
│ ├── main.py # Orchestration script
│ └── generate_test_fixture.py # Test data generation
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Intermediate and final processed data
│ ├── test/ # Test fixtures and mock data
│ └── checksums.json # Integrity tracking for raw data
├── specs/
│ └── 001-llmxive-drift-detection/
│ ├── spec.md
│ ├── data-model.md
│ └──...
├── contracts/
│ └── drift_result.schema.yaml # Output schema definition
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
│ ├── quickstart.md
│ └── data-model.md
├── requirements.txt
├──.ruff.toml
└── pyproject.toml
```

## Data Sources
- **AdvBench**: HuggingFace dataset for adversarial examples.
- **HF4**: HuggingFace dataset for benign logs.
- **Taxonomy**: AgentDoG 1.5 taxonomy definition (canonical source).

## Constraints
- **Memory**: Peak RAM usage must not exceed 7GB during batch processing.
- **Time**: Large-scale benchmarks must complete within 30 minutes.
- **Data Integrity**: All raw data must be verified against checksums.
- **Reproducibility**: All random seeds must be configurable; no synthetic data fallbacks.

## Milestones
1. **Setup**: Project structure, requirements, linting configuration.
2. **Foundational**: Data loading, taxonomy building, utility functions.
3. **User Story 1**: Drift scoring implementation and statistical validation.
4. **User Story 2**: Human-in-the-loop validation and annotation interface.
5. **User Story 3**: Baseline comparison with LLM classifier.
6. **Polish**: Documentation, performance benchmarking, and final testing.
