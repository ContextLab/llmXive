"""
Custom exception classes for the llmXive plant defense prediction pipeline.

Defines specific error codes as per plan.md requirements:
- E_DATASET: Data acquisition or availability failures
- E_PAIRING: Sample pairing failures (<95% match rate)
- E_TIMEOUT: Execution time limit exceeded (>4h)
- E_POWER: Power analysis failure (required n < 28)
"""

class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    
    def __init__(self, message: str, error_code: str = "E-UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class E_DATASET(PipelineError):
    """
    Raised when dataset acquisition fails or required data is unavailable.
    
    Triggers:
    - GEO/Metabolomics Workbench search returns no results
    - Required files missing or corrupted
    - Accession IDs invalid or deprecated
    - Data pairing feasibility <95% with no valid fallback
    """
    def __init__(self, message: str):
        super().__init__(message, "E-DATASET")


class E_PAIRING(PipelineError):
    """
    Raised when sample-level pairing rate is insufficient (<95%).
    
    Triggers:
    - Sample-level pairing <95% AND condition-level aggregation n < 28
    - Critical metadata mismatch preventing pairing
    - Fallback pairing strategy exhausted without success
    """
    def __init__(self, message: str):
        super().__init__(message, "E-PAIRING")


class E_TIMEOUT(PipelineError):
    """
    Raised when CPU time exceeds the 4-hour computational budget.
    
    Triggers:
    - Runtime > 4 hours (14400 seconds) as per FR-008
    - Resource monitoring detects imminent timeout
    """
    def __init__(self, message: str):
        super().__init__(message, "E-TIMEOUT")


class E_POWER(PipelineError):
    """
    Raised when power analysis indicates insufficient sample size.
    
    Triggers:
    - Calculated required n < 28 for effect size r=0.5, alpha=0.05, power=0.8
    - Actual available samples < required n
    - Power analysis aborts the pipeline per plan.md T009/T015
    """
    def __init__(self, message: str):
        super().__init__(message, "E-POWER")
