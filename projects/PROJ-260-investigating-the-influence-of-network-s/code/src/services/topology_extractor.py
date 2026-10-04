import ase
import numpy as np
from scipy.spatial import distance_matrix
import logging
from pathlib import Path

def calculate_rdf(positions, cutoff):
    """Calculates the radial distribution function (RDF)."""
    distances = distance_matrix(positions, positions)
    distances = distances[np.triu_indices_from(distances, k=1)]
    hist, _ = np.histogram(distances, bins=np.arange(0, cutoff + 0.1, 0.1))
    return hist

def determine_cutoff(positions):
    """Determines the bond cutoff based on the first minimum of the RDF."""
    rdf = calculate_rdf(positions, 5.0)
    min_index = np.argmin(rdf)
    cutoff = np.arange(0, 5.0, 0.1)[min_index]
    return cutoff

def construct_bond_network(positions, cutoff):
    """Constructs a bond network based on the cutoff."""
    distances = distance_matrix(positions, positions)
    bonds = distances <= cutoff
    return bonds

def compute_coordination_number(bonds):
    """Computes the coordination number for each atom."""
    return np.sum(bonds, axis=1)

def compute_bond_angle_variance(positions, bonds):
    """Computes the variance of bond angles for each atom."""
    angles = []
    for i in range(len(positions)):
        neighbors = np.where(bonds[i])[0]
        if len(neighbors) >= 2:
            for j in range(len(neighbors)):
                for k in range(j + 1, len(neighbors)):
                    v1 = positions[neighbors[j]] - positions[i]
                    v2 = positions[neighbors[k]] - positions[i]
                    angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
                    angles.append(angle)
    if angles:
        return np.var(angles)
    else:
        return 0.0

def extract_topology(trajectory_file, cutoff=None):
    """Extracts topology information from a trajectory file."""
    try:
        atoms = ase.io.read(trajectory_file)
        positions = atoms.get_positions()

        if cutoff is None:
            cutoff = determine_cutoff(positions)

        bonds = construct_bond_network(positions, cutoff)
        coordination_numbers = compute_coordination_number(bonds)
        bond_angle_variances = compute_bond_angle_variance(positions, bonds)
        
        #Anomaly flagging
        for i, coord_num in enumerate(coordination_numbers):
          if coord_num > 6:
            logging.warning(f"Atom {i} has coordination number > 6: {coord_num}")

        return coordination_numbers, bond_angle_variances

    except Exception as e:
        logging.error(f"Error processing trajectory file: {e}")
        return None, None
