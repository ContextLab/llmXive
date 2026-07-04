# code/utils.R
# Utility functions for the project.
# Extends existing functionality if necessary, but primarily serves as a
# helper if 04_export.R needs to load config or set seeds.

library(yaml)
library(purrr)

load_config <- function(path = "code/config.yaml") {
  if (!file.exists(path)) {
    stop(paste("Config file not found:", path))
  }
  yaml::read_yaml(path)
}

set_random_seed <- function(seed = NULL) {
  if (is.null(seed)) {
    config <- load_config()
    seed <- config$seed
  }
  set.seed(seed)
  cat(sprintf("Random seed set to: %d\n", seed))
}

validate_stimulus_columns <- function(df, required_cols) {
  missing <- setdiff(required_cols, names(df))
  if (length(missing) > 0) {
    stop(paste("Missing required columns:", paste(missing, collapse = ", ")))
  }
  return(TRUE)
}

validate_stimulus_data_integrity <- function(df) {
  # Placeholder for specific integrity checks
  if (nrow(df) == 0) {
    stop("Data frame is empty.")
  }
  return(TRUE)
}

# Helper to safely extract coefficients from glm/lmer models
safe_extract_coef <- function(model, term_name) {
  s <- summary(model)
  coefs <- coef(s)
  # Try to match term_name exactly or as a prefix if levels vary
  matching_rows <- grep(term_name, rownames(coefs), value = TRUE)
  if (length(matching_rows) == 0) {
    return(NULL)
  }
  # Return the first match
  return(coefs[matching_rows[1], ])
}