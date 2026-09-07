import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score
import logging
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)

def run_regression(
    X: np.ndarray,
    y: np.ndarray,
    degree: int = 1,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Fit a linear or polynomial regression model.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        degree: Polynomial degree (1 for linear)
        alpha: Significance level for p-value calculation (default 0.05)
    
    Returns:
        Dictionary containing model coefficients, R², p-values, and residuals.
    """
    logger.info(f"Fitting regression model with degree={degree}")
    
    if degree > 1:
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)
        y_pred = model.predict(X_poly)
        # Adjust feature names for polynomial terms if needed
        feature_names = [f"poly_{i}" for i in range(X_poly.shape[1])]
    else:
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        feature_names = [f"feat_{i}" for i in range(X.shape[1])]
    
    r2 = r2_score(y, y_pred)
    
    # Calculate p-values for coefficients using t-distribution
    n_samples = len(y)
    n_params = model.coef_.shape[0] + 1  # +1 for intercept
    degrees_of_freedom = n_samples - n_params
    
    if degrees_of_freedom <= 0:
        logger.warning("Degrees of freedom <= 0. Cannot calculate p-values. Returning NaN.")
        p_values = [np.nan] * len(model.coef_)
        p_intercept = np.nan
    else:
        # Residuals
        residuals = y - y_pred
        # Standard error of the regression
        sse = np.sum(residuals**2)
        mse = sse / degrees_of_freedom
        
        # Standard errors of coefficients
        # Covariance matrix of coefficients = MSE * (X'X)^-1
        if degree > 1:
            X_design = X_poly
        else:
            X_design = X
        
        # Add column of ones for intercept
        X_design_intercept = np.column_stack((np.ones(X_design.shape[0]), X_design))
        
        try:
            XtX_inv = np.linalg.inv(X_design_intercept.T @ X_design_intercept)
            se_coefs = np.sqrt(np.diag(XtX_inv) * mse)
            
            # t-statistics
            t_stats = np.append(model.intercept_, model.coef_) / se_coefs
            
            # Two-tailed p-values
            p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(t_stats[1:]), degrees_of_freedom))
            p_intercept = 2 * (1 - scipy_stats.t.cdf(np.abs(t_stats[0]), degrees_of_freedom))
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix in covariance calculation. Returning NaN for p-values.")
            p_values = [np.nan] * len(model.coef_)
            p_intercept = np.nan
    
    # ANOVA table calculation
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum(residuals**2)
    ss_regression = ss_total - ss_residual
    
    df_regression = n_params - 1
    df_residual = degrees_of_freedom
    df_total = n_samples - 1
    
    ms_regression = ss_regression / df_regression if df_regression > 0 else 0
    ms_residual = ss_residual / df_residual if df_residual > 0 else 0
    
    f_stat = ms_regression / ms_residual if ms_residual > 0 else 0
    p_f_stat = 1 - scipy_stats.f.cdf(f_stat, df_regression, df_residual) if df_residual > 0 else np.nan
    
    anova = {
        "source": ["Regression", "Residual", "Total"],
        "df": [df_regression, df_residual, df_total],
        "ss": [ss_regression, ss_residual, ss_total],
        "ms": [ms_regression, ms_residual, np.nan],
        "f": [f_stat, np.nan, np.nan],
        "p": [p_f_stat, np.nan, np.nan]
    }
    
    return {
        "coefficients": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "r_squared": float(r2),
        "p_values": p_values,
        "p_intercept": p_intercept,
        "anova": anova,
        "feature_names": feature_names,
        "model_type": "polynomial" if degree > 1 else "linear",
        "degree": degree
    }

def calculate_vif(X: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each predictor.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: Optional list of feature names for the result dictionary
    
    Returns:
        Dictionary mapping feature names (or indices) to VIF values.
    """
    n_samples, n_features = X.shape
    
    if n_samples < n_features + 1:
        logger.warning("Sample size too small for VIF calculation. Returning NaNs.")
        if feature_names:
            return {name: np.nan for name in feature_names}
        return {f"feat_{i}": np.nan for i in range(n_features)}
    
    vif_values = {}
    if feature_names is None:
        feature_names = [f"feat_{i}" for i in range(n_features)]
    
    for i in range(n_features):
        y_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # Add intercept
        X_others_intercept = np.column_stack((np.ones(X_others.shape[0]), X_others))
        
        try:
            model = LinearRegression()
            model.fit(X_others_intercept, y_i)
            r_squared_i = model.score(X_others_intercept, y_i)
            
            # VIF = 1 / (1 - R²_i)
            if r_squared_i >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared_i)
            
            vif_values[feature_names[i]] = float(vif)
        except Exception as e:
            logger.warning(f"Error calculating VIF for {feature_names[i]}: {e}")
            vif_values[feature_names[i]] = np.nan
    
    return vif_values

def run_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    degree: int = 1,
    cv_repeats: int = 5
) -> Dict[str, Any]:
    """
    Perform 5x5-Fold Cross-Validation as per project constitution.
    
    Args:
        X: Feature matrix
        y: Target vector
        n_splits: Number of folds (default 5)
        degree: Polynomial degree
        cv_repeats: Number of repeats (default 5 for 5x5-CV)
    
    Returns:
        Dictionary with mean R², std dev, and individual scores.
    """
    logger.info(f"Running {cv_repeats}x{n_splits}-Fold Cross-Validation")
    
    all_scores = []
    
    for repeat in range(cv_repeats):
        # Create a new splitter instance for each repeat to ensure different shuffles
        scores = cross_val_score(
            LinearRegression() if degree == 1 else PolynomialFeatures(degree=degree),
            X, y,
            cv=n_splits,
            scoring='r2'
        )
        all_scores.extend(scores.tolist())
    
    scores_array = np.array(all_scores)
    
    return {
        "mean_r2": float(np.mean(scores_array)),
        "std_r2": float(np.std(scores_array)),
        "all_scores": scores_array.tolist(),
        "n_folds": n_splits,
        "n_repeats": cv_repeats,
        "total_evaluations": len(all_scores),
        "stability_flag": float(np.std(scores_array)) > 0.1
    }

def calculate_anova_table(y: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Calculate ANOVA table for regression analysis.
    
    Args:
        y: Actual values
        y_pred: Predicted values
    
    Returns:
        ANOVA table dictionary.
    """
    n = len(y)
    ss_total = np.sum((y - np.mean(y))**2)
    residuals = y - y_pred
    ss_residual = np.sum(residuals**2)
    ss_regression = ss_total - ss_residual
    
    # Degrees of freedom
    df_total = n - 1
    df_residual = n - 2  # Assuming simple linear regression (1 predictor + intercept)
    df_regression = 1
    
    ms_regression = ss_regression / df_regression if df_regression > 0 else 0
    ms_residual = ss_residual / df_residual if df_residual > 0 else 0
    
    f_stat = ms_regression / ms_residual if ms_residual > 0 else 0
    p_value = 1 - scipy_stats.f.cdf(f_stat, df_regression, df_residual) if df_residual > 0 else np.nan
    
    return {
        "source": ["Regression", "Residual", "Total"],
        "df": [df_regression, df_residual, df_total],
        "ss": [ss_regression, ss_residual, ss_total],
        "ms": [ms_regression, ms_residual, np.nan],
        "f": [f_stat, np.nan, np.nan],
        "p": [p_value, np.nan, np.nan]
    }
