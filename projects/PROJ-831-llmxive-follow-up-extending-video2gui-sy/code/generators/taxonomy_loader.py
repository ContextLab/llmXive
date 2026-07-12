"""
Taxonomy Loader: Parses the GUI Error Taxonomy YAML file into rule objects.
"""
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ErrorRule:
    """Represents a single error rule from the taxonomy."""
    rule_id: str
    name: str
    description: str
    category: str
    injection_trigger: str
    recovery_path: str
    severity: int  # 1-5
    probability: float  # 0.0-1.0

class TaxonomyLoader:
    """Loads and parses the GUI Error Taxonomy YAML file."""

    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = Path(taxonomy_path)
        self.rules: List[ErrorRule] = []

    def load(self) -> List[ErrorRule]:
        """Load and parse the taxonomy file."""
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {self.taxonomy_path}")

        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or 'rules' not in data:
            raise ValueError("Taxonomy file must contain a 'rules' key with a list of rules")

        self.rules = []
        for item in data['rules']:
            try:
                rule = ErrorRule(
                    rule_id=item.get('rule_id', ''),
                    name=item.get('name', ''),
                    description=item.get('description', ''),
                    category=item.get('category', ''),
                    injection_trigger=item.get('injection_trigger', ''),
                    recovery_path=item.get('recovery_path', ''),
                    severity=int(item.get('severity', 3)),
                    probability=float(item.get('probability', 0.5))
                )
                self.rules.append(rule)
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid rule format in taxonomy: {item}") from e

        return self.rules

    def get_rules_by_category(self, category: str) -> List[ErrorRule]:
        """Filter rules by category."""
        return [r for r in self.rules if r.category == category]

    def get_high_severity_rules(self, min_severity: int = 4) -> List[ErrorRule]:
        """Get rules with severity >= min_severity."""
        return [r for r in self.rules if r.severity >= min_severity]
