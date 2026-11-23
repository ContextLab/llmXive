# R Styler configuration
#
# This script defines a minimal Styler configuration for the R portion of the
# project. It can be sourced in an R session or CI step to enforce a consistent
# style across R scripts.
#
# The Styler package is expected to be installed in the R environment (see
# `init_r_environment.py`). The configuration simply applies the default styling
# rules to all R source files in the repository.
#
if (requireNamespace("styler", quietly = TRUE)) {
  # Apply style to all R files in the repository (excluding hidden directories)
  styler::style_pkg(
    path = here::here(),
    recursive = TRUE,
    exclude = c("^\\.", "^\\.Rproj$", "^\\.git$")
  )
} else {
  warning("Styler package not installed; skipping R code formatting.")
}