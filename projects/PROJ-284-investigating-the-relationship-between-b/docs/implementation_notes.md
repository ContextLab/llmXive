# Implementation Notes

Technical details and design decisions for the Brain Network Dynamics pipeline.

## 1. Architecture

The pipeline is designed as a series of independent, modular stages. Each stage (download, preprocess, metrics, analysis, viz, report) can be executed independently, allowing for flexibility in debugging and partial updates.

## 2. Data Flow

```
Raw Data (HCP) -> Preprocessing -> Clean NIfTI -> Time-Series -> Connectivity Matrix -> Graph Metrics -> Correlation Analysis -> Visualization & Report
```

## 3. Key Algorithms

- **Motion Correction:** FSL `mcflirt` (rigid body registration).
- **Slice-Time Correction:** AFNI `3dTshift`.
- **Normalization:** AFNI `3dQwarp` (non-linear registration to MNI space).
- **Connectivity:** Pearson correlation of ROI time-series.
- **Graph Metrics:** NetworkX implementation of Modularity, Global Efficiency, Participation Coefficient, Within-Module Degree.
- **Statistical Correction:** Benjamini-Hochberg FDR.

## 4. Memory Management

- **Dynamic Batch Sizing:** The pipeline calculates the optimal batch size based on available RAM (default 7GB) to prevent OOM errors during matrix computation.
- **Lazy Loading:** Large files (NIfTI, matrices) are loaded on demand and garbage collected when no longer needed.

## 5. Error Handling

- **Retry Logic:** All network requests to the HCP API include exponential backoff retry logic.
- **Validation:** Preprocessing steps include validation (tSNR, motion) to ensure data quality.
- **Logging:** Structured logging to `logs/pipeline.log` for traceability.

## 6. Testing Strategy

- **Unit Tests:** Test individual functions with mock data.
- **Integration Tests:** Test end-to-end flow with synthetic data.
- **Contract Tests:** Verify API contracts (e.g., HCP fetcher returns NIfTI).
- **CI Validation:** Full pipeline logic validated on CI using synthetic data (since FSL/AFNI are not available on standard runners).

## 7. Future Improvements

- **Dynamic Connectivity:** Implement sliding window correlation for time-varying connectivity.
- **Machine Learning:** Add classification/regression models to predict motor scores from network metrics.
- **Interactive Visualizations:** Use Plotly or similar for interactive network diagrams.
- **Parallel Processing:** Use multiprocessing to speed up subject-level processing.

## 8. Dependencies

- **Nilearn:** For neuroimaging data handling and plotting.
- **NetworkX:** For graph metric calculation.
- **Scikit-learn:** For PCA and statistical utilities.
- **Statsmodels:** For power analysis and advanced statistical tests.
- **Matplotlib/Seaborn:** For static visualizations.

## 9. Known Limitations

- **Scalability:** Processing large cohorts (N > 1000) may require distributed computing.
- **Tool Dependencies:** Full preprocessing requires FSL/AFNI, which are heavy dependencies.
- **Data Access:** HCP data access requires approval and credentials.

## 10. Contact

For technical questions, refer to the project maintainers or open an issue on the repository.