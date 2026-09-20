"""
Basic smoke tests to ensure all core modules can be imported.
"""
import pytest
import sys
from pathlib import Path

def test_import_models():
    from models import AtomicSnapshot, DefectGraph
    assert AtomicSnapshot is not None
    assert DefectGraph is not None

def test_import_utils():
    from utils import DataAvailabilityError, VoronoiFailure, get_logger
    assert DataAvailabilityError is not None
    assert VoronoiFailure is not None

def test_import_config():
    from config import RunMode, Config
    assert RunMode is not None
    assert Config is not None

def test_import_ingest():
    from ingest import DefectGraphBuilder, run_ingestion_pipeline
    assert DefectGraphBuilder is not None

def test_import_metrics():
    from metrics import MetricCalculator
    assert MetricCalculator is not None

def test_import_stats():
    from stats import CorrelationAnalyzer, run_post_hoc_power_analysis
    assert CorrelationAnalyzer is not None

def test_import_viz():
    from viz import VisualizationEngine, run_visualization_pipeline
    assert VisualizationEngine is not None

def test_import_synthetic():
    from synthetic import ThermalConductivityEstimator, run_synthetic_generation
    assert ThermalConductivityEstimator is not None
