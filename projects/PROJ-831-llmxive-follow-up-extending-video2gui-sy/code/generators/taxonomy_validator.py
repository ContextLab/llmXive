"""
Taxonomy Validator: Maps generated tasks to taxonomy rules and produces validation reports.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class TaxonomyValidator:
    """Validates that generated benchmark tasks map correctly to taxonomy rules."""

    def __init__(self, taxonomy_rules: List[Any]):
        self.rules = taxonomy_rules
        self.rule_map = {r.rule_id: r for r in rules}

    def validate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single task against the taxonomy.
        Returns validation details including rule mappings.
        """
        validation = {
            'task_id': task.get('id', ''),
            'is_valid': True,
            'error_rules_applied': [],
            'recovery_paths_valid': True,
            'missing_rules': [],
            'issues': []
        }

        # Check if task has error injection
        if 'error_injection' in task:
            error_info = task['error_injection']
            rule_id = error_info.get('rule_id')

            if rule_id:
                if rule_id in self.rule_map:
                    validation['error_rules_applied'].append(rule_id)
                    # Verify recovery path exists
                    if 'recovery_path' not in task or not task['recovery_path']:
                        validation['recovery_paths_valid'] = False
                        validation['issues'].append(f"Task {task['id']} has error but no recovery path")
                else:
                    validation['is_valid'] = False
                    validation['missing_rules'].append(rule_id)
                    validation['issues'].append(f"Rule {rule_id} not found in taxonomy")
            else:
                validation['is_valid'] = False
                validation['issues'].append("Error injection missing rule_id")

        return validation

    def validate_dataset(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate an entire dataset and produce a validation report.
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_tasks': len(tasks),
            'valid_tasks': 0,
            'invalid_tasks': 0,
            'rule_coverage': {},
            'issues': [],
            'details': []
        }

        for task in tasks:
            validation = self.validate_task(task)
            report['details'].append(validation)

            if validation['is_valid']:
                report['valid_tasks'] += 1
            else:
                report['invalid_tasks'] += 1
                report['issues'].extend(validation['issues'])

            # Track rule coverage
            for rule_id in validation['error_rules_applied']:
                report['rule_coverage'][rule_id] = report['rule_coverage'].get(rule_id, 0) + 1

        report['coverage_rate'] = (
            len(report['rule_coverage']) / len(self.rules)
            if self.rules else 0.0
        )

        return report

    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save the validation report to a JSON file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
