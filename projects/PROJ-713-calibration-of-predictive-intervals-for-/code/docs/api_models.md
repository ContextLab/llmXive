# Models API Documentation

This document provides the API reference for the forecasting models implemented in `code/models/`.
Each model follows a unified interface to ensure interchangeability within the evaluation pipeline.

## Base Interface

All models inherit from a conceptual base interface requiring the following methods:
- `fit(train_series: pd.Series) -> None`: Fits the model to training data.
- `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`: Returns point forecasts, lower bounds, and upper bounds.
- `get_params() -> Dict[str, Any]`: Returns model configuration parameters.

---

## ARIMAModel

**File**: `code/models/arima_model.py`

**Description**:
Wrapper around `statsmodels.tsa.arima.model.ARIMA` and `statsmodels.tsa.statespace.sarimax.SARIMAX`.
Generates prediction intervals using conditional variance methods to comply with FR-003.

### Class: `ARIMAModel`

**Constructor**:
```python
ARIMAModel(order: Tuple[int, int, int], seasonal_order: Optional[Tuple[int, int, int, int]] = None,
 conf_level: float = 0.95, maxiter: int = 50)
```
- `order`: (p, d, q) ARIMA parameters.
- `seasonal_order`: (P, D, Q, s) seasonal parameters.
- `conf_level`: Confidence level for intervals (default 0.95).
- `maxiter`: Maximum iterations for model convergence.

**Methods**:
- `fit(train_series: pd.Series) -> None`:
 Fits the model. Raises `ModelConvergenceError` if the model fails to converge after `maxiter` attempts.
- `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`:
 Returns:
 1. `point_forecast`: Array of predicted values.
 2. `lower_bound`: Array of lower interval bounds.
 3. `upper_bound`: Array of upper interval bounds.

 Intervals are calculated using `conf_int` with `method='conditional'` (or equivalent explicit parameter) as per specification.
- `get_params() -> Dict[str, Any]`:
 Returns the configuration dictionary.

**Dependencies**:
- `statsmodels`
- `numpy`
- `pandas`

---

## ProphetModel

**File**: `code/models/prophet_model.py`

**Description**:
Wrapper around `fbprophet.Prophet`. Generates intervals by simulating uncertainty in trend changepoints and seasonalities.

### Class: `ProphetModel`

**Constructor**:
```python
ProphetModel(conf_level: float = 0.95, uncertainty_samples: int = 1000,
 growth: str = 'linear', changepoint_prior_scale: float = 0.05)
```
- `conf_level`: Target confidence level.
- `uncertainty_samples`: Number of samples for interval simulation (default 1000).
- `growth`: Growth type ('linear', 'logistic', 'flat').
- `changepoint_prior_scale`: Regularization parameter for changepoints.

**Methods**:
- `fit(train_series: pd.Series) -> None`:
 Prepares data (converts to Prophet format with 'ds' and 'y') and fits the model.
- `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`:
 Predicts future values and extracts `yhat_lower` and `yhat_upper` from the forecast dataframe.
- `get_params() -> Dict[str, Any]`:
 Returns the configuration dictionary.

**Dependencies**:
- `prophet`
- `numpy`
- `pandas`

---

## LSTMModel

**File**: `code/models/lstm_model.py`

**Description**:
PyTorch-based LSTM model with a single hidden layer (32 units).
Implements robust fallback logic for interval generation if residuals are non-Gaussian or intervals are invalid.

### Class: `LSTMModel`

**Constructor**:
```python
LSTMModel(horizon: int, input_size: int = 1, hidden_size: int = 32,
 learning_rate: float = 0.01, epochs: int = 50, patience: int = 5,
 conf_level: float = 0.95)
```
- `horizon`: Forecast horizon (steps ahead).
- `hidden_size`: Number of units in the LSTM layer (default 32).
- `learning_rate`: Initial learning rate (default 0.01).
- `epochs`: Maximum training epochs (default 50).
- `patience`: Early stopping patience (default 5).
- `conf_level`: Confidence level for intervals.

**Methods**:
- `fit(train_series: pd.Series) -> None`:
 - Converts series to sliding window tensors.
 - Trains on CPU only.
 - Implements early stopping.
 - **Stability Check**: Detects NaN/Inf in gradients or loss; retries with reduced learning rate (0.1x) up to a max number of attempts.
- `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`:
 - Generates point forecasts.
 - Calculates intervals based on residual distribution.
 - **Fallback**: If residuals are non-Gaussian (variance check) or intervals are invalid (NaN/Inf), switches to Empirical CDF (quantile-based) intervals.
- `get_params() -> Dict[str, Any]`:
 Returns the configuration dictionary.

**Dependencies**:
- `torch`
- `numpy`
- `pandas`

---

## Usage Example

```python
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
import pandas as pd

# Load data
data = pd.read_csv('data/processed/example_series.csv')
series = data['value']

# Initialize Model
model = ARIMAModel(order=(1, 1, 1))

# Fit
model.fit(series)

# Forecast
points, lower, upper = model.forecast(steps=24)
```
