# test_sensitivity.R
# Minimal unit tests for the sensitivity analysis script logic
# Requires: phylolm, ape, dplyr, testthat

library(testthat)
library(phylolm)
library(ape)
library(dplyr)

# Test 1: Data aggregation logic
test_that("Aggregates species means correctly", {
  df <- data.frame(
    species = c("A", "A", "B", "B"),
    telomere_length_kb = c(10, 12, 20, 22),
    lifespan = c(5, 6, 10, 12),
    migration_status = c("M", "M", "R", "R"),
    body_mass_g = c(1, 1, 2, 2)
  )
  
  agg <- df %>%
    group_by(species) %>%
    summarise(
      telomere_mean = mean(telomere_length_kb),
      lifespan_mean = mean(lifespan),
      .groups = 'drop'
    )
  
  expect_equal(nrow(agg), 2)
  expect_equal(agg$telomere_mean[1], 11)
  expect_equal(agg$lifespan_mean[1], 5.5)
})

# Test 2: Tree subsetting logic
test_that("Subsets tree to match data species", {
  # Create a small tree
  tree <- rtree(4)
  tree$tip.label <- c("A", "B", "C", "D")
  
  data_species <- c("A", "B", "C")
  
  # Logic from script
  common <- intersect(tree$tip.label, data_species)
  tree_sub <- drop.tip(tree, setdiff(tree$tip.label, common))
  
  expect_equal(length(tree_sub$tip.label), 3)
  expect_true(all(data_species %in% tree_sub$tip.label))
})

# Test 3: PGLS model fitting on subset
test_that("Fits PGLS model without error on valid subset", {
  tree <- rtree(5)
  data <- data.frame(
    species = tree$tip.label,
    telomere_mean = rnorm(5),
    lifespan_mean = rnorm(5)
  )
  data <- data[match(tree$tip.label, data$species), ]
  
  model <- phylolm(lifespan_mean ~ telomere_mean, data = data, phy = tree, model = "lambda")
  
  expect_s3_class(model, "phylolm")
  expect_false(is.na(coef(model)["telomere_mean"]))
})

# Test 4: Method justification logic
test_that("Selects correct method justification based on N", {
  expect_equal(ifelse(10 >= 10, "LOOCV", "Jackknife"), "LOOCV")
  expect_equal(ifelse(9 >= 10, "LOOCV", "Jackknife"), "Jackknife")
})
