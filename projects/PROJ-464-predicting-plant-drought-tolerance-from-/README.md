# Predicting Plant Drought Tolerance from RSA Data

This repository contains the code, data, and analysis pipeline for the project **Predicting Plant Drought Tolerance from Root System Architecture (RSA) Data**.

## Overview

The goal of this project is to investigate whether quantitative RSA metrics extracted from publicly‑available root images can be associated with drought‑tolerance physiological traits (e.g., stomatal conductance, photosynthetic rate). The pipeline downloads raw data, extracts RSA features, merges them with TRY physiological traits, performs statistical modelling (including VIF checks, PCA, phylogenetic correction, regression, and classification), and generates a reproducible scientific report.

## Repository Structure

```
data/
 raw/ # Downloaded raw images and trait files
 derived/ # Processed CSVs, PCA results, model artifacts
code/ # All pipeline scripts and utilities
tests/ # Unit, integration, and contract tests
results/ # Final figures, tables, and reports
state/ # Execution state, logs, and intermediate YAML files
contracts/ # JSON‑Schema contracts for output validation
docs/ # Documentation and quick‑start guides
```

## Getting Started

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-464-predicting-plant-drought-tolerance-from-
 ```

2. **Create a virtual environment and install dependencies**
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Run the full pipeline**
 ```bash
 python code/run_pipeline.py
 ```

For more detailed instructions see `docs/quickstart.md`.

## Contributing

Contributions are welcome. Please follow the contribution guidelines in `CONTRIBUTING.md` and ensure all tests pass before submitting a pull request.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
