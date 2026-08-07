"""
llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs
Main package initialization.
"""

# Import core configuration symbols to make them available at package level
from config import (
    StrategyType,
    MemoryConstraintError,
    TaskInstance,
    ContextConfiguration,
    ExecutionResult,
    load_environment_config,
    set_global_seed,
)

# Import data layer
from data.loader import ClawSweBenchLoader, ParsedIssue
from data.context_processors import (
    ContextSnippet,
    ProcessedContext,
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    process_context,
)

# Import models
from models.runner import ModelRunner

# Import experiments
from experiments.batch_executor import BatchExecutor, BatchExecutionStats, GlobalSchedulerError

# Import analysis
from analysis.failure_classifier import classify_failure, FailureClassification
from analysis.merge_results import merge_results

__all__ = [
    # Config
    "StrategyType",
    "MemoryConstraintError",
    "TaskInstance",
    "ContextConfiguration",
    "ExecutionResult",
    "load_environment_config",
    "set_global_seed",
    # Data
    "ClawSweBenchLoader",
    "ParsedIssue",
    "ContextSnippet",
    "ProcessedContext",
    "retrieve_tfidf_snippets",
    "retrieve_diff_aware_snippets",
    "retrieve_semantic_summaries",
    "process_context",
    # Models
    "ModelRunner",
    # Experiments
    "BatchExecutor",
    "BatchExecutionStats",
    "GlobalSchedulerError",
    # Analysis
    "classify_failure",
    "FailureClassification",
    "merge_results",
]
