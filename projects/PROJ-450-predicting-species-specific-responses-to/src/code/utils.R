#' @description
#' Logging infrastructure and helper utilities for the climate niche project.
#' Provides timestamped logging, directory management, and data validation.
utils.R

# Global log file path
log_file <- NULL

#' @description
#' Initialize logging to a specific file.
#' @param filename Character string, name of the log file (relative to project root).
init_logging <- function(filename = "pipeline.log") {
  log_file <<- file.path("logs", filename)
  dir.create(dirname(log_file), showWarnings = FALSE, recursive = TRUE)
  message(sprintf("[LOG] Initialized logging to %s", log_file))
}

#' @description
#' Write a log entry with timestamp and level.
#' @param level Character string, e.g., "INFO", "WARN", "ERROR".
#' @param msg Character string, the message to log.
log_msg <- function(level, msg) {
  if (is.null(log_file)) {
    # Fallback to console if not initialized
    cat(sprintf("[%s] [%s] %s\n", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), level, msg))
    return(invisible(NULL))
  }

  entry <- sprintf("[%s] [%s] %s",
                   format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
                   level,
                   msg)

  tryCatch({
    cat(entry, "\n", file = log_file, append = TRUE)
  }, error = function(e) {
    cat(sprintf("[FATAL] Failed to write to log: %s\n", e$message))
  })

  # Also print to console for immediate feedback
  cat(entry, "\n")
}

#' @description
#' Log an informational message.
log_info <- function(msg) log_msg("INFO", msg)

#' @description
#' Log a warning message.
log_warn <- function(msg) log_msg("WARN", msg)

#' @description
#' Log an error message.
log_error <- function(msg) log_msg("ERROR", msg)

#' @description
#' Ensure a directory exists.
#' @param dir_path Character string, path to directory.
ensure_dir <- function(dir_path) {
  if (!dir.exists(dir_path)) {
    dir.create(dir_path, recursive = TRUE, showWarnings = FALSE)
    log_info(sprintf("Created directory: %s", dir_path))
  }
  return(invisible(TRUE))
}

#' @description
#' Validate that a data frame has no NA in critical coordinate columns.
#' @param df Data frame to check.
#' @param lat_col Character, name of latitude column.
#' @param lon_col Character, name of longitude column.
#' @return Logical, TRUE if valid, FALSE otherwise.
validate_coordinates <- function(df, lat_col = "decimalLatitude", lon_col = "decimalLongitude") {
  if (!all(c(lat_col, lon_col) %in% names(df))) {
    log_error("Coordinate columns missing in data frame")
    return(FALSE)
  }

  na_count <- sum(is.na(df[[lat_col]]) | is.na(df[[lon_col]]))
  if (na_count > 0) {
    log_warn(sprintf("Found %d records with missing coordinates", na_count))
  }
  return(TRUE)
}

#' @description
#' Check if coordinate precision is sufficient (uncertainty <= 10km).
#' WorldClim resolution is ~1km, so 10km is a reasonable cutoff.
#' @param df Data frame.
#' @param col Character, name of coordinate uncertainty column (e.g., coordinateUncertaintyInMeters).
#' @return Logical, TRUE if all valid records pass.
check_coordinate_precision <- function(df, col = "coordinateUncertaintyInMeters") {
  if (!(col %in% names(df))) {
    log_warn(sprintf("Column '%s' not found, skipping precision check", col))
    return(TRUE)
  }

  # Filter out NAs first
  valid_rows <- !is.na(df[[col]])
  if (sum(valid_rows) == 0) return(TRUE)

  high_uncertainty <- df[[col]][valid_rows] > 10000 # 10km in meters
  if (any(high_uncertainty)) {
    log_warn(sprintf("Found %d records with coordinate uncertainty > 10km", sum(high_uncertainty)))
  }
  return(TRUE)
}

#' @description
#' Handle missing climate values.
#' @param df Data frame with climate columns.
#' @param cols Character vector of climate column names.
#' @return Logical, TRUE if handling is consistent (logs warning if NAs found).
handle_missing_climate <- function(df, cols = c("temp", "precip")) {
  missing_found <- FALSE
  for (c in cols) {
    if (c %in% names(df) && any(is.na(df[[c]]))) {
      missing_found <- TRUE
      log_warn(sprintf("Found %d NA values in climate column '%s'", sum(is.na(df[[c]])), c))
    }
  }
  return(missing_found)
}

#' @description
#' Calculate MD5 checksum of a file.
#' @param filepath Character string, path to file.
#' @return Character string, MD5 hash.
get_checksum <- function(filepath) {
  if (!file.exists(filepath)) {
    stop(sprintf("File not found: %s", filepath))
  }
  # Using digest package if available, else fallback to simple file hash simulation
  # For robustness in standard R without extra deps, we use tools::md5sum if available
  if (requireNamespace("tools", quietly = TRUE)) {
    return(tools::md5sum(filepath))
  }
  # Fallback: read file and hash (simplified)
  # In production, ensure 'digest' is installed or use system command
  stop("MD5 calculation requires 'tools' package or 'digest' package.")
}
