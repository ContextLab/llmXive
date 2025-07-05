# Updated Scoring System Implementation

## Changes Made

Based on the clarifications about the llmXive scoring rules, we've updated the scoring system with the following changes:

### 1. Stage Progression

**New stages**: Backlog → Ready → In Progress → **In Review** → Done

- Added the **In Review** stage between In Progress and Done
- Papers must go through comprehensive review before completion

### 2. Score Requirements

- **Backlog → Ready**: 5 points (needs technical design)
- **Ready → In Progress**: 5 points (needs implementation plan)
- **In Progress → In Review**: **1 point** (signal paper completion)
- **In Review → Done**: 5 points (comprehensive reviews)

### 3. Review Behavior

- **Positive reviews**: Add points (LLM: +0.5, Human: +1.0)
- **Negative reviews**: **DO subtract points** (LLM: -0.5, Human: -1.0)
- **Score floor**: Still at 0 (cannot go negative)
- **Critical reviews**: Trigger move to **previous stage** with score reset

### 4. Critical Review Handling

Critical reviews now:
1. Mark the review as critical
2. Keep the current score unchanged
3. Signal to StageManager to move back one stage
4. Reset score to 0 in the previous stage

Example flow:
- Project in IN_REVIEW with 3 points
- Critical review identifies fundamental flaw
- Project moves back to IN_PROGRESS
- Score resets to 0
- Must fix issues and rebuild score to advance again

### 5. New Methods

Added to StageManager:
- `move_to_previous_stage()` - Handles moving back on critical reviews
- Support for the IN_REVIEW stage in all methods

## Key Implementation Details

### Score Calculation
```python
if review.is_critical:
    # Score stays same, stage manager handles the move
    new_score = old_score
else:
    # Add/subtract based on review
    score_delta = review.get_score_impact()
    new_score = max(0.0, old_score + score_delta)
```

### Stage Transitions
```python
# IN_PROGRESS to IN_REVIEW (only 1 point needed)
'requirements': {
    'has_paper_draft': True,
    'has_complete_code': True,
    'score_threshold': 1.0,  # Signal completion
}

# IN_REVIEW to DONE (5 points needed)
'requirements': {
    'has_paper_pdf': True,
    'score_threshold': 5.0,  # Comprehensive reviews
}
```

### Critical Review Flow
```python
# 1. Add critical review
tracker.add_review(project_id, critical_review)

# 2. Stage manager handles the move
if review.is_critical:
    manager.move_to_previous_stage(project_id, project_state)
```

## Testing

All 25 tests pass, including:
- New stage transitions
- Critical review → stage move behavior
- Score calculations with negative reviews
- IN_PROGRESS → IN_REVIEW with only 1 point
- IN_REVIEW → DONE requiring 5 points

## Benefits

1. **More realistic review process**: Papers must pass through rigorous review
2. **Lower barrier for review entry**: Only 1 point to enter review stage
3. **High bar for completion**: 5 points of positive reviews to finish
4. **Clear feedback mechanism**: Critical reviews send work back for revision
5. **Encourages iteration**: Most papers will go through multiple review cycles

This implementation better reflects the expected workflow where papers often need revision based on comprehensive reviews before final acceptance.