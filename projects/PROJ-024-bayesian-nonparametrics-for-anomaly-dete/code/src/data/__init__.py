"""
Data package for dataset handling and generation.
Contains dataset downloaders and synthetic data generators.
"""
from .synthetic_generator import (
    AnomalyConfig,
    SignalConfig,
    SyntheticDataset,
    generate_base_signal,
    inject_point_anomalies,
    inject_contextual_anomalies,
    inject_collective_anomalies,
    generate_synthetic_timeseries,
    save_synthetic_dataset,
    load_synthetic_dataset,
    generate_validation_dataset,
    main,
)

__all__ = [
    "AnomalyConfig",
    "SignalConfig",
    "SyntheticDataset",
    "generate_base_signal",
    "inject_point_anomalies",
    "inject_contextual_anomalies",
    "inject_collective_anomalies",
    "generate_synthetic_timeseries",
    "save_synthetic_dataset",
    "load_synthetic_dataset",
    "generate_validation_dataset",
    "main",
]
