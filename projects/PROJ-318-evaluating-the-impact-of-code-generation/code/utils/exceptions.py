class RepoFetcherException(Exception):
    """Exception raised when fetching repository list fails."""
    pass

class RepoLoaderException(Exception):
    """Exception raised when loading repository list fails."""
    pass

class GenerationException(Exception):
    """Exception raised during docstring generation."""
    pass

class CoverageException(Exception):
    """Exception raised during coverage calculation."""
    pass

class StatsException(Exception):
    """Exception raised during statistical analysis."""
    pass

class ModelLoadException(Exception):
    """Exception raised during model loading."""
    pass

class ModelDeviationException(Exception):
    """Exception raised when model deviates from expected configuration."""
    pass

class ASTParsingException(Exception):
    """Exception raised during AST parsing."""
    pass

class FileWalkerException(Exception):
    """Exception raised during file walking."""
    pass

class GitCloneException(Exception):
    """Exception raised during Git cloning."""
    pass

class SerializationException(Exception):
    """Exception raised during serialization/deserialization."""
    pass

class ConfigException(Exception):
    """Exception raised during configuration loading."""
    pass

class MemoryLimitException(Exception):
    """Exception raised when memory limit is exceeded."""
    pass