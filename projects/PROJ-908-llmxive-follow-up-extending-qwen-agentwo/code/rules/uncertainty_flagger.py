import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rules.extractor import ExtractedRule, RuleExtractor

logger = logging.getLogger(__name__)

@dataclass
class UncertaintyFlag:
    trace_id: str
    reason: str
    confidence: float

@dataclass
class UncertaintyReport:
    flags: List[UncertaintyFlag]

class UncertaintyFlagger:
    def flag(self, traces: List[Dict[str, Any]]) -> UncertaintyReport:
        return UncertaintyReport(flags=[])

def main():
    pass
