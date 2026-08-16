"""
Main entry point for the pipeline.
Orchestrates data loading, graph construction, metrics, and stats.
"""
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Relative imports based on provided API surface
from .config import config, RunMode
from .ingest import RealDataLoader, SyntheticDataGenerator, DefectGraphBuilder, DataAudit
from .metrics import MetricCalculator
from .stats import CorrelationAnalyzer
from .utils import DataAvailabilityError, get_logger, log_audit_event

logger = get_logger(__name__, str(config.logs_dir / "main.log"))

def run_pipeline(mode: RunMode = "audit"):
    """
    Orchestrates the full research pipeline:
    1. Data Ingestion (Real or Synthetic)
    2. Graph Construction
    3. Metric Extraction (Integration of T021-T023)
    4. Statistical Analysis
    5. Output Generation
    """
    logger.info(f"Starting pipeline in mode: {mode}")
    config.run_mode = mode

    # Ensure output directories exist
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Data Ingestion
    snapshots = []
    try:
        if mode == "real":
            loader = RealDataLoader()
            # Attempt to fetch real data; will raise DataAvailabilityError if not found
            snapshots = loader.fetch("Cu-Ni") 
        elif mode == "synthetic":
            generator = SyntheticDataGenerator()
            snapshots = generator.generate(config.n_snapshots, config.n_atoms, ["Cu", "Ni"])
        elif mode == "audit":
            # Just check availability
            audit = DataAudit()
            try:
                loader = RealDataLoader()
                _ = loader.fetch("Cu-Ni")
                logger.info("Audit: Real data available. Proceeding with real data.")
                snapshots = loader.fetch("Cu-Ni")
            except DataAvailabilityError:
                logger.info("Audit: Real data not available. Switching to synthetic for demo.")
                generator = SyntheticDataGenerator()
                snapshots = generator.generate(5, 100, ["Cu", "Ni"])
        else:
            logger.error(f"Unknown run mode: {mode}")
            return

        if not snapshots:
            logger.error("No snapshots loaded. Pipeline aborting.")
            return

        log_audit_event("DATA_INGESTION_COMPLETE", {
            "mode": mode,
            "count": len(snapshots),
            "status": "success"
        })

    except DataAvailabilityError as e:
        logger.critical(f"Data ingestion failed: {e}")
        raise e

    # 2. Graph Construction
    logger.info("Constructing defect graphs...")
    builder = DefectGraphBuilder()
    graphs = []
    for i, snap in enumerate(snapshots):
        try:
            graph = builder.build(snap)
            graphs.append(graph)
        except Exception as e:
            logger.error(f"Failed to build graph for snapshot {i}: {e}")
            raise e
    
    log_audit_event("GRAPH_CONSTRUCTION_COMPLETE", {
        "count": len(graphs),
        "status": "success"
    })

    # 3. Metric Extraction (Integration of T021-T023)
    # This step specifically integrates the MetricCalculator which encapsulates
    # Clustering Coefficient, Mean Degree, Moments, and Percolation Threshold.
    logger.info("Extracting topological metrics...")
    calculator = MetricCalculator()
    metrics_list = []
    for i, graph in enumerate(graphs):
        try:
            metrics = calculator.calculate(graph)
            metrics_list.append(metrics)
            logger.debug(f"Metrics for graph {i}: {metrics.get('mean_degree', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to calculate metrics for graph {i}: {e}")
            raise e

    log_audit_event("METRIC_EXTRACTION_COMPLETE", {
        "count": len(metrics_list),
        "status": "success"
    })

    # 4. Statistical Analysis
    logger.info("Performing statistical correlation analysis...")
    conductivities = [s.thermal_conductivity_W_m_K for s in snapshots]
    analyzer = CorrelationAnalyzer()
    
    try:
        results = analyzer.analyze(metrics_list, conductivities)
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise e

    log_audit_event("STATISTICAL_ANALYSIS_COMPLETE", {
        "status": "success",
        "metrics_analyzed": len(metrics_list[0]) if metrics_list else 0
    })

    # 5. Output
    output_path = config.processed_dir / "results_summary.json"
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Pipeline complete. Results saved to {output_path}")
        log_audit_event("PIPELINE_COMPLETE", {
            "output_file": str(output_path),
            "status": "success"
        })
    except IOError as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise e

if __name__ == "__main__":
    # Allow running as script for testing, though typically imported
    # Determine mode from args or default to 'audit'
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "audit"
    run_pipeline(mode_arg)