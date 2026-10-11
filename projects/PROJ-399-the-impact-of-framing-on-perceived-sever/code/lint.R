#!/usr/bin/env Rscript
# T003: Lint all R sources in code/ using lintr.
# Usage: Rscript code/lint.R
# Writes a machine-readable report to results/lint_report.txt and
# exits non-zero if any lint error is found (fail loudly).

args <- commandArgs(trailingOnly = TRUE)
fail_on_error <- !("--no-fail" %in% args)

if (!requireNamespace("lintr", quietly = TRUE)) {
  stop("Required package 'lintr' is not installed. ",
       "Install it with: install.packages('lintr')", call. = FALSE)
}

# Resolve project root relative to this script's location so the run is
# independent of the current working directory.
script_path <- tryCatch(
  normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))),
  error = function(e) NULL
)
if (is.null(script_path) || !nzchar(script_path)) {
  script_path <- "code/lint.R"
}
code_dir <- dirname(script_path)
project_root <- dirname(code_dir)

# Point lintr at this project's config file.
linter_file <- file.path(code_dir, ".lintr")
if (!file.exists(linter_file)) {
  stop("Missing lintr configuration file: ", linter_file, call. = FALSE)
}
options(lintr.linter_file = linter_file)

r_files <- list.files(
  code_dir, pattern = "\\.[Rr]$", full.names = TRUE, recursive = TRUE
)
r_files <- r_files[basename(r_files) != "lint.R" & basename(r_files) != "format.R"]
if (length(r_files) == 0) {
  stop("No R source files found to lint in: ", code_dir, call. = FALSE)
}

cat("Linting", length(r_files), "R file(s) with lintr...\n")

all_lints <- list()
for (f in r_files) {
  file_lints <- tryCatch(
    lintr::lint(f),
    error = function(e) {
      stop("lintr failed on file '", f, "': ", conditionMessage(e),
           call. = FALSE)
    }
  )
  all_lints[[f]] <- file_lints
}

flat_lints <- unlist(all_lints, recursive = FALSE)

results_dir <- file.path(project_root, "results")
dir.create(results_dir, showWarnings = FALSE, recursive = TRUE)
report_path <- file.path(results_dir, "lint_report.txt")

con <- file(report_path, open = "wt")
sink(con, split = TRUE)
cat("lintr report for PROJ-399\n")
cat("Generated:", format(Sys.time(), tz = "UTC"), "UTC\n")
cat("Config:", linter_file, "\n")
cat("Files linted:", length(r_files), "\n")
cat("Total lints:", length(flat_lints), "\n\n")
if (length(flat_lints) == 0) {
  cat("No lint issues found. All clear.\n")
} else {
  for (f in r_files) {
    if (length(all_lints[[f]]) > 0) {
      cat("==", basename(f), "==\n")
      for (l in all_lints[[f]]) {
        cat(sprintf("  line %d, col %d: [%s] %s\n",
                    l$line_number, l$column_number, l$linter, l$message))
      }
    }
  }
}
sink()
close(con)

cat("Lint report written to:", report_path, "\n")

if (fail_on_error && length(flat_lints) > 0) {
  stop("Linting failed with ", length(flat_lints), " issue(s). ",
       "See ", report_path, call. = FALSE)
}
cat("Linting passed.\n")
