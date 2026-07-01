# T002/T003: Project configuration for llmXive
# This file sets global options and initializes the project environment

# Disable stringsAsFactors by default (R 4.0+ default is FALSE, but explicit is better)
options(stringsAsFactors = FALSE)

# Load 'here' to define project root relative to this file
if (requireNamespace("here", quietly = TRUE)) {
  # Set the project root to the parent directory of src/code
  # This ensures paths like here::here("data", "raw") work correctly
  Sys.setenv(R_PROJECT_ROOT = here::here(".."))
  message("Project root set via here::here(): ", Sys.getenv("R_PROJECT_ROOT"))
} else {
  message("Warning: 'here' package not found. R_PROJECT_ROOT may not be set correctly.")
}

# Set a consistent locale for date parsing if possible
tryCatch({
  Sys.setlocale("LC_TIME", "C")
}, error = function(e) {
  message("Could not set LC_TIME locale to C: ", e$message)
})

# Ensure renv is loaded if available
if (requireNamespace("renv", quietly = TRUE)) {
  renv::load()
}

message("Rprofile loaded successfully for llmXive project.")
