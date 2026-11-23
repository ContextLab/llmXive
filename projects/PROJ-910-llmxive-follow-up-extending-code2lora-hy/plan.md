# Project Plan: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

## Overview
This project extends the Code2LoRA framework by introducing an AST-based adapter generation mechanism. The goal is to reduce computational overhead while maintaining performance on software evolution tasks.

## Objectives
1. Implement AST-based feature extraction for code repositories.
2. Develop a lightweight hypernetwork to generate LoRA adapters from AST features.
3. Evaluate the generated adapters against the original neural-encoder baseline.
4. Perform sensitivity analysis on feature complexity to determine minimal viable feature sets.

## Scope
- **In Scope**: AST feature extraction, MLP-based hypernetwork, adapter generation, evaluation on RepoPeftBench, sensitivity analysis.
- **Out of Scope**: GPU-accelerated training, support for non-Python languages, real-time adapter generation in production environments.

## Methodology
1. **Feature Extraction**: Extract static AST features (cyclomatic complexity, inheritance depth, token histograms) and import graph centrality.
2. **Hypernetwork Design**: Use a lightweight MLP to map AST feature vectors to LoRA adapter weights.
3. **Evaluation**: Compare AST-based adapters against the original Code2LoRA neural encoder on exact-match scores and inference latency.
4. **Statistical Analysis**: Perform a **Wilcoxon signed-rank test** (per Spec SC-005) to compare performance distributions.

## Constitution Check (Principle VII: Statistical Rigor)
| Principle | Requirement | Implementation | Status |
|-----------|-------------|----------------|--------|
| VII.1 | Statistical significance testing | **Wilcoxon signed-rank test** (primary) | ✅ Implemented in `code/evaluation/stats.py` |
| VII.2 | Paired comparison | Paired design (AST vs Neural on same tasks) | ✅ Implemented |
| VII.3 | Multiple comparison correction | N/A (single primary comparison) | N/A |

*Note: Plan originally stated 'Paired t-test' but has been amended to 'Wilcoxon signed-rank test' to align with Spec SC-005.*

## Resource Constraints
- **CPU**: Limited to 2 cores (via `taskset` or `psutil` affinity).
- **RAM**: Peak usage ≤ 7 GB.
- **Time**: Total pipeline runtime ≤ 6 hours.

## Data Management
- **Source**: RepoPeftBench (HuggingFace `repo-peft-bench`, "python" split).
- **Storage**: Raw data in `data/raw/`, processed in `data/processed/`.
- **Reproducibility**: All data fetches must fail loudly if the source is unreachable; no synthetic fallbacks.

## Risk Management
| Risk | Mitigation |
|------|------------|
| Data fetch failure | Fail loudly with `DataFetchError`; no synthetic data |
| Memory overflow | Pre-flight and runtime RAM checks with `MemoryLimitError` |
| Statistical test mismatch | Explicitly use Wilcoxon signed-rank test as per Spec SC-005 |
| Adapter incompatibility | Validate base model checkpoint before generation |

## Deliverables
1. `code/feature_extractor/ast_parser.py`: AST feature extraction.
2. `code/hypernetwork/adapter_generator.py`: Adapter generation with latency timing.
3. `code/evaluation/stats.py`: Wilcoxon signed-rank test implementation.
4. `data/results/ast_scores.csv`: Evaluation results with latency.
5. `data/results/stats.json`: Statistical test output.
6. `data/results/ast_generation_latency.json`: Generation latency measurement.

## Timeline
- **Phase 0**: Alignment & Fixes (T000 - Plan/Spec resolution)
- **Phase 1**: Setup (Project structure, dependencies)
- **Phase 2**: Foundational (Config, logging, errors)
- **Phase 7**: Data Acquisition (RepoPeftBench download)
- **Phase 3**: User Story 1 (AST-based adapter generation)
- **Phase 4**: User Story 2 (Evaluation & comparison)
- **Phase 5**: User Story 3 (Sensitivity analysis)
- **Phase 6**: Resource Enforcement
- **Phase 8**: Polish & Documentation
- **Phase 9**: Revision & Compliance Fixes

## Success Criteria
1. AST-based adapter generation completes within 6 hours on 2 cores, ≤ 7 GB RAM.
2. Evaluation produces valid `ast_scores.csv` with exact-match and latency.
3. Wilcoxon signed-rank test confirms statistical significance (p < 0.05) or documents non-significance.
4. Sensitivity analysis identifies a minimal feature set maintaining ≥ 80% of baseline accuracy.
5. All data fetches use real sources; no synthetic data is generated or used.
