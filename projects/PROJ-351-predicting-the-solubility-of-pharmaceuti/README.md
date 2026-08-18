# Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This project implements a comparative study of traditional machine learning (Random Forest) and Graph Neural Networks (MPNN) for predicting the water solubility (logS) of pharmaceutical compounds using the ESOL dataset.

## 🚀 Quick Start

See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for step-by-step instructions to run the full pipeline.

## 📦 Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## 🏗️ Architecture

The project is organized into modular components:

- **`code/`**: Source code for data processing, modeling, and evaluation.
- **`data/`**: Raw and processed datasets, logs.
- **`models/`**: Trained model artifacts.
- **`results/`**: Evaluation metrics, predictions, and visualizations.
- **`tests/`**: Unit and integration tests.
- **`docs/`**: Detailed documentation.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a deep dive into the system design.

## 📊 Methodology

1. **Data Source**: ESOL dataset from MoleculeNet (via HuggingFace Datasets).
2. **Baseline**: Random Forest Regressor using Morgan Fingerprints (radius=2, 2048 bits).
3. **Model**: Message Passing Neural Network (MPNN) implemented in PyTorch Geometric.
4. **Evaluation**: RMSE, R², Paired T-Test, and Power Analysis.
5. **Constraints**: CPU-only execution, <6h training time, strict real-data usage (no synthetic fallbacks).

## 📈 Results

Key results are stored in `results/`:

- `baseline_metrics.json`: Performance of the Random Forest model.
- `gnn_metrics.json`: Performance of the GNN model.
- `model_comparison.json`: Delta analysis between models.
- `final_report.json`: Comprehensive summary including statistical significance.

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

## 🛡️ Reproducibility

Reproducibility is ensured by:
- Pinned random seeds (`code/config/seeds.py`).
- Deterministic data splitting (stratified by logS).
- Checksum verification of downloaded datasets.

## 📝 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Quick Start Guide](docs/QUICKSTART.md)
- [API Reference](docs/API.md) (Coming Soon)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a PR.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- ESOL dataset from MoleculeNet.
- PyTorch Geometric team.
- RDKit community.
