# PROJ-754: Linking Resting-State fMRI Entropy to Real-World Decision Risk-Taking

## Project Structure
- `code/`: Source code modules
- `data/`: Data artifacts (raw, cleaned, derived, results)
- `tests/`: Test suites
- `reports/`: Generated analysis reports
- `specs/`: Feature specifications

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Initialize data directories: `python -m code.scripts.init_data_dirs`
3. Set environment variables: `export HCP_TOKEN=<your_token>`
4. Run linting: `python -m code.config.lint_format --lint-check`
5. Run formatting: `python -m code.config.lint_format --format-check`

## Execution
See `tasks.md` for the ordered list of implementation tasks.