# Task Types Reference

This document provides a complete reference for all 48 task types supported by the llmXive automation system.

## Overview

The system supports 48 distinct task types organized into 12 categories. Each task type has specific input requirements and outputs.

## Task Categories

### 1. Ideation & Design (3 tasks)
- **BRAINSTORM_IDEA**: Generate new research ideas
  - Input: None (uses existing backlog for context)
  - Output: GitHub issue with idea details
  - Attribution: ✓ Tracked

- **WRITE_TECHNICAL_DESIGN**: Create technical design documents
  - Input: `issue_number`, `design_path`
  - Output: Technical design markdown file
  - Attribution: ✓ Tracked

- **REVIEW_TECHNICAL_DESIGN**: Review and score design documents
  - Input: `design_path`
  - Output: Review file with score
  - Attribution: ✓ Tracked

### 2. Planning (2 tasks)
- **WRITE_IMPLEMENTATION_PLAN**: Convert designs to implementation plans
  - Input: `design_path`, `plan_path`
  - Output: Implementation plan markdown file
  - Attribution: ✓ Tracked

- **REVIEW_IMPLEMENTATION_PLAN**: Review implementation plans
  - Input: `plan_path`
  - Output: Review with score
  - Attribution: ✓ Tracked

### 3. Literature & Research (3 tasks)
- **CONDUCT_LITERATURE_SEARCH**: Search for relevant literature
  - Input: `topic`
  - Output: Annotated bibliography
  - Attribution: ✓ Tracked

- **VALIDATE_REFERENCES**: Verify reference validity
  - Input: `references` (list)
  - Output: Validation report
  - Attribution: ✓ Tracked

- **MINE_LLMXIVE_ARCHIVE**: Search internal llmXive papers
  - Input: `topic` or `keywords`
  - Output: List of relevant internal work
  - Attribution: ✓ Tracked

### 4. Code Development (6 tasks)
- **WRITE_CODE**: Implement code modules
  - Input: `plan_path`, `code_path`, `module_description`
  - Output: Python code file
  - Attribution: ✓ Tracked

- **WRITE_TESTS**: Create test suites
  - Input: `code_path`, `test_path`
  - Output: Test file with pytest tests
  - Attribution: ✓ Tracked

- **RUN_TESTS**: Execute test suites
  - Input: `test_path`
  - Output: Test execution results
  - Attribution: Not tracked (execution only)

- **RUN_CODE**: Execute code scripts
  - Input: `code_path`
  - Output: Execution results
  - Attribution: Not tracked (execution only)

- **DEBUG_CODE**: Fix code errors
  - Input: `code_path`, `error`
  - Output: Fixed code
  - Attribution: ✓ Tracked

- **ORGANIZE_INTO_NOTEBOOKS**: Create Jupyter notebooks
  - Input: `code_files`, `notebook_path`
  - Output: Jupyter notebook file
  - Attribution: ✓ Tracked

### 5. Data & Analysis (4 tasks)
- **GENERATE_DATASET**: Create datasets
  - Input: `specifications`
  - Output: Dataset files
  - Attribution: ✓ Tracked

- **ANALYZE_DATA**: Perform statistical analysis
  - Input: `data`
  - Output: Analysis results
  - Attribution: ✓ Tracked

- **PLAN_STATISTICAL_ANALYSIS**: Design analysis approach
  - Input: `research_question`
  - Output: Analysis plan
  - Attribution: ✓ Tracked

- **INTERPRET_RESULTS**: Interpret findings
  - Input: `results`
  - Output: Interpretation report
  - Attribution: ✓ Tracked

### 6. Visualization (3 tasks)
- **PLAN_FIGURES**: Design visualizations
  - Input: `results_summary`
  - Output: Figure specifications
  - Attribution: ✓ Tracked

- **CREATE_FIGURES**: Generate plots
  - Input: `figure_specs`
  - Output: Matplotlib/seaborn code
  - Attribution: ✓ Tracked

- **VERIFY_FIGURES**: Check figure quality
  - Input: `figure_paths`
  - Output: Verification report
  - Attribution: ✓ Tracked

### 7. Paper Writing (6 tasks)
- **WRITE_ABSTRACT**: Write paper abstract
  - Input: `paper_content`
  - Output: Abstract text
  - Attribution: ✓ Tracked

- **WRITE_INTRODUCTION**: Write introduction section
  - Input: `design_path`
  - Output: Introduction text
  - Attribution: ✓ Tracked

- **WRITE_METHODS**: Write methods section
  - Input: `implementation_details`
  - Output: Methods text
  - Attribution: ✓ Tracked

- **WRITE_RESULTS**: Write results section
  - Input: `results_data`
  - Output: Results text
  - Attribution: ✓ Tracked

- **WRITE_DISCUSSION**: Write discussion section
  - Input: `results_summary`
  - Output: Discussion text
  - Attribution: ✓ Tracked

- **COMPILE_BIBLIOGRAPHY**: Create bibliography
  - Input: `citations`
  - Output: BibTeX file
  - Attribution: ✓ Tracked

### 8. Documentation (4 tasks)
- **UPDATE_README_TABLE**: Update README tables
  - Input: `readme_path`, `table_name`, `new_row`
  - Output: Updated README
  - Attribution: ✓ Tracked

- **DOCUMENT_CODE**: Add code documentation
  - Input: `code_path`
  - Output: Documented code
  - Attribution: ✓ Tracked

- **CREATE_API_DOCS**: Generate API documentation
  - Input: `code_directory`
  - Output: API documentation
  - Attribution: ✓ Tracked

- **UPDATE_PROJECT_DOCS**: Update project docs
  - Input: `project_updates`
  - Output: Updated documentation
  - Attribution: ✓ Tracked

### 9. Review & Quality (4 tasks)
- **REVIEW_PAPER**: Review scientific papers
  - Input: `paper_path`
  - Output: Paper review with score
  - Attribution: ✓ Tracked

- **REVIEW_CODE**: Review code quality
  - Input: `code_path`
  - Output: Code review
  - Attribution: ✓ Tracked

- **CHECK_REPRODUCIBILITY**: Verify reproducibility
  - Input: `project_directory`
  - Output: Reproducibility report
  - Attribution: ✓ Tracked

- **CHECK_LOGIC_GAPS**: Identify logical issues
  - Input: `document_path`
  - Output: Logic analysis
  - Attribution: ✓ Tracked

### 10. Project Management (5 tasks)
- **CHECK_PROJECT_STATUS**: Analyze project state
  - Input: `issue_number`
  - Output: Status report with recommendations
  - Attribution: ✓ Tracked

- **UPDATE_PROJECT_STAGE**: Move project stages
  - Input: `issue_number`, `new_stage`
  - Output: Updated GitHub labels
  - Attribution: Not tracked (metadata only)

- **CREATE_ISSUE_COMMENT**: Add issue comments
  - Input: `issue_number`, `comment`
  - Output: GitHub comment
  - Attribution: ✓ Tracked

- **UPDATE_ISSUE_LABELS**: Manage issue labels
  - Input: `issue_number`, `labels`
  - Output: Updated labels
  - Attribution: Not tracked (metadata only)

- **FORK_IDEA**: Create idea variations
  - Input: `issue_number`
  - Output: New issue with variation
  - Attribution: ✓ Tracked

### 11. Compilation & Publishing (3 tasks)
- **COMPILE_LATEX**: Compile LaTeX documents
  - Input: `latex_path`
  - Output: PDF document
  - Attribution: Not tracked (compilation only)

- **VERIFY_COMPILATION**: Check compilation output
  - Input: `pdf_path`
  - Output: Verification report
  - Attribution: ✓ Tracked

- **PREPARE_SUBMISSION**: Prepare for journal submission
  - Input: `paper_directory`
  - Output: Submission package
  - Attribution: ✓ Tracked

### 12. Self-Improvement (7 tasks)
- **IDENTIFY_IMPROVEMENTS**: Find improvement opportunities
  - Input: `artifact_path`
  - Output: List of improvements
  - Attribution: ✓ Tracked

- **IMPLEMENT_CORRECTIONS**: Apply corrections
  - Input: `artifact_path`, `corrections`
  - Output: Corrected artifact
  - Attribution: ✓ Tracked

- **VERIFY_CORRECTIONS**: Verify corrections
  - Input: `corrected_path`
  - Output: Verification report
  - Attribution: ✓ Tracked

- **GENERATE_HELPER_FUNCTION**: Create utility functions
  - Input: `purpose`
  - Output: Python function
  - Attribution: ✓ Tracked

- **GENERATE_ATTRIBUTION_REPORT**: Create attribution report
  - Input: None
  - Output: Markdown report
  - Attribution: Not tracked (reporting only)

- **ADD_TASK_TYPE**: Add new task capabilities
  - Input: `task_name`, `task_description`
  - Output: New task implementation
  - Attribution: ✓ Tracked

- **EDIT_TASK_TYPE**: Modify existing tasks
  - Input: `task_name`, `issue`
  - Output: Updated task code
  - Attribution: ✓ Tracked

## Testing Status

Based on comprehensive integration testing:
- **Total Tasks**: 48
- **Successfully Tested**: 44 (91.7%)
- **Currently Failing**: 3
  - REVIEW_TECHNICAL_DESIGN
  - UPDATE_README_TABLE
  - FORK_IDEA
- **Not Implemented**: 1
  - ADD_TASK_TYPE (listed but not implemented)

## Attribution Summary

- **Tasks with Attribution Tracking**: 39
- **Tasks without Attribution**: 9 (mostly execution/compilation tasks)

Attribution is tracked for all tasks that:
1. Create new content (ideas, code, text)
2. Review or analyze existing content
3. Generate documentation or reports

Attribution is not tracked for:
1. Pure execution tasks (running code/tests)
2. Metadata updates (labels, stages)
3. Compilation tasks
4. The attribution report itself