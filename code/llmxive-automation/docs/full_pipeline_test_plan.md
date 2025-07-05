# Full Pipeline Test Implementation Plan

## Overview

This document outlines the implementation plan for testing the complete llmXive project pipeline from ideation to publication. The test will simulate the entire scientific discovery workflow using controllable "dummy" models.

## Goals

1. Validate the complete pipeline from project creation to publication
2. Test all project state transitions and review mechanisms
3. Ensure proper GitHub integration and web interface updates
4. Identify and fix gaps in the automation system
5. Create a repeatable test framework for future development

## Architecture Overview

### 1. Mock Model System

**Purpose**: Create deterministic, controllable model responses for testing

**Components**:
- `MockModelManager`: Replaces `ModelManager` for testing
- `ScriptedResponses`: Pre-defined responses for each task type
- `ReviewScenarios`: Configurable review outcomes (approval, rejection, revision requests)
- `ModelPersonalities`: Different mock models with distinct behaviors

**Implementation**:
```python
class MockModelManager:
    def __init__(self, scenario_file: str):
        self.scenario = load_scenario(scenario_file)
        self.current_step = 0
    
    def get_response(self, task_type: str, context: dict) -> str:
        return self.scenario.get_response(task_type, self.current_step, context)
```

### 2. Enhanced Task Executor

**New Capabilities**:
- Code execution in sandboxed environment
- Real data generation and analysis
- Figure generation and validation
- LaTeX compilation to PDF
- Reference validation

**New Task Types**:
```python
EXECUTE_CODE = "execute_code"          # Run generated code
VALIDATE_RESULTS = "validate_results"  # Check analysis outputs
GENERATE_FIGURES = "generate_figures"  # Create actual plots
COMPILE_LATEX = "compile_latex"        # Generate PDF
VALIDATE_REFERENCES = "validate_refs"  # Check citations
```

### 3. Pipeline Test Orchestrator

**Purpose**: Coordinate the full pipeline test with proper sequencing

**Features**:
- Step-by-step execution with checkpoints
- State validation after each step
- Error recovery and retry logic
- Progress tracking and reporting

## Detailed Implementation Steps

### Phase 1: Infrastructure Setup (Days 1-3)

1. **Create Mock Model System**
   - Implement `MockModelManager` class
   - Create response templates for all task types
   - Build scenario configuration system
   - Add model personality variations

2. **Enhance Execution Environment**
   - Set up Docker container for code execution
   - Create sandbox Python environment
   - Implement execution timeout and resource limits
   - Add output capture and parsing

3. **Build Test Harness**
   - Create `PipelineTestRunner` class
   - Implement checkpoint/resume functionality
   - Add detailed logging and debugging
   - Create test scenario configurations

### Phase 2: Task Implementation (Days 4-7)

1. **Code Execution Tasks**
   ```python
   def execute_code_task(self, context: dict) -> dict:
       # Extract code from context
       # Create temporary execution environment
       # Run code with timeout
       # Capture outputs and errors
       # Parse results
       # Return structured output
   ```

2. **Data Analysis Pipeline**
   ```python
   def analyze_data_task(self, context: dict) -> dict:
       # Generate synthetic data
       # Run statistical analysis
       # Extract key metrics
       # Format results for paper
   ```

3. **Figure Generation**
   ```python
   def generate_figures_task(self, context: dict) -> dict:
       # Execute plotting code
       # Save figures to appropriate locations
       # Validate figure quality
       # Generate captions
   ```

4. **Document Compilation**
   ```python
   def compile_latex_task(self, context: dict) -> dict:
       # Gather all paper components
       # Run LaTeX compiler
       # Handle compilation errors
       # Validate PDF output
   ```

### Phase 3: Test Scenario Implementation (Days 8-10)

1. **Create Test Project: "Synthetic Data Pattern Analysis"**
   - Simple enough to complete quickly
   - Complex enough to exercise all pipeline stages
   - Generates real data and figures
   - Produces meaningful results

2. **Define Model Behaviors**
   ```yaml
   models:
     - name: "critical_reviewer"
       behavior: "finds issues in first iteration"
       approval_threshold: 0.8
     
     - name: "supportive_reviewer"
       behavior: "generally approves with minor suggestions"
       approval_threshold: 0.3
     
     - name: "domain_expert"
       behavior: "focuses on technical accuracy"
       approval_threshold: 0.6
   ```

3. **Script Full Pipeline Flow**
   - 30+ model interactions
   - Multiple review cycles
   - Deliberate setbacks and recoveries
   - Final successful completion

### Phase 4: Integration and Testing (Days 11-14)

1. **GitHub Integration Testing**
   - Use test repository or branch
   - Verify all API operations
   - Test project board updates
   - Validate web interface updates

2. **End-to-End Pipeline Test**
   - Run complete scenario
   - Monitor each stage transition
   - Verify artifact generation
   - Check final deliverables

3. **Error Handling and Recovery**
   - Test failure scenarios
   - Verify retry mechanisms
   - Validate checkpoint/resume
   - Ensure data consistency

## Test Execution Plan

### Stage 1: Project Creation
```
1. Generate test idea: "Analyzing Patterns in Synthetic Time Series Data"
2. Create GitHub issue
3. Add to project board (Backlog)
4. Generate initial labels
```

### Stage 2: Technical Design
```
5. Create technical design document
6. Add to technical_design_documents/
7. Update README table
8. Generate 3 initial reviews (2 positive, 1 critical)
9. Address critical review
10. Generate 8 more reviews (all positive)
11. Move to Ready (5+ points)
```

### Stage 3: Implementation Planning
```
12. Create implementation plan
13. Add to implementation_plans/
14. Generate 2 reviews (1 requests changes)
15. Update plan based on feedback
16. Generate 10 approving reviews
17. Move to In Progress
```

### Stage 4: Code Development
```
18. Generate initial code
19. Run tests (some fail)
20. Debug and fix code
21. Run tests (all pass)
22. Generate synthetic data
23. Run analysis
24. Create figures
25. Iterate 3 more times with improvements
```

### Stage 5: Paper Writing
```
26. Write Introduction (Model A)
27. Write Methods (Model B)
28. Write Results (Model C)
29. Write Discussion (Model D)
30. Write Abstract (Model E)
31. Generate 3 paper reviews
32. Revise based on feedback
33. Generate 10 approving reviews
```

### Stage 6: Publication
```
34. Compile LaTeX to PDF
35. Organize code repository
36. Update all README files
37. Move to Done
38. Verify GitHub Pages update
```

## Success Criteria

1. **Functional Requirements**
   - All 38 steps complete successfully
   - GitHub issue progresses through all stages
   - All artifacts generated (code, data, figures, PDF)
   - Web interface shows completed project

2. **Quality Requirements**
   - Generated code executes without errors
   - Analysis produces meaningful results
   - Figures are properly formatted
   - PDF compiles successfully
   - All references are valid

3. **Integration Requirements**
   - GitHub API operations succeed
   - Project board updates correctly
   - Attribution tracking works
   - Model contributions recorded

## Risk Mitigation

1. **Technical Risks**
   - **Risk**: Code execution security
   - **Mitigation**: Docker sandbox with resource limits

2. **Integration Risks**
   - **Risk**: GitHub API rate limits
   - **Mitigation**: Implement caching and batching

3. **Timing Risks**
   - **Risk**: Long execution times
   - **Mitigation**: Parallel execution where possible

## Next Steps

1. Review this plan with user
2. Prioritize implementation tasks
3. Set up development environment
4. Begin Phase 1 implementation
5. Create progress tracking dashboard

## Estimated Timeline

- **Phase 1**: 3 days (Infrastructure)
- **Phase 2**: 4 days (Task Implementation)
- **Phase 3**: 3 days (Test Scenarios)
- **Phase 4**: 4 days (Integration & Testing)
- **Total**: 14 days for full implementation

## Alternative: Minimal Viable Test

If full implementation is too extensive, we can create a minimal test that:
1. Uses existing task implementations
2. Simulates code execution (no real running)
3. Uses pre-generated figures/data
4. Tests only critical path transitions
5. Completes in 3-5 days

This would validate the pipeline flow without implementing all execution capabilities.