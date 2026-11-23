import os
import sys
import csv
import logging
import json
import warnings
import numpy as np
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import ttest_ind, wilcoxon

def load_matched_pairs(file_path):
    """Loads matched pairs from a CSV file."""
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []

def save_matched_pairs_with_classification(data, file_path):
  """Saves matched pairs with a 'censored' or 'non-censored' classification."""
  try:
      with open(file_path, 'w', newline='') as csvfile:
          fieldnames = data[0].keys()  # Get headers from the first row
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
          writer.writeheader()
          for row in data:
              writer.writerow(row)
      logging.info(f"Saved classified matched pairs to {file_path}")
  except Exception as e:
      logging.error(f"Error saving classified matched pairs: {e}")

def classify_censored_data(matched_pairs):
    """Classifies data based on interval-censored effect sizes."""
    for pair in matched_pairs:
        if pair['preprint_effect_size'] == '' or pair['journal_effect_size'] == '':  # Simplified check for empty strings
            pair['is_censored'] = 'True'
        else:
            pair['is_censored'] = 'False'
    return matched_pairs

def filter_p_values_for_analysis(matched_pairs):
  """Filters out p-values that are inequalities."""
  filtered_pairs = []
  for pair in matched_pairs:
      if '<' not in pair['preprint_p_value'] and '>' not in pair['journal_p_value']:
          filtered_pairs.append(pair)
  return filtered_pairs

def run_pcurve_analysis(data):
    """Placeholder for p-curve analysis."""
    # Replace with actual p-curve analysis implementation using pypcurve library
    logging.info("Running p-curve analysis...")
    return {}  # Return some results or statistics

def calculate_difference(row):
  """Calculates the difference in effect size between preprint and journal versions."""
  try:
      preprint_es = float(row['preprint_effect_size'])
      journal_es = float(row['journal_effect_size'])
      return journal_es - preprint_es
  except (ValueError, TypeError):
      return np.nan  # Return NaN for invalid values

def main():
    """Main function to orchestrate the analysis."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    file_path = 'data/processed/matched_pairs.csv'
    classified_file_path = 'data/processed/matched_pairs_classified.csv'

    matched_pairs = load_matched_pairs(file_path)
    if not matched_pairs:
        logging.error("No data loaded. Exiting.")
        sys.exit(1)
    
    classified_pairs = classify_censored_data(matched_pairs)
    save_matched_pairs_with_classification(classified_pairs, classified_file_path)

    filtered_pairs = filter_p_values_for_analysis(classified_pairs)

    # Example: Calculate effect size difference for non-censored pairs
    non_censored_pairs = [pair for pair in filtered_pairs if pair['is_censored'] == 'False']
    differences = [calculate_difference(row) for row in non_censored_pairs]

    # Remove NaN values from the differences list before performing t-test
    valid_differences = [d for d in differences if not np.isnan(d)]

    if len(valid_differences) > 1:  # Need at least two data points for a paired t-test
        t_statistic, p_value = ttest_ind(valid_differences, valid_differences, equal_var=False)  # Example t-test

        logging.info(f"Paired T-Test: t={t_statistic:.2f}, p={p_value:.3f}")
    else:
        logging.warning("Not enough non-censored pairs for a meaningful comparison.")
