"""
Module for aggregating per-trace rule sets into a global rule set.

This implements Task T026b: Combine per-trace rule sets from T023 into a 
global rule set required for the benchmarking phase (FR-004).
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
import hashlib

from config import get_config


class RuleAggregator:
    """
    Aggregates per-trace rule sets into a global rule set.
    
    Logic:
    1. Load per-trace rule sets from the output of T023 (rule_induction).
    2. Normalize rules to a canonical form to detect duplicates.
    3. Aggregate rules by frequency of occurrence across traces.
    4. Filter rules based on minimum support (frequency) if configured.
    5. Save the global rule set to `data/processed/rules/global_rules.json`.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_support = config.get('rule_aggregation', {}).get('min_support', 2)
        self.output_path = Path(config['paths']['processed_rules']) / 'global_rules.json'
        self.input_dir = Path(config['paths']['processed_rules'])
        
    def _canonicalize_rule(self, rule: Dict[str, Any]) -> str:
        """
        Convert a rule dict to a canonical string for hashing/deduplication.
        
        This ensures that rules with the same logical meaning but different 
        ordering of conditions are treated as identical.
        """
        # Sort conditions and actions for consistent hashing
        conditions = rule.get('conditions', [])
        actions = rule.get('actions', [])
        
        # Sort conditions by their string representation
        sorted_conditions = sorted(
            [json.dumps(c, sort_keys=True) for c in conditions]
        )
        sorted_actions = sorted(
            [json.dumps(a, sort_keys=True) for a in actions]
        )
        
        return f"COND:{'|'.join(sorted_conditions)}|ACT:{'|'.join(sorted_actions)}"
    
    def _load_per_trace_rules(self, trace_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load per-trace rule sets from the output of T023.
        
        Expected file naming: `data/processed/rules/trace_{trace_id}_rules.json`
        """
        per_trace_rules = {}
        
        for trace_id in trace_ids:
            rule_file = self.input_dir / f'trace_{trace_id}_rules.json'
            
            if not rule_file.exists():
                raise FileNotFoundError(
                    f"Per-trace rule file not found for trace {trace_id}: {rule_file}"
                )
            
            with open(rule_file, 'r') as f:
                rules = json.load(f)
            
            per_trace_rules[trace_id] = rules
        
        return per_trace_rules
    
    def _aggregate_rules(
        self, 
        per_trace_rules: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate rules across all traces, counting support and merging.
        
        Returns a list of global rules with support counts.
        """
        rule_support = defaultdict(lambda: {'count': 0, 'traces': set()})
        rule_templates = {}  # canonical_key -> rule template
        
        for trace_id, rules in per_trace_rules.items():
            for rule in rules:
                canonical_key = self._canonicalize_rule(rule)
                
                # Store the rule template if not already seen
                if canonical_key not in rule_templates:
                    rule_templates[canonical_key] = rule
                
                # Increment support
                rule_support[canonical_key]['count'] += 1
                rule_support[canonical_key]['traces'].add(trace_id)
        
        # Build global rule list
        global_rules = []
        for canonical_key, support_data in rule_support.items():
            # Filter by minimum support
            if support_data['count'] < self.min_support:
                continue
            
            rule_template = rule_templates[canonical_key]
            
            # Create global rule with support metadata
            global_rule = {
                **rule_template,
                'support_count': support_data['count'],
                'support_traces': sorted(list(support_data['traces'])),
                'rule_id': hashlib.md5(canonical_key.encode()).hexdigest()[:12]
            }
            
            global_rules.append(global_rule)
        
        # Sort by support count (descending) for interpretability
        global_rules.sort(key=lambda x: x['support_count'], reverse=True)
        
        return global_rules
    
    def aggregate(self, trace_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main aggregation method.
        
        Args:
            trace_ids: Optional list of trace IDs to aggregate. If None, 
                       discovers all trace rule files in the input directory.
        
        Returns:
            Dictionary containing the global rule set and metadata.
        """
        # Discover trace IDs if not provided
        if trace_ids is None:
            trace_ids = []
            for file in self.input_dir.glob('trace_*_rules.json'):
                # Extract trace_id from filename
                trace_id = file.stem.replace('trace_', '').replace('_rules', '')
                trace_ids.append(trace_id)
        
        if not trace_ids:
            raise ValueError(
                "No trace rule files found. Ensure T023 has completed and "
                "generated per-trace rule files in the processed rules directory."
            )
        
        # Load per-trace rules
        per_trace_rules = self._load_per_trace_rules(trace_ids)
        
        # Aggregate rules
        global_rules = self._aggregate_rules(per_trace_rules)
        
        # Build result
        result = {
            'global_rules': global_rules,
            'metadata': {
                'total_traces_processed': len(trace_ids),
                'total_rules_before_filter': sum(
                    len(rules) for rules in per_trace_rules.values()
                ),
                'total_rules_after_filter': len(global_rules),
                'min_support_threshold': self.min_support,
                'aggregation_timestamp': str(Path().absolute().resolve())  # Placeholder for actual timestamp
            }
        }
        
        return result
    
    def save(self, result: Dict[str, Any]) -> Path:
        """
        Save the aggregated global rules to the output file.
        
        Args:
            result: The aggregated rule set from `aggregate()`.
        
        Returns:
            Path to the saved file.
        """
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return self.output_path


def main():
    """
    Main entry point for rule aggregation.
    
    Usage:
        python -m models.aggregate_rules
    """
    config = get_config()
    
    try:
        aggregator = RuleAggregator(config)
        
        print(f"Starting rule aggregation with min_support={aggregator.min_support}")
        print(f"Input directory: {aggregator.input_dir}")
        print(f"Output file: {aggregator.output_path}")
        
        # Perform aggregation
        result = aggregator.aggregate()
        
        # Save results
        output_path = aggregator.save(result)
        
        # Log summary
        metadata = result['metadata']
        print(f"\nAggregation complete:")
        print(f"  - Traces processed: {metadata['total_traces_processed']}")
        print(f"  - Rules before filtering: {metadata['total_rules_before_filter']}")
        print(f"  - Rules after filtering: {metadata['total_rules_after_filter']}")
        print(f"  - Output saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Ensure T023 (rule_induction.py) has completed successfully.")
        raise
    except Exception as e:
        print(f"ERROR during aggregation: {e}")
        raise


if __name__ == '__main__':
    main()
