"""
llmXive Research Pipeline - Code Package
"""
from .config import get_project_root, ensure_directories, get_config_dict
from .cue_matching import normalize_text, normalize_cues, build_inverse_index, match_cues, resolve_collisions
from .aggregation import join_exposure_data, aggregate_to_user_track, filter_zero_variance, enforce_match_rate
from .state_manager import load_state, save_state, register_file, verify_file, verify_all, get_file_info, clear_stale_entries
from .utils import setup_logging, get_logger

__all__ = [
    'get_project_root', 'ensure_directories', 'get_config_dict',
    'normalize_text', 'normalize_cues', 'build_inverse_index', 'match_cues', 'resolve_collisions',
    'join_exposure_data', 'aggregate_to_user_track', 'filter_zero_variance', 'enforce_match_rate',
    'load_state', 'save_state', 'register_file', 'verify_file', 'verify_all', 'get_file_info', 'clear_stale_entries',
    'setup_logging', 'get_logger'
]
