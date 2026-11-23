import numpy as np
import networkx as nx
from utils import persistence_utils as pu

def test_build_shortest_path_filtration():
    G = nx.path_graph(5)  # linear chain of 5 nodes
    dist = pu.build_shortest_path_filtration(G)
    # For a path graph distances are 0,1,2,3,4 etc.
    assert dist.shape == (5, 5)
    assert np.allclose(dist[np.arange(5), np.arange(5)], 0.0)

def test_compute_persistence_diagram_empty():
    empty = np.zeros((0, 0))
    diagram = pu.compute_persistence_diagram(empty)
    assert diagram == [], "Empty graph should yield empty diagram"

def test_vectorize_zero_diagram():
    diagram = []
    img = pu.vectorize(diagram, resolution=10, sigma=1.0)
    assert img.shape == (10, 10)
    assert np.allclose(img, 0.0)