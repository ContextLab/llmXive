# Reproducibility Documentation

This directory contains all reproducibility artifacts for the project, including logs, checksums, validation reports, and detailed methodology documentation. Below is a quick guide to the most important files:

- `LOGS_LOCATION.md` – where to find runtime logs.
- `checksums.md` – description of checksum generation and verification.
- `validation_status.md` – summary of validation outcomes.
- `quickstart.md` – steps to reproduce the main analyses.
- `final_report.md` – comprehensive reproducibility report.

For a full list, see the table of contents in this README.

*Note: Some documents in this directory refer to Phase 2+ work and are placeholders for future development.*

This directory contains all artifacts required to reproduce the results of the
*Quantifying the Complexity of Knot Diagrams* project.

## Overview

- **Algorithm validation** – `algorithm_validation.md`
- **Checksums** – `checksums.md`, `checksums_authoritative.md`, etc.
- **Derivation notes** – `derivation_notes.md`
- **Data quality reports** – `data_quality_report.md`
- **Visualization guides** – `complexity_visualization_guide.md`
- **Logs** – `logs/` subdirectory with reproducibility logs.
- **Quickstart** – `quickstart_validation.md`

## Getting Started

To run the full reproducibility pipeline:

```bash
python -m code.reproducibility.quickstart_validator
```

Refer to the individual markdown files for detailed explanations of each
component.

