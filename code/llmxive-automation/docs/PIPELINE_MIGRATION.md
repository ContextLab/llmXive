# Pipeline Orchestrator Migration Guide

## Overview

The new pipeline orchestrator provides better project tracking, stage management, and follows the same patterns as our comprehensive test pipeline. This guide helps you migrate from the original orchestrator to the new pipeline-based system.

## Key Differences

### 1. Project-Centric Execution
- **Old**: Tasks are generated based on overall project state
- **New**: Focuses on one project at a time, with stage-aware task generation

### 2. Score Integration
- **Old**: Score tracking is handled separately
- **New**: Fully integrated with ScoreTracker and StageManager

### 3. Stage Awareness
- **Old**: Limited stage-based logic
- **New**: Generates appropriate tasks based on current project stage

## Command Line Changes

### Basic Usage

```bash
# Old way
python main.py --max-tasks 5

# New way
python main.py --use-pipeline --max-tasks 5
```

### Working on Specific Projects

```bash
# New feature - work on specific project
python main.py --use-pipeline --project-id quantum-materials-2025
```

### GitHub Actions

Update your workflow file:

```yaml
# Old
- name: Run automation
  run: python main.py --max-tasks 5

# New
- name: Run automation with pipeline
  run: python main.py --use-pipeline --max-tasks 5
```

## Feature Comparison

| Feature | Original Orchestrator | Pipeline Orchestrator |
|---------|---------------------|---------------------|
| Model Selection | ✓ | ✓ |
| Task Execution | ✓ | ✓ |
| Stage Management | Basic | Advanced |
| Score Tracking | External | Integrated |
| Project Focus | Multiple | Single (per cycle) |
| Task Generation | Generic | Stage-specific |
| Test Coverage | Basic | Comprehensive |

## Migration Steps

1. **Test First**: Run both orchestrators in parallel to compare results
   ```bash
   # Run original
   python main.py --max-tasks 5
   
   # Run pipeline
   python main.py --use-pipeline --max-tasks 5
   ```

2. **Update Scripts**: Add `--use-pipeline` flag to your automation scripts

3. **Update GitHub Actions**: Modify workflow files to use the new flag

4. **Monitor Results**: Check logs to ensure tasks are executing correctly

## Rollback

If you need to rollback, simply remove the `--use-pipeline` flag:

```bash
# Rollback to original
python main.py --max-tasks 5
```

## Benefits of Migration

1. **Better Project Tracking**: Projects are tracked through their complete lifecycle
2. **Smarter Task Selection**: Tasks are generated based on project stage and needs
3. **Score Integration**: Automatic score tracking and stage advancement
4. **Comprehensive Testing**: Backed by our 41-step test scenario
5. **Cleaner Code**: Follows established patterns from our test infrastructure

## Troubleshooting

### No Projects Selected
- Check that you have open issues with proper labels
- Verify GitHub access (token or CLI)

### Tasks Not Executing
- Check model loading in logs
- Verify task executor initialization

### Stage Not Advancing
- Check project scores with score tracker
- Verify stage transition thresholds

## Future Enhancements

The pipeline orchestrator is designed to support:
- Parallel project execution
- Custom stage definitions
- Advanced prioritization algorithms
- Real-time progress monitoring