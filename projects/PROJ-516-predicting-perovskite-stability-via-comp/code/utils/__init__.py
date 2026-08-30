"""
Utilities package for the Perovskite Stability Pipeline.
"""
from .config_manager import ConfigError, load_dotenv_file, get_api_key, validate_environment
from .data_fetcher import FetchError, fetch_with_retry, fetch_text_with_retry
from .formula_parser import FormulaParseError, parse_formula, validate_perovskite_formula, assign_perovskite_sites, compute_compositional_fingerprints, get_deterministic_assignment, main
from .state_manager import compute_sha256, load_state, save_state, update_artifact_state, verify_artifact, update_state_for_multiple_artifacts
from .validator import ValidationError, calculate_title_token_overlap, validate_title_token_overlap, validate_data_entries
from .checksum_verifier import ChecksumError, compute_sha256, validate_checksum, verify_artifacts_from_manifest, generate_checksum_manifest

__all__ = [
    # config_manager
    "ConfigError",
    "load_dotenv_file",
    "get_api_key",
    "validate_environment",
    # data_fetcher
    "FetchError",
    "fetch_with_retry",
    "fetch_text_with_retry",
    # formula_parser
    "FormulaParseError",
    "parse_formula",
    "validate_perovskite_formula",
    "assign_perovskite_sites",
    "compute_compositional_fingerprints",
    "get_deterministic_assignment",
    "main",
    # state_manager
    "compute_sha256",
    "load_state",
    "save_state",
    "update_artifact_state",
    "verify_artifact",
    "update_state_for_multiple_artifacts",
    # validator
    "ValidationError",
    "calculate_title_token_overlap",
    "validate_title_token_overlap",
    "validate_data_entries",
    # checksum_verifier
    "ChecksumError",
    "compute_sha256",
    "validate_checksum",
    "verify_artifacts_from_manifest",
    "generate_checksum_manifest",
]