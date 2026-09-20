import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from rules.extractor import RuleExtractor

logger = logging.getLogger(__name__)

def generate_rules_artifact(rules: List[Any], output_path: Path):
    logger.info(f"Generating rules artifact at {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in rules], f, indent=2)

def main():
    pass
