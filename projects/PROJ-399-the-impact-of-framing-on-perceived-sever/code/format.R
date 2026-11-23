#!/usr/bin/env Rscript
# T003: Automatic code formatting for R sources using styler.
# Usage: Rscript code/format.R [--check]
#   default : rewrites files in place (tidyverse style)
#   --check : only report files that would change; exit non-zero if any

args <- commandArgs(trailingOnly = TRUE)
check_only <- "--check" %in% args

if (!requireNamespace("styler", quietly = TRUE)) {
  stop("Required package 'styler' is not installed. ",
       "Install it with: install.packages('styler')", call. = FALSE)
}

script_path <- tryCatch(
  normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))),
  error = function(e) NULL
)
if (is.null(script_path) || !nzchar(script_path)) {
  script_path <- "code/format.R"
}
code_dir <- dirname(script_path)

r_files <- list.files(
  code_dir, pattern = "\\.[Rr]$", full.names = TRUE, recursive = TRUE
)
r_files <- r_files[basename(r_files) != "format.R"]
if (length(r_files) == 0) {
  stop("No R source files found to format in: ", code_dir, call. = FALSE)
}

cat(if (check_only) "Checking" else "Formatting", length(r_files),
    "R file(s) with styler...\n")

any_changed <- FALSE
for (f in r_files) {
  if (check_only) {
    changed <- styler::style_file(f, dry = "fail")
    if (!isTRUE(changed)) {
      cat("Would reformat:", basename(f), "\n")
      any_changed <- TRUE
    }
  } else {
    styler::style_file(f)
  }
}

if (check_only && any_changed) {
  stop("Formatting check failed: files above deviate from styler style. ",
       "Run 'Rscript code/format.R' to fix.", call. = FALSE)
}
cat("Formatting ", if (check_only) "check passed.\n" else "complete.\n")
