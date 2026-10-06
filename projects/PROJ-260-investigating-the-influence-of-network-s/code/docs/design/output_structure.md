# Output Directory Structure

This document defines the directory hierarchy for the `PROJ-260` project output artifacts.
All paths are relative to the project root.

## Output Directories (`outputs/`)

The `outputs/` directory contains final reports, visualizations, and summary documents.

### `outputs/figures/`
- **Purpose**: Stores generated plots and visualizations.
- **Contents**:
 - RDF plots (showing cutoff determination).
 - VDOS spectra (frequency vs. density).
 - Correlation scatter plots (with confidence interval bands).
 - Sensitivity analysis charts.
 - Network topology visualizations (if applicable).
- **Format**: Primarily `.png` and `.pdf` for publication quality.

### `outputs/reports/`
- **Purpose**: Stores final analysis reports and documentation.
- **Contents**:
 - `final_report.html` or `final_report.pdf`: Comprehensive summary of findings.
 - `assumptions.md`: Documentation of statistical assumptions (e.g., effect sizes).
 - `tolerance_report.txt`: Numerical tolerance thresholds used in calculations.
 - `sensitivity_analysis.md`: Results of threshold sweeps and robustness checks.

## Directory Hierarchy Diagram

```
outputs/
├── figures/
│ ├── rdf_cutoff.png
│ ├── vdos_spectrum.png
│ ├── correlation_scatter.png
│ └──...
└── reports/
 ├── final_report.html
 ├── assumptions.md
 ├── tolerance_report.txt
 └── sensitivity_analysis.md
```
