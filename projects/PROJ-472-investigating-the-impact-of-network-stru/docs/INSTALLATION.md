# Installation Guide

This guide covers the installation and setup of the Network Structure & Neural Avalanche Dynamics research pipeline.

## Prerequisites

- **Python**: 3.11 or higher
- **pip**: Package installer for Python
- **MRtrix3**: Required for tractography preprocessing (optional if using pre-processed data)
- **Git**: For version control

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd network-structure-avalanche-dynamics
```

## Step 2: Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r code/requirements.txt
```

### Key Dependencies

- `numpy`: Numerical computing
- `pandas`: Data manipulation
- `networkx`: Network analysis
- `mne`: EEG processing
- `powerlaw`: Power-law fitting
- `scipy`: Statistical functions
- `matplotlib`: Visualization
- `python-dotenv`: Environment variable management
- `requests`: HTTP requests for data download

## Step 4: Setup Environment Variables

Copy the example environment file and configure it:

```bash
cp code/.env.example code/.env
```

Edit `code/.env` to set:
- `DATA_ROOT`: Path to your data directory
- `SIMULATION_SEED`: Random seed for reproducibility
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Step 5: Verify Installation

Run the setup script to verify the environment:

```bash
python code/utils/data_setup.py
```

This script will:
- Check directory structure
- Verify checksums (if available)
- Log any missing dependencies

## Step 6: Run the Pipeline

Execute the main pipeline:

```bash
python code/main.py --config code/config.yaml
```

## Troubleshooting

### MRtrix3 Not Found

If you encounter errors related to MRtrix3 commands (e.g., `tck2connectome`), ensure MRtrix3 is installed and added to your system PATH.

**Linux**:
```bash
sudo apt-get install mrtrix3
```

**macOS**:
```bash
brew install mrtrix
```

### Missing OpenNeuro Data

If the download fails, verify your internet connection and ensure the OpenNeuro dataset (ds003813) is accessible. You may need to configure proxy settings if behind a corporate firewall.

### Permission Errors

Ensure you have write permissions to the `data/` directory. You may need to adjust ownership or permissions:

```bash
chmod -R u+w data/
```

## Next Steps

- Refer to `docs/README.md` for an overview of the project.
- Check `docs/API_REFERENCE.md` for detailed module documentation.
- Run `tests/` to verify the installation.
