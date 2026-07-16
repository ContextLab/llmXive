"""
llmXive Automated Science Pipeline - Code Package
"""
from .config import set_random_seed, get_path
from .data_model import DesignType, Dataset, PreprocessedRecord, AnalysisResult
from .ingest import run_ingestion
from .preprocess import run_preprocessing
from .analysis import run_analysis_pipeline
from .report import run_reporting_pipeline

__version__ = "0.1.0"
__all__ = [
    "set_random_seed",
    "get_path",
    "DesignType",
    "Dataset",
    "PreprocessedRecord",
    "AnalysisResult",
    "run_ingestion",
    "run_preprocessing",
    "run_analysis_pipeline",
    "run_reporting_pipeline"
]
