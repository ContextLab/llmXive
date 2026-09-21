"""
Data retrieval and preprocessing module for the llmXive project.

This module provides functionality for:
- Connecting to MDSplus databases to retrieve plasma discharge data.
- Fetching specific plasma parameters (EFIT, islands, tau_e, h98y2).
- Preprocessing raw time-series data into unified analysis-ready DataFrames.
- Validating data against defined schema contracts.
"""
from .retrieval import get_efit_data, fetch_island_width, derive_island_width, fetch_data_for_discharge
from .preprocessing import align_time_series, extract_snapshot, calculate_island_width, determine_confinement_mode, parse_discharge_data, process_multiple_discharges, generate_checksum, save_unified_dataset
from .validator import load_schema, validate_dataframe_against_schema, validate_input_schema, validate_output_schema, validate_parsed_data
