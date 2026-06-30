"""
Custom exceptions for the distribution shift detection pipeline.
"""

class E_NO_DATA(Exception):
    """
    Raised when required real-world CDC data files are missing.
    
    This exception enforces Constitution Principle VI and FR-001/FR-006,
    ensuring the pipeline halts immediately if the primary data sources
    (fluview_ili.csv or ground_truth_events.csv) are not present.
    No fallback to synthetic or local placeholder data is permitted.
    """
    pass
