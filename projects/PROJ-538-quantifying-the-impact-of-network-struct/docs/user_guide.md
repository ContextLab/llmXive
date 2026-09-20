# User Guide

## Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- pip package manager
- git (for cloning the repository)

### Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify installation**:
 ```bash
 pytest tests/ -v --cov=code
 ```

## Running the Pipeline

### Basic Execution

To run the complete pipeline:
```bash
python -m code.main
```

This will automatically:
1. Check for real data availability
2. Ingest data (real or synthetic)
3. Construct defect networks
4. Calculate topological metrics
5. Perform statistical analysis
6. Generate visualizations
7. Save results to `data/processed/`

### Configuration Options

#### Running with Real Data
```bash
# Ensure real data sources are accessible
python -m code.main
```

The system will:
- Query OpenKim and Materials Cloud APIs
- If data is found, use real snapshots
- If not, automatically switch to synthetic mode

#### Running with Synthetic Data
```bash
# Force synthetic mode
export DATA_MODE=SYNTHETIC
python -m code.main
```

Or modify `code/config.py`:
```python
from config import RunMode, Config
Config.set_mode(RunMode.SYNTHETIC)
```

## Understanding the Output

### Audit Log (`data/audit_log.json`)
```json
{
 "query_status": "success",
 "found_count": 50,
 "metadata_completeness": 0.95,
 "timestamp": "2024-01-15T10:30:00Z"
}
```

### Processed Data
- **`raw_snapshots.parquet`**: Ingested atomic configurations
- **`defect_graphs.json`**: Network representations
- **`metrics.json`**: Topological descriptors
- **`correlation_results.json`**: Statistical correlations
- **`power_analysis_report.json`**: Power analysis results
- **`sensitivity_report.csv`**: Sensitivity analysis
- **`correlation_heatmap.png`**: Visual correlation matrix
- **`scatter_plots/`**: Individual metric plots

### Interpreting Results

#### Correlation Coefficients
- **Pearson**: Linear relationships (range: -1 to 1)
- **Spearman**: Monotonic relationships (range: -1 to 1)
- **p-value**: Statistical significance (typically < 0.05 is significant)
- **Bonferroni-corrected p-value**: Adjusted for multiple comparisons

#### Power Analysis
- **Minimum detectable effect size**: Smallest effect detectable with given sample size
- **Power**: Probability of detecting an effect if it exists (typically > 0.8 is desired)
- **Sample size warning**: If N < 20, results may be underpowered

#### Sensitivity Analysis
- **Rank stability**: Whether metric rankings change across significance thresholds
- **Magnitude difference**: Maximum change in correlation coefficient (should be < 0.1)

## Troubleshooting

### Common Issues

#### "DataAvailabilityError: Real data not found"
- **Cause**: Cannot reach external APIs or no data found
- **Solution**: System automatically switches to synthetic mode; no action needed

#### "VoronoiFailure: Tessellation failed"
- **Cause**: Invalid atomic coordinates or missing periodic boundary data
- **Solution**: Check input data integrity; system logs error and may use fallback method

#### "MemoryError"
- **Cause**: Dataset too large for available memory
- **Solution**: Enable streaming mode or reduce dataset size

#### "ImportError: No module named..."
- **Cause**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

### Debug Mode

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
python -m code.main
```

Check `data/audit_log.json` for detailed error messages.

## Advanced Usage

### Custom Data Sources

To use custom data sources:
1. Place data files in `data/raw/`
2. Modify `code/ingest.py` to include custom loader
3. Update `code/config.py` with data path

### Adding New Metrics

1. Implement calculation in `code/metrics.py`
2. Add to `MetricCalculator` class
3. Update `contracts/` schema if needed
4. Add visualization in `code/viz.py`

### Extending Statistical Tests

1. Add test method to `CorrelationAnalyzer` in `code/stats.py`
2. Update output schema in `contracts/`
3. Add results to `correlation_results.json`

## Best Practices

### Data Management
- Always check `data/audit_log.json` before running analysis
- Verify metadata completeness before proceeding
- Keep raw data separate from processed data

### Reproducibility
- Use fixed random seeds for synthetic generation
- Document all configuration changes
- Version control all code and configuration files

### Performance
- Process large datasets in chunks
- Cache intermediate results where possible
- Monitor memory usage during execution

### Validation
- Run unit tests before major changes
- Verify results against known benchmarks
- Check for edge cases (N=1, missing data, etc.)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review `data/audit_log.json` for error details
3. Consult the API reference for module documentation
4. Contact the project maintainers

## Contributing

We welcome contributions! Please see the main README for contribution guidelines.
