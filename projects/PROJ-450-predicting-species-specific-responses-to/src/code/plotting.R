#' Generate Visualization for Niche Shifts vs Regional Warming
#'
#' Creates a scatter plot of ΔN vs ΔT, colored by taxonomic group.
#'
#' @param input_results Path to results/regression_results.csv
#' @param input_shifts Path to data/processed/shifts.csv
#' @param output_plot Path to figures/shifts_vs_warming.png
#' @param log_path Path to logs/analysis.log
#' @param width Plot width in pixels
#' @param height Plot height in pixels
#'
#' @export
generate_plot <- function(
  input_results = "results/regression_results.csv",
  input_shifts = "data/processed/shifts.csv",
  output_plot = "figures/shifts_vs_warming.png",
  log_path = "logs/analysis.log",
  width = 1200,
  height = 800
) {
  # Load utilities
  source("src/code/utils.R")

  # Initialize logging
  init_logging(log_path, task = "T027-Plotting")
  log_msg("INFO", "Starting plot generation (T027)")
  log_msg("INFO", paste("Input results:", input_results))
  log_msg("INFO", paste("Input shifts:", input_shifts))
  log_msg("INFO", paste("Output plot:", output_plot))

  # Check inputs
  if (!file.exists(input_shifts)) {
    log_msg("ERROR", "Shifts file not found.")
    stop("Shifts file missing")
  }
  if (!file.exists(input_results)) {
    log_msg("WARN", "Results file not found. Plotting will proceed without regression line.")
  }

  # Load data
  shifts <- read.csv(input_shifts, stringsAsFactors = FALSE)
  log_msg("INFO", paste("Loaded", nrow(shifts), "shift records for plotting"))

  # Ensure required columns exist
  required_cols <- c("species", "delta_N", "delta_T", "taxonomic_group")
  missing_cols <- setdiff(required_cols, names(shifts))
  if (length(missing_cols) > 0) {
    log_msg("ERROR", paste("Missing columns:", paste(missing_cols, collapse = ", ")))
    stop("Missing required columns in shifts data")
  }

  # Load results for regression line (optional)
  regression_line <- NULL
  if (file.exists(input_results)) {
    results_df <- read.csv(input_results, stringsAsFactors = FALSE)
    if (nrow(results_df) > 0) {
      regression_line <- results_df[1, ] # Take first row
      log_msg("INFO", "Loaded regression parameters for plot line.")
    }
  }

  # Create plot
  log_msg("INFO", "Constructing ggplot object...")
  p <- ggplot2::ggplot(shifts, ggplot2::aes(x = delta_T, y = delta_N, color = taxonomic_group)) +
    ggplot2::geom_point(size = 3, alpha = 0.7) +
    ggplot2::labs(
      title = "Niche Shift (ΔN) vs Regional Warming (ΔT)",
      x = "Regional Warming (ΔT, °C)",
      y = "Niche Shift Magnitude (ΔN, standard units)",
      color = "Taxonomic Group"
    ) +
    ggplot2::theme_minimal() +
    ggplot2::theme(
      plot.title = ggplot2::element_text(hjust = 0.5, size = 16, face = "bold"),
      axis.title = ggplot2::element_text(size = 12),
      legend.title = ggplot2::element_text(size = 12)
    )

  # Add regression line if available
  if (!is.null(regression_line)) {
    log_msg("INFO", "Adding regression line to plot...")
    slope <- regression_line$slope
    # Estimate intercept from mean values or assume 0 if not provided (simplified)
    # Better: re-run lm if data allows, but here we approximate or use provided stats
    # For robustness, we re-calculate intercept from the data used in regression if possible.
    # Since we don't have the exact model object, we'll skip the line or draw a rough one.
    # To be safe, we'll just log that we have the stats but not draw a potentially wrong line.
    log_msg("INFO", "Regression stats available, but exact intercept not stored. Skipping line overlay to avoid error.")
    # Alternatively, if we had the model object, we'd do:
    # p <- p + ggplot2::geom_abline(intercept = intercept, slope = slope, linetype = "dashed")
  }

  # Save plot
  log_msg("INFO", paste("Saving plot to", output_plot, "with dimensions", width, "x", height))
  dir.create(dirname(output_plot), showWarnings = FALSE, recursive = TRUE)
  ggplot2::ggsave(
    filename = output_plot,
    plot = p,
    width = width / 100, # Convert px to inches (assuming 100 DPI)
    height = height / 100,
    dpi = 100
  )
  log_msg("INFO", "Plot saved successfully.")
}

# Run if called directly
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) > 0) {
    # Parse arguments if needed
    generate_plot()
  } else {
    generate_plot()
  }
}