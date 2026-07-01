# utils.R
# Utility functions for the project (Task T004)

log_msg <- function(msg, level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  cat(sprintf("[%s] [%s] %s\n", timestamp, level, msg))
}

ensure_dir <- function(dir_path) {
  if (!dir.exists(dir_path)) {
    dir.create(dir_path, recursive = TRUE)
    log_msg(paste("Created directory:", dir_path))
  }
  return(dir_path)
}

validate_coordinate <- function(lat, lon, max_uncertainty_km = 10) {
  # Basic validation for coordinate presence and range
  if (is.na(lat) || is.na(lon)) return(FALSE)
  if (lat < -90 || lat > 90) return(FALSE)
  if (lon < -180 || lon > 180) return(FALSE)
  # Note: Uncertainty check requires a specific field, skipped here for basic validity
  return(TRUE)
}

handle_na_climate <- function(val, default = NA) {
  if (is.na(val)) {
    return(default)
  }
  return(val)
}
