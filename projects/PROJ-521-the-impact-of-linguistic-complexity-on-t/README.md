# The Impact of Linguistic Complexity on Trust in AI‑Generated Text

**Project ID:** PROJ‑521
**Branch:** `001‑linguistic‑complexity‑trust`

## Overview

This research project investigates whether linguistic complexity in AI‑generated text (e.g., sentence structure, lexical diversity) predicts readers’ trust ratings when the source is explicitly identified as AI‑generated.

The pipeline consists of three main stages:

1. **Data Generation** – Sample Wikipedia articles, generate AI‑generated text samples with the Gemma‑2B model, and compute objective complexity metrics (Flesch‑Kincaid, MTLD, average sentence length).
2. **Trust Collection** – Present the generated samples to participants (simulated for CI, real via Prolific for production) and record 5‑point Likert trust ratings, applying attention‑check filtering.
3. **Statistical Analysis** – Perform separate univariate linear regressions (including quadratic terms) for each complexity metric, apply Bonferroni correction, conduct post‑hoc power analysis, and run an ordinal logistic regression as a sensitivity check. Visualizations of the fitted Trust‑vs‑Complexity curves are saved as PNG files.

All scripts are pure Python, CPU‑only, and reproducible via fixed random seeds.

## Repository Structure

```text
projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/
├── code/ # Core CLI scripts
│ ├── generate_text.py
│ ├── collect_trust.py
│ ├── analyze.py
│ ├── utils.py
│ └── requirements.txt
├── data/
│ ├── raw/
│ │ ├── generated_text.csv
│ │ └── trust_responses.csv
│ ├── processed/
│ │ ├── cleaned_responses.csv
│ │ └── analysis_inputs.csv
│ └── outputs/
│ ├── regression_results.json
│ └── figures/
├── specs/
│ └── 001-the-impact-of-linguistic-complexity-on-t/
│ ├── spec.md
│ ├── plan.md
│ ├── research.md
│ ├── data-model.md
│ ├── quickstart.md
│ └── contracts/
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
└── state/
 └── projects/
 └── PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml
```

## Installation

1. **Clone the repository**
 ```bash
 git clone https://github.com/your-org/your-repo.git
 cd your-repo
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code/requirements.txt
 ```

4. **(Optional) Set environment variables for Prolific**
 ```bash
 export PROLIFIC_API_KEY="your-api-key"
 ```

## Quickstart – Running the Full Pipeline

```bash
# Step 1: Generate text samples
cd projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code
python generate_text.py --num-samples 200 --seed 42

# Step 2: Collect trust ratings (simulation for CI)
python collect_trust.py --simulate --num-participants 100 --seed 42

# Step 3: Analyze the data
python analyze.py --input data/processed/analysis_inputs.csv --output data/outputs/
```

After the analysis completes you will find:

- `data/outputs/regression_results.json` – regression coefficients, p‑values, Bonferroni‑adjusted results, and power‑analysis output.
- `data/outputs/figures/` – PNG visualizations of Trust vs. each complexity metric with fitted curves and 95 % confidence intervals.

## Testing

```bash
# Unit tests
pytest tests/unit/

# Contract (schema) tests
pytest tests/contract/

# End‑to‑end integration test
pytest tests/integration/
```

## Contributing

Contributions are welcome. Please follow the existing code style (ruff + black) and ensure all new tests pass. Update the `state` YAML file when adding new data artifacts to keep checksums in sync.

## License

This project is licensed under the MIT License.