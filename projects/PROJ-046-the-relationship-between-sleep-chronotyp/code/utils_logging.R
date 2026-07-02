# utils_logging.R
# Logging infrastructure for the Chronotype-Moral Judgement pipeline.
# Provides functions for warnings, informational messages, and fatal aborts.
# All logs are written to the project's logs directory.

# Ensure dependencies are loaded (base R only for this utility)
# No external packages required for basic file I/O and logging.

#' Get the log directory path
#'
#' Retrieves the path to the logs directory, creating it if it doesn't exist.
#' Uses the LOGS_DIR environment variable if set, otherwise defaults to "logs".
#'
#' @return Character string of the absolute path to the logs directory.
get_log_dir <- function() {
  log_dir <- Sys.getenv("LOGS_DIR", unset = "logs")
  if (!dir.exists(log_dir)) {
    dir.create(log_dir, recursive = TRUE, showWarnings = FALSE)
  }
  return(log_dir)
}

#' Generate a timestamped log prefix
#'
#' @param level Character string representing the log level (INFO, WARN, ERROR).
#' @return Character string formatted as "[YYYY-MM-DD HH:MM:SS] [LEVEL] "
get_log_prefix <- function(level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  return(sprintf("[%s] [%s] ", timestamp, level))
}

#' Log a message to the console and a file
#'
#' Writes a formatted message to the console (cat) and appends it to the
#' specified log file in the logs directory.
#'
#' @param message Character string of the message content.
#' @param level Character string: "INFO", "WARN", or "ERROR".
#' @param log_file Character string (optional). Filename in the logs directory.
#'                 Defaults to "pipeline.log".
log_message <- function(message, level = "INFO", log_file = "pipeline.log") {
  prefix <- get_log_prefix(level)
  full_message <- paste0(prefix, message)

  # Write to console
  cat(full_message, "\n", sep = "")

  # Write to file
  log_path <- file.path(get_log_dir(), log_file)
  cat(full_message, "\n", sep = "", file = log_path, append = TRUE)
}

#' Log a warning
#'
#' Wrapper for log_message with level "WARN". Also triggers a standard R warning.
#'
#' @param message Character string of the warning message.
#' @param log_file Character string. Defaults to "pipeline.log".
log_warn <- function(message, log_file = "pipeline.log") {
  log_message(message, level = "WARN", log_file = log_file)
  warning(message, call. = FALSE)
}

#' Log an informational message
#'
#' Wrapper for log_message with level "INFO".
#'
#' @param message Character string of the info message.
#' @param log_file Character string. Defaults to "pipeline.log".
log_info <- function(message, log_file = "pipeline.log") {
  log_message(message, level = "INFO", log_file = log_file)
}

#' Log an error and abort execution
#'
#' Writes an error message to the log file and the console, then stops
#' execution of the script using stop().
#'
#' @param message Character string of the error message.
#' @param log_file Character string. Defaults to "pipeline.log".
#' @param code Integer (optional). Error code to append to the message.
log_abort <- function(message, log_file = "pipeline.log", code = NULL) {
  if (!is.null(code)) {
    message <- sprintf("Error (Code %d): %s", code, message)
  }
  log_message(message, level = "ERROR", log_file = log_file)
  stop(message, call. = FALSE)
}

#' Log a specific exclusion event
#'
#' Helper function to log data exclusions to a dedicated exclusion log file.
#'
#' @param reason Character string explaining why the row was excluded.
#' @param row_id Character or integer identifier for the row (optional).
#' @param log_file Character string. Defaults to "exclusions.log".
log_exclusion <- function(reason, row_id = NULL, log_file = "exclusions.log") {
  if (!is.null(row_id)) {
    msg <- sprintf("Row %s excluded: %s", row_id, reason)
  } else {
    msg <- sprintf("Exclusion: %s", reason)
  }
  log_message(msg, level = "WARN", log_file = log_file)
}

#' Initialize the logging system
#'
#' Ensures the log directory exists and writes a startup message.
#' Can be called at the beginning of any pipeline script.
#'
#' @param log_file Character string. Defaults to "pipeline.log".
init_logging <- function(log_file = "pipeline.log") {
  # Ensure directory exists
  _ <- get_log_dir()
  log_info("Logging system initialized.")
}