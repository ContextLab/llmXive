# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Prerequisites

- Python 3.11+
- `pip`
- Access to a terminal

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin `pandas`, `numpy`, `pyyaml`.*

## Running the Pipeline

The pipeline is designed to handle the **Feasibility Termination State** automatically.

1.  **Execute the main pipeline**:
    ```bash
    python src/feasibility.py
    ```
    *Note: `src/feasibility.py` will first check `plan.md` for a verified AGP URL. Since none exists in the `# Verified datasets` block, it will immediately trigger the Feasibility Termination State.*

2.  **Verify Outputs**:
    The following files will be generated in `data/processed/` and `outputs/reports/`:
    - `feasibility_report.json` (Feasibility Report)
    - `reports/feasibility_report.md` (Final report)

3.  **View the Report**:
    Open `outputs/reports/feasibility_report.md` to see the detailed explanation of the blockage.

## Testing

Run the test suite to verify the logic:
```bash
pytest tests/ -v
```
*Note: Tests will verify that the Feasibility Termination State generates the correct artifacts and that no "Happy Path" code attempts to download non-existent data.*

## Troubleshooting

- **Issue**: "No verified URL found."
  - **Resolution**: This is expected behavior for this revision. The `# Verified datasets` block does not contain an AGP URL. The pipeline correctly halts and generates a feasibility report.
- **Issue**: "Missing dependency."
  - **Resolution**: Ensure `requirements.txt` is installed in the active virtual environment.