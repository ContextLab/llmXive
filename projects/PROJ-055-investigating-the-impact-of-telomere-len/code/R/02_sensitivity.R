#!/usr/bin/env Rscript

# T026: Sensitivity Analysis (LOOCV or Jackknife)
# Performs Leave-One-Out Cross-Validation (LOOCV) if species count >= 10,
# otherwise performs a Jackknife (leave-one-out) sensitivity analysis.
# Output: results/sensitivity_log.csv

# Load required libraries
if (!require("phylolm", quietly = TRUE)) stop("Package 'phylolm' is required but not installed.")
if (!require("ape", quietly = TRUE)) stop("Package 'ape' is required but not installed.")
if (!require("dplyr", quietly = TRUE)) stop("Package 'dplyr' is required but not installed.")

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript 02_sensitivity.R <merged_data.csv> <tree_file.newick> <output_csv>")
}

data_path <- args[1]
tree_path <- args[2]
output_path <- args[3]

message("Loading data from: ", data_path)
message("Loading tree from: ", tree_path)
message("Output will be saved to: ", output_path)

# Load Data
df <- read.csv(data_path, stringsAsFactors = FALSE)

# Ensure required columns exist
required_cols <- c("species", "telomere_length_kb", "lifespan", "migration_status", "body_mass_g")
if (!all(required_cols %in% names(df))) {
  stop("Input data missing required columns: ", paste(setdiff(required_cols, names(df)), collapse = ", "))
}

# Load Tree
tree <- read.tree(tree_path)

# Check for species overlap
tree_species <- tree$tip.label
data_species <- unique(df$species)

# Map data species to tree tip labels (handling potential naming mismatches if necessary, 
# but assuming strict matching per previous pipeline steps)
common_species <- intersect(data_species, tree_species)

if (length(common_species) < 3) {
  stop("Not enough species overlap between data and tree for modeling (need >= 3). Found: ", length(common_species))
}

# Filter data to common species
df_filtered <- df[df$species %in% common_species, ]

# Aggregate by species if there are multiple records per species (as per US2 logic)
# We take the mean of telomere and lifespan for each species
df_agg <- df_filtered %>%
  group_by(species) %>%
  summarise(
    telomere_length_kb = mean(telomere_length_kb, na.rm = TRUE),
    lifespan = mean(lifespan, na.rm = TRUE),
    migration_status = first(migration_status), # Keep status as is
    body_mass_g = mean(body_mass_g, na.rm = TRUE)
  ) %>%
  ungroup()

# Re-check overlap after aggregation
df_agg <- df_agg[df_agg$species %in% tree_species, ]

n_species <- nrow(df_agg)
message("Total species for analysis: ", n_species)

# Determine Method
if (n_species >= 10) {
  method_justification <- "LOOCV (species count >= 10)"
  method <- "LOOCV"
} else {
  method_justification <- "Jackknife (species count < 10)"
  method <- "Jackknife"
}
message("Selected method: ", method, " (Justification: ", method_justification, ")")

# Prepare results container
results_list <- list()

# Function to fit model on a subset
fit_model <- function(sub_df, sub_tree) {
  # Ensure rownames match tree tip labels for phylolm
  rownames(sub_df) <- sub_df$species
  # Sort data to match tree order if necessary, though phylolm handles matching usually
  # We subset the tree to match the data
  if (!all(sub_df$species %in% sub_tree$tip.label)) {
    stop("Species mismatch in subset")
  }
  sub_tree <- drop.tip(sub_tree, setdiff(sub_tree$tip.label, sub_df$species))
  
  tryCatch({
    # Fit PGLS: lifespan ~ telomere_length
    fit <- phylolm(lifespan ~ telomere_length_kb, data = sub_df, phy = sub_tree, model = "lambda")
    return(fit)
  }, error = function(e) {
    message("Model fitting failed for subset: ", e$message)
    return(NULL)
  })
}

# Loop through each species to leave out
species_ids <- df_agg$species

for (i in seq_along(species_ids)) {
  leave_out <- species_ids[i]
  keep_idx <- which(species_ids != leave_out)
  
  if (length(keep_idx) < 3) {
    # Not enough data to fit model
    results_list[[i]] <- data.frame(
      species_id = leave_out,
      coefficient = NA,
      se = NA,
      p_value = NA,
      method_justification = method_justification,
      status = "Skipped (insufficient data)"
    )
    next
  }
  
  sub_data <- df_agg[keep_idx, ]
  sub_tree <- tree
  
  # Ensure tree tips match sub_data species
  tips_to_drop <- setdiff(sub_tree$tip.label, sub_data$species)
  if (length(tips_to_drop) > 0) {
    sub_tree <- drop.tip(sub_tree, tips_to_drop)
  }
  
  fit <- fit_model(sub_data, sub_tree)
  
  if (is.null(fit)) {
    results_list[[i]] <- data.frame(
      species_id = leave_out,
      coefficient = NA,
      se = NA,
      p_value = NA,
      method_justification = method_justification,
      status = "Fit Error"
    )
    next
  }
  
  # Extract stats
  coefs <- coef(summary(fit))
  # The coefficient for telomere_length_kb is usually the second row
  if (nrow(coefs) >= 2) {
    coef_val <- coefs["telomere_length_kb", "Estimate"]
    se_val <- coefs["telomere_length_kb", "Std. Error"]
    p_val <- coefs["telomere_length_kb", "Pr(>|t|)"]
  } else {
    coef_val <- NA
    se_val <- NA
    p_val <- NA
  }
  
  results_list[[i]] <- data.frame(
    species_id = leave_out,
    coefficient = coef_val,
    se = se_val,
    p_value = p_val,
    method_justification = method_justification,
    status = "OK"
  )
}

# Combine results
final_df <- do.call(rbind, results_list)

# Ensure output directory exists
out_dir <- dirname(output_path)
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE)
}

# Save results
write.csv(final_df, output_path, row.names = FALSE)
message("Sensitivity analysis complete. Results saved to: ", output_path)

# Optional: Print summary
valid_results <- sum(final_df$status == "OK")
message("Successfully fitted models for ", valid_results, " out of ", n_species, " iterations.")