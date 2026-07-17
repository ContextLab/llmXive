import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

@dataclass
class ExclusionReason:
    reason: str
    count: int

@dataclass
class BiasReport:
    exclusions: List[ExclusionReason]
    total_excluded: int

def load_exclusion_log(path: Path) -> List[Dict[str, Any]]:
    """Load exclusion log."""
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)

def analyze_exclusion_bias(logs: List[Dict[str, Any]]) -> BiasReport:
    """Analyze bias in excluded entries."""
    reasons = {}
    for log in logs:
        r = log.get('reason', 'unknown')
        reasons[r] = reasons.get(r, 0) + 1
    
    exclusions = [ExclusionReason(r, c) for r, c in reasons.items()]
    return BiasReport(exclusions, sum(c for _, c in reasons.items()))

def write_bias_report(report: BiasReport, path: Path):
    """Write bias report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(report), f, indent=2)

def main():
    pass
