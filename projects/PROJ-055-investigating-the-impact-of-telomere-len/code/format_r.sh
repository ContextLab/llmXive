#!/bin/bash
# Script to format R code using styler and lintr

set -e

echo "Running R code formatter (styler)..."

R --slave -e "
  library(styler)
  library(lintr)

  # Find all R files in the code directory
  r_files <- list.files('code/R', pattern = '\\\\.R$', full.names = TRUE, recursive = TRUE)

  if (length(r_files) == 0) {
    message('No R files found in code/R to format.')
  } else {
    message('Formatting ', length(r_files), ' R files...')
    for (file in r_files) {
      style_file(file, scope = 'tokens')
      message('Formatted: ', file)
    }
  }

  # Check for linting issues
  lint_files <- list.files('code/R', pattern = '\\\\.R$', full.names = TRUE, recursive = TRUE)
  if (length(lint_files) > 0) {
    results <- lapply(lint_files, lint)
    issues <- unlist(results)
    if (length(issues) > 0) {
      message('Linting issues found:')
      print(issues)
      quit(status = 1)
    } else {
      message('No linting issues found.')
    }
  }
"

echo "R code formatting complete."
