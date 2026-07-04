# Linting and Formatting Guide for PROJ-399

## Overview
This project uses `lintr` for static code analysis and `styler` for automatic formatting of R code.

## Configuration
- Lint configuration: `code/.lintr`
- Project profile: `code/.Rprofile`

## Running Lints
```r
# Run all lints in the code directory
source("code/.Rprofile")
run_lint("code")

# Check a specific file
lintr::lint("code/01_data_prep.R")
```

## Formatting Code
```r
# Format all R files in the code directory
source("code/.Rprofile")
format_code("code")

# Or use styler directly
styler::style_dir("code", recurse = TRUE)
```

## Pre-commit Hooks
To run lints before committing, add a pre-commit hook:

```bash
#.git/hooks/pre-commit
#!/bin/bash
Rscript -e "source('code/.Rprofile'); if (!run_lint('code')) exit 1"
```

## IDE Integration
### RStudio
- Install `lintr` and `styler` packages
- Go to Tools > Global Options > Code > Editing
- Check "Run linters on save"
- Configure `lintr` to use the project's `.lintr` file

### VS Code
- Install the `R` extension
- Configure `r.lsp.linter` to use `lintr`
- Enable auto-formatting with `styler`

## Common Lint Rules
- Line length: 100 characters (except in data prep files)
- Indentation: 2 spaces
- Naming: snake_case for objects
- Assignment: ` <- ` preferred
- Quotes: Double quotes only

## Exclusions
Some files have relaxed rules:
- `code/01_data_prep.R`: Long URLs and paths
- `code/02_power_analysis.R`: Explanatory comments

## Troubleshooting
If lints fail unexpectedly:
1. Check if `lintr` is installed: `install.packages("lintr")`
2. Verify `.lintr` file exists in project root
3. Run `lintr::lint_dir()` manually to see detailed output
4. Check for syntax errors in the R files
