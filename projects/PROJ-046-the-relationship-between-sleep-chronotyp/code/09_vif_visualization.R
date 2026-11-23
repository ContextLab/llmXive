#!/usr/bin/env Rscript
# T037: VIF Visualization
# Depends on: T019 (code/03_analysis.R producing data/derived/ancova_results.csv)
# Output: reports/vif_visualization.png

# Load required libraries
if (!require("tidyverse")) {
  stop("Package 'tidyverse' is required but not installed. Please run renv::restore().")
}

if (!require("ggplot2")) {
  stop("Package 'ggplot2' is required but not installed. Please run renv::restore().")
}

# Define paths
project_root <- rprojroot::find_root(rprojroot::is_r_project)
input_path <- file.path(project_root, "data", "derived", "ancova_results.csv")
output_dir <- file.path(project_root, "reports")
output_path <- file.path(output_dir, "vif_visualization.png")

# Ensure output directory exists
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Check if input file exists
if (!file.exists(input_path)) {
  stop(paste("Input file not found:", input_path, 
             ". Please run code/03_analysis.R (T019) first to generate ANCOVA results with VIF data."))
}

# Read the ANCOVA results
cat("Reading ANCOVA results from:", input_path, "\n")
ancova_data <- read.csv(input_path, stringsAsFactors = FALSE)

# Validate expected columns
required_cols <- c("subscale", "predictor", "vif")
missing_cols <- setdiff(required_cols, names(ancova_data))
if (length(missing_cols) > 0) {
  stop(paste("Input file missing required columns:", paste(missing_cols, collapse = ", ")))
}

# Filter out rows where VIF is NA or not numeric (safety check)
clean_data <- ancova_data %>%
  filter(!is.na(vif) & is.numeric(vif)) %>%
  arrange(subscale, predictor)

if (nrow(clean_data) == 0) {
  stop("No valid VIF data found in the input file after filtering.")
}

cat("Found", nrow(clean_data), "VIF records to visualize.\n")

# Create the bar plot
# Color coding: Red for VIF > 2 (high collinearity), Green for VIF <= 2
plot_data <- clean_data %>%
  mutate(
    collinearity_flag = ifelse(vif > 2, "High (VIF > 2)", "Acceptable (VIF <= 2)"),
    subscale = factor(subscale, levels = unique(subscale))
  )

p <- ggplot(plot_data, aes(x = predictor, y = vif, fill = collinearity_flag)) +
  geom_bar(stat = "identity", width = 0.7) +
  facet_wrap(~ subscale, scales = "free_x") +
  scale_fill_manual(values = c("High (VIF > 2)" = "#D55E00", "Acceptable (VIF <= 2)" = "#0072B2")) +
  labs(
    title = "Variance Inflation Factors (VIF) by MFQ Subscale",
    subtitle = "Red bars indicate VIF > 2, suggesting potential multicollinearity issues.",
    x = "Predictor",
    y = "VIF Value",
    fill = "Collinearity Status"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    axis.text.x = element_text(angle = 45, hjust = 1),
    strip.background = element_rect(fill = "grey90", color = "grey50"),
    legend.position = "bottom"
  )

# Save the plot
cat("Saving visualization to:", output_path, "\n")
ggsave(
  filename = output_path,
  plot = p,
  width = 10,
  height = 8,
  dpi = 300,
  bg = "white"
)

cat("VIF visualization successfully generated.\n")
cat("Next step: Ensure code/04_report.Rmd includes this image.\n")