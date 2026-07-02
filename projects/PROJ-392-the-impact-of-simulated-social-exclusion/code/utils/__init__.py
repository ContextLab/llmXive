"""
Utility modules for the Social Exclusion fMRI analysis pipeline.
This file ensures the utils directory is recognized as a Python package.
"""
from .checksums import compute_sha256, generate_checksums, verify_checksums
from .provenance import generate_provenance_record, write_provenance_sidecar
from .framing_validator import FramingError, scan_for_causal_verbs, validate_report

__all__ = [
    'compute_sha256',
    'generate_checksums',
    'verify_checksums',
    'generate_provenance_record',
    'write_provenance_sidecar',
    'FramingError',
    'scan_for_causal_verbs',
    'validate_report'
]
