# API Reference

## Code Modules

### `code/config.py`

#### Classes
- **RunMode**: Enum defining execution modes
 - `REAL`: Use real data from external sources
 - `SYNTHETIC`: Generate synthetic data

- **Config**: Configuration management class
 - Methods:
 - `get_data_path()`: Returns data directory path
 - `get_mode()`: Returns current run mode
 - `set_mode(mode: RunMode)`: Sets execution mode

### `code/ingest.py`

#### Classes
- **DefectGraphBuilder**: Constructs defect networks from atomic data
 - Methods:
 - `build_graph(snapshot: AtomicSnapshot) -> DefectGraph`: Builds graph from snapshot
 - `validate_graph(graph: DefectGraph) -> bool`: Validates graph structure

- **DataAudit**: Audits data availability
 - Methods:
 - `query_openkim(elements: List[str]) -> Dict`: Queries OpenKim API
 - `query_materials_cloud(elements: List[str]) -> Dict`: Queries Materials Cloud API
 - `generate_audit_log() -> None`: Writes audit log to disk

- **RealDataLoader**: Loads real data from external sources
 - Methods:
 - `load_snapshots() -> List[AtomicSnapshot]`: Loads atomic snapshots
 - `validate_metadata(snapshot: AtomicSnapshot) -> bool`: Validates metadata

- **SyntheticDataGenerator**: Generates synthetic data
 - Methods:
 - `generate_snapshots(n: int, seed: int) -> List[AtomicSnapshot]`: Generates snapshots

- **ThermalConductivityEstimator**: Estimates thermal conductivity
 - Methods:
 - `estimate(snapshot: AtomicSnapshot) -> float`: Estimates conductivity

#### Functions
- `run_ingestion_pipeline() -> None`: Orchestrates data ingestion

### `code/synthetic.py`

#### Classes
- **ThermalConductivityEstimator**: Implements Callaway model
 - Methods:
 - `estimate(defect_density: float, mass_diff: float) -> float`: Estimates conductivity

#### Functions
- `run_synthetic_generation() -> None`: Generates synthetic data

### `code/metrics.py`

#### Classes
- **MetricCalculator**: Computes topological metrics
 - Methods:
 - `calculate_clustering_coefficient(graph: DefectGraph) -> float`: Clustering coefficient
 - `calculate_mean_degree(graph: DefectGraph) -> float`: Mean degree
 - `calculate_degree_moments(graph: DefectGraph) -> Dict`: Degree distribution moments
 - `calculate_percolation_threshold(graph: DefectGraph) -> float`: Percolation threshold

### `code/stats.py`

#### Classes
- **CorrelationAnalyzer**: Performs statistical correlation analysis
 - Methods:
 - `pearson_correlation(x: List, y: List) -> Tuple[float, float]`: Pearson correlation
 - `spearman_correlation(x: List, y: List) -> Tuple[float, float]`: Spearman correlation
 - `apply_bonferroni_correction(p_values: List[float]) -> List[float]`: Bonferroni correction

#### Functions
- `run_post_hoc_power_analysis() -> Dict`: Performs power analysis
- `run_sensitivity_analysis() -> None`: Performs sensitivity analysis

### `code/viz.py`

#### Classes
- **VisualizationEngine**: Generates visualizations
 - Methods:
 - `generate_scatter_plot(x: List, y: List, title: str) -> None`: Scatter plot
 - `generate_correlation_heatmap(correlations: Dict) -> None`: Correlation heatmap

#### Functions
- `run_visualization_pipeline() -> None`: Orchestrates visualization generation

### `code/models.py`

#### Pydantic Models
- **AtomicSnapshot**: Atomic configuration data
 - Fields: `atoms`, `species`, `coordinates`, `box`, `thermal_conductivity_W_m_K`

- **DefectGraph**: Network representation
 - Fields: `nodes`, `edges`, `metadata`

- **CorrelationResult**: Correlation analysis output
 - Fields: `metric`, `correlation_coefficient`, `p_value`, `method`

- **SensitivityResult**: Sensitivity analysis output
 - Fields: `threshold`, `correlation_coefficient`, `p_value`, `rank_stability_flag`

- **PowerAnalysisResult**: Power analysis output
 - Fields: `minimum_detectable_effect_size`, `power`, `sample_size`

### `code/utils.py`

#### Exceptions
- **DataAvailabilityError**: Raised when real data unavailable
- **VoronoiFailure**: Raised when Voronoi tessellation fails

#### Functions
- `get_logger(name: str) -> logging.Logger`: Gets logger instance
- `log_audit_event(event: Dict) -> None`: Logs audit event to file

### `code/interfaces.py`

#### Abstract Classes
- **IVoronoiNeighborFinder**: Interface for neighbor detection
 - Methods:
 - `find_neighbors(atoms: np.ndarray, species: List[str], box: np.ndarray) -> List[Tuple[int, int]]`: Finds neighbors

### `code/main.py`

#### Functions
- `run_pipeline() -> None`: Main pipeline orchestrator

## Data Contracts

### `contracts/atomic_snapshot.schema.yaml`
JSON Schema for `AtomicSnapshot` model

### `contracts/defect_graph.schema.yaml`
JSON Schema for `DefectGraph` model

### `contracts/correlation_result.schema.yaml`
JSON Schema for `CorrelationResult` model

### `contracts/sensitivity_result.schema.yaml`
JSON Schema for `SensitivityResult` model

### `contracts/power_analysis.schema.yaml`
JSON Schema for `PowerAnalysisResult` model

## Output Files

### `data/audit_log.json`
- Contains: `query_status`, `found_count`, `metadata_completeness`
- Generated by: `DataAudit`

### `data/processed/raw_snapshots.parquet`
- Contains: Ingested atomic snapshots
- Generated by: `RealDataLoader` or `SyntheticDataGenerator`

### `data/processed/metrics.json`
- Contains: Topological metrics for each graph
- Generated by: `MetricCalculator`

### `data/processed/correlation_results.json`
- Contains: Correlation analysis results
- Generated by: `CorrelationAnalyzer`

### `data/processed/power_analysis_report.json`
- Contains: Power analysis results
- Generated by: `run_post_hoc_power_analysis`

### `data/processed/sensitivity_report.csv`
- Contains: Sensitivity analysis results
- Columns: `threshold`, `correlation_coefficient`, `p_value`, `rank_stability_flag`
- Generated by: `run_sensitivity_analysis`

### `data/processed/correlation_heatmap.png`
- 300 DPI correlation heatmap
- Generated by: `VisualizationEngine`

### `data/processed/scatter_plots/`
- Individual scatter plots for each metric
- Generated by: `VisualizationEngine`

## Configuration

### Environment Variables
- `DATA_MODE`: Set to `REAL` or `SYNTHETIC`
- `DATA_PATH`: Custom data directory path
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Configuration File
- `code/config.py`: Central configuration management
- Key settings:
 - `RunMode`: Execution mode
 - Data paths
 - Logging configuration
 - API endpoints for real data sources
