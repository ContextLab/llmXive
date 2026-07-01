#' @description
#' Generate plots for niche shift analysis.
#' Creates scatter plot of Delta N vs Delta T.
plotting.R

# Source utilities
source("src/code/utils.R")

#' @description
#' Generate scatter plot of niche shift vs warming.
#' @param data_path Character, path to data with shifts.
#' @param output_path Character, path to save PNG.
#' @param width Integer, plot width in pixels.
#' @param height Integer, plot height in pixels.
generate_shift_plot <- function(data_path = "data/processed/centroids.csv",
                                output_path = "results/shift_plot.png",
                                width = 1200,
                                height = 800) {

  # Initialize logging
  init_logging("plotting.log")
  log_info("Starting plot generation")

  ensure_dir(dirname(output_path))

  # Load data
  if (!file.exists(data_path)) {
    log_error(sprintf("Data file not found: %s", data_path))
    stop("Input data missing")
  }

  log_info(sprintf("Loading data from %s", data_path))
  df <- read.csv(data_path, stringsAsFactors = FALSE)

  # Check for required columns
  if (!all(c("delta_N", "delta_T") %in% names(df))) {
    log_error("Missing delta columns in data")
    stop("Data schema mismatch")
  }

  # Log plot parameters
  log_info(sprintf("Generating scatter plot: Delta N vs Delta T"))
  log_info(sprintf("Resolution: %dx%d px", width, height))

  # Create plot
  # Using base R for simplicity, or ggplot2 if available
  # Assuming ggplot2 is installed (T002)
  if (requireNamespace("ggplot2", quietly = TRUE)) {
    log_info("Using ggplot2 for rendering")
    p <- ggplot2::ggplot(df, ggplot2::aes(x = delta_T, y = delta_N)) +
      ggplot2::geom_point(size = 2, alpha = 0.6) +
      ggplot2::labs(title = "Niche Shift vs Regional Warming",
                    x = expression(Delta*T),
                    y = expression(Delta*N)) +
      ggplot2::theme_minimal()

    log_info("Plot object created")

    # Save plot
    ggplot2::ggsave(output_path, plot = p, width = width/72, height = height/72, dpi = 72)
  } else {
    log_warn("ggplot2 not found. Using base R plotting.")
    png(output_path, width = width, height = height)
    plot(df$delta_T, df$delta_N,
         main = "Niche Shift vs Regional Warming",
         xlab = expression(Delta*T),
         ylab = expression(Delta*N),
         pch = 19, col = rgb(0, 0, 1, 0.5))
    dev.off()
  }

  log_info(sprintf("Plot saved to %s", output_path))

  return(invisible(TRUE))
}