import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

class RubricEngine:
    """
    Engine to calculate scores based on a loaded rubric schema.
    Implements weighted sum of criteria as defined in contracts/rubric_schema.json.
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the engine, optionally loading a schema immediately.
        
        Args:
            schema_path: Path to the rubric_schema.json file. If None, 
                         looks in contracts/rubric_schema.json relative to project root.
        """
        self.schema: Dict[str, Any] = {}
        self.schema_path = schema_path or self._default_schema_path()
        self.threshold_high: float = 40.0
        self.threshold_low: float = 10.0
        
        if os.path.exists(self.schema_path):
            self.load_schema(self.schema_path)

    @staticmethod
    def _default_schema_path() -> str:
        """Determine the default path to the rubric schema."""
        # Try relative to current working directory first, then project root
        candidates = [
            "contracts/rubric_schema.json",
            Path(__file__).parent.parent.parent / "contracts" / "rubric_schema.json"
        ]
        for candidate in candidates:
            path = Path(candidate)
            if path.exists():
                return str(path)
        return "contracts/rubric_schema.json"

    def load_schema(self, path: str) -> None:
        """
        Load and validate the rubric schema from a JSON file.
        
        Args:
            path: Path to the JSON schema file.
            
        Raises:
            FileNotFoundError: If the schema file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            ValueError: If the schema structure is invalid.
        """
        with open(path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        
        if not isinstance(self.schema, dict):
            raise ValueError("Schema must be a JSON object")
        
        # Extract thresholds if present, otherwise use defaults
        self.threshold_high = self.schema.get('threshold_high', 40.0)
        self.threshold_low = self.schema.get('threshold_low', 10.0)

    def _extract_text_feature(self, text: str, key: str, method: Optional[str] = None) -> Optional[str]:
        """
        Extract a specific feature from text based on the schema's feature_extraction_method.
        
        Args:
            text: The input text to search.
            key: The feature key to extract (e.g., 'hypothesis_clarity').
            method: The extraction method (e.g., 'regex_match', 'header_search').
            
        Returns:
            The extracted string or None if not found.
        """
        if not method:
            # Default fallback: look for the key as a header or keyword
            pattern = rf"(?i)\b{re.escape(key)}\b"
            match = re.search(pattern, text)
            return match.group(0) if match else None

        if method == "regex_match":
            # Try to match the key as a regex pattern
            try:
                match = re.search(key, text, re.IGNORECASE)
                return match.group(0) if match else None
            except re.error:
                # If key is not a valid regex, treat as literal
                if key.lower() in text.lower():
                    return key
                return None

        elif method == "header_search":
            # Look for the key in markdown-style headers or capitalized lines
            pattern = rf"(^|\n)\s*#{1,3}\s*.*{re.escape(key)}.*"
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(0)
            # Fallback: look for key followed by a colon on its own line
            pattern = rf"(^|\n)\s*{re.escape(key)}\s*:"
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            return match.group(0) if match else None

        return None

    def _evaluate_criteria(self, text: str, criteria_list: List[Dict]) -> Tuple[float, List[Dict]]:
        """
        Evaluate a list of criteria against the input text.
        
        Args:
            text: The text to evaluate.
            criteria_list: List of criterion definitions with 'key' and 'weight'.
            
        Returns:
            Tuple of (total_score, list of individual criterion results).
        """
        total_score = 0.0
        results = []

        for criterion in criteria_list:
            key = criterion.get('key')
            weight = criterion.get('weight', 1.0)
            
            if not key:
                continue

            # Extract the feature
            extracted = self._extract_text_feature(text, key)
            
            # Scoring logic: 
            # If found, score = weight * 10 (max per criterion)
            # If not found, score = 0
            # This assumes a 0-10 scale per criterion, weighted sum yields final score
            if extracted:
                score = weight * 10.0
            else:
                score = 0.0
            
            total_score += score
            results.append({
                'key': key,
                'found': extracted is not None,
                'extracted_value': extracted,
                'weight': weight,
                'score': score
            })

        return total_score, results

    def score(self, text: str) -> Dict[str, Any]:
        """
        Score the input text according to the loaded rubric schema.
        
        Args:
            text: The text to score.
            
        Returns:
            Dictionary containing:
            - 'total_score': The final calculated score.
            - 'categories': Breakdown by category (Protocol Alignment, Scientific Core, etc.).
            - 'threshold_high': The high threshold from schema.
            - 'threshold_low': The low threshold from schema.
            - 'status': "high" if >= threshold_high, "low" if < threshold_low, else "medium".
        """
        if not self.schema:
            raise RuntimeError("No schema loaded. Call load_schema() first.")

        categories = self.schema.get('categories', self.schema)
        # Handle both nested 'categories' key and top-level category definitions
        if 'categories' not in self.schema and not isinstance(categories.get('Protocol Alignment'), dict):
            # If schema is flat, treat it as categories
            categories = self.schema

        results = {
            'total_score': 0.0,
            'categories': {},
            'threshold_high': self.threshold_high,
            'threshold_low': self.threshold_low
        }

        # If the schema has a top-level 'categories' key, use it
        if 'categories' in self.schema:
            cat_defs = self.schema['categories']
        else:
            # Otherwise, assume top-level keys are categories
            cat_defs = self.schema

        for category_name, definition in cat_defs.items():
            if not isinstance(definition, dict):
                continue
            
            criteria = definition.get('criteria', [])
            if not criteria:
                continue

            score, criterion_results = self._evaluate_criteria(text, criteria)
            
            results['categories'][category_name] = {
                'score': score,
                'criteria_details': criterion_results
            }
            results['total_score'] += score

        # Determine status based on thresholds
        if results['total_score'] >= self.threshold_high:
            results['status'] = 'high'
        elif results['total_score'] < self.threshold_low:
            results['status'] = 'low'
        else:
            results['status'] = 'medium'

        return results

    def is_high_score(self, score: float) -> bool:
        """Check if a score meets the high threshold."""
        return score >= self.threshold_high

    def is_low_score(self, score: float) -> bool:
        """Check if a score is below the low threshold."""
        return score < self.threshold_low


def main():
    """
    CLI entry point for testing the rubric engine.
    Usage: python -m src.scoring.rubric_engine --schema <path> --text <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Rubric Engine CLI")
    parser.add_argument("--schema", type=str, help="Path to rubric schema JSON")
    parser.add_argument("--text", type=str, help="Path to text file to score")
    parser.add_argument("--text-inline", type=str, help="Inline text to score")
    
    args = parser.parse_args()

    engine = RubricEngine(args.schema)
    
    if args.text:
        with open(args.text, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text_inline:
        text = args.text_inline
    else:
        print("Error: Must provide --text or --text-inline")
        sys.exit(1)

    result = engine.score(text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()