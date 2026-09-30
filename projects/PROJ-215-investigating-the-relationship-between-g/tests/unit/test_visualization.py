import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from scipy.spatial.distance import squareform

from code.visualization import (
    load_beta_diversity, 
    categorize_mental_health, 
    calculate_centroids, 
    run_pcoa_from_distance,
    plot_pcoa
)

def test_categorize_mental_health_high_phq():
    row = pd.Series({'phq9': 12, 'gad7': 5})
    assert categorize_mental_health(row) == "High Risk"

def test_categorize_mental_health_high_gad():
    row = pd.Series({'phq9': 5, 'gad7': 12})
    assert categorize_mental_health(row) == "High Risk"

def test_categorize_mental_health_low_both():
    row = pd.Series({'phq9': 4, 'gad7': 4})
    assert categorize_mental_health(row) == "Low Risk"

def test_categorize_mental_health_missing():
    row = pd.Series({'phq9': np.nan, 'gad7': 4})
    assert categorize_mental_health(row) == "Unknown"

def test_calculate_centroids():
    coords = np.array([
        [1.0, 2.0, 3.0],
        [2.0, 4.0, 6.0],
        [10.0, 20.0, 30.0]
    ])
    labels = pd.Series(['A', 'A', 'B'])
    centroids = calculate_centroids(coords, labels)
    
    assert 'A' in centroids.index
    assert 'B' in centroids.index
    # Check A centroid is mean of first two rows
    assert centroids.loc['A', 'PC1'] == 1.5
    assert centroids.loc['A', 'PC2'] == 3.0
    assert centroids.loc['A', 'PC3'] == 4.5
    # Check B centroid is the third row
    assert centroids.loc['B', 'PC1'] == 10.0

def test_run_pcoa_from_distance():
    # Create a simple distance matrix for 3 points
    # Points: (0,0), (1,0), (0,1)
    # Distances: 1, 1, sqrt(2)
    condensed = np.array([1.0, 1.0, np.sqrt(2)])
    dist_matrix = squareform(condensed)
    
    coords = run_pcoa_from_distance(dist_matrix, n_components=2)
    assert coords.shape == (3, 2)
    assert not np.any(np.isnan(coords))

def test_plot_pcoa_saves_file():
    coords = np.array([
        [1.0, 2.0, 3.0],
        [2.0, 4.0, 6.0],
        [10.0, 20.0, 30.0],
        [11.0, 21.0, 31.0]
    ])
    labels = pd.Series(['High Risk', 'High Risk', 'Low Risk', 'Low Risk'])
    centroids = calculate_centroids(coords, labels)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot.png")
        plot_pcoa(coords, labels, centroids, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
