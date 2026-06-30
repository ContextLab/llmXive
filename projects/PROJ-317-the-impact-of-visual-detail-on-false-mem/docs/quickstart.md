# Quick Start Guide

This guide provides a step-by-step walkthrough to get the Visual Detail and False Memory research pipeline up and running.

## Prerequisites

- Python 3.11+
- pip
- Git (optional, for cloning)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-317-the-impact-of-visual-detail-on-false-mem

# Install dependencies
cd code
pip install -r requirements.txt
cd..
```

## Step 2: Create Project Structure

Run the setup script to create all necessary directories:

```bash
python code/setup_project_structure.py
```

This creates:
- `data/stimuli/`
- `data/stimuli_metadata/`
- `data/responses/`
- `data/processed/`
- `data/ethics/`
- `data/logs/`
- `figures/`

## Step 3: Generate Mock Stimuli

Since we are using mock data for development, generate synthetic images:

```bash
python code/cli.py manipulate --input code/data/sample_images --output data/stimuli
```

*Note: If `code/data/sample_images` is empty, the script will use the internal mock generator to create images.*

This will:
- Create enhanced and reduced detail versions of each image.
- Save manipulated images to `data/stimuli/`.
- Generate YAML metadata files in `data/stimuli_metadata/`.

## Step 4: Run Power Analysis

Calculate the required sample size:

```bash
python code/cli.py power-analysis
```

Check the output:
```bash
cat data/processed/power_analysis.json
```

## Step 5: Simulate Participant Sessions

Run a simulation with 10 participants:

```bash
python code/cli.py simulate --n-sessions 10 --output data/responses
```

This generates:
- Response data in `data/responses/`.
- Logs in `data/logs/`.

## Step 6: Analyze Data

Run the statistical analysis and generate visualizations:

```bash
python code/cli.py analyze --input data/responses --output data/processed
```

This produces:
- `data/processed/anova_results.json`
- `data/processed/bonferroni_results.json`
- `figures/false_memory_rates.png`

## Step 7: View Results

Open the generated visualization:

```bash
# On Linux
xdg-open figures/false_memory_rates.png

# On macOS
open figures/false_memory_rates.png

# On Windows
start figures/false_memory_rates.png
```

## Troubleshooting

- **Import Errors**: Ensure you are running scripts from the project root or adjust `PYTHONPATH`.
- **Missing Files**: Verify that `data/stimuli/` contains images before running the analyze command.
- **Log Files**: Check `data/logs/system.log` for detailed error messages.

## Next Steps

- Read the [Analysis Guide](analysis_guide.md) to understand the statistical methods.
- Review the [Ethics Guidelines](ethics/ethics_guidelines.md) before planning human subject studies.
- Explore the [API Reference](api_reference.md) for detailed function documentation.
