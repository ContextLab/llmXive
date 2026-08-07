"""
Configuration module for llmXive research pipeline.
Implements Constitution Principle I: Deterministic Reproducibility.
"""

import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# ============================================================================
# Constitution Principle I: Hardcoded Random Seeds
# ============================================================================
# All stochastic processes must be seeded with this fixed value to ensure
# that experiments are exactly reproducible given the same code and data.
# Changing this value invalidates previous results and requires a full
# re-run of the experiment suite.
# ============================================================================

RANDOM_SEED = 42

# Environment Variable Keys
HF_TOKEN_ENV = "HF_TOKEN"
MODEL_PATH_ENV = "MODEL_PATH"
DATA_DIR_ENV = "DATA_DIR"
OUTPUT_DIR_ENV = "OUTPUT_DIR"
LOG_LEVEL_ENV = "LOG_LEVEL"

# Default Paths (relative to project root)
DEFAULT_DATA_DIR = "data"
DEFAULT_OUTPUT_DIR = "data/intermediate"
DEFAULT_LOG_LEVEL = "INFO"

# Model Configuration Defaults
DEFAULT_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_QUANTIZATION = "Q4_K_M"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.0  # Deterministic by default for reproducibility
DEFAULT_TOP_P = 1.0

# Experiment Budgets (in seconds)
INSTANCE_TIMEOUT = 3600  # 60 minutes per instance
TOTAL_WALL_CLOCK_LIMIT = 259200  # 72 hours total

# Analysis Thresholds
CONTEXT_LENGTH_THRESHOLD = 500  # Lines for "high complexity" filtering
PASS_THRESHOLD = 0.05  # P-value threshold for significance
MIN_PASS_DIFF = 0.05  # Minimum 5% difference for meaningful comparison

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# Data Models (Constitution Principle III: Data Integrity)
# ============================================================================
# These classes define the schema for Task Instances, Context Configurations,
# and Execution Results. They serve as the single source of truth for data
# structures used throughout the pipeline.
# ============================================================================

class FailureType(Enum):
    """Classification of execution failure modes."""
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_OOM = "memory_oom"
    SYNTAX_ERROR = "syntax_error"
    UNKNOWN = "unknown"


class StrategyType(Enum):
    """Types of context processing strategies."""
    BASELINE_NAIVE = "baseline_naive"
    TF_IDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"


@dataclass
class TaskInstance:
    """
    Represents a single task instance from the Claw-SWE-Bench dataset.
    Encapsulates the problem statement, repository context, and metadata.
    """
    instance_id: str
    problem_statement: str
    repo: str
    base_commit: str
    relevant_files: List[str]
    imports_graph: Optional[Dict[str, List[str]]] = None
    total_lines: int = 0
    complexity_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "instance_id": self.instance_id,
            "problem_statement": self.problem_statement,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "relevant_files": self.relevant_files,
            "imports_graph": self.imports_graph,
            "total_lines": self.total_lines,
            "complexity_score": self.complexity_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskInstance":
        """Reconstruct from dictionary."""
        return cls(
            instance_id=data["instance_id"],
            problem_statement=data["problem_statement"],
            repo=data["repo"],
            base_commit=data["base_commit"],
            relevant_files=data["relevant_files"],
            imports_graph=data.get("imports_graph"),
            total_lines=data.get("total_lines", 0),
            complexity_score=data.get("complexity_score", 0.0)
        )


@dataclass
class ContextConfiguration:
    """
    Configuration for how context is processed and fed to the model.
    Defines the strategy and parameters used for context compression.
    """
    strategy: StrategyType
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    truncation_method: str = "first_n"  # Options: "first_n", "last_n", "random"
    retrieval_k: int = 10  # Number of snippets to retrieve for TF-IDF/Diff
    summary_length: int = 500  # Target length for semantic summarization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy": self.strategy.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "truncation_method": self.truncation_method,
            "retrieval_k": self.retrieval_k,
            "summary_length": self.summary_length
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextConfiguration":
        """Reconstruct from dictionary."""
        strategy_str = data.get("strategy", "baseline_naive")
        try:
            strategy = StrategyType(strategy_str)
        except ValueError:
            strategy = StrategyType.BASELINE_NAIVE

        return cls(
            strategy=strategy,
            max_tokens=data.get("max_tokens", DEFAULT_MAX_TOKENS),
            temperature=data.get("temperature", DEFAULT_TEMPERATURE),
            top_p=data.get("top_p", DEFAULT_TOP_P),
            truncation_method=data.get("truncation_method", "first_n"),
            retrieval_k=data.get("retrieval_k", 10),
            summary_length=data.get("summary_length", 500)
        )


@dataclass
class ExecutionResult:
    """
    Represents the outcome of executing a model on a specific task instance
    with a specific context configuration.
    """
    instance_id: str
    config: ContextConfiguration
    success: bool
    pass_fail: bool  # Did the solution pass the tests?
    output_text: str
    error_message: Optional[str] = None
    failure_type: Optional[FailureType] = None
    tokens_used: int = 0
    execution_time_seconds: float = 0.0
    context_lines_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "instance_id": self.instance_id,
            "config": self.config.to_dict(),
            "success": self.success,
            "pass_fail": self.pass_fail,
            "output_text": self.output_text,
            "error_message": self.error_message,
            "failure_type": self.failure_type.value if self.failure_type else None,
            "tokens_used": self.tokens_used,
            "execution_time_seconds": self.execution_time_seconds,
            "context_lines_used": self.context_lines_used,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """Reconstruct from dictionary."""
        config = ContextConfiguration.from_dict(data["config"])
        failure_type = None
        if data.get("failure_type"):
            try:
                failure_type = FailureType(data["failure_type"])
            except ValueError:
                failure_type = FailureType.UNKNOWN

        return cls(
            instance_id=data["instance_id"],
            config=config,
            success=data["success"],
            pass_fail=data["pass_fail"],
            output_text=data["output_text"],
            error_message=data.get("error_message"),
            failure_type=failure_type,
            tokens_used=data.get("tokens_used", 0),
            execution_time_seconds=data.get("execution_time_seconds", 0.0),
            context_lines_used=data.get("context_lines_used", 0),
            metadata=data.get("metadata", {})
        )


# ============================================================================
# Existing Functions (Preserved)
# ============================================================================

def set_global_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for all major stochastic libraries to ensure reproducibility.
    This function MUST be called at the entry point of any experiment script.

    Args:
        seed: The random seed value (defaults to RANDOM_SEED constant).
    """
    # Python built-in random
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior in CUDA operations
        # Note: This may reduce performance but is required for reproducibility
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Hugging Face datasets and transformers
    try:
        import datasets
        datasets.set_seed(seed)
    except ImportError:
        pass

    try:
        import transformers
        # Transformers often use torch/numpy internally, but explicit setting helps
        transformers.set_seed(seed)
    except ImportError:
        pass


def get_env_var(name: str, default: str | None = None) -> str | None:
    """
    Retrieve an environment variable with an optional default.

    Args:
        name: The environment variable name.
        default: Default value if the variable is not set.

    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(name, default)


def get_hf_token() -> str:
    """
    Retrieve the Hugging Face token from environment variables.

    Returns:
        The HF token string.

    Raises:
        RuntimeError: If the token is not set in the environment.
    """
    token = get_env_var(HF_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"Environment variable '{HF_TOKEN_ENV}' is not set. "
            "Please set it to your Hugging Face access token."
        )
    return token


def get_model_path() -> str:
    """
    Retrieve the model path from environment variables or use default.

    Returns:
        The path to the model.
    """
    path = get_env_var(MODEL_PATH_ENV)
    return path if path else DEFAULT_MODEL_NAME


def get_data_dir() -> str:
    """
    Retrieve the data directory from environment variables or use default.

    Returns:
        The path to the data directory.
    """
    path = get_env_var(DATA_DIR_ENV)
    return path if path else DEFAULT_DATA_DIR


def get_output_dir() -> str:
    """
    Retrieve the output directory from environment variables or use default.

    Returns:
        The path to the output directory.
    """
    path = get_env_var(OUTPUT_DIR_ENV)
    return path if path else DEFAULT_OUTPUT_DIR


def get_log_level() -> str:
    """
    Retrieve the log level from environment variables or use default.

    Returns:
        The log level string.
    """
    level = get_env_var(LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL)
    return level.upper()