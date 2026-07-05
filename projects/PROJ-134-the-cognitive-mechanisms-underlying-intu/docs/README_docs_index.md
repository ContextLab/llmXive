# Documentation Index

This document provides an index to all project documentation.

---

## Overview

The project documentation is organized into the following sections:

1. **Getting Started**
2. **Data Reference**
3. **Usage Examples**
4. **API Reference**
5. **Contributing**

---

## Documentation Files

### 1. Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start](quickstart.md) | Get up and running in 10 minutes |
| [Installation Guide](../README.md#installation) | Detailed installation instructions |
| [Configuration Guide](../README.md#configuration) | How to configure the pipeline |

### 2. Data Reference

| Document | Description |
|----------|-------------|
| [Data Schema Reference](data_schema.md) | Complete schema definitions and validation rules |
| [Data Formats](data_schema.md#file-formats) | CSV and JSON output formats |
| [Data Integrity](data_schema.md#data-integrity) | Checksum and state management |

### 3. Usage Examples

| Document | Description |
|----------|-------------|
| [Usage Examples](usage_examples.md) | Practical examples for all pipeline components |
| [Testing Guide](../README.md#testing) | How to run and write tests |
| [Troubleshooting](usage_examples.md#troubleshooting) | Common issues and solutions |

### 4. API Reference

| Module | Description |
|--------|-------------|
| `code/config.py` | Configuration and constants |
| `code/utils/schema.py` | Pydantic data schemas |
| `code/utils/hashing.py` | Checksum and state management |
| `code/utils/logging_utils.py` | Logging infrastructure |
| `code/data/simulation_mfq.py` | Synthetic MFQ generation |
| `code/data/simulation_stories.py` | Synthetic stories and VR logs generation |
| `code/data/ingest.py` | Data loading and merging |
| `code/data/preprocess.py` | VR scene mapping |
| `code/models/bayesian.py` | Bayesian model execution |
| `code/models/regression.py` | Mixed-effects regression |
| `code/analysis/model_comparison.py` | AIC/WAIC and PPC |
| `code/analysis/validation.py` | Parameter recovery and sensitivity |
| `code/reports/generate_report.py` | Report generation |

### 5. Contributing

| Document | Description |
|----------|-------------|
| [Contributing Guide](../README.md#contributing) | How to contribute to the project |
| [Code Standards](../README.md#coding-standards) | Formatting and linting rules |
| [Test Coverage](../README.md#testing) | Testing requirements |

---

## External References

- [PyMC Documentation](https://www.pymc.io/projects/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Moral Foundations Theory](https://moralfoundations.org/)
- [Open Science Framework](https://osf.io/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |
| 1.1.0 | TBD | Real data ingestion support |

---

## Feedback

Found an error or have suggestions? Please open an issue on the repository.