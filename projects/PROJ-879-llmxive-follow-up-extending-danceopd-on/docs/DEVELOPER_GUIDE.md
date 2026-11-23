# Developer Guide

## Setup

### Prerequisites

- Python 3.11
- pip

### Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```
3. Set up data directories:
 ```bash
 python setup_data_dirs.py
 ```

### Configuration

Edit `code/config.yaml` to set:
- Seed values
- Paths to data directories
- Hyperparameters (e.g., `TEACHER_WEIGHTS_PATH`)

## Development Workflow

1. **Run Tests**:
 ```bash
 pytest tests/
 ```
2. **Linting**:
 ```bash
 ruff check code/
 black --check code/
 ```
3. **Formatting**:
 ```bash
 black code/
 ```

## Adding New Features

1. Create a new task in `tasks.md`
2. Implement the feature in the appropriate module
3. Add unit and integration tests
4. Update documentation

## Debugging

- Use `logging` module for debug messages
- Check `data/results/` for intermediate results
- Review `exclusion_log.json` for undefined route issues

## Common Issues

### Missing Data Sources

If ImageNet-1K or LAION-400M are unavailable, the pipeline will save partial results and exit cleanly.

### Timeout

The 6-hour timeout is enforced via `signal.SIGALRM`. Partial results are saved before exiting.

### Memory Exhaustion

Use chunked loading and streaming to reduce memory usage.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
