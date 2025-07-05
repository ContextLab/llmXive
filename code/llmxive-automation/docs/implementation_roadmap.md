# Implementation Roadmap: Full Pipeline Test with Validation

## Executive Summary

This roadmap outlines the step-by-step implementation of a comprehensive pipeline test system that includes both execution and validation of every artifact and state change, with special focus on the scoring system.

## Phase 1: Mock Model Infrastructure (Days 1-2)

### 1.1 Create Mock Model System
```python
# File: src/testing/mock_model_manager.py
class MockModelManager:
    """Replaces ModelManager for deterministic testing"""
    
    def __init__(self, scenario_path: str):
        self.scenario = self.load_scenario(scenario_path)
        self.models = self.create_mock_models()
        self.response_history = []
    
    def get_model(self, model_id: str = None):
        """Return a mock model with scripted responses"""
        if model_id:
            return self.models.get(model_id, self.models['default'])
        return self.select_model_by_scenario()
```

### 1.2 Create Response Templates
```yaml
# File: tests/scenarios/full_pipeline_test.yaml
scenario:
  name: "Full Pipeline Test"
  models:
    - id: "enthusiastic_reviewer"
      responses:
        REVIEW_TECHNICAL_DESIGN:
          positive: |
            This technical design shows excellent promise! The approach is well-thought-out
            and addresses the core challenges effectively. Score: APPROVE (+0.5)
        
    - id: "critical_reviewer"
      responses:
        REVIEW_TECHNICAL_DESIGN:
          critical: |
            CRITICAL ISSUE: The design lacks consideration for edge cases in data validation.
            This could lead to incorrect results. Score: CRITICAL (RESET TO 0)
```

### 1.3 Implement Scenario Controller
```python
# File: src/testing/scenario_controller.py
class ScenarioController:
    """Controls test scenario execution"""
    
    def __init__(self, scenario_config: dict):
        self.config = scenario_config
        self.current_step = 0
        self.checkpoints = {}
    
    def get_next_response(self, task_type: str, context: dict) -> dict:
        """Get the next scripted response based on scenario"""
        step = self.config['steps'][self.current_step]
        response = self.generate_response(step, task_type, context)
        self.current_step += 1
        return response
```

## Phase 2: Scoring System Implementation (Days 3-4)

### 2.1 Implement Score Tracker
```python
# File: src/scoring/score_tracker.py
class ScoreTracker:
    """Tracks and validates project scores"""
    
    def __init__(self, github_handler):
        self.github = github_handler
        self.score_history = []
    
    def process_review(self, issue_number: int, review: Review) -> float:
        """Process a review and update score"""
        current_score = self.get_current_score(issue_number)
        
        if review.is_critical:
            new_score = 0.0
            self.add_label(issue_number, "critical-issue-identified")
        else:
            delta = self.calculate_delta(review)
            new_score = max(0.0, current_score + delta)
        
        self.update_score_label(issue_number, new_score)
        self.score_history.append({
            'timestamp': datetime.now(),
            'issue': issue_number,
            'old_score': current_score,
            'new_score': new_score,
            'review': review
        })
        
        return new_score
```

### 2.2 Create Score Validation Tests
```python
# File: tests/test_scoring_system.py
class TestScoringSystem:
    """Comprehensive tests for scoring system"""
    
    def test_llm_positive_review(self):
        """Test LLM positive review adds 0.5"""
        tracker = ScoreTracker(mock_github)
        review = Review(is_positive=True, is_human=False, author="llm-1")
        
        new_score = tracker.process_review(1, review)
        assert new_score == 0.5
        assert mock_github.has_label(1, "score: 0.5")
    
    def test_critical_review_reset(self):
        """Test critical review resets score to 0"""
        tracker = ScoreTracker(mock_github)
        
        # Build up score
        tracker.process_review(1, Review(is_positive=True, is_human=True))  # +1.0
        tracker.process_review(1, Review(is_positive=True, is_human=True))  # +1.0
        assert tracker.get_current_score(1) == 2.0
        
        # Critical review
        tracker.process_review(1, Review(is_critical=True))
        assert tracker.get_current_score(1) == 0.0
        assert mock_github.has_label(1, "critical-issue-identified")
```

## Phase 3: Artifact Validation System (Days 5-6)

### 3.1 Implement File Validators
```python
# File: src/validation/artifact_validators.py
class FileSystemValidator:
    """Validates file system artifacts"""
    
    def validate_technical_design(self, project_id: str) -> ValidationResult:
        """Comprehensive validation of technical design artifacts"""
        
        validations = []
        
        # Check main design file
        design_path = f"technical_design_documents/{project_id}/design.md"
        validations.append(self.check_file_exists(design_path))
        validations.append(self.check_markdown_structure(design_path, [
            "# Technical Design",
            "## Problem Statement",
            "## Proposed Solution",
            "## Implementation Details",
            "## Validation Strategy"
        ]))
        
        # Check README table update
        readme_path = "technical_design_documents/README.md"
        validations.append(self.check_table_entry(readme_path, project_id))
        
        return ValidationResult("technical_design", validations)
```

### 3.2 Implement GitHub Validators
```python
# File: src/validation/github_validators.py
class GitHubStateValidator:
    """Validates GitHub state (issues, labels, project board)"""
    
    def validate_issue_labels(self, issue_number: int, 
                            expected_labels: List[str]) -> ValidationResult:
        """Validate issue has expected labels"""
        
        actual_labels = self.github.get_labels(issue_number)
        
        validations = []
        for expected in expected_labels:
            validations.append(
                ValidationCheck(
                    name=f"has_label_{expected}",
                    passed=expected in actual_labels,
                    message=f"Expected label '{expected}'"
                )
            )
        
        # Check no unexpected labels
        unexpected = set(actual_labels) - set(expected_labels)
        validations.append(
            ValidationCheck(
                name="no_unexpected_labels",
                passed=len(unexpected) == 0,
                message=f"Unexpected labels: {unexpected}"
            )
        )
        
        return ValidationResult("issue_labels", validations)
```

## Phase 4: Pipeline Test Orchestrator (Days 7-8)

### 4.1 Create Test Orchestrator
```python
# File: src/testing/pipeline_test_orchestrator.py
class PipelineTestOrchestrator:
    """Orchestrates full pipeline test execution"""
    
    def __init__(self, scenario_path: str, validation_level: str = "full"):
        self.scenario = load_scenario(scenario_path)
        self.mock_models = MockModelManager(scenario_path)
        self.validators = self.init_validators()
        self.test_results = []
    
    def run_pipeline_test(self) -> TestReport:
        """Execute full pipeline test"""
        
        project_state = self.initialize_project()
        
        for step in self.scenario['steps']:
            print(f"\n=== Executing Step {step['number']}: {step['description']} ===")
            
            # Execute step
            result = self.execute_step(step, project_state)
            
            # Validate results
            validation = self.validate_step(step, project_state)
            
            # Record results
            self.test_results.append({
                'step': step,
                'execution_result': result,
                'validation_result': validation,
                'project_state': copy.deepcopy(project_state)
            })
            
            # Check if we should continue
            if validation.has_critical_failures():
                print(f"CRITICAL FAILURE at step {step['number']}")
                break
            
            # Update project state
            project_state = self.update_project_state(project_state, result)
        
        return self.generate_test_report()
```

### 4.2 Create Step Definitions
```python
# File: tests/scenarios/steps/full_pipeline_steps.py
PIPELINE_STEPS = [
    {
        'number': 1,
        'description': 'Generate project idea',
        'action': 'BRAINSTORM',
        'validates': {
            'creates_issue': True,
            'adds_labels': ['idea', 'stage: backlog'],
            'score': 0
        }
    },
    {
        'number': 8,
        'description': 'First positive review (LLM)',
        'action': 'REVIEW_TECHNICAL_DESIGN',
        'model': 'enthusiastic_reviewer',
        'validates': {
            'score': 0.5,
            'adds_labels': ['score: 0.5'],
            'creates_comment': True
        }
    },
    {
        'number': 9,
        'description': 'Critical review identifies issue',
        'action': 'REVIEW_TECHNICAL_DESIGN', 
        'model': 'critical_reviewer',
        'validates': {
            'score': 0,  # Reset!
            'adds_labels': ['score: 0', 'critical-issue-identified'],
            'removes_labels': ['score: 0.5'],
            'stage_remains': 'backlog'
        }
    },
    # ... more steps
]
```

## Phase 5: Execution Environment (Days 9-10)

### 5.1 Create Sandboxed Executor
```python
# File: src/execution/sandbox_executor.py
class SandboxExecutor:
    """Executes code in sandboxed environment"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.docker_client = docker.from_env()
    
    def execute_code(self, code: str, language: str = 'python') -> ExecutionResult:
        """Execute code in Docker container"""
        
        container = self.create_container(language)
        try:
            # Copy code to container
            self.copy_code_to_container(container, code)
            
            # Execute with timeout
            result = container.exec_run(
                cmd=self.get_execution_command(language),
                timeout=self.timeout
            )
            
            return ExecutionResult(
                stdout=result.output.decode('utf-8'),
                stderr=result.stderr.decode('utf-8') if result.stderr else '',
                exit_code=result.exit_code,
                timed_out=False
            )
        finally:
            container.remove(force=True)
```

### 5.2 Add Real Execution Tasks
```python
# File: src/task_executor_enhanced.py
class EnhancedTaskExecutor(TaskExecutor):
    """Enhanced executor with real code execution"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sandbox = SandboxExecutor()
    
    def execute_run_code(self, context: dict) -> dict:
        """Actually run generated code"""
        
        code_file = context['code_file']
        code_content = self.github.get_file_content(code_file)
        
        # Execute in sandbox
        result = self.sandbox.execute_code(code_content)
        
        # Save outputs
        output_file = code_file.replace('.py', '_output.txt')
        self.github.create_file(
            output_file,
            f"# Execution Output\n\n```\n{result.stdout}\n```\n"
        )
        
        return {
            'success': result.exit_code == 0,
            'output_file': output_file,
            'execution_time': result.execution_time
        }
```

## Phase 6: Integration Testing (Days 11-12)

### 6.1 Create End-to-End Test
```python
# File: tests/test_full_pipeline.py
class TestFullPipeline:
    """End-to-end pipeline test"""
    
    def test_complete_pipeline(self, tmp_repo):
        """Test complete pipeline from idea to publication"""
        
        # Initialize test environment
        orchestrator = PipelineTestOrchestrator(
            scenario_path="tests/scenarios/full_pipeline_test.yaml",
            validation_level="full"
        )
        
        # Run pipeline
        report = orchestrator.run_pipeline_test()
        
        # Verify all steps passed
        assert report.all_steps_passed()
        
        # Verify final state
        final_state = report.final_project_state()
        assert final_state['stage'] == 'Done'
        assert final_state['score'] >= 5.0
        assert final_state['has_paper_pdf'] == True
        assert final_state['has_all_artifacts'] == True
        
        # Verify web interface would show completed project
        assert orchestrator.validate_web_interface_state()
```

### 6.2 Create Validation Report Generator
```python
# File: src/reporting/validation_reporter.py
class ValidationReporter:
    """Generates detailed validation reports"""
    
    def generate_html_report(self, test_results: TestResults) -> str:
        """Generate interactive HTML report"""
        
        template = """
        <html>
        <head>
            <title>Pipeline Test Report</title>
            <style>
                .passed { color: green; }
                .failed { color: red; }
                .score-chart { width: 100%; height: 300px; }
            </style>
        </head>
        <body>
            <h1>Pipeline Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Steps: {total_steps}</p>
                <p>Passed: <span class="passed">{passed_steps}</span></p>
                <p>Failed: <span class="failed">{failed_steps}</span></p>
            </div>
            
            <div class="score-progression">
                <h2>Score Progression</h2>
                <canvas id="scoreChart" class="score-chart"></canvas>
            </div>
            
            <div class="detailed-results">
                <h2>Detailed Results</h2>
                {detailed_results_html}
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                {chart_javascript}
            </script>
        </body>
        </html>
        """
        
        return self.render_template(template, test_results)
```

## Implementation Schedule

### Week 1
- **Days 1-2**: Mock Model Infrastructure
- **Days 3-4**: Scoring System Implementation
- **Days 5-6**: Artifact Validation System

### Week 2  
- **Days 7-8**: Pipeline Test Orchestrator
- **Days 9-10**: Execution Environment
- **Days 11-12**: Integration Testing

### Week 3
- **Days 13-14**: History Tracking System
  - Implement ProjectHistoryTracker
  - Create markdown/JSON formatters
  - Integrate with task executor
  - Add paper history section generator
- **Days 15-16**: Bug fixes, documentation, and final testing

## Success Metrics

1. **Complete Pipeline Execution**: All 38 steps execute successfully
2. **Accurate Scoring**: Score calculations match expected values at each step
3. **Artifact Validation**: All required files/artifacts created correctly
4. **State Transitions**: Projects move through stages according to rules
5. **Error Recovery**: System handles and recovers from failures gracefully
6. **Performance**: Full test completes in under 30 minutes
7. **History Tracking**: Complete audit trail with timestamps, authors, and artifacts
8. **Paper History Section**: Auto-generated history section with links to all artifacts

## Next Steps

1. Review this implementation roadmap
2. Prioritize which components to build first
3. Set up development environment
4. Begin Phase 1 implementation

Would you like to proceed with this implementation plan, or would you prefer to start with a specific component first?