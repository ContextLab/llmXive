# Design Document

## Architecture
The pipeline is modular, consisting of distinct stages:
1. **Data Ingestion**: Download and validate experimental barrier datasets.
2. **Descriptor Generation**: Compute quantum chemical descriptors using DFTB+ (semi-empirical) and Psi4 (DFT).
3. **Model Training**: Train Random Forest models on generated descriptors.
4. **Evaluation**: Compare model performance (MAE) and computational cost.

## Data Flow
Raw Data (Zenodo) -> CSV -> Descriptors (CSV) -> Models (Pickle) -> Reports (Markdown/JSON)

## Error Handling
Convergence failures in quantum calculations are caught, logged, and skipped to ensure pipeline robustness. Memory usage is monitored to prevent OOM crashes.
