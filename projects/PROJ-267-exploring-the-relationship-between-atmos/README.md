# PROJ-267: Exploring the Relationship Between Atmospheric Rivers and Gravity Anomalies

## Overview

This research project investigates potential correlations between atmospheric river (AR) events
and gravitational field anomalies measured by GRACE-FO satellites over the West Coast of North
America.

## Scientific Context

Atmospheric rivers transport significant water mass across regions. The redistribution of this
mass may produce measurable changes in the local gravitational field. GRACE-FO (Gravity Recovery
and Climate Experiment Follow-On) provides monthly gravity field solutions at ~100 km resolution,
enabling detection of such mass variations.

## Research Questions

1. Do AR events correlate with detectable gravity anomalies in the target region?
2. What is the temporal lag between AR intensity peaks and gravity anomaly peaks?
3. Are observed correlations distinguishable from measurement noise and control regions?

## Directory Structure

```
projects/PROJ-267-exploring-the-relationship-between-atmos/
├── code/ # Python scripts and modules
│ ├── 01_data_ingestion.py
│ ├── 02_preprocessing.py
│ ├── 03_merge_output.py
│ ├── 04_correlation.py
│ ├── 05_bootstrap_correction.py
│ ├── 06_control_validation.py
│ ├── 07_visualization_timeseries.py
│ ├── 08_visualization_scatter.py
│ ├── 09_visualization_spatial.py
│ ├── 10_sensitivity_report.py
│ └── 11_temporal_bias_analysis.py
├── data/
│ ├── raw/ # Downloaded datasets (GRACE-FO, NOAA AR)
│ └── processed/ # Processed and merged datasets
├── tests/ # Test suites
├── docs/ # Documentation
├── contracts/ # Schema definitions
├── state/ # Project state tracking
└── specs/ # Feature specifications
```

## Getting Started

See `quickstart.md` for detailed installation and execution instructions.

## Data Sources

- **GRACE-FO Mascon Solutions**: NASA JPL RL06 mascon data
- **NOAA AR Catalog**: CPC Atmospheric River Catalog

## License

Research project - All rights reserved.
All analyses must comply with Constitution Principles I-VII regarding citation verification,
data provenance, and scientific integrity.
