"""
Custom exception types for the llmXive cross-dataset APF consistency pipeline.

These exceptions are used to enforce strict data integrity and pipeline
failure reporting, ensuring that errors are caught and handled explicitly
rather than failing silently or with generic errors.
"""

class DataIntegrityError(Exception):
    """
    Raised when data fails validation checks regarding its structural
    or content integrity.

    Examples:
        - Missing required BIDS fields (e.g., sampling_frequency)
        - Mismatched channel counts
        - Presence of NaN values in signal data where not allowed
        - Checksum mismatches
    """
    pass

class MissingMetadataError(Exception):
    """
    Raised when a required metadata field is absent from the dataset
    description or sidecar files.

    This is a specific subclass of DataIntegrityError to allow for
    granular error handling in the ingestion pipeline.
    """
    pass

class PipelineFailureError(Exception):
    """
    Raised when a preprocessing or analysis pipeline step fails
    unexpectedly or produces invalid output.

    This indicates a logic error, resource exhaustion (OOM), or
    an unrecoverable state in the processing workflow.
    """
    pass