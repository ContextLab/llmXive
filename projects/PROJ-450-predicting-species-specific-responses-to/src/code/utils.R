# src/code/utils.R
# Shared utilities for logging, directory creation, and data validation.
# Task: T004 (Enhanced) and T009 (Tested)

# --- Logging ---
init_logging <- function(prefix = "project") {
  log_file <- file.path("logs", paste0(prefix, "_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".log"))
  create_dir_if_missing("logs")
  con <- file(log_file, open = "a")
  return(con)
}

log_message <- function(con, level, msg) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  line <- paste0("[", timestamp, "] [", level, "] ", msg, "\n")
  writeLines(line, con)
}

log_info <- function(con, msg) log_message(con, "INFO", msg)
log_warning <- function(con, msg) log_message(con, "WARNING", msg)
log_error <- function(con, msg) log_message(con, "ERROR", msg)

close_log <- function(con) {
  close(con)
}

# --- Directory Creation ---
create_dir_if_missing <- function(dir_path) {
  if (!dir.exists(dir_path)) {
    dir.create(dir_path, recursive = TRUE)
  }
}

# --- Checksum Validation ---
compute_checksum <- function(file_path, algo = "md5") {
  if (!file.exists(file_path)) return(NA)
  # Use tools::md5sum or digest package if available. 
  # Base R has tools::md5sum
  tryCatch({
    tools::md5sum(file_path)
  }, error = function(e) {
    NA
  })
}

validate_checksum <- function(file_path, expected_checksum) {
  if (is.na(expected_checksum)) return(TRUE)
  actual <- compute_checksum(file_path)
  return(identical(actual, expected_checksum))
}

# --- Data Validation ---

# Handle missing climate values (NA)
# Returns a logical vector indicating if a value is valid (not NA)
is_valid_climate <- function(value) {
  !is.na(value)
}

# Coordinate precision check (>10km uncertainty)
# GBIF has a 'coordinateUncertaintyInMeters' field.
# 10km = 10,000 meters.
# We assume the dataframe has a column 'coordinateUncertaintyInMeters' or similar.
# If not present, we assume it's valid (or NA -> invalid).
check_coordinate_precision <- function(df, uncertainty_col = "coordinateUncertaintyInMeters", threshold_m = 10000) {
  if (!uncertainty_col %in% colnames(df)) {
    # If column missing, we can't check. Return all TRUE or all FALSE?
    # Conservative: assume valid if no data, or mark as warning.
    # For this task, we return TRUE (assume valid) if column missing.
    return(rep(TRUE, nrow(df)))
  }
  
  # Filter: uncertainty <= threshold OR uncertainty is NA (unknown)
  # If we strictly require < 10km and we don't know, we might exclude.
  # But usually, if uncertainty is not reported, we can't exclude.
  # Let's assume: if uncertainty is NA, we keep it (conservative).
  # If uncertainty is reported and > 10000, we exclude.
  
  valid <- is.na(df[[uncertainty_col]]) | (df[[uncertainty_col]] <= threshold_m)
  return(valid)
}

# Validate coordinates (lat/lon not NA, not 0,0)
validate_coordinates <- function(df, lat_col = "decimalLatitude", lon_col = "decimalLongitude") {
  if (!all(c(lat_col, lon_col) %in% colnames(df))) {
    return(rep(FALSE, nrow(df)))
  }
  
  valid <- !is.na(df[[lat_col]]) & !is.na(df[[lon_col]]) &
           (abs(df[[lat_col]]) > 0.01 | abs(df[[lon_col]]) > 0.01) # Avoid 0,0
  
  return(valid)
}
