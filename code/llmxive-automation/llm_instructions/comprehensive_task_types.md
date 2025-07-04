# Comprehensive Task Types for llmXive Automation

This document defines ALL task types needed for the complete scientific discovery pipeline, from idea generation through paper publication.

## Task Categories and Types

### 1. Ideation & Design Tasks

#### BRAINSTORM_IDEA
- Generate new scientific research ideas
- Output: GitHub issue with idea description

#### WRITE_TECHNICAL_DESIGN
- Create full technical design document for an idea
- Input: Issue number with idea
- Output: Markdown file in technical_design_documents/

#### REVIEW_TECHNICAL_DESIGN
- Review and score a technical design document
- Input: Design document path
- Output: Review file and score update

### 2. Planning Tasks

#### WRITE_IMPLEMENTATION_PLAN
- Convert technical design into detailed implementation plan
- Input: Technical design document
- Output: Implementation plan document

#### REVIEW_IMPLEMENTATION_PLAN
- Review and score an implementation plan
- Input: Implementation plan path
- Output: Review file and score update

### 3. Literature & Research Tasks

#### CONDUCT_LITERATURE_SEARCH
- Search for relevant papers and validate references
- Input: Topic/keywords
- Output: Annotated bibliography with validated links

#### VALIDATE_REFERENCES
- Check that all references exist and are accessible
- Input: List of references or paper path
- Output: Validation report

#### MINE_LLMXIVE_ARCHIVE
- Search completed llmXive papers for related work
- Input: Topic/keywords
- Output: List of relevant internal papers

### 4. Code Development Tasks

#### WRITE_CODE
- Implement code following an implementation plan
- Input: Implementation plan
- Output: Python code files

#### WRITE_TESTS
- Create comprehensive pytest suite
- Input: Code file paths
- Output: Test files

#### RUN_TESTS
- Execute tests and report results
- Input: Test file paths
- Output: Test results report

#### RUN_CODE
- Execute code and capture outputs
- Input: Code file path and parameters
- Output: Execution results

#### DEBUG_CODE
- Fix failing tests or errors
- Input: Error reports
- Output: Fixed code

#### ORGANIZE_INTO_NOTEBOOKS
- Create Jupyter notebooks from code
- Input: Code files
- Output: .ipynb files

### 5. Data & Analysis Tasks

#### GENERATE_DATASET
- Create or find datasets for research
- Input: Data requirements
- Output: Data files and documentation

#### ANALYZE_DATA
- Perform statistical analyses
- Input: Data and analysis plan
- Output: Analysis results

#### PLAN_STATISTICAL_ANALYSIS
- Design statistical approach for paper
- Input: Research questions and data
- Output: Analysis plan document

#### INTERPRET_RESULTS
- Interpret analysis outputs
- Input: Results data
- Output: Interpretation document

### 6. Visualization Tasks

#### PLAN_FIGURES
- Design figures for paper
- Input: Results and paper outline
- Output: Figure plan document

#### CREATE_FIGURES
- Implement planned figures
- Input: Figure plan and data
- Output: Vector graphics (PDF/SVG)

#### VERIFY_FIGURES
- Check all figures export correctly
- Input: Figure files
- Output: Verification report

### 7. Paper Writing Tasks

#### WRITE_PAPER_SECTION
- Write specific paper sections
- Input: Section type (intro/methods/results/discussion)
- Output: Markdown/LaTeX content

#### WRITE_ABSTRACT
- Create paper abstract
- Input: Full paper draft
- Output: Abstract text

#### WRITE_INTRODUCTION
- Write introduction section
- Input: Technical design and literature
- Output: Introduction text

#### WRITE_METHODS
- Write methods section
- Input: Implementation details
- Output: Methods text

#### WRITE_RESULTS
- Write results section
- Input: Analysis outputs and figures
- Output: Results text

#### WRITE_DISCUSSION
- Write discussion section
- Input: Results and interpretations
- Output: Discussion text

#### COMPILE_BIBLIOGRAPHY
- Create formatted bibliography
- Input: Citations used
- Output: Bibliography section

### 8. Documentation Tasks

#### UPDATE_README
- Update any README file
- Input: File path and changes
- Output: Updated README

#### DOCUMENT_CODE
- Add docstrings and comments
- Input: Code files
- Output: Documented code

#### CREATE_API_DOCS
- Generate API documentation
- Input: Code base
- Output: API documentation

#### UPDATE_PROJECT_DOCS
- Update project-wide documentation
- Input: Documentation needs
- Output: Updated docs

### 9. Review & Quality Tasks

#### REVIEW_PAPER
- Comprehensive paper review
- Input: Paper draft
- Output: Review with recommendations

#### REVIEW_CODE
- Code quality and correctness review
- Input: Code files
- Output: Code review report

#### CHECK_REPRODUCIBILITY
- Verify all results can be reproduced
- Input: Paper and code
- Output: Reproducibility report

#### CHECK_LOGIC_GAPS
- Find logical inconsistencies
- Input: Any document
- Output: Logic gap report

### 10. Project Management Tasks

#### CHECK_PROJECT_STATUS
- Analyze if project meets stage requirements
- Input: Project ID
- Output: Status report

#### UPDATE_PROJECT_STAGE
- Move project between pipeline stages
- Input: Project ID and new stage
- Output: Updated project status

#### CREATE_ISSUE_COMMENT
- Add comments to GitHub issues
- Input: Issue number and context
- Output: Posted comment

#### UPDATE_ISSUE_LABELS
- Manage issue labels and scores
- Input: Issue number and labels
- Output: Updated issue

#### FORK_IDEA
- Create related ideas from existing
- Input: Original idea
- Output: New forked ideas

### 11. Compilation & Publishing Tasks

#### COMPILE_LATEX
- Compile paper to PDF
- Input: LaTeX files
- Output: PDF document

#### VERIFY_COMPILATION
- Check PDF renders correctly
- Input: PDF file
- Output: Verification report

#### PREPARE_SUBMISSION
- Prepare paper for submission
- Input: Paper and journal requirements
- Output: Submission package

### 12. Self-Correction Tasks

#### IDENTIFY_IMPROVEMENTS
- Find areas for improvement
- Input: Any artifact
- Output: Improvement suggestions

#### IMPLEMENT_CORRECTIONS
- Apply suggested improvements
- Input: Improvement suggestions
- Output: Corrected artifact

#### VERIFY_CORRECTIONS
- Verify corrections were applied
- Input: Original and corrected versions
- Output: Verification report

## Task Properties

Each task has:
- **Input Requirements**: What information is needed
- **Output Artifacts**: What is produced
- **Quality Checks**: How to verify success
- **Dependencies**: What must exist before task can run
- **Next Steps**: What tasks typically follow

## Task Selection Logic

Tasks are selected based on:
1. **Pipeline Gaps**: Ensuring all stages have adequate items
2. **Human Interest**: Reaction scores and comments
3. **Scientific Value**: LLM assessment of importance
4. **Completeness**: Finishing in-progress work
5. **Staleness**: Reviving inactive projects
6. **Dependencies**: Completing prerequisites first

## Self-Correction Mechanism

The system continuously:
1. Reviews its own outputs
2. Identifies areas for improvement
3. Implements corrections
4. Verifies improvements
5. Learns from patterns of corrections

This creates a self-improving pipeline where quality increases over time.