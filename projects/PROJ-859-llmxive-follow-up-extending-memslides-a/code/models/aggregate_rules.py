"""
Aggregate per-trace rule sets into a global rule set.

This module implements the logic to combine symbolic rules generated during
per-trace induction (T023) into a unified global rule bank. This global set
is required for the benchmarking phase (T031, T032).

The aggregation strategy:
1. Load all per-trace rule sets from the output directory of T023.
2. Parse rules into a canonical format (Condition -> Action).
3. Deduplicate rules based on exact string representation of condition and action.
4. Calculate global statistics (support, confidence) if metadata is available.
5. Save the aggregated set to `data/processed/rules/global_rules.json`.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict

from config import get_config
from utils.validators import SchemaValidator

class RuleAggregator:
    """Aggregates per-trace rule sets into a global rule set."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules_dir = Path(config['paths']['processed_rules'])
        self.output_path = Path(config['paths']['global_rules'])
        self.validator = SchemaValidator()

    def load_per_trace_rules(self) -> List[Dict[str, Any]]:
        """
        Loads all rule sets from the per-trace output directory.
        Expects files named `trace_<id>_rules.json` or similar in the rules directory.
        """
        if not self.rules_dir.exists():
            raise FileNotFoundError(
                f"Per-trace rules directory not found: {self.rules_dir}. "
                "Ensure T023 (rule_induction.py) has completed successfully."
            )

        all_rules = []
        rule_files = list(self.rules_dir.glob("*.json"))

        if not rule_files:
            raise FileNotFoundError(
                f"No rule files found in {self.rules_dir}. "
                "T023 must generate per-trace rule files before aggregation."
            )

        for file_path in rule_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both single rule list and dict with 'rules' key
                    if isinstance(data, list):
                        all_rules.extend(data)
                    elif isinstance(data, dict) and 'rules' in data:
                        all_rules.extend(data['rules'])
                    else:
                        # If it's a single rule object, wrap it
                        if 'condition' in data and 'action' in data:
                            all_rules.append(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {file_path}: {e}")

        return all_rules

    def deduplicate_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates rules based on (condition, action) pairs.
        Keeps the first occurrence and aggregates metadata (e.g., support count).
        """
        seen: Dict[Tuple[str, str], Dict[str, Any]] = {}
        global_id_counter = 0

        for rule in rules:
            condition = rule.get('condition', '')
            action = rule.get('action', '')
            key = (condition, action)

            if key not in seen:
                # New unique rule
                rule['global_id'] = global_id_counter
                global_id_counter += 1
                rule['support_count'] = 1
                seen[key] = rule
            else:
                # Duplicate found, increment support
                seen[key]['support_count'] += 1

        return list(seen.values())

    def sort_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts rules by support count (descending) to prioritize high-frequency patterns.
        """
        return sorted(rules, key=lambda x: x.get('support_count', 0), reverse=True)

    def validate_global_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """Validates the aggregated rules against the global rules schema."""
        # Basic structural validation
        if not rules:
            return False

        for rule in rules:
            if 'condition' not in rule or 'action' not in rule:
                return False
            if 'global_id' not in rule:
                return False
        return True

    def aggregate(self) -> Dict[str, Any]:
        """
        Main aggregation pipeline: Load -> Deduplicate -> Sort -> Validate -> Save.
        """
        print(f"Loading per-trace rules from {self.rules_dir}...")
        raw_rules = self.load_per_trace_rules()
        print(f"Loaded {len(raw_rules)} raw rules.")

        if not raw_rules:
            raise ValueError("No rules loaded to aggregate. T023 may have produced no rules.")

        print("Deduplicating rules...")
        unique_rules = self.deduplicate_rules(raw_rules)
        print(f"Found {len(unique_rules)} unique rules.")

        print("Sorting rules by support...")
        sorted_rules = self.sort_rules(unique_rules)

        if not self.validate_global_rules(sorted_rules):
            raise ValueError("Aggregated rules failed validation.")

        global_set = {
            "global_rules": sorted_rules,
            "metadata": {
                "total_raw_rules": len(raw_rules),
                "unique_rules": len(sorted_rules),
                "deduplication_rate": 1.0 - (len(sorted_rules) / len(raw_rules) if len(raw_rules) > 0 else 0),
                "generated_at": "auto-generated", # Placeholder for actual timestamp logic if needed
                "source": "T026b_aggregation"
            }
        }

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Saving global rules to {self.output_path}...")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(global_set, f, indent=2)

        print(f"Aggregation complete. Saved {len(sorted_rules)} rules.")
        return global_set

def main():
    """Entry point for rule aggregation."""
    config = get_config()
    aggregator = RuleAggregator(config)

    try:
        result = aggregator.aggregate()
        print(f"Success: Global rules saved to {config['paths']['global_rules']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except ValueError as e:
        print(f"Validation Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        raise

if __name__ == "__main__":
    main()
