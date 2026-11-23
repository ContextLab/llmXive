import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("rules.validator")

@dataclass
class ValidationResult:
    rule_id: str
    passed: bool
    reason: str

@dataclass
class ValidationSummary:
    total: int
    passed: int
    failed: int

class RuleValidator:
    def __init__(self, oracle_graph: Dict[str, Any]):
        self.oracle_graph = oracle_graph

    def validate(self, rules: List[Dict[str, Any]]) -> List[ValidationResult]:
        results = []
        for rule in rules:
            # Simplified validation: check if rule logic exists in oracle
            logic = str(rule.get("logic", ""))
            found = False
            for node in self.oracle_graph.get("nodes", []):
                if logic in str(node.get("state_transition", {})):
                    found = True
                    break
            
            results.append(ValidationResult(
                rule_id=rule.get("id", "unknown"),
                passed=found,
                reason="Found in Oracle" if found else "Not found in Oracle"
            ))
        return results

def main():
    logger.info("Starting Rule Validation...")
    rules_path = Path("data/processed/extracted_rules.json")
    oracle_path = Path("data/processed/oracle_graph.json")
    
    if not rules_path.exists() or not oracle_path.exists():
        logger.warning("Required files missing. Skipping validation.")
        return
    
    with open(rules_path, 'r') as f:
        rules_data = json.load(f)
        rules = rules_data.get("rules", [])
    
    with open(oracle_path, 'r') as f:
        oracle_graph = json.load(f)
    
    validator = RuleValidator(oracle_graph)
    results = validator.validate(rules)
    
    summary = ValidationSummary(
        total=len(results),
        passed=len([r for r in results if r.passed]),
        failed=len([r for r in results if not r.passed])
    )
    
    logger.info(f"Validation Summary: {summary}")

if __name__ == "__main__":
    main()
