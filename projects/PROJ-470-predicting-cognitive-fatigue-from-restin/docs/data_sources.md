# Data Sources Documentation

## Overview

This pipeline relies on publicly available EEG datasets with paired fatigue
measurements. The primary source is the Sleep-EDF dataset from PhysioNet,
with the Sleep Heart Health Study (SHHS) as a fallback option.

## Primary Source: Sleep-EDF

### Dataset Information
- **Name**: Sleep-EDF Database Expanded
- **Provider**: PhysioNet
- **URL**: https://physionet.org/content/sleep-edf/
- **Version**: 1.0.0
- **License**: Creative Commons Attribution 4.0 International
- **Size**: ~4 GB (compressed)

### Dataset Structure
```
sleep-edf/
├── SC_STUDY/ # Study subjects
│ ├── SC01.edf # EEG recordings
│ ├── SC01.hyp # Sleep staging
│ └── SC01.feat # Feature annotations (if available)
└── README
```

### Required Variables
For this pipeline, the dataset must contain:
1. **Resting-state EEG recordings**: At least one channel with eyes-closed or eyes-open rest
2. **Pre-fatigue rating**: Baseline cognitive fatigue score before recording
3. **Post-fatigue rating**: Fatigue score after cognitive task or sleep period
4. **Participant metadata**: Age, sex, and recording conditions

### Validation Criteria
The `download.py` module validates:
- Presence of all required variables
- Minimum participant count (N ≥ 30)
- Data integrity (file checksums, format compliance)

### Known Limitations
- **Demographic diversity**: Primarily healthy adult volunteers
- **Fatigue measures**: May use sleepiness scales rather than cognitive fatigue
- **Channel count**: Limited EEG channels (typically 2-4)
- **Recording duration**: Variable; some segments may be <120 seconds

### Fallback Strategy
If Sleep-EDF fails validation:
1. Log detailed `validation_report.json` with missing variables
2. Attempt to fetch SHHS dataset
3. If SHHS also fails, exit with code 1

## Fallback Source: SHHS

### Dataset Information
- **Name**: Sleep Heart Health Study
- **Provider**: PhysioNet
- **URL**:
- **Version**: 1.0.0
- **License**: Creative Commons Attribution 4.0 International
- **Size**: ~50 GB (compressed)

### Dataset Structure
```
shhs/
├── shhs1/ # Cohort 1
│ ├── shhs1-0001.edf
│ └── shhs1-0001.xml
├── shhs2/ # Cohort 2
└── README
```

### Required Variables
Same as Sleep-EDF:
1. Resting-state EEG recordings
2. Pre/post fatigue or sleepiness ratings
3. Participant metadata

### Advantages
- **Large sample**: ~5,000 participants
- **Diverse population**: Includes sleep-disordered breathing patients
- **Clinical measures**: Rich set of comorbidities and outcomes

### Disadvantages
- **Fatigue measures**: May use Epworth Sleepiness Scale rather than cognitive fatigue
- **Data access**: May require additional approval for certain variables
- **Processing complexity**: Larger dataset requires more memory and time

## Data Acquisition Workflow

### Step 1: Configuration
Edit `code/config.yaml`:
```yaml
datasets:
 primary: "sleep-edf"
 fallback: "shhs"
 min_participants: 30
```

### Step 2: Download
Run:
```bash
python code/download.py
```

### Step 3: Validation
The script performs:
1. **Checksum verification**: Ensures file integrity
2. **Variable presence**: Checks for required EEG and fatigue measures
3. **Participant count**: Validates N ≥ 30
4. **Data format**: Confirms EDF+ compliance

### Step 4: Output
- **Success**: Cleaned data in `data/raw/`
- **Failure**: `validation_report.json` with detailed error log

## Data Storage

### Directory Structure
```
data/
├── raw/ # Downloaded raw files
│ ├── sleep-edf/
│ └── shhs/
├── processed/ # Cleaned and preprocessed data
│ ├── lzc_metrics.csv
│ └── pe_metrics.csv
└── analysis/ # Statistical results
 ├── correlation_results.csv
 └── sensitivity_table.csv
```

### File Formats
- **Raw**: EDF+ (European Data Format)
- **Processed**: CSV (comma-separated values)
- **Analysis**: CSV and JSON

### Data Privacy
- All datasets are de-identified
- No personally identifiable information (PII)
- Security scan (`security_scan.py`) verifies no PII leakage

## Download Implementation Details

### Sleep-EDF Fetching
```python
from download import fetch_sleep_edf
data = fetch_sleep_edf(dataset_id="sleep-edf")
```

### SHHS Fetching
```python
from download import fetch_shhs
data = fetch_shhs(dataset_id="shhs")
```

### Error Handling
- **Network failures**: Retry with exponential backoff (max 3 attempts)
- **Checksum mismatch**: Abort with clear error message
- **Missing variables**: Log to `validation_report.json` and continue to fallback

## Alternative Sources (Future)

If both primary and fallback datasets fail:

### Potential Alternatives
1. **MASS Database**: Multi-center sleep study with EEG
2. **ISRUC**: Sleep EEG dataset with clinical annotations
3. **TUH EEG Corpus**: Large EEG database with various conditions

### Requirements for New Sources
- Publicly accessible (no special approval)
- Contains resting-state EEG
- Includes fatigue or related cognitive measures
- N ≥ 30 participants
- Open license for research use

## Citation

When using these datasets in publications:

### Sleep-EDF
```
Kemp, B., Zwinderman, A., Tuk, B., Kamphuisen, H., & Oberye, J. (2000).
Analysis of a sleep-dependent neuronal feedback loop: the slow-wave microcontinuity of the EEG.
IEEE Transactions on Biomedical Engineering, 47(9), 1185-1194.
```

### SHHS
```
Quan, S. F., et al. (1997).
The Sleep Heart Health Study: design, rationale, and methods.
Sleep, 20(12), 1077-1085.
```

### PhysioNet
```
Goldberger, A. L., et al. (2000).
PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals.
Circulation, 101(23), e215-e220.
```

## Troubleshooting

### Download Fails
- **Check internet connection**: PhysioNet requires online access
- **Verify disk space**: Ensure sufficient space for ~50 GB (SHHS)
- **Update dependencies**: `pip install -r code/requirements.txt`

### Validation Fails
- **Review `validation_report.json`**: Identifies missing variables
- **Check dataset version**: Ensure latest version is downloaded
- **Consider fallback**: Switch to SHHS if Sleep-EDF lacks required measures

### Data Quality Issues
- **Inspect raw files**: Use `mne.io.read_raw_edf()` to preview
- **Adjust artifact thresholds**: May need stricter/looser criteria
- **Document exclusions**: Log all rejection reasons for transparency
