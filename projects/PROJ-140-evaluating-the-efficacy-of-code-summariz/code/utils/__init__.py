"""
Utility modules for the code summarization efficacy study.

Exports:
    Config: Configuration manager
    get_config: Function to retrieve global config
    hash_artifacts: SHA-256 hashing utility
    models: Data models
    logging_utils: Logging infrastructure
    interaction_logger: Interaction logging
    anonymize_logs: Data anonymization
    assignment_generator: Latin-square assignment
"""
from .config_manager import Config, get_config
from .hash_artifacts import hash_file, hash_directory
# Other imports will be added as modules are implemented
# from .models import Participant, Task, Summary, AnalysisResult
# from .logging_utils import setup_logger
# from .interaction_logger import InteractionLogger
# from .anonymize_logs import anonymize_logs
# from .assignment_generator import AssignmentGenerator

__all__ = [
    'Config',
    'get_config',
    'hash_file',
    'hash_directory'
]
