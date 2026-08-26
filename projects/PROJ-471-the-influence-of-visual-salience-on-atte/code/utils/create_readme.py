"""
Utility script to regenerate README.md from a template if needed.
Currently, README.md is maintained manually but this script provides
a reference for the expected content structure.
"""
import os
from pathlib import Path

def main():
    readme_path = Path("README.md")
    if readme_path.exists():
        print("README.md already exists. Skipping generation.")
        print("To update, edit README.md manually or remove the file to regenerate.")
        return

    template = """# The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Project ID**: PROJ-471
**Status**: Active Research Pipeline

## Overview

This project implements an automated science pipeline to investigate how visual salience influences attentional bias in moral judgment tasks. The pipeline downloads real eye-tracking data, generates salience maps using DeepGaze II (with GBVS fallback), aligns metrics, and fits Linear Mixed Models (LMMs) to test theoretical predictions.

## Prerequisites

- Python 3.11+
- Git
- A valid Hugging Face token (`HF_TOKEN`) for dataset access
- Minimum 7GB RAM (CPU-only execution)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd PROJ-471-the-influence-of-visual-salience-on-atte
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root based on `.env.example`:
   ```bash
   HF_TOKEN=your_huggingface_token_here
   DATA_PATH=./data
   SEED=42
   ```

## Data Acquisition Protocol

The pipeline automatically downloads the required dataset from Hugging Face (OpenNeuro ds003123) upon first run. No manual download is required.

- **Source**: Hugging Face Datasets (OpenNeuro ds003123)
- **Protocol**: The `code/ingestion/download_data.py` script fetches the dataset using the `datasets` library.
- **Verification**: The `code/ingestion/verify_real_source.py` script validates the dataset checksum and directory structure before processing.
- **Streaming**: If the dataset exceeds 7GB, the pipeline automatically switches to streaming mode to stay within memory limits.

**Note**: The pipeline is configured to **fail loudly** if the real data source is unreachable. Synthetic data fallbacks are strictly forbidden.

## Execution Commands

The pipeline is executed sequentially through its phases. Run the following commands in order:

### 1. Setup & Validation
```bash
# Verify directory structure
python code/setup_directories.py

# Initialize configuration
python code/config_env.py
```

### 2. User Story 1: Data Ingestion & Salience Generation
```bash
# Download and validate real data
python code/ingestion/download_data.py

# Verify real source integrity
python code/ingestion/verify_real_source.py

# Generate salience maps (DeepGaze II with CPU fallback to GBVS)
python code/ingestion/salience_gen.py

# Validate completion and resource usage
python code/ingestion/completion_validator.py
python code/utils/resource_validator.py
```

### 3. User Story 2: Eye Tracking & Alignment
```bash
# Segment faces (YOLOv8)
python code/processing/segmentation.py

# Parse eye-tracking data
python code/processing/eye_tracking.py

# Align salience and fixation metrics
python code/processing/alignment.py

# Validate alignment
python code/processing/alignment_validator.py
```

### 4. User Story 3: Statistical Analysis
```bash
# Power analysis
python code/analysis/lmm_power.py

# Generate low-level features (diagnostic only)
python code/analysis/feature_gen.py

# Calculate VIF
python code/analysis/vif_calc.py
python code/analysis/vif_interpretation.py

# Fit LMMs
python code/analysis/lmm_fit.py

# Apply FDR correction
python code/analysis/robustness.py

# Generate sensitivity plot
python code/analysis/plot_sensitivity.py

# Final results and interpretation
python code/analysis/write_final_results.py
```

### 5. Final Validation
```bash
# Run full integration test
python tests/integration/test_pipeline.py

# Validate final artifacts against schema
python code/utils/final_validator.py
```

## Output Artifacts

All outputs are written to the `data/` directory:

- `data/processed/salience_maps/`: Generated salience maps (`.npy`)
- `data/processed/aligned_metrics.csv`: Merged eye-tracking and salience data
- `data/interim/lmm_results.csv`: Raw LMM output
- `data/processed/results.json`: Final analysis results with p-values and disclaimers
- `data/processed/sensitivity_plot.png`: Sensitivity analysis visualization

## Project Structure

```
.
├── code/
│   ├── ingestion/       # Data download and salience generation
│   ├── processing/      # Eye-tracking parsing and alignment
│   ├── analysis/        # Statistical modeling and robustness checks
│   ├── utils/           # Logging, versioning, validation
│   ├── config.py        # Project configuration
│   └── data_models.py   # Data structures
├── data/
│   ├── raw/             # Downloaded dataset
│   ├── interim/         # Intermediate processing artifacts
│   └── processed/       # Final analysis outputs
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # End-to-end pipeline tests
├── specs/               # Design documents and SCR records
├── requirements.txt
├── .env.example
└── README.md
```

## Governance & Constraints

- **SCR-001**: Low-level covariates (luminance, contrast, edge density) are excluded from the final LMM to prevent multicollinearity.
- **SCR-002**: "Weapons" are explicitly excluded from ROI analysis; only "Face" regions are processed.
- **SCR-003**: GBVS is used as a fallback only if DeepGaze II fails; GBVS maps are tracked separately and excluded from primary success metrics.
- **Data Integrity**: No synthetic data. If real data fetch fails, the pipeline halts with `DATA_MISSING_001`.
- **Compute Limits**: RAM < 7GB, cumulative CPU time < 6 hours.

## License

Research code for academic use. See LICENSE for details.
"""

    readme_path.write_text(template)
    print(f"README.md created at {readme_path.resolve()}")

if __name__ == "__main__":
    main()