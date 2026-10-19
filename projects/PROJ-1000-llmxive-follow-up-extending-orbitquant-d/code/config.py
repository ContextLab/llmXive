"""
Project configuration module.

Provides directory paths, global seeds, and common settings used across
the data acquisition, analysis, and evaluation scripts.

All project-owned paths are resolved via ``llmxive_toolkit.paths`` so that
they always point inside the project root regardless of the current
working directory.
"""
from pathlib import Path
from dataclasses import dataclass
from llmxive_toolkit import paths

# ---------------------------------------------------------------------------
# Global random seeds (single source of truth for reproducibility)
# ---------------------------------------------------------------------------
SEED = 42
NUM_CLUSTERS = 16          # K rotation matrices (FR-003)
SPLIT_SEED = 42            # 80/20 train/test split seed
BONFERRONI_TESTS = 4       # FID, CLIP, MSE, time

# ---------------------------------------------------------------------------
# Project-owned path helpers (via llmxive_toolkit)
# ---------------------------------------------------------------------------
PROJECT_ROOT = paths.root
CODE_DIR = paths.code("")
TESTS_DIR = PROJECT_ROOT / "tests"
RAW_DATA_DIR = paths.data("raw")
PROCESSED_DATA_DIR = paths.data("processed")
LOGS_DIR = paths.data("processed", "logs")
ACTIVATION_STATS_DIR = paths.data("processed", "activation_stats")
ROTATION_MATRICES_DIR = paths.data("processed", "rotation_matrices")
FIGURES_DIR = paths.figures("")

# Frequently used artifact paths
DIVERSE_PROMPTS_PATH = PROCESSED_DATA_DIR / "diverse_prompts.csv"
PROMPTS_CSV_PATH = PROCESSED_DATA_DIR / "prompts.csv"
ENTROPY_SCORES_PATH = PROCESSED_DATA_DIR / "entropy_scores.csv"
CORRELATION_RESULTS_PATH = PROCESSED_DATA_DIR / "correlation_results.json"
CLUSTERING_REPORT_PATH = PROCESSED_DATA_DIR / "clustering_report.json"
MODEL_LOAD_LOG_PATH = LOGS_DIR / "model_load_log.json"
PROXY_FAILURES_LOG_PATH = LOGS_DIR / "proxy_failures.json"
ROUTER_EDGE_CASES_LOG_PATH = LOGS_DIR / "router_edge_cases.json"

@dataclass(frozen=True)
class Config:
    """
    Simple immutable configuration holder.
    """
    project_root: Path = PROJECT_ROOT
    code_dir: Path = CODE_DIR
    tests_dir: Path = TESTS_DIR
    raw_data_dir: Path = RAW_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    seed: int = SEED

    @property
    def coco_captions_dir(self) -> Path:
        return self.raw_data_dir / "coco_captions"

    @property
    def diverse_prompts_path(self) -> Path:
        return self.processed_data_dir / "diverse_prompts.csv"

    @property
    def prompts_csv_path(self) -> Path:
        return self.processed_data_dir / "prompts.csv"

    @property
    def clustering_report_path(self) -> Path:
        return self.processed_data_dir / "clustering_report.json"

    @property
    def data_processed_path(self) -> Path:
        return self.processed_data_dir
