import unittest
import torch
from models.loss_utils import compute_interference_cross_term

class TestInterferenceCrossTerm(unittest.TestCase):
    def test_interference_cross_term_negative_for_ambiguous(self):
        # Create a dummy complex tensor representing an ambiguous sample
        c1 = torch.complex64(tensor=[1.0, 1.0])
        c2 = torch.complex64(tensor=[-1.0, -1.0])

        # Calculate the interference cross-term
        cross_term = compute_interference_cross_term(torch.stack([c1, c2]))

        # Assert that the cross-term is negative
        self.assertLess(cross_term.item(), 0)

if __name__ == '__main__':
    unittest.main()