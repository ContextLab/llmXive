#!/usr/bin/env Rscript

# 02_sensitivity.R
# Performs LOOCV (if species count >= 10) or jackknife sensitivity analysis (if species count < 10)
# Outputs: results/sensitivity_log.csv

library(phylolm)
library(ape)
library(dplyr)
library(readr)

# --- Configuration ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript 02_sensitivity.R <merged_data_path> <tree_path> <output_path>")
}

merged_data_path <- args[1]
tree_path <- args[2]
output_path <- args[3]

# Ensure output directory exists
output_dir <- dirname(output_path)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# --- Load Data ---
message("Loading merged data from ", merged_data_path)
data <- read_csv(merged_data_path, show_col_types = FALSE)

# Check for required columns
required_cols <- c("species", "telomere_length_kb", "lifespan", "migration_status", "body_mass_g")
if (!all(required_cols %in% names(data))) {
  stop("Missing required columns in merged data. Found: ", paste(names(data), collapse = ", "))
}

# Aggregate by species means (as per T027B requirement mentioned in tasks.md)
# The model requires one row per species for the PGLS
species_data <- data %>%
  group_by(species) %>%
  summarise(
    telomere_mean = mean(telomere_length_kb, na.rm = TRUE),
    lifespan_mean = mean(lifespan, na.rm = TRUE),
    migration_status = first(migration_status),
    body_mass_mean = mean(body_mass_g, na.rm = TRUE),
    .groups = 'drop'
  )

# Remove rows with NA in key variables
species_data <- species_data %>%
  filter(!is.na(telomere_mean) & !is.na(lifespan_mean))

n_species <- nrow(species_data)
message("Processing ", n_species, " unique species for sensitivity analysis.")

message("Loading phylogenetic tree from ", tree_path)
tree <- read.tree(tree_path)

# Ensure tree tip labels match data species names
# We subset the tree to only include species present in our data
common_species <- intersect(tree$tip.label, species_data$species)
if (length(common_species) == 0) {
  stop("No common species found between tree and data.")
}

tree_subset <- drop.tip(tree, setdiff(tree$tip.label, common_species))
species_data_subset <- species_data[species_data$species %in% common_species, ]

# Reorder data to match tree tip labels
species_data_subset <- species_data_subset[match(tree_subset$tip.label, species_data_subset$species), ]

# Verify alignment
if (!all(species_data_subset$species == tree_subset$tip.label)) {
  stop("Species order mismatch after subsetting.")
}

# --- Sensitivity Analysis Logic ---
# Determine method: LOOCV if >= 10 species, otherwise Jackknife (leave-one-out is effectively jackknife here, 
# but we will label it appropriately based on the task description's distinction)
# Task says: "LOOCV (if species count >= 10) or jackknife sensitivity analysis (if species count < 10)"
# We will implement leave-one-out for both, but label the justification string.

method_justification <- ifelse(n_species >= 10, "LOOCV", "Jackknife")
message("Using method: ", method_justification, " (N = ", n_species, ")")

results <- list()

# Prepare results dataframe
res_df <- data.frame(
  species_id = character(),
  coefficient = numeric(),
  se = numeric(),
  p_value = numeric(),
  method_justification = character(),
  stringsAsFactors = FALSE
)

# Iterate: Leave one species out
for (i in 1:n_species) {
  # Remove species i
  current_species <- species_data_subset$species[i]
  subset_data <- species_data_subset[-i, ]
  subset_tree <- drop.tip(tree_subset, current_species)
  
  # Re-order subset data to match subset tree
  subset_data <- subset_data[match(subset_tree$tip.label, subset_data$species), ]
  
  # Fit PGLS model: lifespan ~ telomere_length
  # Using phylolm with default Brownian motion or iterative lambda if needed
  # The base model used phylolm, so we stick to it.
  tryCatch({
    model <- phylolm(lifespan_mean ~ telomere_mean, 
                     data = subset_data, 
                     phy = subset_tree, 
                     model = "lambda") # Estimate lambda iteratively as per T023 logic
      
    # Extract stats
    coef_val <- coef(model)["telomere_mean"]
    se_val <- sqrt(vcov(model)["telomere_mean", "telomere_mean"])
    p_val <- summary(model)$coefficients["telomere_mean", "Pr(>|t|)"]
    
    res_df <- rbind(res_df, data.frame(
      species_id = current_species,
      coefficient = coef_val,
      se = se_val,
      p_value = p_val,
      method_justification = method_justification,
      stringsAsFactors = FALSE
    ))
    
    message("  Processed: ", current_species, " (N=", nrow(subset_data), ")")
    
  }, error = function(e) {
    message("  Warning: Failed to fit model for exclusion of ", current_species, ": ", e$message)
    # Record NA for failed iterations to maintain log integrity
    res_df <- rbind(res_df, data.frame(
      species_id = current_species,
      coefficient = NA_real_,
      se = NA_real_,
      p_value = NA_real_,
      method_justification = method_justification,
      stringsAsFactors = FALSE
    ))
  })
}

# --- Save Output ---
message("Saving sensitivity log to ", output_path)
write_csv(res_df, output_path)

message("Sensitivity analysis complete. ", nrow(res_df), " records written.")
message("Method justification used: ", method_justification)

# Exit cleanly
quit(save = "no", status = 0)
