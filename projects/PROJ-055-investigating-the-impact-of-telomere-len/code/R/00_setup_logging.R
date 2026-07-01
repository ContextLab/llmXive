# R logging configuration for the telomere-lifespan project
# This script sets up logging infrastructure for R components
# that are called from Python via rpy2.

# Load required packages
if (!require("logger", quietly = TRUE)) {
  install.packages("logger", repos = "https://cloud.r-project.org")
  library(logger)
}

# Set up logging format
log_formatter <- function(level, message, ...) {
  paste0(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " [", level, "] ", message)
}

# Configure appender to write to logs directory
setup_r_logging <- function(log_file = NULL) {
  # Create logs directory if it doesn't exist
  log_dir <- "logs"
  if (!dir.exists(log_dir)) {
    dir.create(log_dir, recursive = TRUE)
  }
  
  # Generate log filename if not provided
  if (is.null(log_file)) {
    timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
    log_file <- paste0("r_pipeline_", timestamp, ".log")
  }
  
  log_path <- file.path(log_dir, log_file)
  
  # Set up appender
  appender_console <- appender_tee(
    appender_console(),
    appender_file(log_path)
  )
  
  # Configure layout
  layout_console <- layout_simple(
    format = "%s [%t] %m",
    timestamp = function() format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  )
  
  # Set global logger configuration
  log_threshold(log_threshold.INFO())
  log_layout(layout_console)
  log_appender(appender_console)
  
  # Log initialization
  log_info(paste("R logging initialized to:", log_path))
  
  return(log_path)
}

# Memory pressure check for R (using memory.limit on Windows or system calls)
check_r_memory_pressure <- function(threshold_gb = 6) {
  # Get current memory usage (platform-dependent)
  if (.Platform$OS.type == "windows") {
    # Windows: memory.limit() returns MB
    current_mb <- memory.limit()
    current_gb <- current_mb / 1024
  } else {
    # Unix-like: use system command
    tryCatch({
      # Get RSS (Resident Set Size) in KB
      rss_kb <- as.numeric(system("ps -o rss= -p $$", intern = TRUE))
      current_gb <- (rss_kb / 1024) / 1024
    }, error = function(e) {
      # Fallback: assume no pressure if we can't determine
      log_warning("Could not determine memory usage, skipping pressure check")
      return(FALSE)
    })
  }
  
  threshold_bytes <- threshold_gb * 1024^3
  current_bytes <- current_gb * 1024^3
  
  pressure_detected <- current_bytes > threshold_bytes
  
  if (pressure_detected) {
    log_warning(paste(
      "R Memory pressure detected:",
      round(current_gb, 2), "GB (threshold:", threshold_gb, "GB)"
    ))
    log_warning("Consider subsampling data or increasing memory limits")
  } else {
    log_debug(paste(
      "R Memory usage:",
      round(current_gb, 2), "GB (",
      round((current_bytes / threshold_bytes) * 100, 1), "% of threshold)"
    ))
  }
  
  return(pressure_detected)
}

# Example usage when sourced
if (interactive()) {
  log_path <- setup_r_logging()
  log_info("R logging configuration test complete")
  check_r_memory_pressure()
}
