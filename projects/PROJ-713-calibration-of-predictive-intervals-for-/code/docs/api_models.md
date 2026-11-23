# API Documentation: Models

This document provides the API reference for the forecasting models implemented in `code/models/`.
All models follow a unified interface to support the calibration pipeline.

## Common Interface

Every model class implements the following methods:

- `fit(train_series: pd.Series) -> None`: Trains the model on the provided training data.
- `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`: Returns predictions, lower bounds, and upper bounds.
- `get_name() -> str`: Returns the string identifier for the model.

---

## ARIMAModel

**Module**: `code/models/arima_model.py`

A wrapper around `statsmodels.tsa.arima.model.ARIMA` and `SARIMAX` for generating forecasts with conditional variance intervals.

### Class: `ARIMAModel`

**Signature**:
```python
class ARIMAModel:
 def __init__(self, order: Tuple[int, int, int] = (1, 1, 1), seasonal_order: Tuple[int, int, int, int] = (0, 0, 0, 0)):
...
```

**Parameters**:
- `order`: The (p, d, q) order of the model.
- `seasonal_order`: The (P, D, Q, s) seasonal order.

**Methods**:

#### `fit(train_series: pd.Series) -> None`
Fits the ARIMA model to the training data.
- **Logic**: Uses `statsmodels.tsa.arima.model.ARIMA`. If convergence fails, logs a warning and skips the series.
- **Interval Method**: Uses `method='conditional'` for confidence intervals as per FR-003.

#### `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
Generates forecasts for the specified number of steps.
- **Returns**:
 - `predictions`: Array of point forecasts.
 - `lower_bounds`: Lower bound of the 95% confidence interval.
 - `upper_bounds`: Upper bound of the 95% confidence interval.

#### `get_name() -> str`
Returns `"ARIMA"`.

---

## ProphetModel

**Module**: `code/models/prophet_model.py`

A wrapper around `prophet.Prophet` for generating forecasts with uncertainty intervals via residual simulation.

### Class: `ProphetModel`

**Signature**:
```python
class ProphetModel:
 def __init__(self, uncertainty_samples: int = 1000, seasonality_mode: str = 'additive'):
...
```

**Parameters**:
- `uncertainty_samples`: Number of simulated draws for uncertainty estimation.
- `seasonality_mode`: 'additive' or 'multiplicative'.

**Methods**:

#### `fit(train_series: pd.Series) -> None`
Fits the Prophet model.
- **Logic**: Converts the series to a DataFrame with a 'ds' (date) and 'y' (value) column.
- **Uncertainty**: Uses `uncertainty_samples` to simulate residuals for interval generation.

#### `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
Generates forecasts.
- **Returns**:
 - `predictions`: Point forecasts ('yhat').
 - `lower_bounds`: Lower bound ('yhat_lower').
 - `upper_bounds`: Upper bound ('yhat_upper').

#### `get_name() -> str`
Returns `"Prophet"`.

---

## LSTMModel

**Module**: `code/models/lstm_model.py`

A PyTorch-based LSTM model with stability checks and fallback to Empirical CDF intervals.

### Class: `LSTMModel`

**Signature**:
```python
class LSTMModel:
 def __init__(
 self,
 input_size: int = 1,
 hidden_size: int = 32,
 num_layers: int = 1,
 max_epochs: int = 50,
 patience: int = 5,
 learning_rate: float = 0.01
):
...
```

**Parameters**:
- `hidden_size`: Number of units in the hidden layer (default 32).
- `max_epochs`: Maximum training epochs (default 50).
- `patience`: Early stopping patience (default 5).
- `learning_rate`: Initial learning rate (default 0.01).

**Methods**:

#### `fit(train_series: pd.Series) -> None`
Trains the LSTM model.
- **Stability Check**: Detects NaN/Inf in loss. If detected, retries with reduced learning rate (0.1x) up to a maximum number of attempts.
- **CPU Only**: Training is enforced on CPU.

#### `forecast(steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
Generates forecasts.
- **Fallback Logic**: If residuals are non-Gaussian (variance check) or intervals are invalid (NaN/Inf), switches to Empirical CDF (quantile-based) intervals.
- **Returns**:
 - `predictions`: Point forecasts.
 - `lower_bounds`: Lower quantile.
 - `upper_bounds`: Upper quantile.

#### `get_name() -> str`
Returns `"LSTM"`.

---

## Usage Example

```python
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
import pandas as pd

# Load data (example)
data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
train = data.iloc[:8]
test = data.iloc[8:]

# ARIMA
arima = ARIMAModel(order=(1, 1, 1))
arima.fit(train)
preds, lower, upper = arima.forecast(len(test))

# Prophet
prophet = ProphetModel()
prophet.fit(train)
preds, lower, upper = prophet.forecast(len(test))

# LSTM
lstm = LSTMModel()
lstm.fit(train)
preds, lower, upper = lstm.forecast(len(test))
```
