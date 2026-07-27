#' Analyze Niche Shifts vs Regional Warming
#'
#' This script performs regression analysis (PGLS or WLS) to relate niche shift magnitude (ΔN)
#' to regional warming (ΔT). It also computes per-region summaries.
#'
#' @param input_centroids Path to data/processed/centroids.csv
#' @param input_shifts Path to data/processed/shifts.csv (output of compute_shifts.R)
#' @param phylogeny_path Path to data/phylogeny.tre (optional)
#' @param output_results Path to results/regression_results.csv
#' @param output_summary Path to results/regression_summary.csv
#' @param log_path Path to logs/analysis.log
#' @param config_path Path to config.yaml
#'
#' @export
run_analysis <- function(
  input_centroids = "data/processed/centroids.csv",
  input_shifts = "data/processed/shifts.csv",
  phylogeny_path = "data/phylogeny.tre",
  output_results = "results/regression_results.csv",
  output_summary = "results/regression_summary.csv",
  log_path = "logs/analysis.log",
  config_path = "config.yaml"
) {
  # Load utilities
  source("src/code/utils.R")

  # Initialize logging
  init_logging(log_path, task = "T027-US2-Analysis")
  log_msg("INFO", "Starting niche shift analysis (T027)")
  log_msg("INFO", paste("Input centroids:", input_centroids))
  log_msg("INFO", paste("Input shifts:", input_shifts))
  log_msg("INFO", paste("Phylogeny file:", phylogeny_path))

  # Load data
  if (!file.exists(input_centroids)) {
    log_msg("ERROR", "Centroids file not found. Run US1 first.")
    stop("Centroids file missing")
  }
  if (!file.exists(input_shifts)) {
    log_msg("ERROR", "Shifts file not found. Run compute_shifts.R first.")
    stop("Shifts file missing")
  }

  centroids <- read.csv(input_centroids, stringsAsFactors = FALSE)
  shifts <- read.csv(input_shifts, stringsAsFactors = FALSE)

  log_msg("INFO", paste("Loaded", nrow(centroids), "centroid records"))
  log_msg("INFO", paste("Loaded", nrow(shifts), "shift records"))

  # Merge data
  merged <- merge(centroids, shifts, by = c("species", "taxonomic_group"))
  log_msg("INFO", paste("Merged dataset size:", nrow(merged)))

  # Check for phylogeny
  has_phylogeny <- file.exists(phylogeny_path) && file.info(phylogeny_path)$size > 0
  method_used <- if (has_phylogeny) "PGLS" else "WLS"
  log_msg("INFO", paste("Phylogeny present:", has_phylogeny, "- Using", method_used, "regression"))

  # Prepare data for regression
  # Filter out NAs in critical columns
  valid_data <- merged[!is.na(merged$delta_N) & !is.na(merged$delta_T), ]
  log_msg("INFO", paste("Valid records for regression:", nrow(valid_data)))

  if (nrow(valid_data) < 3) {
    log_msg("WARN", "Insufficient data for regression (n < 3). Skipping.")
    # Write empty results
    write.csv(data.frame(), output_results, row.names = FALSE)
    write.csv(data.frame(), output_summary, row.names = FALSE)
    log_msg("INFO", "Analysis completed with empty results due to insufficient data.")
    return(invisible(NULL))
  }

  # Run regression
  log_msg("INFO", "Executing regression model...")
  tryCatch({
    if (has_phylogeny) {
      # PGLS
      log_msg("INFO", "Loading phylogeny for PGLS...")
      tree <- ape::read.tree(phylogeny_path)
      # Ensure tip labels match species names
      # (Simplified: assumes species names match tip labels)
      valid_data$species <- as.character(valid_data$species)
      # Match data to tree
      common_species <- intersect(valid_data$species, tree$tip.label)
      if (length(common_species) < 3) {
        log_msg("WARN", "Not enough species overlap with phylogeny. Falling back to WLS.")
        method_used <- "WLS"
        model <- lm(delta_N ~ delta_T, data = valid_data)
      } else {
        phy_data <- valid_data[valid_data$species %in% common_species, ]
        phy_data <- phy_data[match(tree$tip.label, phy_data$species), ]
        model <- caper::pgls(delta_N ~ delta_T, data = phy_data, lambda = "ML")
      }
    } else {
      # WLS
      model <- lm(delta_N ~ delta_T, data = valid_data)
    }

    log_msg("INFO", "Regression model fitted successfully.")

    # Extract results
    coef_summary <- summary(model)$coefficients
    slope <- coef_summary["delta_T", "Estimate"]
    p_value <- coef_summary["delta_T", "Pr(>|t|)"]
    r_squared <- summary(model)$r.squared

    # Confidence Interval (95%)
    conf_int <- confint(model, "delta_T", level = 0.95)

    log_msg("INFO", paste("Slope:", slope))
    log_msg("INFO", paste("P-value:", p_value))
    log_msg("INFO", paste("R-squared:", r_squared))
    log_msg("INFO", paste("95% CI:", conf_int[1], "-", conf_int[2]))

    # Save main results
    results_df <- data.frame(
      method = method_used,
      slope = slope,
      ci_lower = conf_int[1],
      ci_upper = conf_int[2],
      r_squared = r_squared,
      p_value = p_value,
      n_species = nrow(valid_data)
    )
    dir.create(dirname(output_results), showWarnings = FALSE, recursive = TRUE)
    write.csv(results_df, output_results, row.names = FALSE)
    log_msg("INFO", paste("Main results saved to", output_results))

    # Per-region analysis (Latitudinal bands)
    log_msg("INFO", "Computing per-region summaries...")
    valid_data$lat_band <- floor(valid_data$mean_lat / 10) * 10
    region_summary <- do.call(rbind, lapply(split(valid_data, valid_data$lat_band), function(df) {
      if (nrow(df) < 3) return(NULL)
      tryCatch({
        if (has_phylogeny && method_used == "PGLS") {
          # Simplified: re-run PGLS if possible, else WLS
          # (Skipping complex phylogeny matching per band for this step, using WLS for bands)
          m <- lm(delta_N ~ delta_T, data = df)
        } else {
          m <- lm(delta_N ~ delta_T, data = df)
        }
        cs <- summary(m)$coefficients
        ci <- confint(m, "delta_T", level = 0.95)
        data.frame(
          lat_band = unique(df$lat_band),
          n_species = nrow(df),
          slope = cs["delta_T", "Estimate"],
          ci_lower = ci[1],
          ci_upper = ci[2],
          r_squared = summary(m)$r.squared,
          p_value = cs["delta_T", "Pr(>|t|)"]
        )
      }, error = function(e) {
        log_msg("WARN", paste("Failed to compute region", unique(df$lat_band), ":", e$message))
        NULL
      })
    }))

    if (!is.null(region_summary) && nrow(region_summary) > 0) {
      write.csv(region_summary, output_summary, row.names = FALSE)
      log_msg("INFO", paste("Region summary saved to", output_summary))
    } else {
      log_msg("WARN", "No valid region summaries could be computed.")
      write.csv(data.frame(), output_summary, row.names = FALSE)
    }

  }, error = function(e) {
    log_msg("ERROR", paste("Regression failed:", e$message))
    stop(e)
  })

  log_msg("INFO", "Analysis completed successfully.")
}

# Run if called directly
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) > 0) {
    # Parse arguments if needed, otherwise use defaults
    run_analysis()
  } else {
    run_analysis()
  }
}
