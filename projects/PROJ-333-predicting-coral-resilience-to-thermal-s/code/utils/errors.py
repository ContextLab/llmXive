class NCBIError(Exception):
    """Base exception for NCBI-related errors."""
    pass

class NCBITimeoutError(NCBIError):
    """Exception raised when an NCBI request times out."""
    pass

class NCBIConnectionError(NCBIError):
    """Exception raised when connection to NCBI fails."""
    pass

class ChecksumError(Exception):
    """Base exception for checksum verification errors."""
    pass

class ChecksumMismatchError(ChecksumError):
    """Exception raised when file checksum does not match expected value."""
    pass

class ChecksumFetchError(ChecksumError):
    """Exception raised when fetching checksum from remote source fails."""
    pass
