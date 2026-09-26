import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from rules.extractor import ExtractedRule, RuleExtractor

logger = logging.getLogger("rules.uncertainty_flagger")

@dataclass
class UncertaintyFlag:
    rule_id: str
    reason: str
    confidence: float

@dataclass
class UncertaintyReport:
    total_rules: int
    uncertain_rules: int
    flags: List[UncertaintyFlag]

class UncertaintyFlagger:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def flag(self, rules: List[ExtractedRule]) -> List[UncertaintyFlag]:
        flags = []
        for rule in rules:
            if rule.confidence < self.threshold:
                flags.append(UncertaintyFlag(
                    rule_id=rule.id,
                    reason=f"Low confidence ({rule.confidence})",
                    confidence=rule.confidence
                ))
        return flags

def main():
    logger.info("Running Uncertainty Flagging...")
    rules_path = Path("data/processed/extracted_rules.json")
    
    if not rules_path.exists():
        logger.warning("Extracted rules not found.")
        return
    
    with open(rules_path, 'r') as f:
        data = json.load(f)
        rules = [ExtractedRule(**r) for r in data.get("rules", [])]
    
    flagger = UncertaintyFlagger()
    flags = flagger.flag(rules)
    
    report = UncertaintyReport(
        total_rules=len(rules),
        uncertain_rules=len(flags),
        flags=flags
    )
    
    logger.info(f"Uncertainty Report: {report.uncertain_rules} uncertain rules found.")

if __name__ == "__main__":
    main()
