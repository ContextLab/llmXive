"""
Configuration management for the training pipeline.

This module defines a hierarchy of dataclasses representing the
configuration sections used throughout the project, provides utilities
for creating a default configuration, loading from / saving to a YAML
file, simple schema validation, and helper accessors required by the
existing unit tests.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Dataclass definitions for each configuration subsection
# ----------------------------------------------------------------------


@dataclass
class EnvironmentConfig:
    """Environment‑related flags."""

    cpu_only: bool = True
    """If ``True`` the pipeline must run in CPU‑only mode."""


@dataclass
class DataConfig:
    """Paths to data directories."""

    raw_dir: str = "data/raw"
    curated_dir: str = "data/curated"
    eval_dir: str = "data/eval"
    validation_dir: str = "data/validation"


@dataclass
class GenerationConfig:
    """Parameters for the video generation stage."""

    model_name: str = "Wan-AI/Wan2.1-Turbo"
    batch_size: int = 1
    num_samples: int = 10
    prompt_file: str = "data/prompts.jsonl"


@dataclass
class FilteringConfig:
    """Filtering hyper‑parameters."""

    discard_percentile: int = 40
    """Bottom percentile of scores to discard (e.g., 40 means discard the lowest 40 %)."""


@dataclass
class TrainingConfig:
    """Training hyper‑parameters."""

    epochs: int = 10
    learning_rate: float = 1e-4
    batch_size: int = 4
    seed: int = 42


@dataclass
class EvaluationConfig:
    """Evaluation‑stage settings."""

    eval_set_size: int = 30
    results_path: str = "data/eval/results.json"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    log_dir: str = "logs"
    level: str = "INFO"


@dataclass
class ProjectConfig:
    """Project‑level metadata."""

    name: str = "PROJ-951-llmxive-follow-up-extending-physisforcin"
    version: str = "0.1.0"


@dataclass
class Config:
    """Root configuration object aggregating all sections."""

    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    data: DataConfig = field(default_factory=DataConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Config":
        """Create a ``Config`` instance from a plain dict (e.g. from YAML)."""
        # Helper to instantiate a dataclass from a sub‑dict, falling back to defaults.
        def _make(cls, subdict: Optional[Dict[str, Any]]) -> Any:
            if subdict is None:
                return cls()
            return cls(**subdict)

        return Config(
            environment=_make(EnvironmentConfig, d.get("environment")),
            data=_make(DataConfig, d.get("data")),
            generation=_make(GenerationConfig, d.get("generation")),
            filtering=_make(FilteringConfig, d.get("filtering")),
            training=_make(TrainingConfig, d.get("training")),
            evaluation=_make(EvaluationConfig, d.get("evaluation")),
            logging=_make(LoggingConfig, d.get("logging")),
            project=_make(ProjectConfig, d.get("project")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the configuration to a plain ``dict`` suitable for YAML."""
        return asdict(self)

# ----------------------------------------------------------------------
# Public helper functions
# ----------------------------------------------------------------------


def create_default_config() -> Config:
    """
    Return a ``Config`` instance populated with the library’s default values.
    """
    logger.debug("Creating default configuration.")
    return Config()


# Alias kept for backwards compatibility with earlier code / tests.
get_default_config = create_default_config


def validate_config_schema(cfg: Config) -> None:
    """
    Perform a light‑weight validation of the configuration.

    The current implementation checks only a few critical constraints.
    Raises ``ValueError`` if a constraint is violated.
    """
    logger.debug("Validating configuration schema.")
    if not (0 <= cfg.filtering.discard_percentile <= 100):
        raise ValueError(
            f"discard_percentile must be between 0 and 100, got {cfg.filtering.discard_percentile}"
        )
    if cfg.training.epochs <= 0:
        raise ValueError("training.epochs must be a positive integer")
    if cfg.training.batch_size <= 0:
        raise ValueError("training.batch_size must be a positive integer")
    # Add further checks as the project evolves.


def load_config(path: str) -> Config:
    """
    Load a configuration from a YAML file.

    Parameters
    ----------
    path: str
        Path to the YAML configuration file.

    Returns
    -------
    Config
        The populated configuration object.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed.
    """
    cfg_path = Path(path)
    logger.debug("Loading configuration from %s", cfg_path)
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cfg = Config.from_dict(raw)
    validate_config_schema(cfg)
    return cfg


def save_config(cfg: Config, path: str) -> None:
    """
    Serialise a ``Config`` instance to a YAML file.

    Parameters
    ----------
    cfg: Config
        Configuration to persist.
    path: str
        Destination file path.
    """
    cfg_path = Path(path)
    logger.debug("Saving configuration to %s", cfg_path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    with cfg_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.to_dict(), f, sort_keys=False)

    logger.info("Configuration saved to %s", cfg_path)


def get_filter_discard_threshold(cfg: Config) -> int:
    """
    Convenience accessor used by the filtering code.

    Returns the ``discard_percentile`` value from the filtering section.
    """
    return cfg.filtering.discard_percentile


def get_config(path: Optional[str] = None) -> Config:
    """
    Retrieve the project configuration.

    If *path* is supplied, the configuration is loaded from that file.
    Otherwise, a default configuration is returned.

    Parameters
    ----------
    path: Optional[str]
        Path to a YAML configuration file.

    Returns
    -------
    Config
    """
    if path:
        return load_config(path)
    return create_default_config()


# ----------------------------------------------------------------------
# Minimal command‑line interface (used by ``python -m src.training.config``)
# ----------------------------------------------------------------------


def main() -> None:
    """
    Simple CLI that prints the default configuration as YAML.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Print or write the default training configuration."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="File to write the configuration to (default: stdout).",
    )
    args = parser.parse_args()

    cfg = create_default_config()
    yaml_str = yaml.safe_dump(cfg.to_dict(), sort_keys=False)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml_str, encoding="utf-8")
        logger.info("Default configuration written to %s", out_path)
    else:
        print(yaml_str)


if __name__ == "__main__":
    main()