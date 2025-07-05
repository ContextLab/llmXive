# Pipeline Validation Framework

## Overview

This document defines the validation framework for testing the llmXive pipeline, ensuring all artifacts are created correctly and the scoring system functions properly.

## 1. Artifact Validation System

### 1.1 File Validators

```python
class ArtifactValidator:
    """Base class for validating pipeline artifacts"""
    
    def validate_technical_design(self, project_id: str) -> ValidationResult:
        """Validate technical design document"""
        checks = [
            self.check_file_exists(f"technical_design_documents/{project_id}/design.md"),
            self.check_design_structure(),
            self.check_readme_table_entry("technical_design_documents/README.md", project_id),
            self.check_contributor_list(),
            self.check_github_issue_reference()
        ]
        return ValidationResult(checks)
    
    def validate_implementation_plan(self, project_id: str) -> ValidationResult:
        """Validate implementation plan"""
        checks = [
            self.check_file_exists(f"implementation_plans/{project_id}/plan.md"),
            self.check_plan_structure(),
            self.check_readme_table_entry("implementation_plans/README.md", project_id),
            self.check_milestones(),
            self.check_timeline()
        ]
        return ValidationResult(checks)
    
    def validate_code_artifacts(self, project_id: str) -> ValidationResult:
        """Validate generated code and test files"""
        checks = [
            self.check_code_directory_structure(f"code/{project_id}/"),
            self.check_helpers_package(),
            self.check_test_files(),
            self.check_requirements_file(),
            self.check_readme_with_reproduction()
        ]
        return ValidationResult(checks)
    
    def validate_data_artifacts(self, project_id: str) -> ValidationResult:
        """Validate data files and metadata"""
        checks = [
            self.check_data_files(f"data/{project_id}/"),
            self.check_data_readme(),
            self.check_data_format(),
            self.check_metadata_json()
        ]
        return ValidationResult(checks)
    
    def validate_paper_artifacts(self, project_id: str) -> ValidationResult:
        """Validate paper files"""
        checks = [
            self.check_latex_files(f"papers/{project_id}/"),
            self.check_pdf_exists(),
            self.check_figures_directory(),
            self.check_bibliography(),
            self.check_paper_sections()
        ]
        return ValidationResult(checks)
```

### 1.2 GitHub Artifact Validators

```python
class GitHubValidator:
    """Validate GitHub-specific artifacts"""
    
    def validate_issue_state(self, issue_number: int, expected_state: dict) -> ValidationResult:
        """Validate issue labels, comments, and metadata"""
        issue = self.github.get_issue(issue_number)
        
        checks = [
            self.check_labels(issue, expected_state['labels']),
            self.check_project_column(issue, expected_state['column']),
            self.check_score_label(issue, expected_state['score']),
            self.check_stage_label(issue, expected_state['stage']),
            self.check_assignees(issue, expected_state.get('assignees', []))
        ]
        return ValidationResult(checks)
    
    def validate_comments(self, issue_number: int, expected_comments: list) -> ValidationResult:
        """Validate issue comments"""
        comments = self.github.get_comments(issue_number)
        
        checks = []
        for expected in expected_comments:
            checks.append(self.check_comment_exists(comments, expected))
            checks.append(self.check_comment_author(comments, expected))
            checks.append(self.check_comment_content(comments, expected))
        
        return ValidationResult(checks)
    
    def validate_project_board(self, project_id: int) -> ValidationResult:
        """Validate project board state"""
        board = self.github.get_project_board(project_id)
        
        checks = [
            self.check_column_cards('Backlog', board),
            self.check_column_cards('Ready', board),
            self.check_column_cards('In Progress', board),
            self.check_column_cards('Done', board)
        ]
        return ValidationResult(checks)
```

## 2. Score System Validation

### 2.1 Score Calculator

```python
class ScoreSystem:
    """Manages and validates the review scoring system"""
    
    # Score values
    LLM_POSITIVE = 0.5
    LLM_NEGATIVE = -0.5
    HUMAN_POSITIVE = 1.0
    HUMAN_NEGATIVE = -1.0
    CRITICAL_RESET = 0
    ADVANCEMENT_THRESHOLD = 5.0
    
    def calculate_score(self, reviews: List[Review]) -> float:
        """Calculate total score from reviews"""
        score = 0.0
        
        for review in reviews:
            if review.is_critical:
                # Critical review resets score to 0
                score = self.CRITICAL_RESET
            else:
                # Add/subtract based on review type
                if review.is_positive:
                    score += self.HUMAN_POSITIVE if review.is_human else self.LLM_POSITIVE
                else:
                    score += self.HUMAN_NEGATIVE if review.is_human else self.LLM_NEGATIVE
                
                # Score cannot go below 0
                score = max(0.0, score)
        
        return score
    
    def should_advance(self, score: float) -> bool:
        """Check if score meets advancement threshold"""
        return score >= self.ADVANCEMENT_THRESHOLD
```

### 2.2 Score Validation Tests

```python
class ScoreValidationTests:
    """Test cases for score system validation"""
    
    def test_score_scenarios(self):
        """Test various scoring scenarios"""
        
        scenarios = [
            {
                'name': 'Basic advancement',
                'reviews': [
                    Review(is_positive=True, is_human=False),  # +0.5
                    Review(is_positive=True, is_human=False),  # +0.5
                    Review(is_positive=True, is_human=True),   # +1.0
                    Review(is_positive=True, is_human=True),   # +1.0
                    Review(is_positive=True, is_human=True),   # +1.0
                    Review(is_positive=True, is_human=True),   # +1.0
                ],
                'expected_score': 5.0,
                'should_advance': True
            },
            {
                'name': 'Mixed reviews',
                'reviews': [
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=False, is_human=False),  # -0.5
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=True, is_human=False),   # +0.5
                ],
                'expected_score': 4.0,
                'should_advance': False
            },
            {
                'name': 'Critical reset',
                'reviews': [
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_positive=True, is_human=True),    # +1.0
                    Review(is_critical=True),                   # Reset to 0
                    Review(is_positive=True, is_human=True),    # +1.0
                ],
                'expected_score': 1.0,
                'should_advance': False
            },
            {
                'name': 'Score floor at zero',
                'reviews': [
                    Review(is_positive=False, is_human=True),   # -1.0 -> 0
                    Review(is_positive=False, is_human=True),   # -1.0 -> 0
                    Review(is_positive=True, is_human=False),   # +0.5
                ],
                'expected_score': 0.5,
                'should_advance': False
            }
        ]
        
        return self.run_scenarios(scenarios)
```

### 2.3 Label Management

```python
class ScoreLabelManager:
    """Manages score-related GitHub labels"""
    
    def update_score_label(self, issue_number: int, score: float):
        """Update issue with current score label"""
        # Remove old score labels
        old_labels = self.get_score_labels(issue_number)
        for label in old_labels:
            self.remove_label(issue_number, label)
        
        # Add new score label
        score_label = f"score: {score}"
        self.add_label(issue_number, score_label)
        
        # Check for advancement
        if score >= 5.0:
            self.add_label(issue_number, "ready-to-advance")
    
    def validate_score_label(self, issue_number: int, expected_score: float) -> bool:
        """Validate that issue has correct score label"""
        labels = self.get_labels(issue_number)
        expected_label = f"score: {expected_score}"
        
        # Check score label exists
        score_labels = [l for l in labels if l.startswith("score:")]
        if len(score_labels) != 1:
            return False
        
        # Check score value
        return score_labels[0] == expected_label
```

## 3. Stage Transition Validation

### 3.1 Transition Rules

```python
class StageTransitionValidator:
    """Validates stage transitions follow rules"""
    
    TRANSITIONS = {
        'Backlog': {
            'next': 'Ready',
            'requirements': ['technical_design', 'score >= 5']
        },
        'Ready': {
            'next': 'In Progress',
            'requirements': ['implementation_plan', 'score >= 5']
        },
        'In Progress': {
            'next': 'Done',
            'requirements': ['paper_pdf', 'code_complete', 'score >= 5']
        },
        'Done': {
            'next': None,
            'requirements': []
        }
    }
    
    def validate_transition(self, from_stage: str, to_stage: str, 
                          project_state: dict) -> ValidationResult:
        """Validate a stage transition"""
        expected = self.TRANSITIONS[from_stage]
        
        # Check correct next stage
        if to_stage != expected['next']:
            return ValidationResult(False, f"Invalid transition: {from_stage} -> {to_stage}")
        
        # Check requirements
        checks = []
        for req in expected['requirements']:
            if req == 'score >= 5':
                checks.append(self.check_score(project_state))
            elif req == 'technical_design':
                checks.append(self.check_technical_design(project_state))
            elif req == 'implementation_plan':
                checks.append(self.check_implementation_plan(project_state))
            elif req == 'paper_pdf':
                checks.append(self.check_paper_pdf(project_state))
            elif req == 'code_complete':
                checks.append(self.check_code_complete(project_state))
        
        return ValidationResult(checks)
```

## 4. Integration Test Framework

### 4.1 Pipeline Step Validator

```python
class PipelineStepValidator:
    """Validates each step in the pipeline test"""
    
    def __init__(self):
        self.artifact_validator = ArtifactValidator()
        self.github_validator = GitHubValidator()
        self.score_validator = ScoreSystem()
        self.transition_validator = StageTransitionValidator()
    
    def validate_step(self, step_number: int, step_config: dict, 
                     project_state: dict) -> StepValidationResult:
        """Validate a single pipeline step"""
        
        validations = []
        
        # Validate artifacts created
        if 'creates_files' in step_config:
            for file_path in step_config['creates_files']:
                validations.append(self.artifact_validator.check_file_exists(file_path))
        
        # Validate GitHub state
        if 'github_state' in step_config:
            validations.append(
                self.github_validator.validate_issue_state(
                    project_state['issue_number'],
                    step_config['github_state']
                )
            )
        
        # Validate score
        if 'expected_score' in step_config:
            current_score = self.score_validator.calculate_score(project_state['reviews'])
            validations.append(
                current_score == step_config['expected_score'],
                f"Score mismatch: expected {step_config['expected_score']}, got {current_score}"
            )
        
        # Validate stage transition
        if 'transitions_to' in step_config:
            validations.append(
                self.transition_validator.validate_transition(
                    project_state['current_stage'],
                    step_config['transitions_to'],
                    project_state
                )
            )
        
        return StepValidationResult(step_number, validations)
```

### 4.2 Full Pipeline Test Configuration

```yaml
pipeline_test:
  project_id: "test-2025-001"
  steps:
    - number: 1
      action: "create_idea"
      creates_files: []
      github_state:
        labels: ["idea", "stage: backlog"]
        column: "Backlog"
        score: 0
    
    - number: 5
      action: "create_technical_design"
      creates_files:
        - "technical_design_documents/test-2025-001/design.md"
      github_state:
        labels: ["idea", "stage: backlog", "has-technical-design"]
        column: "Backlog"
        score: 0
    
    - number: 8
      action: "add_positive_review_llm"
      expected_score: 0.5
      github_state:
        labels: ["idea", "stage: backlog", "has-technical-design", "score: 0.5"]
    
    - number: 9
      action: "add_critical_review"
      expected_score: 0  # Reset due to critical
      github_state:
        labels: ["idea", "stage: backlog", "has-technical-design", "score: 0", "needs-revision"]
    
    - number: 11
      action: "add_multiple_positive_reviews"
      reviews_added: 10  # Mix of LLM and human
      expected_score: 5.5
      transitions_to: "Ready"
      github_state:
        labels: ["idea", "stage: ready", "has-technical-design", "score: 5.5", "ready-to-advance"]
        column: "Ready"
```

## 5. Validation Report Generation

```python
class ValidationReporter:
    """Generates comprehensive validation reports"""
    
    def generate_report(self, test_results: List[StepValidationResult]) -> str:
        """Generate markdown report of test results"""
        
        report = ["# Pipeline Validation Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        
        # Summary
        total_steps = len(test_results)
        passed_steps = sum(1 for r in test_results if r.passed)
        report.append(f"## Summary\n")
        report.append(f"- Total Steps: {total_steps}\n")
        report.append(f"- Passed: {passed_steps}\n")
        report.append(f"- Failed: {total_steps - passed_steps}\n")
        
        # Detailed results
        report.append("\n## Detailed Results\n")
        for result in test_results:
            status = "✅" if result.passed else "❌"
            report.append(f"\n### Step {result.step_number}: {status}\n")
            
            for check in result.checks:
                check_status = "✓" if check.passed else "✗"
                report.append(f"- {check_status} {check.description}\n")
                if not check.passed:
                    report.append(f"  - Error: {check.error_message}\n")
        
        # Score progression
        report.append("\n## Score Progression\n")
        report.append(self.generate_score_chart(test_results))
        
        return "".join(report)
```

## 6. Implementation Priority

1. **Phase 1**: Implement score system validation (Critical)
2. **Phase 2**: Implement artifact validators
3. **Phase 3**: Implement GitHub state validators
4. **Phase 4**: Implement transition validators
5. **Phase 5**: Create comprehensive test scenarios
6. **Phase 6**: Generate validation reports

This validation framework ensures every aspect of the pipeline is tested and verified, with particular attention to the complex scoring system that drives project advancement.