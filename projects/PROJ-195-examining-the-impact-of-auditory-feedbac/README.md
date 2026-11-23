# Examining the Impact of Auditory Feedback on Motor Sequence Learning

**Project ID**: PROJ-195

## Overview

This project investigates how auditory feedback (normal, delayed, and pitch-shifted) influences motor sequence learning. Using fMRI data from the OpenNeuro dataset `ds000246`, we apply a rigorous preprocessing pipeline (fMRIPrep), first-level and group-level GLM analysis, and brain-behavior correlation to determine if auditory cortex activation predicts learning rates.

## Key Features

- **Data Acquisition**: Automated download and validation of OpenNeuro `ds000246` (subjects 01-10).
- **Preprocessing**: fMRIPrep pipeline with motion QC and exclusion (>2mm displacement).
- **Statistical Modeling**:
 - First-level GLM with contrast: `(delayed + pitch-shifted) - normal`.
 - Group-level one-sample t-test against zero.
 - Voxel-wise FDR correction (q < 0.05).
- **Brain-Behavior Correlation**: Pearson correlation between auditory cortex activation and behavioral learning rate slopes.
- **Visualization**: Statistical map overlays and scatter plots.

## Project Structure

```text
.
├── code/ # Python implementation scripts
│ ├── download.py # Dataset download and filtering
│ ├── preprocess.py # fMRIPrep execution and QC
│ ├── glm_first_level.py # First-level GLM fitting
│ ├── glm_group.py # Group-level analysis
│ ├── behavior.py # Behavioral metric extraction
│ ├── correlation_analysis.py # Brain-behavior correlation
│ ├── viz.py # Visualization generation
│ └──... # Utilities and config loaders
├── data/
│ ├── raw/ # Downloaded BIDS dataset
│ ├── processed/ # GLM outputs, QC logs, behavioral metrics
│ └── derivatives/ # fMRIPrep outputs
├── roi_masks/ # ROI masks (e.g., auditory_cortex.nii.gz)
├── tests/ # Unit and integration tests
├── docs/ # Documentation and reports
├── stats_config.yaml # GLM and FDR configuration
└── README.md
```

## Prerequisites

- **Python**: 3.8+
- **Docker**: Required for fMRIPrep execution
- **System Dependencies**: `git`, `curl`, `ffmpeg` (for fMRIPrep)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-195-examining-the-impact-of-auditory-feedback-motor-learning
 ```

2. **Create a Python environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify Docker installation**:
 ```bash
 docker --version
 docker run hello-world
 ```

## Quick Start

### 1. Setup Project Structure
Run the setup script to create necessary directories:
```bash
python code/setup_project.py
```

### 2. Download Data
Download the dataset subset (subjects 01-10) from OpenNeuro:
```bash
python code/download.py
```

### 3. Generate ROI Mask
Create the auditory cortex mask:
```bash
python code/generate_roi_mask.py
```

### 4. Preprocess Data
Run fMRIPrep and perform QC:
```bash
python code/preprocess.py
```
*Note: This step requires Docker and may take significant time.*

### 5. Run First-Level GLM
Fit GLMs for each valid subject:
```bash
python code/glm_first_level.py
```

### 6. Run Group-Level Analysis
Perform group t-test and FDR correction:
```bash
python code/glm_group.py
```

### 7. Extract Behavioral Metrics
Calculate learning rate slopes from reaction times:
```bash
python code/behavior.py
```

### 8. Correlation Analysis
Correlate brain activation with behavior:
```bash
python code/correlation_analysis.py
```

### 9. Generate Visualizations
Create statistical maps and plots:
```bash
python code/viz.py
```

## Configuration

- **Stats Config**: `stats_config.yaml` defines GLM parameters, FDR threshold, and ROI paths.
- **Docker Config**: `code/docker_config.env` specifies the fMRIPrep version.

## Testing

Run the test suite:
```bash
pytest tests/
```

## License

This project is for research purposes.

## Contact

For questions, refer to the project documentation or contact the research team.