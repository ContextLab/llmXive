"""
Schema definitions for statistical modeling results.
Includes results for stationarity, cointegration, causality, and validation tests.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StationarityTestResult(BaseModel):
    """Result of an Augmented Dickey-Fuller (ADF) test."""
    variable: str
    statistic: float
    p_value: float
    is_stationary: bool
    transformation_applied: Optional[str] = Field(None, description="e.g., 'log', 'diff'")

class CointegrationTestResult(BaseModel):
    """Result of a Johansen Cointegration Test."""
    test_type: str = Field("Johansen", description="Type of cointegration test")
    statistic_trace: float
    p_value_trace: float
    statistic_max_eig: Optional[float] = Field(None, description="Max Eigen statistic")
    p_value_max_eig: Optional[float] = Field(None, description="Max Eigen p-value")
    cointegration_rank: int
    model_selection: str = Field(..., description="Selected model type: 'VAR' or 'VECM'")

class GrangerCausalityResult(BaseModel):
    """Result of a Granger Causality F-test."""
    test_direction: str = Field(..., description="Format: 'X -> Y'")
    f_statistic: float
    p_value: float
    is_causal: bool
    lag_length: int

class CollinearityDiagnostic(BaseModel):
    """Diagnostic results for multicollinearity (VIF)."""
    variable: str
    vif_score: float
    is_high: bool
    threshold: float = Field(33.0, description="Threshold for high collinearity")

class BootstrapValidationResult(BaseModel):
    """Results from Moving Block Bootstrap (MBB) validation."""
    original_coefficient: float
    confidence_interval_95: List[float]
    ci_width: float
    convergence_achieved: bool
    block_length: int
    iterations: int
    warning: Optional[str] = Field(None, description="Warnings regarding statistical properties")

class ModelResult(BaseModel):
    """Aggregated result of the statistical modeling phase."""
    model_type: str = Field(..., description="VAR or VECM")
    optimal_lag_length: int
    stationarity_results: List[StationarityTestResult]
    cointegration_result: CointegrationTestResult
    granger_causality_results: List[GrangerCausalityResult]
    collinearity_diagnostics: List[CollinearityDiagnostic]
    validation_result: Optional[BootstrapValidationResult] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
