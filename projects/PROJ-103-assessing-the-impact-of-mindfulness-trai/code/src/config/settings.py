# Mirror of code/config/settings.py to satisfy existing src.config.settings imports
from code.config import settings as _settings

get_dataset_paths = _settings.get_dataset_paths
get_preprocessing_params = _settings.get_preprocessing_params
get_atlas_choice = _settings.get_atlas_choice
get_motion_thresholds = _settings.get_motion_thresholds
get_statistical_thresholds = _settings.get_statistical_thresholds
