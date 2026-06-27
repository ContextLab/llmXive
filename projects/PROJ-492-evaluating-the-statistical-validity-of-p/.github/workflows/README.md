# GitHub Actions Workflow Documentation

## Workflow: audit.yml

This workflow runs on:
- Push to main/master branches
- Pull requests targeting main/master branches

## What it does:

1. **Checkout**: Pulls the repository code
2. **Python Setup**: Installs Python 3.9 with pip caching
3. **Dependencies**: Installs all packages from requirements.txt
4. **Directory Verification**: Ensures required directories exist (src/, tests/, data/)
5. **Import Validation**: Verifies Python modules can be imported
6. **Resource Check**: Reports available CPU and memory (enforces <= 2 vCPU, <= 2GB RAM)
7. **Test Execution**: Runs pytest if tests are available
8. **Success Report**: Confirms CI pipeline completion

## Resource Constraints

- CPU: <= 2 vCPU (enforced in workflow steps)
- RAM: <= 2GB (enforced in workflow steps)
- Timeout: 60 minutes per job

## Error Handling

The workflow will fail with explicit error messages if:
- Required directories are missing
- Python modules cannot be imported
- Resource limits are exceeded

## Future Enhancements

As the project matures, this workflow will be extended to:
- Run Monte-Carlo validation (T062)
- Execute full audit pipeline (T032)
- Validate schema compliance (T057, T058)
- Check Constitution Principles (PT005C)
- Generate and verify manifests (T056)
