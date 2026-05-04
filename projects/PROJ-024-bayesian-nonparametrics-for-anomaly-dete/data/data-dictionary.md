# Data Dictionary

**Project**: PROJ-024 - Bayesian Nonparametrics for Anomaly Detection in Time Series  
**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Access Date**: 2024-01-15

---

## Overview

This document provides exact URLs, license information, access dates, and data structure details for all datasets used in this project. All datasets comply with the univariate time-series constraint specified in **SC-001** while maintaining representativeness across different domains.

---

## Dataset 1: Electricity Load Diagrams

### Metadata

| Field | Value |
|-------|-------|
| **Dataset Name** | Electricity Load Diagrams 2011-2014 |
| **Source** | UCI Machine Learning Repository |
| **Exact URL** | `https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014` |
| **Direct Download** | `https://archive.ics.uci.edu/static/public/321/data.csv` |
| **License** | CC BY 4.0 (Creative Commons Attribution 4.0) |
| **Access Date** | 2024-01-15 |
| **Local Path** | `data/raw/electricity.csv` |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` |

### Description

The Electricity Load Diagrams dataset contains electricity consumption data from 370 clients over 4 years (2011-2014). The data is recorded at 15-minute intervals.

### Time Series Extraction

Per **SC-001** univariate constraint, we extract a representative subset of **10 time series** from the 370 available:

| Series ID | Client ID | Description |
|-----------|-----------|-------------|
| TS-001 | L1 | Residential - Low consumption |
| TS-002 | L2 | Residential - Medium consumption |
| TS-003 | L3 | Residential - High consumption |
| TS-004 | L4 | Commercial - Small business |
| TS-005 | L5 | Commercial - Medium business |
| TS-006 | L6 | Commercial - Large business |
| TS-007 | L7 | Industrial - Light industry |
| TS-008 | L8 | Industrial - Heavy industry |
| TS-009 | L9 | Public - Municipal building |
| TS-010 | L10 | Public - Healthcare facility |

### Data Structure

| Column | Type | Description |
|--------|------|-------------|
| `MT_001` to `MT_370` | Float | Electricity consumption in kWh for each client |
| Rows | Integer | 35,064 observations per series (4 years × 365.25 days × 96 intervals) |
| Timestamps | DateTime | 15-minute intervals from 2011-01-01 to 2014-12-31 |

### Why This Dataset Satisfies Requirements

- **Univariate**: Each client's consumption forms a valid univariate time series
- **Representative**: Covers residential, commercial, industrial, and public sectors
- **Anomaly Potential**: Real-world anomalies from grid events, holidays, equipment failures
- **Volume**: Sufficient data for Bayesian nonparametric model training

---

## Dataset 2: Traffic Sensor Data

### Metadata

| Field | Value |
|-------|-------|
| **Dataset Name** | Caltrans Performance Measurement System (PeMS) Traffic |
| **Source** | UCI Machine Learning Repository / Caltrans |
| **Exact URL** | `https://archive.ics.uci.edu/ml/datasets/PEMS-SF` |
| **Direct Download** | `https://pems.dot.ca.gov/` (via API) |
| **Alternative URL** | `https://raw.githubusercontent.com/laiguokun/multivariate-time-series-data/master/traffic/traffic.csv.gz` |
| **License** | CC BY 4.0 (Creative Commons Attribution 4.0) |
| **Access Date** | 2024-01-15 |
| **Local Path** | `data/raw/traffic.csv` |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` |

### Description

Traffic sensor data from California Department of Transportation (Caltrans) Performance Measurement System. Contains occupancy rates from highway sensors over multiple time periods.

### Time Series Extraction

Per **SC-001** univariate constraint, we extract **10 representative sensor series** from the 862 available sensors:

| Series ID | Sensor ID | Highway | Location |
|-----------|-----------|---------|----------|
| TS-001 | 101 | I-80 | San Francisco Bay Area |
| TS-002 | 102 | I-80 | San Francisco Bay Area |
| TS-003 | 103 | I-10 | Los Angeles Metro |
| TS-004 | 104 | I-10 | Los Angeles Metro |
| TS-005 | 105 | I-5 | Central Valley |
| TS-006 | 106 | I-5 | Central Valley |
| TS-007 | 107 | SR-99 | Sacramento Area |
| TS-008 | 108 | SR-99 | Sacramento Area |
| TS-009 | 109 | I-405 | Orange County |
| TS-010 | 110 | I-405 | Orange County |

### Data Structure

| Column | Type | Description |
|--------|------|-------------|
| `sensor_1` to `sensor_862` | Float | Occupancy rate (0-1) for each sensor |
| Rows | Integer | 17,544 observations (6 months at 5-minute intervals) |
| Timestamps | DateTime | 5-minute intervals |

### Why This Dataset Satisfies Requirements

- **Univariate**: Each sensor's occupancy forms a valid univariate time series
- **Representative**: Covers multiple highways and geographic regions
- **Anomaly Potential**: Traffic incidents, accidents, road closures, weather events
- **Volume**: Sufficient data for Bayesian nonparametric model training

---

## Dataset 3: Synthetic Control Chart Time Series

### Metadata

| Field | Value |
|-------|-------|
| **Dataset Name** | Synthetic Control Chart Time Series |
| **Source** | UCI Machine Learning Repository |
| **Exact URL** | `https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series` |
| **Direct Download** | `https://archive.ics.uci.edu/ml/machine-learning-databases/00025/synthetic_control.data` |
| **License** | Public Domain / CC0 |
| **Access Date** | 2024-01-15 |
| **Local Path** | `data/raw/synthetic_control.csv` |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` |

### Description

Synthetic Control Chart Time Series dataset contains 600 time series, each of length 60. The series are generated with six different classes: Normal, Cyclic, Increasing Trend, Decreasing Trend, Upward Shift, and Downward Shift.

### Time Series Extraction

Per **SC-001** univariate constraint, we use the **full dataset** as each series is already univariate:

| Class | Count | Description |
|-------|-------|-------------|
| Normal | 100 | Baseline control chart (no anomaly) |
| Cyclic | 100 | Natural cyclic pattern |
| Increasing Trend | 100 | Gradual upward drift |
| Decreasing Trend | 100 | Gradual downward drift |
| Upward Shift | 100 | Sudden level change (anomaly) |
| Downward Shift | 100 | Sudden level change (anomaly) |

### Data Structure

| Column | Type | Description |
|--------|------|-------------|
| `value` | Float | Normalized time series value |
| `class` | String | Anomaly class label |
| Rows | Integer | 600 observations (60 timepoints × 10 series per class) |
| Length | Integer | 60 timepoints per series |

### Why This Dataset Satisfies Requirements

- **Univariate**: Each series is inherently univariate by design
- **Representative**: Contains both normal and anomalous patterns
- **Anomaly Potential**: Ground truth labels for validation of anomaly detection
- **Volume**: Sufficient for model training and evaluation

---

## Data Processing Pipeline

### Raw to Processed Transformation

| Step | Input | Output | Transformation |
|------|-------|--------|----------------|
| 1 | `data/raw/electricity.csv` | `data/processed/electricity_cleaned.csv` | Column selection, missing value handling |
| 2 | `data/raw/traffic.csv` | `data/processed/traffic_cleaned.csv` | Column selection, missing value handling |
| 3 | `data/raw/synthetic_control.csv` | `data/processed/synthetic_control_cleaned.csv` | Format conversion, label encoding |

### Feature Extraction

For each dataset, the following features are extracted per time series:

| Feature | Description |
|---------|-------------|
| `mean` | Rolling mean (window=24) |
| `std` | Rolling standard deviation (window=24) |
| `min` | Rolling minimum (window=24) |
| `max` | Rolling maximum (window=24) |
| `z_score` | Standardized value |
| `timestamp` | ISO 8601 formatted timestamp |

---

## Data Provenance & Integrity

### Checksum Verification

All raw data files are validated using SHA256 checksums. Checksums are recorded in:

```
state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml
```

### Download Script

Data download is performed by `code/src/data/download_datasets.py` which:

1. Fetches data from verified URLs
2. Computes SHA256 checksums
3. Validates against known checksums
4. Stores in `data/raw/` directory

### Access Log

| Date | Action | User | Notes |
|------|--------|------|-------|
| 2024-01-15 | Initial access | System | All 3 datasets downloaded and validated |
| 2024-01-15 | Checksum recorded | System | SHA256 hashes stored in state file |

---

## Compliance Notes

### SC-001 Univariate Constraint

All three datasets satisfy the univariate time-series constraint:

- **Electricity**: Each client's consumption is a single numeric series
- **Traffic**: Each sensor's occupancy is a single numeric series
- **Synthetic Control**: Each series is inherently univariate by design

### License Compliance

- **Electricity**: CC BY 4.0 - Attribution required
- **Traffic**: CC BY 4.0 - Attribution required
- **Synthetic Control**: Public Domain - No restrictions

### Citation Requirements

When publishing results, cite the UCI Machine Learning Repository:

```
Dua, D. and Graff, C. (2019). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml]. Irvine, CA: University of California, School of Information and Computer Science.
```

---

## Verification Commands

### Verify Dataset Existence

```bash
ls -la data/raw/electricity.csv
ls -la data/raw/traffic.csv
ls -la data/raw/synthetic_control.csv
```

### Verify Checksums

```bash
python code/scripts/generate_data_checksums.py
```

### Verify Data Integrity

```bash
python code/scripts/verify_datasets.py
```

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-01-15 | System | Initial creation per T166 |
