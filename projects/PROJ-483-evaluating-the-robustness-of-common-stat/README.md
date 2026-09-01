# Evaluating the Robustness of Common Statistical Tests to Non-Independence

This project quantifies the inflation of Type I error rates and the reduction of statistical power in common statistical tests (t-test, ANOVA, Chi-squared) when the assumption of independence is violated.

## Motivation

Statistical tests like the t-test and ANOVA assume that observations are independent. In real-world datasets, this assumption is often violated due to temporal autocorrelation, hierarchical structures, or spatial proximity. This project investigates how these violations affect the reliability of statistical inference.

## Key Findings (Preliminary)

- **Type I Error Inflation**: As dependency strength ($r$) increases, the observed Type I error rate deviates significantly from the nominal $\alpha = 0.05$.
- **Power Reduction**: The presence of non-independence reduces the statistical power to detect true effects.
- **Test Sensitivity**: Different tests exhibit varying degrees of robustness to different dependency structures.

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd PROJ-483-evaluating-the-robustness-of-common-stat
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

## Usage

### 1. Data Preparation

Run the data loader to fetch and validate datasets:
```bash
python code/run_data_loader.py
```

This will download datasets from verified URLs (UCI/OpenML) and store them in `data/raw/`.

### 2. Run Simulation

Execute the main simulation pipeline:
```bash
python code/main.py
```

This will:
- Generate synthetic data under the null hypothesis.
- Inject dependency structures (AR(1), Block, Spatial).
- Run statistical tests.
- Aggregate results and calculate metrics.

### 3. Visualization

Generate plots of the results:
```bash
python code/visualizer.py --input results/aggregated.csv --output figures/
```

## Project Structure

- `code/`: Source code for the simulation pipeline.
- `data/`: Raw and processed datasets.
- `results/`: Simulation outputs (raw p-values, aggregated metrics).
- `docs/`: Design documentation.
- `tests/`: Unit and integration tests.

## Configuration

Edit `code/config.yaml` to adjust:
- Random seeds.
- Dependency strength values ($r$).
- Number of replications.
- Alpha levels for hypothesis testing.

## Requirements

- Python 3.10+
- numpy, scipy, pandas, statsmodels, matplotlib, seaborn, scikit-learn, requests, pyyaml

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- UCI Machine Learning Repository
- OpenML
- Statistical community for foundational methods.
