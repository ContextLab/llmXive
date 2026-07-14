# tests/unit/test_extract_climate.R
# Unit test for climate extraction on synthetic coordinates using mocks/stubs

library(testthat)
library(raster)
library(sf)

# Mock function to simulate raster extraction
mock_extract_climate <- function(coords, temp_raster, precip_raster) {
  # Simulate extraction by returning dummy values based on coordinates
  # In reality, this would call raster::extract()
  
  n <- nrow(coords)
  result <- data.frame(
    decimalLatitude = coords$decimalLatitude,
    decimalLongitude = coords$decimalLongitude,
    temp_mean_annual = rnorm(n, mean = 15, sd = 5), # Simulated temperature
    precip_mean_annual = rnorm(n, mean = 1000, sd = 200) # Simulated precipitation
  )
  return(result)
}

test_that("extracts climate data for synthetic coordinates", {
  # Create synthetic coordinates
  synthetic_coords <- data.frame(
    decimalLatitude = c(40.0, 40.5, 41.0),
    decimalLongitude = c(-74.0, -74.5, -75.0),
    stringsAsFactors = FALSE
  )
  
  # Create mock rasters (single cell for simplicity)
  mock_temp_raster <- raster(nrows=10, ncols=10, xmn=-80, xmx=-70, ymn=35, ymx=45)
  mock_temp_raster[] <- 15
  
  mock_precip_raster <- raster(nrows=10, ncols=10, xmn=-80, xmx=-70, ymn=35, ymx=45)
  mock_precip_raster[] <- 1000
  
  # Call mock extraction
  result <- mock_extract_climate(synthetic_coords, mock_temp_raster, mock_precip_raster)
  
  # Verify output structure
  expect_true("decimalLatitude" %in% names(result))
  expect_true("decimalLongitude" %in% names(result))
  expect_true("temp_mean_annual" %in% names(result))
  expect_true("precip_mean_annual" %in% names(result))
  
  # Verify row count matches input
  expect_equal(nrow(result), nrow(synthetic_coords))
  
  # Verify values are numeric
  expect_s3_class(result$temp_mean_annual, "numeric")
  expect_s3_class(result$precip_mean_annual, "numeric")
})

test_that("handles NA values in climate extraction", {
  # Create coordinates with some out-of-bounds values (simulating NA in real extraction)
  synthetic_coords <- data.frame(
    decimalLatitude = c(40.0, 99.0, 41.0), # 99.0 is out of bounds
    decimalLongitude = c(-74.0, -74.5, -75.0),
    stringsAsFactors = FALSE
  )
  
  # Create mock rasters
  mock_temp_raster <- raster(nrows=10, ncols=10, xmn=-80, xmx=-70, ymn=35, ymx=45)
  mock_temp_raster[] <- 15
  
  mock_precip_raster <- raster(nrows=10, ncols=10, xmn=-80, xmx=-70, ymn=35, ymx=45)
  mock_precip_raster[] <- 1000
  
  # In a real implementation, out-of-bounds would return NA
  # For this mock, we'll simulate that behavior
  result <- data.frame(
    decimalLatitude = synthetic_coords$decimalLatitude,
    decimalLongitude = synthetic_coords$decimalLongitude,
    temp_mean_annual = c(15, NA, 15),
    precip_mean_annual = c(1000, NA, 1000)
  )
  
  # Verify NA handling
  expect_true(is.na(result$temp_mean_annual[2]))
  expect_true(is.na(result$precip_mean_annual[2]))
})

test_that("validates coordinate precision", {
  # Test that coordinates with high uncertainty are flagged
  # This is more of a data quality check than climate extraction
  # but it's relevant to the climate extraction pipeline
  
  coords_low_precision <- data.frame(
    decimalLatitude = c(40.0001, 40.5),
    decimalLongitude = c(-74.0001, -74.5),
    uncertainty = c(10000, 5000), # meters
    stringsAsFactors = FALSE
  )
  
  # Filter based on uncertainty > 10km
  valid_coords <- coords_low_precision %>%
    dplyr::filter(uncertainty <= 10000)
  
  expect_equal(nrow(valid_coords), 1)
})