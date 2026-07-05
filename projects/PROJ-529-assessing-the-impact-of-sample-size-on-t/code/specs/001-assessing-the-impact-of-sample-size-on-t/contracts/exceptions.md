# Exception Contracts

## DataAcquisitionError
Raised when data fetch fails (network error, 404, rate limit) or the returned corpus size is below the required threshold (50).
- **Action**: Triggers fallback to simulation mode (T019).

## ZeroVarianceError
Raised when a study or pooled estimate has zero variance (SE=0), making inverse-variance weighting impossible.
- **Action**: Apply small constant perturbation or exclude study (per `code/utils/exceptions.py`).

## NegativeVarianceError
Raised when REML estimation yields a negative tau^2.
- **Action**: Clamp tau^2 to zero or switch to method-of-moments estimator.

## ConvergenceError
Raised when GAM or other iterative models fail to converge.
- **Action**: Switch to fallback model (segmented regression) or reduce complexity.
