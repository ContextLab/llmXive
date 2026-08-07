# CI/CD Configuration Guide

## Resource Constraints
This project enforces strict resource limits to ensure reproducibility and cost control:
- **CPU**: 2 cores
- **Memory**: 7GB
- **Timeout**: 6 hours (default GitHub Actions limit, enforced via job timeout if needed)

## Environment Variables
The CI runner sets the following environment variables automatically via container options:
- `CPU_COUNT`: Limited to 2
- `MEMORY_LIMIT`: Limited to 7GB

## Constitution Principles
- **Principle I (Reproducibility)**: All runs use the same containerized environment.
- **Principle VI (Resource Limits)**: Hard limits enforced at the container level.

## Adding New Steps
When adding new CI steps:
1. Ensure they respect the 2-core/7GB limit.
2. Add any new artifacts to the "Upload Artifacts" step.
3. Update `tasks.md` if new verification steps are added.