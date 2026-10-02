import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

def compute_dtw_matrix(seq1: List[float], seq2: List[float]) -> List[List[float]]:
    """
    Computes the DTW matrix for two sequences.
    """
    n, m = len(seq1), len(seq2)
    dtw = [[float('inf')] * (m + 1) for _ in range(n + 1)]
    dtw[0][0] = 0.0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i-1] - seq2[j-1])
            dtw[i][j] = cost + min(dtw[i-1][j], dtw[i][j-1], dtw[i-1][j-1])
    
    return dtw

def compute_dtw_alignment(seq1: List[float], seq2: List[float]) -> List[Tuple[int, int]]:
    """
    Computes the DTW alignment path.
    """
    dtw = compute_dtw_matrix(seq1, seq2)
    n, m = len(seq1), len(seq2)
    path = []
    i, j = n, m
    while i > 0 or j > 0:
        path.append((i-1, j-1))
        if i == 0:
            j -= 1
        elif j == 0:
            i -= 1
        else:
            if dtw[i-1][j] < dtw[i][j-1] and dtw[i-1][j] < dtw[i-1][j-1]:
                i -= 1
            elif dtw[i][j-1] < dtw[i-1][j-1]:
                j -= 1
            else:
                i -= 1
                j -= 1
    return path[::-1]

def save_dtw_matrix(matrix: List[List[float]], path: str):
    with open(path, "w") as f:
        json.dump(matrix, f)

def run_dtw_analysis(static_scores: List[float], dynamic_scores: List[float], output_path: str):
    """
    Runs DTW analysis and saves the matrix.
    """
    matrix = compute_dtw_matrix(static_scores, dynamic_scores)
    save_dtw_matrix(matrix, output_path)
    logger.info(f"DTW matrix saved to {output_path}")

def main():
    """
    Main entry point for correlation analysis.
    """
    logger.info("Correlation analysis module loaded.")

if __name__ == "__main__":
    main()