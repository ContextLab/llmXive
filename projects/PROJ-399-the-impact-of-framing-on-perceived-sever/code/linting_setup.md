# Linting & Formatting Setup (T003)

This project uses **lintr** for static analysis and **styler** for
automatic formatting of R code.

## Files

- `code/.lintr` — lintr configuration (line length 100, project-specific
 linter exclusions, generated-file exclusions).
- `code/lint.R` — lints every `*.R` file under `code/` using the project
 config and writes `results/lint_report.txt`. Exits non-zero on lint
 errors (fail loudly; pass `--no-fail` to only report).
- `code/format.R` — formats R sources with styler (tidyverse style).
 Supports `--check` mode for CI.

## Usage

```bash
# Install tools (once)
R -e "install.packages(c('lintr', 'styler'))"

# Check code quality
Rscript code/lint.R

# Auto-format code
Rscript code/format.R

# CI-style formatting check (no writes, non-zero exit on deviation)
Rscript code/format.R --check
```

## Notes

- `lint.R` and `format.R` themselves are excluded from linting/formatting
 to avoid self-referential tooling churn.
- The lint report is written to `results/lint_report.txt` so runs leave
 an auditable artifact on disk.
- Both scripts locate the project root relative to their own path, so
 they can be invoked from any working directory.