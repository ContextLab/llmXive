"""
Utilities package for llmXive pipeline.

This package contains helper modules for logging, environment configuration,
timeout handling, and other cross-cutting concerns.
"""

from .logging import (
    PipelineError,
    ParseError,
    TimeoutError,
    OOMError,
    NetworkError,
    ChunkContext,
    get_logger,
    retry_on_transient_errors,
    handle_parse_error,
    handle_timeout_error,
    handle_oom_error,
    handle_network_error,
    main as logging_main
)

from .env_config import (
    load_environment,
    get_hf_token,
    get_env_var,
    validate_required_env_vars,
    get_environment_summary,
    main as env_config_main
)

from .timeout import (
    timeout_handler,
    enforce_timeout,
    main as timeout_main
)

__all__ = [
    # Logging
    "PipelineError",
    "ParseError",
    "TimeoutError",
    "OOMError",
    "NetworkError",
    "ChunkContext",
    "get_logger",
    "retry_on_transient_errors",
    "handle_parse_error",
    "handle_timeout_error",
    "handle_oom_error",
    "handle_network_error",
    "logging_main",
    
    # Environment configuration
    "load_environment",
    "get_hf_token",
    "get_env_var",
    "validate_required_env_vars",
    "get_environment_summary",
    "env_config_main",
    
    # Timeout handling
    "timeout_handler",
    "enforce_timeout",
    "timeout_main",
]