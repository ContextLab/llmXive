"""
Models package for GNN anomaly detection and baselines.

This package contains:
- GCN implementation (gcn.py)
- Baseline models (baselines.py)
- Metrics calculation (metrics.py)
"""

from .gcn import GCNAnomalyDetector, train_gcn, load_graph_data, main
from .baselines import FeatureEngineeredBaseline, extract_structural_features, main as baseline_main
from .metrics import MetricCalculator, load_config_threshold, check_target_auc, save_metrics, main as metrics_main

__all__ = [
    'GCNAnomalyDetector',
    'train_gcn',
    'load_graph_data',
    'main',
    'FeatureEngineeredBaseline',
    'extract_structural_features',
    'baseline_main',
    'MetricCalculator',
    'load_config_threshold',
    'check_target_auc',
    'save_metrics',
    'metrics_main'
]