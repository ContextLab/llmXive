import unittest
import networkx as nx

from utils.graph_utils import (
    is_dag,
    validate_dag,
    nesting_depth,
    branching_factor,
    get_random_valid_path_different_from_reference,
)


class TestGraphUtils(unittest.TestCase):
    def setUp(self):
        # Simple DAG: a linear chain 0→1→2
        self.chain = nx.DiGraph()
        self.chain.add_edges_from([(0, 1), (1, 2)])

        # Cyclic graph: 0→1→0
        self.cycle = nx.DiGraph()
        self.cycle.add_edges_from([(0, 1), (1, 0)])

        # Branching DAG: 0→1, 0→2, 1→3, 2→3
        self.branch = nx.DiGraph()
        self.branch.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])

    def test_is_dag(self):
        self.assertTrue(is_dag(self.chain))
        self.assertFalse(is_dag(self.cycle))

    def test_validate_dag(self):
        self.assertTrue(validate_dag(self.chain))
        self.assertFalse(validate_dag(self.cycle))
        empty = nx.DiGraph()
        self.assertFalse(validate_dag(empty))

    def test_nesting_depth(self):
        # Chain of length 3 → depth should be 3 nodes
        self.assertEqual(nesting_depth(self.chain), 3)
        # Branching graph longest path is 0→1→3 or 0→2→3 → length 3
        self.assertEqual(nesting_depth(self.branch), 3)

    def test_branching_factor(self):
        # Chain: in-degrees are [0,1,1] → average = 2/3 ≈ 0.6667
        self.assertAlmostEqual(branching_factor(self.chain), (0 + 1 + 1) / 3)
        # Branching graph: in-degrees [0,1,1,2] → average = 4/4 = 1.0
        self.assertAlmostEqual(branching_factor(self.branch), 1.0)

    def test_random_valid_path_different_from_reference(self):
        # In the chain, only one simple path exists; function should return None
        reference = [0, 1, 2]
        result = get_random_valid_path_different_from_reference(self.chain, reference, max_attempts=10)
        self.assertIsNone(result)

        # In the branching graph, there are two distinct paths from 0 to 3
        reference = [0, 1, 3]
        result = get_random_valid_path_different_from_reference(self.branch, reference, max_attempts=10)
        # The alternative path should be [0,2,3]
        self.assertIsNotNone(result)
        self.assertNotEqual(result, reference)
        self.assertEqual(result, [0, 2, 3])

if __name__ == "__main__":
    unittest.main()