#!/usr/bin/env python
"""Demonstrate the validation system for llmXive projects."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from validation import (
    TechnicalDesignValidator,
    CodeValidator,
    GitHubIssue,
    GitHubIssueValidator,
    StageConsistencyValidator,
    ValidationReportGenerator
)
from scoring.stage_manager import ProjectStage


def print_validation_result(result):
    """Pretty print a validation result."""
    print(f"\n🔍 {result.summary()}")
    
    # Show errors first
    errors = result.get_errors()
    if errors:
        print("\n❌ Errors:")
        for error in errors:
            print(f"   - {error.message}")
    
    # Show warnings
    warnings = result.get_warnings()
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning.message}")
    
    # Summary of passed checks
    passed = [c for c in result.checks if c.passed]
    if passed:
        print(f"\n✅ Passed {len(passed)} checks")


def demo_file_validation():
    """Demonstrate file validation."""
    print("=== File Validation Demo ===")
    
    # Technical Design Validation
    print("\n1. Technical Design Validation")
    design_validator = TechnicalDesignValidator()
    
    # Simulate validation (would check actual files)
    result = design_validator.validate("example-project-123")
    print_validation_result(result)
    
    # Code Validation
    print("\n2. Code Validation")
    code_validator = CodeValidator()
    
    result = code_validator.validate("example-project-123")
    print_validation_result(result)


def demo_github_validation():
    """Demonstrate GitHub validation."""
    print("\n\n=== GitHub Validation Demo ===")
    
    # Create sample issue
    issue = GitHubIssue(
        number=456,
        title="Implement quantum entanglement detection algorithm",
        state="open",
        labels=["in-progress", "enhancement"],
        body="This issue tracks the implementation of a novel quantum entanglement detection algorithm..." * 5,
        assignees=["alice", "bob"],
        created_at=datetime.now()
    )
    
    # Validate issue
    print("\n1. Issue Validation")
    issue_validator = GitHubIssueValidator()
    result = issue_validator.validate("456", {
        'issue': issue,
        'expected_stage': ProjectStage.IN_PROGRESS
    })
    print_validation_result(result)
    
    # Stage consistency validation
    print("\n2. Stage Consistency Validation")
    consistency_validator = StageConsistencyValidator()
    result = consistency_validator.validate("example-project-123", {
        'issue': issue,
        'card_column': "In Progress",
        'stage': ProjectStage.IN_PROGRESS,
        'score': 3.5
    })
    print_validation_result(result)


def demo_full_project_validation():
    """Demonstrate full project validation with report generation."""
    print("\n\n=== Full Project Validation Demo ===")
    
    # Create report generator
    generator = ValidationReportGenerator()
    
    # Mock project data
    issue = GitHubIssue(
        number=789,
        title="ML model for protein folding prediction",
        state="open",
        labels=["in-review", "research"],
        body="Developing a machine learning model for accurate protein folding prediction..." * 10,
        assignees=["researcher1", "researcher2"]
    )
    
    project_data = {
        'stage': ProjectStage.IN_REVIEW,
        'github_issue': issue,
        'repository_labels': [
            "backlog", "ready", "in-progress", "in-review", "done",
            "needs-review", "critical-review", "research"
        ],
        'project_board': {
            'name': "Research Projects",
            'columns': ["Backlog", "Ready", "In Progress", "In Review", "Done"],
            'cards': []
        },
        'card_column': "In Review",
        'score': 4.5,
        'has_data': True,
        'review_files': [
            "project-789/Design/alice__01-15-2025__M.md",
            "project-789/Implementation/bob__01-18-2025__A.md"
        ]
    }
    
    # Run validation
    print("\nRunning comprehensive validation...")
    results = generator.validate_project("project-789", project_data)
    
    # Print summary
    summary = results['summary']
    status_emoji = {
        'PASSED': '✅',
        'PASSED_WITH_WARNINGS': '⚠️',
        'FAILED': '❌'
    }.get(summary['overall_status'], '❓')
    
    print(f"\n{status_emoji} Overall Status: {summary['overall_status']}")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Errors: {summary['errors']}, Warnings: {summary['warnings']}")
    
    # Save reports
    print("\nSaving validation reports...")
    saved_files = generator.save_report("project-789", results)
    
    for format_type, path in saved_files.items():
        print(f"💾 Saved {format_type} report: {path}")
    
    # Show snippet of markdown report
    print("\n📝 Markdown Report Preview:")
    md_content = generator.generate_markdown_report("project-789", results)
    lines = md_content.split('\n')[:20]
    for line in lines:
        print(f"   {line}")
    print("   ...")


def demo_dashboard():
    """Demonstrate validation dashboard for multiple projects."""
    print("\n\n=== Validation Dashboard Demo ===")
    
    generator = ValidationReportGenerator()
    
    # Simulate results for multiple projects
    all_results = []
    
    projects = [
        ("quantum-ml-001", "PASSED", 95.0, 0, 2),
        ("protein-fold-002", "PASSED_WITH_WARNINGS", 85.0, 0, 5),
        ("climate-sim-003", "FAILED", 65.0, 3, 8),
        ("drug-discovery-004", "PASSED", 100.0, 0, 0),
        ("neural-arch-005", "PASSED_WITH_WARNINGS", 78.0, 0, 6)
    ]
    
    for proj_id, status, pass_rate, errors, warnings in projects:
        all_results.append({
            'project_id': proj_id,
            'summary': {
                'overall_status': status,
                'pass_rate': pass_rate,
                'total_checks': 50,
                'passed_checks': int(50 * pass_rate / 100),
                'errors': errors,
                'warnings': warnings
            },
            'file_validations': {},
            'github_validations': {}
        })
    
    # Generate dashboard
    dashboard = generator.generate_summary_dashboard(all_results)
    
    print("\n📋 Dashboard Preview:")
    lines = dashboard.split('\n')
    for line in lines:
        print(f"   {line}")
    
    # Save dashboard
    dashboard_path = generator.output_dir / "validation_dashboard.md"
    dashboard_path.write_text(dashboard)
    print(f"\n💾 Saved dashboard: {dashboard_path}")


def main():
    """Run all validation demos."""
    print("=== llmXive Validation System Demo ===")
    print("\nThis demo shows the validation system checking:")
    print("- File artifacts (technical designs, code, papers)")
    print("- GitHub state (issues, labels, project boards)")
    print("- Consistency between different components")
    print("- Comprehensive reporting and dashboards")
    
    # Run demos
    demo_file_validation()
    demo_github_validation()
    demo_full_project_validation()
    demo_dashboard()
    
    print("\n\n=== Demo Complete ===")
    print("\nThe validation system provides:")
    print("- Comprehensive checks for all artifact types")
    print("- GitHub integration validation")
    print("- Stage consistency verification")
    print("- Detailed reports in markdown and JSON")
    print("- Summary dashboards for multiple projects")
    print("- Clear error/warning categorization")
    print("- Actionable recommendations")


if __name__ == '__main__':
    main()