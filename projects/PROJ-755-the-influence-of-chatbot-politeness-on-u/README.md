# The Influence of Chatbot Politeness on User-Perceived Quality

## Project Overview
This project investigates the relationship between chatbot politeness and user-perceived quality using the HCI_P2 dataset. It implements a robust statistical pipeline including data acquisition, politeness scoring, cumulative link mixed-effects modeling (CLMM), and robustness analysis.

## Environment Configuration

### Local Development
To run this project locally, you must configure your environment variables.

1. Create a `.env` file in the project root based on the template:
 ```bash
 cp code/.env.example.env
 ```
2. Edit `.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_actual_token_here
 ```

**Important**: The `.env` file contains sensitive credentials and must never be committed to version control. It is excluded via `.gitignore`.

### CI/CD and Reproducibility
For GitHub Actions and other CI environments, secrets must be injected via the platform's secret management system (e.g., GitHub Repository Secrets).

- Do **not** rely on `.env` files in CI.
- This ensures the pipeline runs reproducibly on fresh runners without local state, adhering to **Constitution Principle I**.

Example GitHub Actions usage:
```yaml
env:
 HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

## Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure R and required packages (`lme4`, `ordinal`) are installed for CLMM analysis.

## Usage
Run the pipeline scripts in order:
```bash
python code/01_download_and_score.py
python code/02_fit_clmm.py
python code/03_robustness_analysis.py
```

## Project Structure
- `code/`: Source code for the pipeline
- `data/`: Raw and processed data (excluded from git)
- `tests/`: Unit and integration tests
- `contracts/`: Schema definitions
- `docs/`: Documentation

## License
[License Information]

## Contributors
[Contributor List]