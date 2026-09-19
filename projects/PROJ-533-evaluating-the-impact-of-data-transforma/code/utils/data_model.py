"""
Data model definitions for the data transformation sensitivity study.

This module defines the core entities (Dataset, Transformation, TestResult)
based on the specification in T006 (data-model.md).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class Dataset:
    """
    Represents a raw or processed dataset used in the study.

    Attributes:
        source_url: URL where the dataset was downloaded from (UCI/OpenML).
        sample_size: Total number of observations (rows).
        continuous_vars: List of column names representing continuous variables.
        group_labels: List of group labels if the data is grouped (for ANOVA/t-test).
        shapiro_p: Shapiro-Wilk p-value indicating normality of the data (before transformation).
        checksum: SHA-256 checksum of the raw dataset file for integrity verification.
        data: Optional numpy array or pandas DataFrame containing the actual data.
    """
    source_url: str
    sample_size: int
    continuous_vars: List[str]
    group_labels: List[str]
    shapiro_p: float
    checksum: str
    data: Optional[Any] = None  # Can be np.ndarray or pd.DataFrame
    dataset_id: Optional[str] = None  # Generated ID if not provided
    missing_ratio: float = 0.0
    imputation_method: Optional[str] = None
    excluded_reason: Optional[str] = None

    def __post_init__(self):
        """Validate basic constraints."""
        if self.sample_size < 0:
            raise ValueError("sample_size must be non-negative")
        if not isinstance(self.continuous_vars, list):
            raise TypeError("continuous_vars must be a list")
        if not isinstance(self.group_labels, list):
            raise TypeError("group_labels must be a list")


@dataclass
class Transformation:
    """
    Represents a data transformation applied to a Dataset.

    Attributes:
        method: Name of the transformation method (e.g., 'box_cox', 'yeo_johnson', 'rank_inverse').
        lambda_param: The lambda parameter used (if applicable, e.g., for Box-Cox).
        transformed_values: The resulting transformed data (numpy array).
        original_values: The original data before transformation.
        success: Boolean indicating if the transformation was successful.
        error_message: Error message if the transformation failed.
    """
    method: str
    lambda_param: Optional[float] = None
    transformed_values: Optional[np.ndarray] = None
    original_values: Optional[np.ndarray] = None
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate constraints."""
        if self.success and self.transformed_values is None:
            raise ValueError("transformed_values must be provided if success is True")
        if not self.success and self.error_message is None:
            raise ValueError("error_message must be provided if success is False")


@dataclass
class TestResult:
    """
    Represents the result of a statistical test performed on transformed data.

    Attributes:
        test_type: Type of statistical test performed (e.g., 't_test', 'anova', 'shapiro_wilk').
        p_value: The calculated p-value from the test.
        significant: Boolean indicating if the result is significant (p < alpha).
        transformation: Reference to the Transformation object used.
        condition: The condition or group being tested (e.g., 'control', 'treatment').
        effect_size: Calculated effect size (e.g., Cohen's d) if applicable.
        dataset_id: ID of the dataset this result belongs to.
        alpha_threshold: The significance threshold used (default 0.05).
    """
    test_type: str
    p_value: float
    significant: bool
    transformation: Transformation
    condition: Optional[str] = None
    effect_size: Optional[float] = None
    dataset_id: Optional[str] = None
    alpha_threshold: float = 0.05

    def __post_init__(self):
        """Validate constraints."""
        if not (0.0 <= self.p_value <= 1.0):
            raise ValueError("p_value must be between 0.0 and 1.0")
        
        # Recalculate significance if not explicitly set but alpha is provided
        if self.significant is None:
            self.significant = self.p_value < self.alpha_threshold