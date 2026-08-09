"""
llmXive Research Pipeline: Gut Microbiome and Sleep Architecture Correlation Study

This package contains the implementation of the automated science pipeline
for investigating the correlation between gut microbiome composition and
sleep architecture.

Modules:
- ingest: Data loading, validation, and preprocessing
- analysis: Statistical correlation analysis and method selection
- diagnostics: Collinearity, VIF, power, and sensitivity analysis
- report: Report generation with associational framing
- config: Configuration management
- reference_validator: Citation verification and validation logic
- constitution_checker: Integrity and checksum validation
"""

__version__ = "1.0.0"
__project__ = "PROJ-340-investigating-the-correlation-between-gu"

# Ensure all submodules are importable from the package root
from . import ingest
from . import analysis
from . import diagnostics
from . import report
from . import config
from . import reference_validator
from . import constitution_checker

__all__ = [
    "ingest",
    "analysis",
    "diagnostics",
    "report",
    "config",
    "reference_validator",
    "constitution_checker",
]