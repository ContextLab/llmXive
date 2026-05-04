"""
Baselines package for anomaly detection comparison.
Contains ARIMA, Moving Average, and LSTM Autoencoder baselines.
"""
from .arima import ARIMAConfig, ARIMAPrediction, ARIMABaseline, create_baseline, main as arima_main
from .moving_average import (
    MovingAverageConfig,
    MovingAveragePrediction,
    MovingAverageState,
    MovingAverageBaseline,
    create_baseline,
    main as ma_main,
)

__all__ = [
    "ARIMAConfig",
    "ARIMAPrediction",
    "ARIMABaseline",
    "create_baseline",
    "ARIMABaseline",
    "MovingAverageConfig",
    "MovingAveragePrediction",
    "MovingAverageState",
    "MovingAverageBaseline",
    "arima_main",
    "ma_main",
]
