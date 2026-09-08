# Quick Start Guide

## Examining the Impact of Auditory Feedback on Motor Sequence Learning

This guide provides an end-to-end execution flow for the research pipeline.
All commands should be run from the project root directory (`projects/PROJ-195-examining-the-impact-of-auditory-feedbac`).

### Prerequisites

- Python 3.9+
- Docker (for fMRIPrep)
- Sufficient disk space (~14GB for the dataset subset)
- Internet connection for dataset download

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Project Initialization

Ensure the directory structure is created:

```bash
python code/create_data_dirs.py
```

### 3. Data Acquisition

Download the dataset subset (subjects `sub-01` to `sub-10` from `ds000246`):

```bash
python code/download.py
```

This will:
- Fetch the dataset from OpenNeuro
- Validate the download integrity
- Select the specified subjects
- Log any deviations to `data/processed/preprocessing.log`

### 4. Preprocessing with fMRIPrep

First, ensure the fMRIPrep Docker image is available:

```bash
python code/pull_fmriprep_image.py
```

Then run the preprocessing pipeline:

```bash
python code/preprocess.py
```

This will:
- Execute fMRIPrep for each valid subject
- Extract motion parameters and perform QC
- Exclude subjects with motion > 2mm
- Generate `data/processed/valid_subjects.txt`

### 5. ROI Mask Generation

Generate the auditory cortex ROI mask:

```bash
python code/generate_roi_mask.py
```

This creates `roi_masks/auditory_cortex.nii.gz` using the Harvard-Oxford atlas.

### 6. First-Level GLM Analysis

Run the first-level GLM for each valid subject:

```bash
python code/glm_first_level.py
```

This will:
- Load event files and create design matrices
- Fit the GLM for each subject
- Generate contrast maps (perturbed > normal)

### 7. Contrast Map Generation

Generate and save contrast maps:

```bash
python code/glm_contrast_generation.py
```

Outputs are saved to `data/processed/`.

### 8. Group-Level Analysis

Perform the group-level one-sample t-test:

```bash
python code/glm_group.py
```

### 9. FDR Correction and Cluster Extraction

Apply voxel-wise FDR correction and extract significant clusters:

```bash
python code/glm_fdr_correction.py
```

This generates:
- `data/processed/fdr_clusters.csv`
- `data/processed/fdr_mask.nii.gz`

If no clusters survive FDR, the null result handler will:

```bash
python code/glm_null_result_handler.py
```

### 10. ROI Beta Extraction

Extract mean beta values from the auditory cortex ROI:

```bash
python code/extract_roi_betas.py
```

Output: `data/processed/roi_betas.csv`

### 11. Behavioral Analysis

Extract behavioral metrics and calculate learning rates:

```bash
python code/behavior.py
```

This generates:
- `data/processed/behavioral_metrics.csv`
- `data/processed/learning_rates.csv`

### 12. Correlation Analysis

Calculate Pearson correlation between brain activation and learning rates:

```bash
python code/correlation_analysis.py
```

### 13. Visualization

Generate visualizations including scatter plots and statistical maps:

```bash
python code/viz.py
```

### 14. Report Generation

Generate the final report summary:

```bash
python code/generate_report_summary.py
```

Output: `docs/report_summary.csv`

### Validation

To verify the pipeline ran correctly:

1. Check that all expected output files exist in `data/processed/`
2. Review `data/processed/preprocessing.log` for any deviations
3. Verify `docs/report_summary.csv` contains the expected columns

### Troubleshooting

- **Docker issues**: Ensure Docker is running and you have sufficient permissions
- **Memory errors**: Reduce the number of subjects or increase system memory
- **Missing data**: Re-run `code/download.py` to ensure all data is present

### Next Steps

For detailed API documentation, see `docs/api.md`.
For project overview and setup instructions, see `README.md`.