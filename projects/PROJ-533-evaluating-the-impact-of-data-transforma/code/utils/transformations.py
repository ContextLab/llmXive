import numpy as np
from scipy import stats
from typing import Tuple, Optional, Union, List
import warnings
import logging
from pathlib import Path

def box_cox_transform(data: np.ndarray) -> np.ndarray:
    """Applies Box-Cox transformation to data."""
    transformed_data, _ = stats.boxcox(data)
    return transformed_data

def safe_box_cox(data: np.ndarray) -> np.ndarray:
  """Apply the box cox transform while handling non positive values"""
  if np.any(data <= 0):
      raise ValueError("Box-Cox requires strictly positive data.")
  return box_cox_transform(data)

def yeo_johnson_transform(data: np.ndarray) -> np.ndarray:
    """Applies Yeo-Johnson transformation to data."""
    transformed_data, _ = stats.yeojohnson(data)
    return transformed_data

def rank_inverse_normal_transform(data: np.ndarray) -> np.ndarray:
    """Applies rank-based inverse normal transform to data."""
    ranked_data = stats.rankdata(data)
    transformed_data = stats.norm.ppf((ranked_data - 0.5) / len(data))
    return transformed_data

def apply_transformation(data: np.ndarray, transformation: str) -> np.ndarray:
    """Applies a specified transformation to the data."""
    if transformation == "boxcox":
        try:
            return box_cox_transform(data)
        except ValueError as e:
            logging.warning(f"Box-Cox failed: {e}")
            return data
    elif transformation == "yeojohnson":
        return yeo_johnson_transform(data)
    elif transformation == "rankinverse":
        return rank_inverse_normal_transform(data)
    else:
        raise ValueError("Invalid transformation specified.")

def transform_to_normality(data: np.ndarray, transformations: List[str]) -> np.ndarray:
  """Apply list of transformations until normality is achieved."""
  transformed = data
  for t in transformations:
      try:
          transformed = apply_transformation(transformed, t)
      except Exception as e:
          logging.warning(f"Transformation {t} failed with error: {e}")

  return transformed
