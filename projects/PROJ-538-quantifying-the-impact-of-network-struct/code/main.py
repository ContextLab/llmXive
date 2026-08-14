"""
Main entry point for the pipeline.
Orchestrates data loading, graph construction, metrics, and stats.
"""
import sys
from .config import config, RunMode
from .ingest import RealDataLoader, SyntheticDataGenerator, DefectGraphBuilder, DataAudit
from .metrics import MetricCalculator
from .stats import CorrelationAnalyzer
from .utils import DataAvailabilityError, get_logger
import json

logger = get_logger(__name__, str(config.logs_dir / "main.log"))

def run_pipeline(mode: RunMode = "audit"):
    logger.info(f"Starting pipeline in mode: {mode}")
    
    config.run_mode = mode

    # 1. Data Ingestion
    snapshots = []
    if mode == "real":
        loader = RealDataLoader()
        try:
            snapshots = loader.fetch("Cu-Ni") # Example material
        except DataAvailabilityError as e:
            logger.error(f"Real data fetch failed: {e}")
            # In a real orchestrator, we might switch to synthetic here
            # But per constraints, we let the error propagate if real is required
            raise e
    elif mode == "synthetic":
        generator = SyntheticDataGenerator()
        snapshots = generator.generate(config.n_snapshots, config.n_atoms, ["Cu", "Ni"])
    elif mode == "audit":
        # Just check availability
        audit = DataAudit()
        # Try real, if fail, report
        try:
            loader = RealDataLoader()
            _ = loader.fetch("Cu-Ni")
        except DataAvailabilityError:
            logger.info("Audit: Real data not available. Switching to synthetic for demo.")
            generator = SyntheticDataGenerator()
            snapshots = generator.generate(5, 100, ["Cu", "Ni"])

    if not snapshots:
        logger.error("No snapshots loaded.")
        return

    # 2. Graph Construction
    builder = DefectGraphBuilder()
    graphs = []
    for snap in snapshots:
        graph = builder.build(snap)
        graphs.append(graph)

    # 3. Metric Extraction
    calculator = MetricCalculator()
    metrics_list = []
    for graph in graphs:
        metrics = calculator.calculate(graph)
        metrics_list.append(metrics)

    # 4. Statistical Analysis
    conductivities = [s.thermal_conductivity_W_m_K for s in snapshots]
    analyzer = CorrelationAnalyzer()
    results = analyzer.analyze(metrics_list, conductivities)

    # 5. Output
    output_path = config.processed_dir / "results_summary.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pipeline complete. Results saved to {output_path}")

if __name__ == "__main__":
    run_pipeline()
