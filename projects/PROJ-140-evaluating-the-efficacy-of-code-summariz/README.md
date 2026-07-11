# PROJ-140: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

This project implements a human-subject study to evaluate how different code summarization techniques (LLM-generated, rule-based, and baseline) affect bug localization accuracy and speed.

## Table of Contents

- [Installation](#installation)
- [Data Preparation](#data-preparation)
- [Running the Analysis Pipeline](#running-the-analysis-pipeline)
- [Expected Outputs](#expected-outputs)
- [Reproducibility](#reproducibility)
- [Contributing](#contributing)

---

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd PROJ-140
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure environment variables (optional, for custom paths):
 ```bash
 cp.env.example.env
 # Edit.env as needed
 ```

---

## Data Preparation

Before running the analysis, ensure the required data is prepared:

1. **Download Defects4J dataset**:
 ```bash
 python code/data_prep/download_defects4j.py
 ```
 This will fetch and extract 60 stratified buggy methods into `data/defects4j/`.

2. **Generate code summaries**:
 ```bash
 python code/data_prep/generate_summaries.py
 ```
 This produces:
 - `data/summaries/llm_sim_summaries.csv` (deterministic LLM simulation)
 - `data/summaries/rule_summaries.csv` (rule-based summaries)

3. **Run the study (optional)**:
 If you are conducting the human subject study, follow the instructions in `docs/study_protocol.md` to collect interaction logs.

---

## Running the Analysis Pipeline

Once data is prepared, run the statistical analysis pipeline:

```bash
python code/analysis/run_statistics.py
```

This script performs the following steps:

1. Loads anonymized interaction logs from `data/interaction_logs/anonymized_logs.csv`.
2. Computes Top-K accuracy and speed metrics.
3. Runs McNemar's tests for accuracy comparisons.
4. Runs Linear Mixed-Effects (LME) models for speed analysis.
5. Computes effect sizes (Odds Ratios, Cohen's d) with bootstrapped confidence intervals.
6. Applies Holm-Bonferroni correction for multiple comparisons.
7. Performs sensitivity analysis across different significance thresholds.
8. Detects outliers and flags them.

**Note**: Ensure that `data/interaction_logs/anonymized_logs.csv` exists before running this script. If you have not conducted the study, you can use a synthetic dataset for testing purposes (see `code/tests/test_statistics.py` for examples).

---

## Expected Outputs

After running `code/analysis/run_statistics.py`, the following files will be generated in `data/analysis_results/`:

- `results.csv`: Main analysis results containing accuracy, speed, p-values, effect sizes, and corrected p-values.
- `sensitivity_analysis.csv`: Results of the sensitivity analysis across different significance thresholds (0.01, 0.05, 0.10).
- `outlier_flags.json`: JSON file listing detected outliers and their details.
- `correction_results.json`: Holm-Bonferroni correction details.
- `bootstrap_results.json`: Bootstrapped confidence intervals for effect sizes.

Example snippet from `results.csv`:

| comparison | metric | value | p_value | corrected_p | effect_size | ci_lower | ci_upper |
|------------|--------|-------|---------|-------------|-------------|----------|----------|
| baseline_vs_llm | accuracy | 0.75 | 0.003 | 0.009 | 2.1 | 1.3 | 3.4 |
| baseline_vs_rule | speed | 12.5s | 0.045 | 0.090 | 0.8 | 0.1 | 1.5 |

---

## Reproducibility

This project is designed to be reproducible on GitHub Actions free-tier (≤6h runtime, ≤7GB RAM, no GPU).

To verify reproducibility:

1. Run the baseline generation script:
 ```bash
 python code/utils/generate_baseline_results.py
 ```
 This creates `data/analysis_results/baseline_results.json` as the ground truth.

2. Run the CI reproducibility test:
 ```bash
.github/workflows/test_reproducibility.yml
 ```
 This workflow:
 - Installs dependencies.
 - Runs `code/analysis/run_statistics.py`.
 - Verifies runtime ≤6h and memory ≤7GB.
 - Checks that results match `baseline_results.json` within 5% numerical tolerance.

For local reproducibility testing, you can also run:
```bash
python code/tests/test_reproducibility.py
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run tests to ensure everything works.
5. Submit a pull request.

For more details, see `CONTRIBUTING.md`.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.