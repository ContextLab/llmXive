# Cross-Modal Comparison of Neural Prediction Error Signals

This project implements an automated pipeline to download, preprocess, and analyze EEG data from OpenNeuro datasets (ds000246 for auditory, ds000117 for visual) to compare neural prediction error signals across modalities.

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-cross-modal-comparison
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment variables** (optional):
 Copy `.env.example` to `.env` and update any necessary paths or credentials:
 ```bash
 cp.env.example.env
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── data/ # Data loading and preprocessing
│ ├── analysis/ # Metrics and source localization
│ ├── validation/ # Reliability checks
│ ├── utils/ # Utilities (logging, etc.)
│ ├── config.py # Global configuration
│ └── main.py # Orchestration script
├── data/ # Data artifacts (generated)
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Preprocessed data
│ └── results/ # Analysis results
├── docs/ # Documentation
├── tests/ # Test suites
├── requirements.txt # Dependencies
└── README.md # This file
```

## Usage

See `docs/quickstart.md` for a step-by-step guide to running the pipeline.

## Data Sources

This project uses real data from OpenNeuro:
- **Auditory**: ds000246
- **Visual**: ds000117

No synthetic data is generated or used.

## License

[Insert License Information]
