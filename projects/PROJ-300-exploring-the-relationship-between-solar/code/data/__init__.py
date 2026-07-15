"""
Data module for solar wind and geomagnetic tail reconnection analysis.
This file is part of PROJ-300.
"""
from .ingest import fetch_omni_sw, fetch_themis_ey
from .clean import clean_and_resample
from .lag import calculate_physics_lag, apply_lag_shift
