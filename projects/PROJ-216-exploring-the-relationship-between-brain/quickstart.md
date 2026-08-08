# Quickstart Guide

## Running the Pipeline

1. **Setup Environment**
 ```bash
 pip install -e.
 ```

2. **Verify Dependencies**
 ```bash
 python code/dependency_check.py
 ```

3. **Run Preprocessing**
 ```bash
 python code/preprocess.py
 ```

4. **Compute Graph Metrics**
 ```bash
 python code/graph_metrics.py
 ```

5. **Statistical Analysis**
 ```bash
 python code/stats.py
 ```

## Code Quality

Ensure all code passes linting and formatting checks before committing:

```bash
# Run linter
ruff check code/

# Run formatter
black code/
```

## Testing

Run the test suite:
```bash
pytest tests/
```
