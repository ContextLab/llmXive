# R Profile for PROJ-450
# Task: T003
# Sets global options and project root

# Set stringsAsFactors to FALSE globally
options(stringsAsFactors = FALSE)

# Define project root using here::here()
# This ensures relative paths work consistently across the project
if (requireNamespace("here", quietly = TRUE)) {
  # The here package automatically detects the project root from the
  # .Rproj file or git root. We can just call here() to confirm or set options.
  # No need to assign it to a global variable unless needed for specific paths.
  # However, setting the option for 'here' if needed:
  # options(here_start = here()) 
} else {
  warning("Package 'here' is not installed. Relative paths may not work as expected.")
}

# Optional: Set a custom prompt
# options(prompt = "PROJ450> ")
