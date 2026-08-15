# R Environment Setup Script for PROJ-002
# Installs required R packages if not already present

required_packages <- c("phylolm", "ape", "data.table", "ggplot2")

install_if_missing <- function(pkg) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    message(paste("Installing", pkg, "..."))
    install.packages(pkg, repos = "https://cloud.r-project.org/")
    library(pkg, character.only = TRUE)
  }
}

sapply(required_packages, install_if_missing)

message("R environment setup complete.")
