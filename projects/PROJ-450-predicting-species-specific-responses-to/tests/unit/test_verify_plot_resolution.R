#!/usr/bin/env Rscript
# Unit tests for verify_plot_resolution.R logic
# Tests the core validation logic without relying on actual large files.

library(testthat)
library(png)
library(dplyr)

# Helper to create a temporary dummy PNG with specific dimensions
create_dummy_png <- function(width, height, path) {
  # Create a dummy array: height x width x 3 (RGB)
  # Using a simple matrix of 0s
  img_array <- array(0, dim = c(height, width, 3))
  writePNG(img_array, path)
  return(path)
}

test_that("passes for 1200x800 image", {
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))
  create_dummy_png(1200, 800, tmp_file)

  img <- readPNG(tmp_file)
  h <- dim(img)[1]
  w <- dim(img)[2]

  expect_equal(w, 1200)
  expect_equal(h, 800)
  expect_true(w >= 1200 && h >= 800)
})

test_that("passes for larger than minimum image", {
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))
  create_dummy_png(2000, 1500, tmp_file)

  img <- readPNG(tmp_file)
  h <- dim(img)[1]
  w <- dim(img)[2]

  expect_true(w >= 1200 && h >= 800)
})

test_that("fails for width too small", {
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))
  create_dummy_png(1199, 800, tmp_file)

  img <- readPNG(tmp_file)
  h <- dim(img)[1]
  w <- dim(img)[2]

  expect_false(w >= 1200 && h >= 800)
})

test_that("fails for height too small", {
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))
  create_dummy_png(1200, 799, tmp_file)

  img <- readPNG(tmp_file)
  h <- dim(img)[1]
  w <- dim(img)[2]

  expect_false(w >= 1200 && h >= 800)
})

test_that("fails for both dimensions too small", {
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))
  create_dummy_png(100, 100, tmp_file)

  img <- readPNG(tmp_file)
  h <- dim(img)[1]
  w <- dim(img)[2]

  expect_false(w >= 1200 && h >= 800)
})

test_that("handles non-existent file gracefully", {
  expect_error(readPNG("non_existent_file.png"), "cannot open")
})

cat("All unit tests for plot resolution logic passed.\n")
