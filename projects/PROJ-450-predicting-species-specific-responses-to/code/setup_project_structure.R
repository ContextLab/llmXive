#!/usr/bin/env Rscript
# T001: Create project structure per implementation plan
# Creates: src/, data/, results/, tests/ directories
# Subdirectories follow standard R research pipeline conventions

create_directories <- function() {
  # Define the directory structure to create
  dirs <- c(
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "results",
    "figures",
    "tests/unit",
    "tests/integration",
    "specs"
  )

  created_count <- 0
  skipped_count <- 0

  for (dir_path in dirs) {
    if (!dir.exists(dir_path)) {
      dir.create(dir_path, recursive = TRUE, showWarnings = FALSE)
      cat(sprintf("Created directory: %s\n", dir_path))
      created_count <- created_count + 1
    } else {
      cat(sprintf("Directory already exists: %s\n", dir_path))
      skipped_count <- skipped_count + 1
    }
  }

  cat(sprintf("\nSetup complete. Created %d directories, skipped %d existing.\n",
              created_count, skipped_count))
  return(invisible(TRUE))
}

# Execute if run as script
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) > 0 && args[1] == "--force") {
    cat("Force mode not implemented; skipping existing dirs only.\n")
  }
  create_directories()
}
