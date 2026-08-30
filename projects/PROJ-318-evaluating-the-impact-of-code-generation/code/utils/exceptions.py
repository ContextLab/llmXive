"""Custom exceptions for the llmXive pipeline."""

class GenerationException(Exception):
    """Exception raised for docstring generation errors."""
    pass

class CoverageException(Exception):
    """Exception raised for coverage calculation errors."""
    pass

class StatsException(Exception):
    """Exception raised for statistical analysis errors."""
    pass

class ModelLoadException(Exception):
    """Exception raised for model loading errors."""
    pass

class ModelDeviationException(Exception):
    """Exception raised for model devicization errors."""
    pass

class ASTParsingException(Exception):
    """Exception raised for AST parsing errors."""
    pass

class FileWalkerException(Exception):
    """Exception raised for file walking errors."""
    pass

class GitCloneException(Exception):
    """Exception raised for Git cloning errors."""
    pass

class RepoFetcherException(Exception):
    """Exception raised for repository fetching errors."""
    pass

class RepoLoaderException(Exception):
    """Exception raised for repository loading errors."""
    pass

class SerializationException(Exception):
    """Exception raised for serialization errors."""
    pass

class ConfigException(Exception):
    """Exception raised for configuration errors."""
    pass

class MemoryLimitException(Exception):
    """Exception raised when RAM usage exceeds the configured limit."""
    pass