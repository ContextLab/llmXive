# R profile for PROJ-399
# Sets up linting hooks and project-specific configurations

# Load project-specific options
options(
  lintr.linter_file = ".lintr",
  lintr.exclude = c("data/", "results/"),
  lintr.diagnostics = TRUE,
  lintr.diagnostics_on_save = TRUE
)

# Set working directory to project root if running from code/
if (getwd() == file.path(getwd(), "code")) {
  setwd("..")
}

# Load renv if available
if (requireNamespace("renv", quietly = TRUE)) {
  renv::load()
}

# Define linting helper function
run_lint <- function(path = ".") {
  if (!requireNamespace("lintr", quietly = TRUE)) {
    stop("lintr package is required but not installed. Please install it: install.packages('lintr')")
  }
  
  results <- lintr::lint_dir(path = path, linter = lintr::lint_dir, cache = TRUE)
  
  if (length(results) > 0) {
    cat("Linting issues found:\n")
    print(results)
    return(FALSE)
  } else {
    cat("No linting issues found.\n")
    return(TRUE)
  }
}

# Define format helper function
format_code <- function(path = ".") {
  if (!requireNamespace("styler", quietly = TRUE)) {
    stop("styler package is required but not installed. Please install it: install.packages('styler')")
  }
  
  cat("Formatting R files in", path, "\n")
  styled <- styler::style_dir(path = path, recurse = TRUE, dry = "fail")
  cat("Formatting complete.\n")
  return(TRUE)
}

# Print startup message
cat("PROJ-399 R environment loaded. Use run_lint() and format_code() helpers.\n")
