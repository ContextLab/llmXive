"""Shared rotation utilities for the isotropy analysis.

This module provides functions to convert celestial coordinates to 3D unit
vectors and apply rotations to those vectors, used in both power analysis
and null-distribution simulations.
"""
import numpy as np
from scipy.spatial.transform import Rotation

def unit_vectors_from_ra_dec(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    """
    Convert arrays of RA/Dec (degrees) to 3-D unit vectors.
    
    Args:
        ra_deg: Array of Right Ascension in degrees.
        dec_deg: Array of Declination in degrees.
        
    Returns:
        An array of shape (N, 3) containing unit vectors.
    """
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    return np.stack([x, y, z], axis=1)

def rotate_vectors(vectors: np.ndarray, rot: Rotation) -> np.ndarray:
    """
    Apply a scipy Rotation to an array of shape (N, 3).
    
    Args:
        vectors: Array of vectors to rotate.
        rot: A scipy.spatial.transform.Rotation object.
        
    Returns:
        The rotated vectors.
    """
    return rot.apply(vectors)
