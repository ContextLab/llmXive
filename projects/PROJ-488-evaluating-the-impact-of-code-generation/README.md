# Evaluating the Impact of Code Generation (PROJ-488)

This project evaluates the impact of LLM-generated code (CodeParrot/CodeGen) versus human-written code (CodeSearchNet) using static analysis metrics (radon, pylint) and statistical testing (Mann-Whitney U, Cliff's delta).

## ⚠️ Constitutional Amendment Status

**CRITICAL**: Before running the pipeline, ensure that the Constitutional Amendment PRs have been approved and merged:
- **Amendment VI**: Permitting use of CodeParrot/CodeGen as the LLM-generated code source.
- **Amendment VII**: Permitting use of radon and pylint for metric extraction.

Check the current status in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` under `amendment_status`. **Do not proceed** if amendments are not marked as `approved`.

## Prerequisites

- Python 3.11+
- pip
- Access to HuggingFace datasets (internet connection required)

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

### End-to-End Pipeline

To run the full pipeline (Data Ingestion → Preprocessing → Metric Extraction → Statistical Analysis → Visualization):

```bash
python code/main.py --run-all
```

This command will:
1. Verify amendment status.
2. Download and preprocess datasets (CodeSearchNet, CodeParrot/CodeGen).
3. Filter for Python functions and balance lengths.
4. Extract static analysis metrics.
5. Perform statistical comparisons.
6. Generate visualizations and guidelines.

### Step-by-Step Execution

If you prefer to run stages individually:

1. **Data Ingestion & Preprocessing**:
 ```bash
 python code/data_ingestion.py
 python code/data_filtering.py
 python code/length_filtering.py
 ```

2. **Metric Extraction**:
 ```bash
 python code/metric_extraction.py
 ```

3. **Statistical Analysis**:
 ```bash
 python code/statistical_analysis.py
 python code/cliffs_delta_analysis.py
 python code/run_bh_correction.py
 ```

4. **Visualization**:
 ```bash
 python code/visualization.py
 ```

5. **Guideline Generation**:
 ```bash
 python code/guideline_generator.py
 ```

## Output Artifacts

- **Processed Data**: `data/processed/`
- **Metrics**: `data/metrics/`
- **Figures**: `results/figures/`
- **Reports**: `results/` (guidelines.md, sensitivity.md, justification.md, etc.)
- **State**: `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`

## Project Structure

```
.
├── code/ # Source code modules
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Filtered and sampled data
│ └── metrics/ # Aggregated metric scores
├── results/ # Final outputs (figures, reports)
├── state/ # Pipeline state and hashes
├── specs/ # Design documents
├── tests/ # Unit and integration tests
├── README.md
├── quickstart.md
└── requirements.txt
```

## License

This project follows the llmXive research pipeline guidelines.