# Data Dictionary: UCI Time Series Anomaly Detection Datasets

This document provides comprehensive information about the datasets used in the Bayesian Nonparametrics for Anomaly Detection project, including licensing, provenance, format specifications, and usage guidelines.

## Dataset Overview

This project uses three benchmark time series datasets from the UCI Machine Learning Repository and NAB (Numenta Anomaly Benchmark) for evaluating anomaly detection models:

1. **Electricity Load Diagrams** - Power consumption time series
2. **Traffic (PEMS-SF)** - Highway traffic sensor data
3. **Synthetic Control Chart** - Generated time series with controlled anomaly injection

---

## 1. Electricity Load Diagrams Dataset

### Provenance
- **Source**: UCI Machine Learning Repository
- **Dataset Name**: Electricity Load Diagrams 2011-2014
- **Original URL**: `https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014`
- **Project Download Path**: `data/raw/electricity.csv`

### License Information
- **License**: UCI Machine Learning Repository License (Attribution Required)
- **License Type**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution Required**: Yes
- **Commercial Use**: Permitted with attribution
- **Redistribution**: Permitted with attribution

### Citation Requirements
```
Dua, D. and Graff, C. (2019). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml]. 
Irvine, CA: University of California, School of Information and Computer Science.
```

### Data Format
- **File Format**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Time Resolution**: 30-minute intervals
- **Total Time Span**: 2011-2014 (approximately 4 years)
- **Number of Series**: 370 electricity consumption series (one per client)
- **Features**: 
  - Timestamp (datetime)
  - Consumption values (numeric, kW)
  - Client ID (categorical)

### Data Characteristics
- **Typical Range**: 0.1 - 5.0 kW per client
- **Missing Values**: Minimal (< 1% of total observations)
- **Seasonality**: Strong daily and weekly patterns
- **Anomaly Types**: Point anomalies (spikes/drops), contextual anomalies (unusual consumption patterns)

### Usage Notes
- Aggregated to single series for this project (sum across all clients)
- Preprocessing: Missing values interpolated using linear interpolation
- Normalization: Z-score normalization applied before model training

---

## 2. Traffic (PEMS-SF) Dataset

### Provenance
- **Source**: Caltrans Performance Measurement System (PeMS)
- **Dataset Name**: PEMS-SF Traffic Sensor Data
- **Original URL**: `https://pems.dot.ca.gov/` (archived in UCI Repository)
- **Project Download Path**: `data/raw/traffic.csv`

### License Information
- **License**: California Department of Transportation (Caltrans) Public Data License
- **License Type**: Public Domain / Open Government Data
- **Attribution Required**: Recommended (not legally required but academic best practice)
- **Commercial Use**: Permitted
- **Redistribution**: Permitted

### Citation Requirements
```
Caltrans Performance Measurement System (PeMS). 
California Department of Transportation, Division of Information Management.
https://pems.dot.ca.gov/
```

### Data Format
- **File Format**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Time Resolution**: 5-minute intervals
- **Total Time Span**: Multiple months (aggregated from sensor network)
- **Number of Series**: Aggregated from 325 sensors to single occupancy rate series
- **Features**:
  - Timestamp (datetime)
  - Occupancy rate (numeric, 0-100%)
  - Sensor aggregation metadata

### Data Characteristics
- **Typical Range**: 0% - 100% occupancy
- **Missing Values**: Moderate (sensor outages, ~2-5% of observations)
- **Seasonality**: Strong daily (rush hours) and weekly (weekday vs weekend) patterns
- **Anomaly Types**: Point anomalies (sensor failures), collective anomalies (traffic incidents)

### Usage Notes
- Aggregated occupancy rate across all sensors
- Preprocessing: Missing values filled using forward-fill then linear interpolation
- Normalization: Min-max scaling to [0, 1] range

---

## 3. Synthetic Control Chart Dataset

### Provenance
- **Source**: UCI Machine Learning Repository (Synthetic Control Chart Time Series Data)
- **Dataset Name**: Synthetic Control Chart Time Series
- **Original URL**: `https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series`
- **Project Download Path**: `data/raw/synthetic_control.csv`

### License Information
- **License**: UCI Machine Learning Repository License (Attribution Required)
- **License Type**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution Required**: Yes
- **Commercial Use**: Permitted with attribution
- **Redistribution**: Permitted with attribution

### Citation Requirements
```
Dua, D. and Graff, C. (2019). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml]. 
Irvine, CA: University of California, School of Information and Computer Science.
```

### Data Format
- **File Format**: CSV (Comma-Separated Values)
- **Encoding**: ASCII/UTF-8
- **Time Resolution**: Discrete time steps (60 points per series)
- **Total Series**: 600 control chart time series
- **Features**:
  - Time step index (integer, 0-59)
  - Control chart value (numeric)
  - Class label (normal or anomaly type)

### Data Characteristics
- **Normal Patterns**: 6 baseline patterns (normal, upward shift, downward shift, etc.)
- **Anomaly Types**: 
  - Normal (no anomaly)
  - Upward shift
  - Downward shift
  - Increasing trend
  - Decreasing trend
  - Cyclic pattern
  - Systematic pattern
- **Control Limits**: 3-sigma control limits (±3 standard deviations)

### Usage Notes
- Used for validation and testing of anomaly detection algorithms
- Ground truth labels available for all series
- Split: 400 training series, 200 test series
- Normalization: Standardized per-series (zero mean, unit variance)

---

## 4. NAB Benchmark Datasets (Supplementary)

### Provenance
- **Source**: Numenta Anomaly Benchmark (NAB)
- **Dataset Examples**: 
  - `nyc_taxi.csv` - New York City taxi passenger counts
  - `ec2_request_latency_system_failure.csv` - AWS EC2 request latency
  - `machine_temperature_system_failure.csv` - Machine temperature readings
- **Original URL**: `https://github.com/numenta/NAB`
- **Project Download Path**: `data/raw/nab_*.csv`

### License Information
- **License**: Apache License 2.0
- **License Type**: Open Source Software License
- **Attribution Required**: Yes
- **Commercial Use**: Permitted
- **Redistribution**: Permitted with license notice

### Citation Requirements
```
Ahmad, S., Lavin, A., Purdy, S., & Agha, Z. (2017). 
Unsupervised Real-Time Anomaly Detection for Streaming Data. 
Neurocomputing, 234, 134-149.
```

---

## License Summary Table

| Dataset | License Type | Attribution Required | Commercial Use | Citation Required |
|---------|--------------|---------------------|----------------|-------------------|
| Electricity | CC BY 4.0 | Yes | Yes | Yes |
| Traffic (PEMS-SF) | Public Domain | Recommended | Yes | Recommended |
| Synthetic Control | CC BY 4.0 | Yes | Yes | Yes |
| NAB Benchmark | Apache 2.0 | Yes | Yes | Yes |

---

## Data Quality Assurance

### Download Verification
All datasets are verified using SHA-256 checksums upon download:
- Checksums stored in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- Verification script: `code/scripts/generate_data_checksums.py`
- Failed downloads trigger automatic retry with exponential backoff

### Data Integrity
- All downloaded files must pass checksum validation before use
- Data files > 1MB are considered valid downloads (prevents empty file errors)
- Any data corruption detected during processing triggers re-download

### Privacy Considerations
- All datasets are publicly available and anonymized
- No personally identifiable information (PII) present
- Traffic data aggregated across sensors to prevent individual identification
- Electricity data aggregated across all clients

---

## Data Usage Compliance Checklist

- [x] All datasets have valid license documentation
- [x] Attribution statements included in project documentation
- [x] Citation requirements documented for academic use
- [x] Download URLs verified as accessible and current
- [x] SHA-256 checksums recorded for all data files
- [x] No PII present in any dataset
- [x] Commercial use permissions verified for all datasets
- [x] Redistribution rights documented for project outputs

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial data dictionary creation |
| 1.0.1 | 2024-01-20 | Added NAB benchmark datasets |
| 1.1.0 | 2024-02-01 | Updated license information, added compliance checklist |

---

## References

1. UCI Machine Learning Repository: https://archive.ics.uci.edu/
2. Caltrans PeMS: https://pems.dot.ca.gov/
3. Numenta Anomaly Benchmark: https://github.com/numenta/NAB
4. Creative Commons Attribution 4.0: https://creativecommons.org/licenses/by/4.0/
5. Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0

---

*This data dictionary is maintained as part of the Bayesian Nonparametrics for Anomaly Detection project (PROJ-024). For questions about dataset usage or licensing, please refer to the project's LICENSE file or contact the project maintainers.*
