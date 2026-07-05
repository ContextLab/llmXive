# User Guide

## Introduction

This guide explains how to use the "Assessing the Impact of Data Resolution on Statistical Power" pipeline. The system analyzes how changing the resolution of spatial data affects the ability to detect spatial patterns (statistical power).

## Prerequisites

- Python 3.9 or higher
- Access to the NLCD dataset (downloaded automatically)
- 7GB+ RAM recommended

## Installation

1. Clone the repository.
2. Navigate to the project directory:
 ```bash
 cd projects/PROJ-421-assessing-the-impact-of-data-resolution-
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Step-by-Step Execution

### Step 1: Setup Directories
Ensure the project structure is initialized:
```bash
python code/setup_dirs.py
```

### Step 2: Ingest Data
Download the high-resolution NLCD data for Colorado:
```bash
python code/data_ingestion.py
```
*Output*: `data/raw/nlcd_30m_colorado.tif`

### Step 3: Generate Resolutions
Create coarser resolution rasters (60m, 120m, 240m, 480m):
```bash
python code/resampling.py
```
*Output*: `data/derived/` containing resampled rasters.

### Step 4: Run Analysis
Compute Moran's I and statistical power for each resolution:
```bash
python code/analysis.py
```
*Output*: `data/results/power_results.csv`

### Step 5: Generate Reports
Create the final report and threshold identification:
```bash
python code/generate_final_report.py
```
*Output*: `data/results/final_report.md`, `data/results/threshold_report.txt`

## Understanding the Output

### `power_results.csv`
Contains columns:
- `resolution`: Pixel size (e.g., 30m, 60m).
- `moran_i`: Spatial autocorrelation statistic.
- `p_value`: Significance of the statistic.
- `power`: Estimated statistical power.

### `threshold_report.txt`
Identifies the resolution where power drops below 0.80.

### `final_report.md`
Comprehensive summary including:
- Threshold resolution.
- Type II error delta.
- Sensitivity analysis results.

## Troubleshooting

- **Memory Errors**: Ensure you have at least 7GB RAM. The pipeline uses memory-mapped I/O to mitigate this.
- **Download Failures**: The system includes retry logic. Check your internet connection.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt`.

## Customization

Edit `code/config.py` to:
- Change target resolutions.
- Adjust the random seed.
- Modify file paths.
