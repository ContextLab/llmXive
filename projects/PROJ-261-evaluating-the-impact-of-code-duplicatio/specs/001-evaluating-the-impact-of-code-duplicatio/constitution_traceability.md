# Constitution Check Traceability Matrix

This document maps each Constitution Check principle to the concrete task IDs that satisfy it, providing end-to-end traceability for the llmXive automated science pipeline.

## Constitution Principles

### Principle I: Reproducibility

**Requirement**: All experiments must be reproducible with documented seeds, configurations, and environment specifications.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T002 | Initialize Python 3.11 project with requirements.txt (datasets, transformers, bitsandbytes, scipy, matplotlib, pytest) |
| T006 | Configure seeds, thresholds, and model parameters in config.py |
| T043 | Document random seeds, thresholds (0.7, 0.8, 0.9 explicitly called out), and ALL configuration parameters in config.py for reproducibility |

### Principle II: Verified Accuracy

**Requirement**: All measurements and calculations must be validated against known benchmarks and have unit tests.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T029 | Unit test for bug_detection.py pass@1 accuracy calculation |
| T030 | Unit test for correlation_analysis.py Spearman coefficient computation |
| T034 | Save correlation results with p-values to data/analysis/correlation_results.csv |
| T035 | Add validation task to verify SC-004 – significance threshold documented |

### Principle III: Data Hygiene

**Requirement**: All data must be scanned for PII, validated for integrity, and have checksums recorded.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T014 | Unit test for PII scan detection |
| T017 | Implement pii_scanner.py to scan all files under data/ for PII patterns |
| T025 | Add checksum computation for all output files AND intermediate files/logs, record in artifact_hashes state manifest |
| T036 | Add checksum computation for correlation results and record in artifact_hashes state manifest |
| T044 | Add checksum computation for visualization outputs and record in artifact_hashes state manifest |

### Principle IV: Single Source of Truth

**Requirement**: All metrics and results must be stored in a single canonical location with checksums.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T021 | Implement main.py pipeline orchestration to join clone-density and perplexity metrics |
| T025 | Add checksum computation for all output files AND intermediate files/logs |
| T036 | Add checksum computation for correlation results and record in artifact_hashes state manifest |
| T044 | Add checksum computation for visualization outputs and record in artifact_hashes state manifest |

### Principle V: Versioning Discipline

**Requirement**: All artifacts must have version tracking and checksum verification.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T025 | Add checksum computation for all output files AND intermediate files/logs, record in artifact_hashes state manifest |
| T036 | Add checksum computation for correlation results and record in artifact_hashes state manifest |
| T044 | Add checksum computation for visualization outputs and record in artifact_hashes state manifest |

### Principle VI: Statistical Correlation Integrity

**Requirement**: All statistical analyses must use validated methods with p-value reporting.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T032 | Implement correlation_analysis.py to calculate Spearman rank correlation |
| T034 | Save correlation results with p-values to data/analysis/correlation_results.csv |
| T035 | Add validation task to verify SC-004 – significance threshold documented |

### Principle VII: Clone Detection Consistency

**Requirement**: Clone detection must use consistent thresholds and methods across all analyses.

**Satisfying Tasks**:
| Task ID | Description |
|---------|-------------|
| T019 | Implement ast_cloner.py to parse Python files via the built-in ast module and compute clone density |
| T040 | Extend correlation_analysis.py to perform sensitivity analysis for clone-detection thresholds 0.7, 0.8, 0.9 |

## Summary

| Principle | Count | Tasks |
|-----------|-------|-------|
| I. Reproducibility | 3 | T002, T006, T043 |
| II. Verified Accuracy | 4 | T029, T030, T034, T035 |
| III. Data Hygiene | 5 | T014, T017, T025, T036, T044 |
| IV. Single Source of Truth | 4 | T021, T025, T036, T044 |
| V. Versioning Discipline | 3 | T025, T036, T044 |
| VI. Statistical Correlation Integrity | 3 | T032, T034, T035 |
| VII. Clone Detection Consistency | 2 | T019, T040 |
| **Total Unique Tasks** | **12** | T002, T006, T014, T017, T019, T021, T025, T029, T030, T032, T034, T035, T036, T040, T043, T044 |

## Cross-Reference to tasks.md

This traceability matrix is also documented in `tasks.md` under the **Constitution Traceability** section. This artifact provides expanded rationale and task descriptions for audit purposes.

## Update History

- Created: T051 implementation
- Last Updated: 2026-05-22 (per research.md review cycle)