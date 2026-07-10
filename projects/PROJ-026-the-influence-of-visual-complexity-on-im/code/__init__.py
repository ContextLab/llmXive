"""
llmXive research-implementer agent system prompt project.
"""
from .config import get_project_root, ensure_directories, get_data_path
from .utils.logging import setup_logging, get_logger
from .data.models import ImageStimulus, ParticipantResponse, AggregatedScore
from .data.process import filter_trials, calculate_d_score, aggregate_d_scores
from .data.load import load_response_logs
from .stimuli.metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from .stimuli.process import categorize_complexity, process_stimuli_batch
from .stimuli.validate import validate_image, validate_batch
from .analysis.pca import run_pca_check
from .analysis.permutation import run_permutation_test, calculate_power
from .viz.plot import plot_boxplot, plot_sensitivity

__version__ = "0.1.0"
__all__ = [
    "get_project_root",
    "ensure_directories",
    "get_data_path",
    "setup_logging",
    "get_logger",
    "ImageStimulus",
    "ParticipantResponse",
    "AggregatedScore",
    "filter_trials",
    "calculate_d_score",
    "aggregate_d_scores",
    "load_response_logs",
    "calculate_edge_density",
    "calculate_entropy",
    "calculate_fractal_dim",
    "categorize_complexity",
    "process_stimuli_batch",
    "validate_image",
    "validate_batch",
    "run_pca_check",
    "run_permutation_test",
    "calculate_power",
    "plot_boxplot",
    "plot_sensitivity",
]
