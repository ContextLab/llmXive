# .Rprofile: Project-specific startup configuration
# This file ensures the environment is set up correctly on startup.

# Load renv automatically if available
if (file.exists("renv/activate.R")) {
  source("renv/activate.R")
}

# Set options for reproducibility and CI compatibility
options(
  # Use the project-specific library path
  lib.loc = "../.R/library",
  
  # Disable interactive prompts
  interactive = FALSE,
  
  # Set CRAN mirror to a reliable default
  repos = c(CRAN = "https://cloud.r-project.org"),
  
  # Increase warning threshold for cleaner logs in CI
  warn = 1,
  
  # Ensure consistent locale settings
  LC_ALL = "C",
  
  # Disable specific verbose messages during package loading
  warnPartialMatchAttr = FALSE,
  warnPartialMatchDollar = FALSE
)

# Load custom utilities if they exist
if (file.exists("utils.R")) {
  source("utils.R")
}

# Set the working directory to the project root relative to code/
# This ensures paths in scripts are resolved correctly
if (dir.exists("..")) {
  setwd("..")
}

# Print a startup message for debugging
message("Project environment configured successfully.")
