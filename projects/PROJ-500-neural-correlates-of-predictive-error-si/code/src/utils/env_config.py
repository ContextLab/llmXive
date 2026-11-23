"""
Environment variable validation and error handling infrastructure.

This module provides a robust mechanism for validating required environment
variables, loading configuration with type coercion, and handling errors
gracefully with structured logging.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field

from .logging import get_logger, log_error, log_event

logger = get_logger(__name__)


@dataclass
class EnvVarDefinition:
    """Definition of a single environment variable requirement."""
    name: str
    required: bool = True
    default: Optional[Any] = None
    type_hint: Type[Any] = str
    description: str = ""
    allowed_values: Optional[List[Any]] = None


@dataclass
class ValidationResult:
    """Result of environment variable validation."""
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    resolved_config: Dict[str, Any] = field(default_factory=dict)


class EnvConfig:
    """
    Centralized environment variable management and validation.

    Usage:
        config = EnvConfig()
        config.define("DATA_ROOT", required=True, type_hint=Path, description="Root data directory")
        config.define("LOG_LEVEL", default="INFO", allowed_values=["DEBUG", "INFO", "WARNING", "ERROR"])
        
        result = config.validate()
        if not result.success:
            config.fail_fast(result)
        
        # Access validated config
        data_root = config.get("DATA_ROOT")
    """

    def __init__(self):
        self.definitions: Dict[str, EnvVarDefinition] = {}
        self._resolved: Dict[str, Any] = {}
        self._validated = False

    def define(
        self,
        name: str,
        required: bool = True,
        default: Optional[Any] = None,
        type_hint: Type[Any] = str,
        description: str = "",
        allowed_values: Optional[List[Any]] = None
    ) -> 'EnvConfig':
        """Define a required environment variable."""
        self.definitions[name] = EnvVarDefinition(
            name=name,
            required=required,
            default=default,
            type_hint=type_hint,
            description=description,
            allowed_values=allowed_values
        )
        return self

    def _coerce_type(self, value: str, type_hint: Type[Any], var_name: str) -> Any:
        """Coerce string value to target type."""
        if value is None:
            return None
        
        try:
            if type_hint == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif type_hint == int:
                return int(value)
            elif type_hint == float:
                return float(value)
            elif type_hint == Path:
                return Path(value)
            else:
                return type_hint(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert {var_name}='{value}' to {type_hint.__name__}: {e}")

    def validate(self) -> ValidationResult:
        """Validate all defined environment variables."""
        errors = []
        warnings = []
        resolved = {}

        logger.info("Starting environment variable validation")

        for name, definition in self.definitions.items():
            raw_value = os.getenv(name)
            
            # Check required
            if raw_value is None:
                if definition.required:
                    if definition.default is not None:
                        resolved[name] = definition.default
                        warnings.append(f"{name} is required but missing; using default: {definition.default}")
                    else:
                        errors.append(f"Required environment variable '{name}' is not set.")
                    continue
                else:
                    # Optional with default
                    if definition.default is not None:
                        resolved[name] = definition.default
                    continue

            # Type coercion
            try:
                coerced = self._coerce_type(raw_value, definition.type_hint, name)
            except ValueError as e:
                errors.append(str(e))
                continue

            # Allowed values check
            if definition.allowed_values is not None:
                if coerced not in definition.allowed_values:
                    errors.append(
                        f"Environment variable '{name}' has value '{coerced}'. "
                        f"Allowed values: {definition.allowed_values}"
                    )
                    continue

            resolved[name] = coerced

        result = ValidationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            resolved_config=resolved
        )

        if result.success:
            log_event("env_validation_success", details={"count": len(resolved)})
        else:
            log_error("env_validation_failed", details={"errors": errors})

        self._resolved = resolved
        self._validated = True
        return result

    def fail_fast(self, result: ValidationResult) -> None:
        """Log errors and exit if validation failed."""
        if not result.success:
            for error in result.errors:
                logger.error(error)
            logger.error(f"Environment validation failed with {len(result.errors)} error(s).")
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(warning)
            sys.exit(1)

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        """Get a validated environment variable."""
        if not self._validated:
            raise RuntimeError("Environment must be validated before access. Call validate() first.")
        
        if name not in self._resolved:
            if default is not None:
                return default
            raise KeyError(f"Environment variable '{name}' was not resolved during validation.")
        
        return self._resolved[name]

    def get_path(self, name: str) -> Path:
        """Get a validated environment variable as a Path."""
        val = self.get(name)
        if not isinstance(val, Path):
            val = Path(val)
        return val

    def load_from_file(self, path: Union[str, Path]) -> None:
        """
        Load environment variables from a .env file (simple key=value format).
        Does not override existing os.environ values unless explicitly set.
        """
        env_path = Path(path)
        if not env_path.exists():
            logger.warning(f"Environment file not found: {env_path}")
            return

        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    logger.warning(f"Skipping invalid line {line_num} in {env_path}: {line}")
                    continue
                
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if key and key not in os.environ:
                    os.environ[key] = value
                    logger.debug(f"Loaded env var from file: {key}")


# Global instance for convenience
_global_env_config = EnvConfig()


def get_env_config() -> EnvConfig:
    """Get the global environment configuration instance."""
    return _global_env_config


def validate_environment() -> ValidationResult:
    """
    Validate the global environment configuration.
    
    This is a convenience wrapper that calls validate() on the global instance
    and exits if validation fails.
    """
    result = _global_env_config.validate()
    if not result.success:
        _global_env_config.fail_fast(result)
    return result


def get_env(name: str, default: Optional[Any] = None, required: bool = True) -> Any:
    """
    Get an environment variable with type coercion and error handling.
    
    Args:
        name: Name of the environment variable
        default: Default value if not set (ignored if required=True)
        required: Whether the variable is required
        
    Returns:
        The value of the environment variable
        
    Raises:
        ValueError: If required variable is missing or invalid
    """
    val = os.getenv(name)
    if val is None:
        if required:
            raise ValueError(f"Required environment variable '{name}' is not set.")
        return default
    return val
