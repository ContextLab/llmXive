"""
Base configuration loader for environment variables.

This module provides a centralized configuration management system that loads
settings from environment variables with sensible defaults. It is designed to
support the llmXive automated science pipeline for investigating the correlation
between gut microbiome composition and circadian rhythm disruption.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Centralized configuration container for the project.

    Attributes:
        project_root (Path): Root directory of the project.
        data_root (Path): Root directory for data storage.
        data_raw (Path): Directory for raw data downloads.
        data_processed (Path): Directory for processed data.
        data_outputs (Path): Directory for analysis outputs and figures.
        code_root (Path): Root directory for code modules.
        tests_root (Path): Root directory for tests.
        docs_root (Path): Root directory for documentation.
        log_dir (Path): Directory for log files.
        seed (int): Random seed for reproducibility.
        n_jobs (int): Number of parallel jobs for computations.
        max_memory_gb (int): Maximum memory allocation in GB.
        agp_url (str): URL for American Gut Project data.
        oh_url (str): URL for Open Humans metadata.
        checksum_agp (str): Expected checksum for AGP data verification.
        checksum_oh (str): Expected checksum for OH data verification.
        fdr_method (str): Method for FDR correction (default: 'benjamini_hochberg').
        alpha (float): Significance threshold for statistical tests.
        min_sample_size (int): Minimum sample size required for analysis.
        outlier_cap_percentile (float): Percentile for outlier capping.
        imputation_strategy (str): Strategy for missing data imputation.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    data_raw: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "raw")
    data_processed: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    data_outputs: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "outputs")
    code_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "code")
    tests_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "tests")
    docs_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "docs")
    log_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    seed: int = 42
    n_jobs: int = -1
    max_memory_gb: int = 14
    agp_url: str = "https://s3.amazonaws.com/microbiome-datasets/american-gut/16S_data.biom"
    oh_url: str = "https://api.openhumans.org/api/v1/project/12345/download/"
    checksum_agp: str = ""
    checksum_oh: str = ""
    fdr_method: str = "benjamini_hochberg"
    alpha: float = 0.05
    min_sample_size: int = 40
    outlier_cap_percentile: float = 0.99
    imputation_strategy: str = "median"

    def __post_init__(self):
        """Ensure all paths exist and are absolute."""
        self.project_root = self.project_root.resolve()
        self.data_root = self.data_root.resolve()
        self.data_raw = self.data_raw.resolve()
        self.data_processed = self.data_processed.resolve()
        self.data_outputs = self.data_outputs.resolve()
        self.code_root = self.code_root.resolve()
        self.tests_root = self.tests_root.resolve()
        self.docs_root = self.docs_root.resolve()
        self.log_dir = self.log_dir.resolve()

        # Create directories if they don't exist
        for path in [
            self.data_root,
            self.data_raw,
            self.data_processed,
            self.data_outputs,
            self.code_root,
            self.tests_root,
            self.docs_root,
            self.log_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables.

        Returns:
            Config: A Config instance populated with environment variables.
        """
        config = cls()

        # Override with environment variables if present
        if os.getenv("PROJECT_ROOT"):
            config.project_root = Path(os.getenv("PROJECT_ROOT")).resolve()
            # Re-derive other paths based on new project root
            config.data_root = config.project_root / "data"
            config.data_raw = config.project_root / "data" / "raw"
            config.data_processed = config.project_root / "data" / "processed"
            config.data_outputs = config.project_root / "data" / "outputs"
            config.code_root = config.project_root / "code"
            config.tests_root = config.project_root / "tests"
            config.docs_root = config.project_root / "docs"
            config.log_dir = config.project_root / "logs"

            # Ensure directories exist
            for path in [
                config.data_root,
                config.data_raw,
                config.data_processed,
                config.data_outputs,
                config.code_root,
                config.tests_root,
                config.docs_root,
                config.log_dir
            ]:
                path.mkdir(parents=True, exist_ok=True)

        if os.getenv("DATA_ROOT"):
            config.data_root = Path(os.getenv("DATA_ROOT")).resolve()
        if os.getenv("DATA_RAW"):
            config.data_raw = Path(os.getenv("DATA_RAW")).resolve()
        if os.getenv("DATA_PROCESSED"):
            config.data_processed = Path(os.getenv("DATA_PROCESSED")).resolve()
        if os.getenv("DATA_OUTPUTS"):
            config.data_outputs = Path(os.getenv("DATA_OUTPUTS")).resolve()
        if os.getenv("CODE_ROOT"):
            config.code_root = Path(os.getenv("CODE_ROOT")).resolve()
        if os.getenv("TESTS_ROOT"):
            config.tests_root = Path(os.getenv("TESTS_ROOT")).resolve()
        if os.getenv("DOCS_ROOT"):
            config.docs_root = Path(os.getenv("DOCS_ROOT")).resolve()
        if os.getenv("LOG_DIR"):
            config.log_dir = Path(os.getenv("LOG_DIR")).resolve()

        if os.getenv("RANDOM_SEED"):
            try:
                config.seed = int(os.getenv("RANDOM_SEED"))
            except ValueError:
                pass

        if os.getenv("N_JOBS"):
            try:
                config.n_jobs = int(os.getenv("N_JOBS"))
            except ValueError:
                pass

        if os.getenv("MAX_MEMORY_GB"):
            try:
                config.max_memory_gb = int(os.getenv("MAX_MEMORY_GB"))
            except ValueError:
                pass

        if os.getenv("AGP_URL"):
            config.agp_url = os.getenv("AGP_URL")
        if os.getenv("OH_URL"):
            config.oh_url = os.getenv("OH_URL")
        if os.getenv("CHECKSUM_AGP"):
            config.checksum_agp = os.getenv("CHECKSUM_AGP")
        if os.getenv("CHECKSUM_OH"):
            config.checksum_oh = os.getenv("CHECKSUM_OH")

        if os.getenv("FDR_METHOD"):
            config.fdr_method = os.getenv("FDR_METHOD")
        if os.getenv("ALPHA"):
            try:
                config.alpha = float(os.getenv("ALPHA"))
            except ValueError:
                pass
        if os.getenv("MIN_SAMPLE_SIZE"):
            try:
                config.min_sample_size = int(os.getenv("MIN_SAMPLE_SIZE"))
            except ValueError:
                pass
        if os.getenv("OUTLIER_CAP_PERCENTILE"):
            try:
                config.outlier_cap_percentile = float(os.getenv("OUTLIER_CAP_PERCENTILE"))
            except ValueError:
                pass
        if os.getenv("IMPUTATION_STRATEGY"):
            config.imputation_strategy = os.getenv("IMPUTATION_STRATEGY")

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the configuration.
        """
        return {
            "project_root": str(self.project_root),
            "data_root": str(self.data_root),
            "data_raw": str(self.data_raw),
            "data_processed": str(self.data_processed),
            "data_outputs": str(self.data_outputs),
            "code_root": str(self.code_root),
            "tests_root": str(self.tests_root),
            "docs_root": str(self.docs_root),
            "log_dir": str(self.log_dir),
            "seed": self.seed,
            "n_jobs": self.n_jobs,
            "max_memory_gb": self.max_memory_gb,
            "agp_url": self.agp_url,
            "oh_url": self.oh_url,
            "checksum_agp": self.checksum_agp,
            "checksum_oh": self.checksum_oh,
            "fdr_method": self.fdr_method,
            "alpha": self.alpha,
            "min_sample_size": self.min_sample_size,
            "outlier_cap_percentile": self.outlier_cap_percentile,
            "imputation_strategy": self.imputation_strategy,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key (str): Configuration key.
            default (Any): Default value if key not found.

        Returns:
            Any: Configuration value or default.
        """
        return self.to_dict().get(key, default)


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the singleton Config instance.

    Returns:
        Config: The singleton Config instance.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """
    Reset the singleton Config instance.

    This is useful for testing or when environment variables change.
    """
    global _config
    _config = None


if __name__ == "__main__":
    # Example usage
    config = get_config()
    print("Project Root:", config.project_root)
    print("Data Root:", config.data_root)
    print("Seed:", config.seed)
    print("N Jobs:", config.n_jobs)
    print("Alpha:", config.alpha)
    print("Config Dictionary:", config.to_dict())