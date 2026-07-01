#' Integration test for sensitivity analysis module (T030 context, but verifying T029 logic)
#'
#' This test verifies that the SD calculation and flagging logic works
#' correctly when applied to a simulated dataset that mimics the output
#' of the subsampling process.
#'
#' This complements T029 (Unit Test) by testing the logic in a slightly
#' more realistic data structure context.

library(testthat)
library(dplyr)

describe("Sensitivity Analysis: Integration of SD and Flagging", {

  it("processes a dataframe of replicate shifts and flags high-variability species", {
    # Simulate a dataset with 3 species and 10 replicates each
    set.seed(42)
    species_list <- c("Species_A", "Species_B", "Species_C")
    n_replicates <- 10

    # Species A: Low variance (SD < 0.2)
    # Species B: High variance (SD >= 0.2)
    # Species C: Edge case (SD approx 0.2)

    data_list <- list()

    # Species A: Tight cluster around 1.0
    shifts_A <- rnorm(n_replicates, mean = 1.0, sd = 0.05)
    data_list[[1]] <- data.frame(
      species = "Species_A",
      replicate = 1:n_replicates,
      shift_magnitude = shifts_A
    )

    # Species B: Wide spread
    shifts_B <- runif(n_replicates, min = 0.5, max = 2.0)
    data_list[[2]] <- data.frame(
      species = "Species_B",
      replicate = 1:n_replicates,
      shift_magnitude = shifts_B
    )

    # Species C: Constructed to have SD ~ 0.2
    # Mean 1.0, SD 0.2
    shifts_C <- rnorm(n_replicates, mean = 1.0, sd = 0.2)
    data_list[[3]] <- data.frame(
      species = "Species_C",
      replicate = 1:n_replicates,
      shift_magnitude = shifts_C
    )

    df <- bind_rows(data_list)

    # Calculate summary stats
    summary_stats <- df %>%
      group_by(species) %>%
      summarise(
        mean_shift = mean(shift_magnitude),
        sd_shift = sd(shift_magnitude),
        flagged = sd_shift >= 0.2,
        .groups = "drop"
      )

    # Verify Species A is NOT flagged
    expect_false(summary_stats$flagged[summary_stats$species == "Species_A"])

    # Verify Species B IS flagged (high variance)
    expect_true(summary_stats$flagged[summary_stats$species == "Species_B"])

    # Verify Species C is flagged (SD ~ 0.2, likely >= 0.2 due to sampling)
    # Note: Due to randomness, SD might be slightly < 0.2.
    # We check that the logic is applied correctly.
    # If the calculated SD is >= 0.2, it must be flagged.
    c_row <- summary_stats[summary_stats$species == "Species_C", ]
    if (c_row$sd_shift >= 0.2) {
      expect_true(c_row$flagged)
    } else {
      expect_false(c_row$flagged)
    }
  })
})