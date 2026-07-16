# Quickstart Guide: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

This guide provides instructions for setting up the environment and running the pilot analysis for the `llmXive` automated science pipeline project **PROJ-523**.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- A Unix-like environment (Linux/macOS) or WSL2 on Windows

## 1. Environment Setup

### Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies

Install the required Python packages defined in `code/requirements.txt`:

```bash
pip install -r code/requirements.txt
```

**Note**: This project requires `healpy>=1.15.0`. If you encounter compilation issues with `healpy`, ensure you have the necessary build tools (e.g., `fftw3-dev` on Linux or Xcode Command Line Tools on macOS).

## 2. Project Structure

The project follows this directory layout:

```
PROJ-523-quantifying-the-impact-of-data-gaps-on-r/
├── code/ # Source code
│ ├── analysis/ # Analysis modules (power spectra, parameter estimation)
│ ├── gap_filling/ # Gap-filling algorithms
│ ├── pipeline/ # Pipeline orchestration (pilot, budget check)
│ ├── simulation/ # CMB map generation
│ ├── config.py # Global configuration
│ ├── data_io.py # I/O utilities
│ └──...
├── data/ # Data storage
│ ├── raw/ # Raw input data (if any)
│ ├── derived/ # Processed data (masks, leakage matrices)
│ ├── metadata/ # JSON metadata for realizations
│ └── results/ # Final analysis results
├── tests/ # Test suite
├── specs/ # Design documents
├── requirements.txt # Python dependencies
└── quickstart.md # This file
```

## 3. Running the Pilot Analysis

The pilot analysis is a minimal run (1 realization, 1 algorithm, 1 gap fraction) designed to:
1. Verify the environment and data flow.
2. Estimate runtime for the full budget.
3. Generate `data/results/pilot_log.json`.

### Execute the Pilot

Run the pilot script from the project root:

```bash
python code/pipeline/pilot_runner.py
```

**Expected Output:**
- The script will generate a simulated CMB map.
- Apply a gap mask.
- Run a gap-filling algorithm.
- Compute power spectra.
- Save metadata and logs.

Upon successful completion, you should see:
```
Pilot run completed successfully.
Execution time recorded in data/results/pilot_log.json
```

### Verify Pilot Output

Check the generated log file:

```bash
cat data/results/pilot_log.json
```

This file contains the execution time and configuration details used for the budget calculation in the next step.

## 4. Running the Budget Check

Once the pilot is complete, run the budget check to determine the feasible configuration for the full analysis:

```bash
python code/pipeline/budget_check.py
```

This will read `data/results/pilot_log.json`, calculate the maximum number of realizations possible within the time budget, and output the final configuration to `data/results/run_log.yaml`.

## 5. Running the Full Integration (Optional)

To run the full pipeline with the determined configuration:

```bash
python code/pipeline/integration_hook.py
```

This script orchestrates the budget check and triggers the main analysis loop.

## 6. Troubleshooting

- **Import Errors**: Ensure you are running the script from the project root and the virtual environment is activated.
- **healpy Installation**: If `healpy` fails to install, try `pip install --upgrade pip` first, or install system dependencies (e.g., `sudo apt-get install libfftw3-dev`).
- **File Not Found**: Verify that the `data/` directories exist. You can recreate them by running:
 ```bash
 mkdir -p data/raw data/derived data/metadata data/results
 ```

## 7. Next Steps

After verifying the pilot and budget check, proceed to implement the full user stories as defined in `tasks.md`.

- **User Story 1**: Generate Simulated CMB Maps with Controlled Gap Patterns
- **User Story 2**: Apply Gap-Filling Algorithms and Compute Power Spectra
- **User Story 3**: Estimate Cosmological Parameters and Quantify Bias

For detailed task breakdowns, refer to `tasks.md`.