# Contributing Guidelines

## Data Integrity Policy
**CRITICAL**: Do not use synthetic data for final research claims.
- Use `--simulate` flag ONLY for local pipeline verification and CI testing.
- The production pipeline MUST fail loudly (exit code 1) if `data/raw/` is empty or contains no real session files.
- Synthetic data is strictly forbidden for generating final statistical results or publication figures.
- All final claims must be derived from data collected via the web-based simulator (FR-007) or verified real-world sources.

## Schema Compliance
- All session data MUST conform to `contracts/session.schema.yaml`.
- Any deviation from the schema will cause the data loader to reject the file.

## Development Workflow
1. Ensure all tests pass before committing.
2. Update documentation when changing APIs.
3. Use `black` for formatting and `ruff` for linting.
4. Write unit tests for new functionality.
