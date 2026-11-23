"""
Schema validation utilities.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import sys

class SchemaValidator:
    """Base validator for schema checks."""
    def validate(self, data: Any, schema: Dict[str, Any]) -> bool:
        raise NotImplementedError

class TraceValidator(SchemaValidator):
    """Validates trace structure."""
    def validate(self, data: Dict[str, Any]) -> bool:
        required = ['trace_id', 'tool_sequence']
        return all(k in data for k in required)

class MetricsValidator(SchemaValidator):
    """Validates metrics structure."""
    def validate(self, data: Dict[str, Any]) -> bool:
        required = ['trace_id', 'entropy', 'repetition_freq']
        return all(k in data for k in required)

class BenchmarkValidator(SchemaValidator):
    """Validates benchmark results."""
    def validate(self, data: Dict[str, Any]) -> bool:
        required = ['baseline_acc', 'compressed_acc', 'latency']
        return all(k in data for k in required)
