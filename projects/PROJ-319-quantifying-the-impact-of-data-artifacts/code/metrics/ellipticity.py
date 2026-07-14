"""Ellipticity calculation metrics for planetary nebulae.

This module implements the calculation of ellipticity using second-order moments
as per the Conselice (2003) definition or similar astronomical standards.
"""
import logging
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

def calculate_ellipticity(image: np.ndarray) -> Tuple[float, float]:
    """Calculate ellipticity components (e1, e2) using second-order moments.

    The ellipticity is defined as:
    e1 = (Q_xx - Q_yy) / (Q_xx + Q_yy)
    e2 = 2 * Q_xy / (Q_xx + Q_yy)

    Where Q_ij are the second-order moments of the light distribution.

    Args:
        image: 2D array representing the image intensity.

    Returns:
        Tuple (e1, e2) representing the ellipticity components.
    """
    if image.ndim != 2:
        raise ValueError("Image must be a 2D array.")

    # Calculate the center of light (first moments)
    y, x = np.indices(image.shape)
    total_flux = np.sum(image)
    if total_flux == 0:
        logger.warning("Image has zero flux, returning zero ellipticity.")
        return 0.0, 0.0

    x_bar = np.sum(x * image) / total_flux
    y_bar = np.sum(y * image) / total_flux

    # Calculate second-order moments
    # Q_xx = sum((x - x_bar)^2 * I)
    # Q_yy = sum((y - y_bar)^2 * I)
    # Q_xy = sum((x - x_bar) * (y - y_bar) * I)
    Q_xx = np.sum((x - x_bar) ** 2 * image)
    Q_yy = np.sum((y - y_bar) ** 2 * image)
    Q_xy = np.sum((x - x_bar) * (y - y_bar) * image)

    trace = Q_xx + Q_yy
    if trace == 0:
        logger.warning("Trace of moment matrix is zero, returning zero ellipticity.")
        return 0.0, 0.0

    e1 = (Q_xx - Q_yy) / trace
    e2 = 2 * Q_xy / trace

    return e1, e2