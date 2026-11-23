"""
Rubric Engine for scoring agent outputs against the ResearchClawBench protocol.
Loads schema from contracts/rubric_schema.json and calculates scores.
"""
import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "rubric_schema.json"

class RubricEngine:
    """
    Engine to calculate scores based on a dynamic JSON schema.
    """
    def __init__(self, schema_path: Optional[Path] = None):
        self.schema_path = schema_path or SCHEMA_PATH
        self.schema = self._load_schema()
        self.threshold_high = self.schema.get("threshold_high", 40)
        self.threshold_low = self.schema.get("threshold_low", 10)

    def _load_schema(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Rubric schema not found at {self.schema_path}")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _extract_criteria_value(self, text: str, criteria_key: str) -> float:
        """
        Extracts a value for a specific criteria key from the text.
        Implementation based on 'feature_extraction_method' in schema (regex match).
        Returns 1.0 if found, 0.0 otherwise.
        """
        # Simple heuristic: check if the key (or a variation) appears in the text
        # This mimics the "regex match for step headers" described in T010a
        pattern = re.compile(re.escape(criteria_key), re.IGNORECASE)
        if pattern.search(text):
            return 1.0
        # Fallback for specific keys mentioned in schema
        if criteria_key == "protocol_step_1" and "Step 1" in text:
            return 1.0
        if criteria_key == "protocol_step_2" and "Step 2" in text:
            return 1.0
        if criteria_key == "hypothesis_clarity" and "hypothesis" in text.lower():
            return 1.0
        if criteria_key == "methodology_soundness" and "method" in text.lower():
            return 1.0
        return 0.0

    def calculate_score(self, text: str, rubric_name: str = "Protocol Alignment") -> float:
        """
        Calculates a score for the given text based on the specified rubric.
        """
        if rubric_name not in self.schema:
            raise ValueError(f"Rubric '{rubric_name}' not found in schema")

        rubric_config = self.schema[rubric_name]
        criteria_list = rubric_config.get("criteria", [])

        if not criteria_list:
            return 0.0

        total_weight = sum(c.get("weight", 0) for c in criteria_list)
        if total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for criterion in criteria_list:
            key = criterion.get("key")
            weight = criterion.get("weight", 0)
            value = self._extract_criteria_value(text, key)
            weighted_sum += value * weight

        # Normalize to 0-100 scale if weights are fractions summing to 1
        # Assuming weights sum to 1.0 based on T010a definition
        score = weighted_sum * 100
        return round(score, 2)

    def validate_against_thresholds(self, score: float, rubric_name: str = "Protocol Alignment") -> Tuple[bool, str]:
        """
        Validates a score against the schema-defined thresholds.
        Returns (is_valid, message)
        """
        if score >= self.threshold_high:
            return True, f"Score {score} >= {self.threshold_high} (High)"
        elif score < self.threshold_low:
            return True, f"Score {score} < {self.threshold_low} (Low)"
        else:
            return False, f"Score {score} is between {self.threshold_low} and {self.threshold_high} (Ambiguous)"

    def main(self):
        """Entry point for CLI usage."""
        print(f"Rubric Engine loaded from {self.schema_path}")
        print(f"Thresholds: High={self.threshold_high}, Low={self.threshold_low}")
        # Example usage
        sample_text = "Step 1: Mix A and B. Step 2: Heat to 50C."
        score = self.calculate_score(sample_text)
        print(f"Sample Score: {score}")

def main():
    engine = RubricEngine()
    engine.main()

if __name__ == "__main__":
    main()
