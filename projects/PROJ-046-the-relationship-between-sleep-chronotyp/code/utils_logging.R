# utils_logging.R
# Logging infrastructure for the chronotype-moral-judgement pipeline.
# Provides consistent logging, warning, and abort mechanisms.

# Global log file path (can be overridden by environment variable)
get_log_file <- function() {
  env_log <- Sys.getenv("LOG_FILE", unset = "logs/pipeline.log")
  if (!file.exists(dirname(env_log))) {
    dir.create(dirname(env_log), recursive = TRUE)
  }
  return(env_log)
}

# Initialize logging (creates log file and directory if needed)
init_logging <- function() {
  log_file <- get_log_file()
  if (!file.exists(log_file)) {
    file.create(log_file)
  }
  message("Logging initialized to: ", log_file)
}

# Write a log message to the log file and console
log_message <- function(msg, level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  log_line <- sprintf("[%s] [%s] %s", timestamp, level, msg)
  
  # Write to log file
  log_file <- get_log_file()
  writeLines(log_line, log_file, sep = "\n", append = TRUE)
  
  # Print to console
  cat(log_line, "\n")
}

# Log a warning
log_warning <- function(msg) {
  log_message(msg, level = "WARNING")
}

# Log an error
log_error <- function(msg) {
  log_message(msg, level = "ERROR")
}

# Log an abort condition and terminate the script
log_abort <- function(msg) {
  log_message(msg, level = "ABORT")
  
  # Create an error flag file if specified in environment
  error_flag <- Sys.getenv("ERROR_FLAG_FILE", unset = "logs/pipeline_error.flag")
  if (error_flag != "") {
    writeLines(paste(Sys.time(), msg), error_flag)
  }
  
  # Terminate the script
  stop(paste("PIPELINE ABORT:", msg))
}

# Log a debug message (only if DEBUG mode is enabled)
log_debug <- function(msg) {
  debug_mode <- Sys.getenv("DEBUG", unset = "FALSE")
  if (debug_mode == "TRUE") {
    log_message(msg, level = "DEBUG")
  }
}

# Initialize logging on load
init_logging()
