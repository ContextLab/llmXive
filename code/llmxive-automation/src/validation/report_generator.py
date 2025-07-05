"""Generate validation reports for llmXive projects."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict
import logging

from .base import ValidationResult, ValidationCheck
from .file_validators import (
    TechnicalDesignValidator,
    ImplementationPlanValidator,
    CodeValidator,
    PaperValidator,
    ReviewValidator,
    DataValidator
)
from .github_validators import (
    GitHubIssueValidator,
    GitHubLabelValidator,
    ProjectBoardValidator,
    StageConsistencyValidator,
    MilestoneValidator
)

logger = logging.getLogger(__name__)


class ValidationReportGenerator:
    """Generate comprehensive validation reports."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize report generator.
        
        Args:
            output_dir: Directory for report output (default: reports/validation)
        """
        self.output_dir = Path(output_dir or "reports/validation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize validators
        self.file_validators = {
            'technical_design': TechnicalDesignValidator(),
            'implementation_plan': ImplementationPlanValidator(),
            'code': CodeValidator(),
            'paper': PaperValidator(),
            'review': ReviewValidator(),
            'data': DataValidator()
        }
        
        self.github_validators = {
            'issue': GitHubIssueValidator(),
            'labels': GitHubLabelValidator(),
            'board': ProjectBoardValidator(),
            'consistency': StageConsistencyValidator(),
            'milestone': MilestoneValidator()
        }
    
    def validate_project(self, project_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all validations for a project.
        
        Args:
            project_id: Project identifier
            project_data: All project data including files, GitHub state, etc.
            
        Returns:
            Dictionary with all validation results
        """
        results = {
            'project_id': project_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'file_validations': {},
            'github_validations': {},
            'summary': {}
        }
        
        # Run file validations
        stage = project_data.get('stage')
        
        # Validate based on stage
        if stage and stage.value in ['ready', 'in_progress', 'in_review', 'done']:
            # Should have technical design
            results['file_validations']['technical_design'] = \
                self.file_validators['technical_design'].validate(project_id)
        
        if stage and stage.value in ['in_progress', 'in_review', 'done']:
            # Should have implementation plan
            results['file_validations']['implementation_plan'] = \
                self.file_validators['implementation_plan'].validate(project_id)
            
            # Should have code
            results['file_validations']['code'] = \
                self.file_validators['code'].validate(project_id)
        
        if stage and stage.value in ['in_review', 'done']:
            # Should have paper
            context = {'stage': stage.value}
            results['file_validations']['paper'] = \
                self.file_validators['paper'].validate(project_id, context)
        
        # Validate reviews if present
        review_files = project_data.get('review_files', [])
        for review_file in review_files:
            results['file_validations'][f'review_{review_file}'] = \
                self.file_validators['review'].validate(review_file)
        
        # Validate data if present
        if project_data.get('has_data'):
            results['file_validations']['data'] = \
                self.file_validators['data'].validate(project_id)
        
        # Run GitHub validations
        if 'github_issue' in project_data:
            issue_context = {
                'issue': project_data['github_issue'],
                'expected_stage': stage
            }
            results['github_validations']['issue'] = \
                self.github_validators['issue'].validate(str(project_data['github_issue'].number), issue_context)
        
        if 'repository_labels' in project_data:
            label_context = {'labels': project_data['repository_labels']}
            results['github_validations']['labels'] = \
                self.github_validators['labels'].validate(project_data.get('repository', 'unknown'), label_context)
        
        if 'project_board' in project_data:
            board_context = {
                'columns': project_data['project_board']['columns'],
                'cards': project_data['project_board']['cards'],
                'issues': project_data.get('all_issues', [])
            }
            results['github_validations']['board'] = \
                self.github_validators['board'].validate(project_data['project_board']['name'], board_context)
        
        # Check consistency
        if all(k in project_data for k in ['github_issue', 'card_column', 'stage', 'score']):
            consistency_context = {
                'issue': project_data['github_issue'],
                'card_column': project_data['card_column'],
                'stage': stage,
                'score': project_data['score']
            }
            results['github_validations']['consistency'] = \
                self.github_validators['consistency'].validate(project_id, consistency_context)
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from validation results.
        
        Args:
            results: Full validation results
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'errors': 0,
            'warnings': 0,
            'info': 0,
            'by_category': {}
        }
        
        # Process all validation results
        for category in ['file_validations', 'github_validations']:
            category_stats = {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'warnings': 0
            }
            
            for val_type, validation in results[category].items():
                if isinstance(validation, ValidationResult):
                    category_stats['total'] += len(validation.checks)
                    category_stats['passed'] += validation.passed_count
                    category_stats['failed'] += validation.failed_count
                    category_stats['errors'] += len(validation.get_errors())
                    category_stats['warnings'] += len(validation.get_warnings())
                    
                    # Update totals
                    summary['total_checks'] += len(validation.checks)
                    summary['passed_checks'] += validation.passed_count
                    summary['failed_checks'] += validation.failed_count
                    summary['errors'] += len(validation.get_errors())
                    summary['warnings'] += len(validation.get_warnings())
                    summary['info'] += len([c for c in validation.checks if c.severity == 'info'])
            
            summary['by_category'][category] = category_stats
        
        # Calculate percentages
        if summary['total_checks'] > 0:
            summary['pass_rate'] = (summary['passed_checks'] / summary['total_checks']) * 100
        else:
            summary['pass_rate'] = 0
        
        # Determine overall status
        if summary.get('errors', 0) > 0:
            summary['overall_status'] = 'FAILED'
        elif summary['warnings'] > 0:
            summary['overall_status'] = 'PASSED_WITH_WARNINGS'
        else:
            summary['overall_status'] = 'PASSED'
        
        return summary
    
    def generate_markdown_report(self, project_id: str, results: Dict[str, Any]) -> str:
        """Generate a markdown report from validation results.
        
        Args:
            project_id: Project identifier
            results: Validation results
            
        Returns:
            Markdown report content
        """
        report = []
        
        # Header
        report.append(f"# Validation Report: {project_id}")
        report.append(f"\nGenerated: {results['timestamp']}")
        report.append("")
        
        # Summary
        summary = results['summary']
        status_emoji = {
            'PASSED': '✅',
            'PASSED_WITH_WARNINGS': '⚠️',
            'FAILED': '❌'
        }.get(summary['overall_status'], '❓')
        
        report.append(f"## Summary {status_emoji}")
        report.append("")
        report.append(f"**Overall Status**: {summary['overall_status']}")
        if 'pass_rate' in summary:
            report.append(f"**Pass Rate**: {summary['pass_rate']:.1f}%")
        else:
            report.append(f"**Pass Rate**: N/A")
        report.append("")
        report.append("| Metric | Count |")
        report.append("|--------|-------|")
        report.append(f"| Total Checks | {summary.get('total_checks', 0)} |")
        report.append(f"| Passed | {summary.get('passed_checks', 0)} |")
        report.append(f"| Failed | {summary.get('failed_checks', 0)} |")
        report.append(f"| Errors | {summary.get('errors', 0)} |")
        report.append(f"| Warnings | {summary.get('warnings', 0)} |")
        report.append(f"| Info | {summary.get('info', 0)} |")
        report.append("")
        
        # File Validations
        if results['file_validations']:
            report.append("## File Validations")
            report.append("")
            
            for val_type, validation in results['file_validations'].items():
                if isinstance(validation, ValidationResult):
                    report.append(f"### {validation.item_type.replace('_', ' ').title()}: {validation.item_id}")
                    report.append("")
                    report.append(validation.summary())
                    report.append("")
                    
                    # Show failed checks first
                    errors = validation.get_errors()
                    warnings = validation.get_warnings()
                    
                    if errors:
                        report.append("**Errors:**")
                        for check in errors:
                            report.append(f"- {check}")
                        report.append("")
                    
                    if warnings:
                        report.append("**Warnings:**")
                        for check in warnings:
                            report.append(f"- {check}")
                        report.append("")
                    
                    # Show passed checks
                    passed = [c for c in validation.checks if c.passed]
                    if passed and (errors or warnings):  # Only show if there were issues
                        report.append("<details>")
                        report.append("<summary>Passed Checks</summary>")
                        report.append("")
                        for check in passed:
                            report.append(f"- {check}")
                        report.append("")
                        report.append("</details>")
                        report.append("")
        
        # GitHub Validations
        if results['github_validations']:
            report.append("## GitHub Validations")
            report.append("")
            
            for val_type, validation in results['github_validations'].items():
                if isinstance(validation, ValidationResult):
                    report.append(f"### {validation.item_type.replace('_', ' ').title()}")
                    report.append("")
                    report.append(validation.summary())
                    report.append("")
                    
                    # Group checks by severity
                    by_severity = defaultdict(list)
                    for check in validation.checks:
                        if not check.passed:
                            by_severity[check.severity].append(check)
                    
                    for severity in ['error', 'warning', 'info']:
                        if by_severity[severity]:
                            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[severity]
                            report.append(f"**{severity.title()}s {emoji}:**")
                            for check in by_severity[severity]:
                                report.append(f"- {check.message}")
                            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        if summary.get('errors', 0) > 0:
            report.append("### Critical Issues to Address")
            report.append("")
            
            # Collect all errors
            all_errors = []
            for category in ['file_validations', 'github_validations']:
                for validation in results[category].values():
                    if isinstance(validation, ValidationResult):
                        all_errors.extend(validation.get_errors())
            
            # Group similar errors
            error_types = defaultdict(list)
            for error in all_errors:
                error_types[error.name].append(error)
            
            for error_type, errors in error_types.items():
                report.append(f"- **{error_type}**: {errors[0].message}")
                if len(errors) > 1:
                    report.append(f"  (and {len(errors)-1} more)")
            report.append("")
        
        if summary.get('warnings', 0) > 0:
            report.append("### Suggested Improvements")
            report.append("")
            
            # Top 5 warnings
            all_warnings = []
            for category in ['file_validations', 'github_validations']:
                for validation in results[category].values():
                    if isinstance(validation, ValidationResult):
                        all_warnings.extend(validation.get_warnings())
            
            for warning in all_warnings[:5]:
                report.append(f"- {warning.message}")
            
            if len(all_warnings) > 5:
                report.append(f"- ... and {len(all_warnings)-5} more warnings")
            report.append("")
        
        return "\n".join(report)
    
    def generate_json_report(self, project_id: str, results: Dict[str, Any]) -> str:
        """Generate a JSON report from validation results.
        
        Args:
            project_id: Project identifier  
            results: Validation results
            
        Returns:
            JSON report content
        """
        # Convert ValidationResult objects to dictionaries
        json_results = {
            'project_id': project_id,
            'timestamp': results['timestamp'],
            'summary': results['summary'],
            'file_validations': {},
            'github_validations': {}
        }
        
        for category in ['file_validations', 'github_validations']:
            for val_type, validation in results[category].items():
                if isinstance(validation, ValidationResult):
                    json_results[category][val_type] = {
                        'item_type': validation.item_type,
                        'item_id': validation.item_id,
                        'passed': validation.passed,
                        'has_warnings': validation.has_warnings,
                        'passed_count': validation.passed_count,
                        'failed_count': validation.failed_count,
                        'checks': [
                            {
                                'name': check.name,
                                'passed': check.passed,
                                'message': check.message,
                                'severity': check.severity,
                                'details': check.details,
                                'timestamp': check.timestamp.isoformat()
                            }
                            for check in validation.checks
                        ],
                        'metadata': validation.metadata
                    }
        
        return json.dumps(json_results, indent=2)
    
    def save_report(self, project_id: str, results: Dict[str, Any], 
                   formats: List[str] = ['markdown', 'json']) -> Dict[str, Path]:
        """Save validation report to files.
        
        Args:
            project_id: Project identifier
            results: Validation results
            formats: List of formats to save ('markdown', 'json')
            
        Returns:
            Dictionary mapping format to file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        
        if 'markdown' in formats:
            md_content = self.generate_markdown_report(project_id, results)
            md_path = self.output_dir / f"{project_id}_{timestamp}.md"
            md_path.write_text(md_content)
            saved_files['markdown'] = md_path
            logger.info(f"Saved markdown report: {md_path}")
        
        if 'json' in formats:
            json_content = self.generate_json_report(project_id, results)
            json_path = self.output_dir / f"{project_id}_{timestamp}.json"
            json_path.write_text(json_content)
            saved_files['json'] = json_path
            logger.info(f"Saved JSON report: {json_path}")
        
        # Also save latest symlinks
        for fmt, path in saved_files.items():
            latest_link = self.output_dir / f"{project_id}_latest.{path.suffix[1:]}"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(path.name)
        
        return saved_files
    
    def generate_summary_dashboard(self, all_results: List[Dict[str, Any]]) -> str:
        """Generate a dashboard summarizing multiple project validations.
        
        Args:
            all_results: List of validation results for multiple projects
            
        Returns:
            Dashboard markdown content
        """
        dashboard = []
        
        dashboard.append("# llmXive Validation Dashboard")
        dashboard.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
        dashboard.append(f"\nProjects Validated: {len(all_results)}")
        dashboard.append("")
        
        # Overall statistics
        total_checks = sum(r['summary']['total_checks'] for r in all_results)
        total_passed = sum(r['summary']['passed_checks'] for r in all_results)
        total_errors = sum(r['summary']['errors'] for r in all_results)
        total_warnings = sum(r['summary']['warnings'] for r in all_results)
        
        overall_pass_rate = (total_passed / total_checks * 100) if total_checks > 0 else 0
        
        dashboard.append("## Overall Statistics")
        dashboard.append("")
        dashboard.append(f"- **Total Checks**: {total_checks}")
        dashboard.append(f"- **Overall Pass Rate**: {overall_pass_rate:.1f}%")
        dashboard.append(f"- **Total Errors**: {total_errors}")
        dashboard.append(f"- **Total Warnings**: {total_warnings}")
        dashboard.append("")
        
        # Project summary table
        dashboard.append("## Project Summary")
        dashboard.append("")
        dashboard.append("| Project | Status | Pass Rate | Errors | Warnings |")
        dashboard.append("|---------|--------|-----------|---------|----------|")
        
        for result in sorted(all_results, key=lambda r: r['summary']['pass_rate'], reverse=True):
            summary = result['summary']
            status_emoji = {
                'PASSED': '✅',
                'PASSED_WITH_WARNINGS': '⚠️', 
                'FAILED': '❌'
            }.get(summary['overall_status'], '❓')
            
            dashboard.append(
                f"| {result['project_id']} | {status_emoji} {summary['overall_status']} | "
                f"{summary['pass_rate']:.1f}% | {summary['errors']} | {summary['warnings']} |"
            )
        
        dashboard.append("")
        
        # Common issues
        dashboard.append("## Common Issues")
        dashboard.append("")
        
        issue_counts = defaultdict(int)
        for result in all_results:
            for category in ['file_validations', 'github_validations']:
                for validation in result[category].values():
                    if isinstance(validation, dict) and 'checks' in validation:
                        for check in validation['checks']:
                            if not check['passed']:
                                issue_counts[check['name']] += 1
        
        # Top 10 issues
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_issues:
            dashboard.append("| Issue | Count |")
            dashboard.append("|-------|-------|")
            for issue, count in top_issues:
                dashboard.append(f"| {issue} | {count} |")
        else:
            dashboard.append("No common issues found across projects.")
        
        dashboard.append("")
        
        return "\n".join(dashboard)