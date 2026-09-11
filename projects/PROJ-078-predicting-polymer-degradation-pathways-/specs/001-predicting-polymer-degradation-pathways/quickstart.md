# Quickstart: Predicting Polymer Degradation Pathways

## Prerequisites

*   Python 3.11 or higher
*   Pip package manager

## Installation

1.  Clone the repository:

    ```bash
    git clone [repository URL]
    cd [repository directory]
    ```

2.  Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Data Ingestion:**

    ```bash
    python src/data/ingestion.py --source webbooks --output data/processed_data.csv
    ```

2.  **Model Training:**

    ```bash
    python src/models/gnn.py --data data/processed_data.csv --epochs 100
    ```

3.  **Feature Attribution and Validation:**

    ```bash
    python src/analysis/statistical_validation.py --model model.pth --data data/processed_data.csv
    ```

## Data Format

The input data should be a CSV file with the following columns:

*   `smiles`: SMILES string of the polymer.
*   `temperature`: Temperature during degradation (float).
*   `ph`: pH during degradation (float).
*   `uv_exposure`: UV exposure level during degradation (float).
*   `degradation_pathway`: Degradation pathway (string).

## Output

The project will generate the following outputs:

*   `data/processed_data.csv`: Processed dataset with filtered and converted data.
*   `model.pth`: Trained GNN model.
*   `report.txt`: Statistical report with feature importance scores and validation results.
