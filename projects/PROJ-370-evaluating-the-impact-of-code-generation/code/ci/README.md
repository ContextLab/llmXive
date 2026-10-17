# Continuous Integration configuration

This directory holds the project's CI configuration for linting.

- ``github_actions_ci.yml`` — GitHub Actions workflow that runs
 ``ruff check.`` and ``black --check.`` on every push and pull
 request. It is kept here (a project-owned path) because the
 top-level ``.github/`` directory is managed by the platform; copy it
 to ``.github/workflows/ci.yml`` in a standalone checkout to enable
 it on GitHub.

Tool configuration (line-length 88, exclude patterns for ``data/``,
``results/``, ``logs/``, ``venv/``, ``__pycache__``, ``state/``) lives
in the root ``pyproject.toml`` under ``[tool.black]`` and
``[tool.ruff]``.

Local verification:

```bash
ruff check.
black --check.
```