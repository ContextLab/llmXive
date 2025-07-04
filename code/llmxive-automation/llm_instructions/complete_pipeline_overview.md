# Complete llmXive Automation Pipeline Overview

This document provides an overview of the complete scientific discovery automation pipeline.

## Pipeline Architecture

```
┌─────────────────────┐
│   Model Manager     │ ← Dynamically selects trending models from HuggingFace
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Conversation Manager│ ← Task-specific system prompts
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Task Executor     │ ← 40+ task types covering entire pipeline
└──────────┬──────────┘
           │
    ┌──────┴──────┬─────────┬─────────┬─────────┐
    │             │         │         │         │
┌───▼───┐  ┌─────▼────┐ ┌──▼───┐ ┌──▼──┐ ┌───▼────┐
│GitHub │  │   Code   │ │ Lit  │ │LaTeX│ │ Self   │
│Handler│  │  Runner  │ │Search│ │Comp │ │Correct │
└───────┘  └──────────┘ └──────┘ └─────┘ └────────┘
```

## Complete Task Flow

### 1. Ideation Phase
```
BRAINSTORM_IDEA → GitHub Issue (Backlog)
    ↓
WRITE_TECHNICAL_DESIGN → Design Document
    ↓
REVIEW_TECHNICAL_DESIGN → Review + Score Update
    ↓
[Score ≥ 10] → Move to Ready
```

### 2. Planning Phase
```
WRITE_IMPLEMENTATION_PLAN → Implementation Plan
    ↓
REVIEW_IMPLEMENTATION_PLAN → Review + Score Update
    ↓
[Score ≥ 5] → Move to In Progress
```

### 3. Research Phase
```
CONDUCT_LITERATURE_SEARCH → Bibliography
    ↓
VALIDATE_REFERENCES → Validated Papers
    ↓
MINE_LLMXIVE_ARCHIVE → Internal References
```

### 4. Development Phase
```
WRITE_CODE → Python Modules
    ↓
WRITE_TESTS → Test Suite
    ↓
RUN_TESTS → Test Results
    ↓
DEBUG_CODE → Fixed Code
    ↓
DOCUMENT_CODE → Documented Code
    ↓
ORGANIZE_INTO_NOTEBOOKS → Jupyter Notebooks
```

### 5. Analysis Phase
```
GENERATE_DATASET → Data Files
    ↓
PLAN_STATISTICAL_ANALYSIS → Analysis Plan
    ↓
ANALYZE_DATA → Results
    ↓
INTERPRET_RESULTS → Interpretation
```

### 6. Visualization Phase
```
PLAN_FIGURES → Figure Plan
    ↓
CREATE_FIGURES → Figure Scripts
    ↓
VERIFY_FIGURES → Validated Figures
```

### 7. Writing Phase
```
WRITE_ABSTRACT → Abstract
WRITE_INTRODUCTION → Introduction
WRITE_METHODS → Methods
WRITE_RESULTS → Results  
WRITE_DISCUSSION → Discussion
COMPILE_BIBLIOGRAPHY → References
```

### 8. Compilation Phase
```
COMPILE_LATEX → PDF Document
    ↓
VERIFY_COMPILATION → Validated PDF
    ↓
PREPARE_SUBMISSION → Submission Package
```

### 9. Quality & Self-Correction
```
At any stage:
IDENTIFY_IMPROVEMENTS → Improvement Report
    ↓
IMPLEMENT_CORRECTIONS → Updated Artifact
    ↓
VERIFY_CORRECTIONS → Validation
```

## Task Prioritization Algorithm

The system uses multi-factor prioritization:

```python
priority_score = (
    0.3 * category_weight +      # complete_work > advance_item > pipeline_fill
    0.3 * urgency +              # Based on staleness and dependencies
    0.2 * human_interest +       # Thumbs up/down reactions
    0.2 * llm_judgment +         # LLM's assessment of scientific value
    0.05 * random_factor         # Prevent deterministic behavior
)
```

## Key Features

### 1. Complete Automation
- Every step from idea to published paper
- No manual intervention required
- Self-correcting and improving

### 2. Quality Control
- Multiple review stages
- Automated testing
- Reference validation
- Logic gap detection

### 3. Reproducibility
- All code tested
- Figures regeneratable
- Results verifiable
- Full documentation

### 4. Self-Improvement
- Identifies own weaknesses
- Implements corrections
- Learns from patterns
- Continuously improves

## GitHub Integration

### Labels System
- `Score: X.X` - Tracks review points
- `backlog`, `ready`, `in-progress`, `done` - Stage labels
- Keyword labels - Topic classification

### File Organization
```
llmXive/
├── technical_design_documents/
│   └── {project_id}/
│       └── design.md
├── implementation_plans/
│   └── {project_id}/
│       └── implementation_plan.md
├── code/
│   └── {project_id}/
│       ├── src/
│       ├── tests/
│       └── notebooks/
├── papers/
│   └── {project_id}/
│       ├── sections/
│       ├── figures/
│       └── paper.tex
├── reviews/
│   └── {project_id}/
│       ├── Design/
│       ├── Implementation/
│       ├── Paper/
│       └── Code/
└── data/
    └── {project_id}/
```

## Execution Modes

### 1. GitHub Actions (Automated)
- Runs every 3 hours
- Selects tasks automatically
- Updates repository

### 2. CLI (Manual)
```bash
# Run full cycle
python -m llmxive_automation

# Run specific task
python -m llmxive_automation --task BRAINSTORM_IDEA

# Dry run
python -m llmxive_automation --dry-run
```

## Resource Management

### Memory Constraints
- 4-bit model quantization
- Max 3.5GB model size
- Context window management

### Execution Limits
- 5 minute timeout per task
- 10 minute timeout for tests
- 30 minute GitHub Action limit

## Success Metrics

### Pipeline Health
- Minimum 5 items in backlog
- Minimum 2 items ready
- At least 1 item in progress

### Quality Metrics
- Test coverage > 80%
- All references validated
- No logic gaps detected
- Reproducible results

## Error Handling

### Retry Logic
- 3 attempts with increasing temperature
- Fallback models if primary fails
- Graceful degradation

### Recovery Strategies
- Checkpoint saving
- Partial progress preservation
- Error reporting

This complete pipeline enables fully automated scientific discovery from initial idea through published paper, with continuous self-improvement and quality assurance.