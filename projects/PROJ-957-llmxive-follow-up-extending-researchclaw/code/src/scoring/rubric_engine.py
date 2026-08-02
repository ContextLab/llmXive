"""
Rubric Engine for ResearchClawBench.

Implements the scoring logic defined in contracts/rubric_schema.json.
Calculates weighted scores for 'Protocol Alignment' and 'Scientific Core'
based on criteria weights and feature extraction methods.
"""

import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure we can import from the project root structure if run as script
# but rely on the installed package structure for normal usage
try:
    from config import Config
except ImportError:
    # Fallback for direct execution in code/ directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import Config


class RubricEngine:
    """
    Engine to calculate scores based on a JSON schema definition.
    
    The schema defines:
    - Rubrics (e.g., "Protocol Alignment", "Scientific Core")
    - Criteria for each rubric (key, weight)
    - Thresholds (threshold_high, threshold_low)
    - Feature extraction method (e.g., regex match)
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the RubricEngine.
        
        Args:
            schema_path: Path to the rubric_schema.json file.
                        Defaults to 'contracts/rubric_schema.json' relative to project root.
        """
        self.config = Config.load()
        self.project_root = Path(__file__).parent.parent.parent
        
        if schema_path is None:
            self.schema_path = self.project_root / "contracts" / "rubric_schema.json"
        else:
            self.schema_path = Path(schema_path)
        
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Rubric schema not found at: {self.schema_path}")
        
        self.schema = self._load_schema()
        self.threshold_high = self.schema.get("threshold_high", 40)
        self.threshold_low = self.schema.get("threshold_low", 10)
        self.feature_extraction_method = self.schema.get("feature_extraction_method", "regex_match")

    def _load_schema(self) -> Dict[str, Any]:
        """Load and validate the JSON schema file."""
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation
        if "rubrics" not in data:
            raise ValueError("Schema must contain 'rubrics' key")
        
        return data

    def _extract_feature(self, text: str, key: str) -> float:
        """
        Extract a feature value from text based on the schema's method.
        
        Currently supports 'regex_match' which looks for the key as a header
        or specific marker in the text.
        
        Args:
            text: The text to analyze.
            key: The feature key to look for (e.g., 'protocol_step_1').
        
        Returns:
            float: 1.0 if found, 0.0 if not found.
        """
        if self.feature_extraction_method == "regex_match":
            # Look for the key as a header or distinct marker
            # Pattern: Key as a header (e.g., "### protocol_step_1" or "## protocol_step_1")
            # or simply the key appearing in the text
            pattern = rf"(?i)(^|\s|[#\-\*])\s*{re.escape(key)}\s*(\s|$)"
            if re.search(pattern, text):
                return 1.0
            # Fallback: simple substring match if regex fails to capture context
            if key.lower() in text.lower():
                return 1.0
            return 0.0
        else:
            # Default fallback for unknown methods
            if key.lower() in text.lower():
                return 1.0
            return 0.0

    def calculate_rubric_score(self, rubric_name: str, text: str) -> float:
        """
        Calculate the score for a specific rubric based on the text.
        
        Args:
            rubric_name: The name of the rubric (e.g., "Protocol Alignment").
            text: The text content to score.
        
        Returns:
            float: The calculated score (0-100).
        """
        rubric_def = self.schema["rubrics"].get(rubric_name)
        if not rubric_def:
            raise ValueError(f"Rubric '{rubric_name}' not found in schema")
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        criteria = rubric_def.get("criteria", [])
        if not criteria:
            return 0.0
        
        for criterion in criteria:
            key = criterion["key"]
            weight = criterion["weight"]
            
            feature_value = self._extract_feature(text, key)
            weighted_sum += feature_value * weight
            total_weight += weight
        
        # Normalize by total weight and scale to 100
        if total_weight == 0:
            return 0.0
        
        normalized_score = (weighted_sum / total_weight) * 100
        return normalized_score

    def calculate_total_score(self, text: str) -> Dict[str, float]:
        """
        Calculate scores for all rubrics defined in the schema.
        
        Args:
            text: The text content to score.
        
        Returns:
            Dict[str, float]: A dictionary mapping rubric names to their scores.
        """
        scores = {}
        for rubric_name in self.schema["rubrics"].keys():
            scores[rubric_name] = self.calculate_rubric_score(rubric_name, text)
        return scores

    def evaluate(self, text: str) -> Dict[str, Any]:
        """
        Perform a full evaluation of the text against the rubric.
        
        Args:
            text: The text content to evaluate.
        
        Returns:
            Dict containing scores, thresholds, and pass/fail status.
        """
        scores = self.calculate_total_score(text)
        total_score = sum(scores.values()) / len(scores) if scores else 0.0
        
        status = "neutral"
        if total_score >= self.threshold_high:
            status = "pass"
        elif total_score <= self.threshold_low:
            status = "fail"
        
        return {
            "scores": scores,
            "total_score": total_score,
            "threshold_high": self.threshold_high,
            "threshold_low": self.threshold_low,
            "status": status
        }

def main():
    """
    CLI entry point for testing the rubric engine.
    Reads a sample text (or generates a dummy one if no input provided)
    and prints the evaluation results.
    
    Usage:
        python -m src.scoring.rubric_engine
    """
    # For demonstration, we generate a dummy text that should trigger a high score
    # based on the schema defined in T010a (assuming keys like 'protocol_step_1', 'hypothesis_clarity')
    
    dummy_text_pass = """
    ### protocol_step_1
    Step 1: Mix A and B.
    ### protocol_step_2
    Step 2: Heat to 50C.
    ### hypothesis_clarity
    The hypothesis is clear.
    ### methodology_soundness
    The methodology is sound.
    """
    
    dummy_text_fail = """
    Here is a random text with no steps or clarity.
    Just some words.
    """
    
    engine = RubricEngine()
    
    print("Evaluating PASS text:")
    result_pass = engine.evaluate(dummy_text_pass)
    print(json.dumps(result_pass, indent=2))
    
    print("\nEvaluating FAIL text:")
    result_fail = engine.evaluate(dummy_text_fail)
    print(json.dumps(result_fail, indent=2))
    
    # Write output to a file as per task requirements
    output_path = Path(__file__).parent.parent.parent / "results" / "rubric_engine_test.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "pass_result": result_pass,
            "fail_result": result_fail
        }, f, indent=2)
    
    print(f"\nResults written to {output_path}")

if __name__ == "__main__":
    main()
