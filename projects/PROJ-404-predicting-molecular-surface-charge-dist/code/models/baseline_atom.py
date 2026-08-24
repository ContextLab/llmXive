"""
Atom-Type Average Baseline Model for Molecular Surface Charge Prediction.

This module implements a simple baseline model that predicts the surface charge
of a molecule by assigning the mean charge value observed for each atomic number
in the training set. It serves as a non-learnable (or trivially learnable)
lower bound for more complex geometric GNNs.
"""

from typing import Dict, Optional, List, Tuple
import torch
import torch.nn as nn
from data.dataset import MoleculeData


class AtomTypeAverageBaseline(nn.Module):
    """
    A baseline model that predicts atomic charges based on the average charge
    of each atom type (atomic number) observed in the training data.

    This model does not learn weights during training in the traditional sense.
    Instead, it relies on a pre-computed mapping of atomic number -> mean charge.
    During the forward pass, it assigns these mean values to atoms based on their
    atomic number.

    Attributes:
        atomic_mean_charges (Dict[int, float]): A mapping from atomic number to
            the mean charge value for that atom type.
    """

    def __init__(self, atomic_mean_charges: Optional[Dict[int, float]] = None):
        """
        Initializes the baseline model.

        Args:
            atomic_mean_charges: A dictionary mapping atomic numbers to their
                mean charges. If None, initializes with an empty dictionary.
                The model expects this to be populated before the first
                evaluation or training step if not provided at init.
        """
        super().__init__()
        self.atomic_mean_charges: Dict[int, float] = atomic_mean_charges or {}
        
        # Register the dictionary as a buffer to ensure it's handled correctly
        # if we were to convert to a state dict, though for this baseline
        # we treat it as a configuration/property.
        # We store it as a plain attribute as it's not a learnable parameter.

    def fit(self, data_loader: torch.utils.data.DataLoader) -> None:
        """
        Computes the mean charge for each atomic number from the provided data loader.
        
        This method iterates through the dataset to calculate the average charge
        associated with each unique atomic number (Z).

        Args:
            data_loader: A PyTorch DataLoader yielding MoleculeData objects.
        """
        charge_sums: Dict[int, float] = {}
        charge_counts: Dict[int, int] = {}

        for batch in data_loader:
            # batch.x contains atomic numbers (integers)
            # batch.y contains target charges (floats)
            # Ensure inputs are on CPU for aggregation
            atomic_numbers = batch.x.cpu()
            charges = batch.y.cpu()

            for z, charge in zip(atomic_numbers, charges):
                z_int = int(z.item())
                c_val = float(charge.item())
                
                if z_int not in charge_sums:
                    charge_sums[z_int] = 0.0
                    charge_counts[z_int] = 0
                
                charge_sums[z_int] += c_val
                charge_counts[z_int] += 1

        self.atomic_mean_charges = {}
        for z in charge_sums:
            if charge_counts[z] > 0:
                self.atomic_mean_charges[z] = charge_sums[z] / charge_counts[z]

    def forward(self, batch: MoleculeData) -> torch.Tensor:
        """
        Predicts charges for the input batch based on atomic types.

        For each atom in the batch, the model looks up the mean charge for its
        atomic number. If an atomic number was not seen during `fit`, it defaults
        to 0.0.

        Args:
            batch: A MoleculeData object containing `x` (atomic numbers) and
                potentially other attributes (ignored for this baseline).

        Returns:
            A torch.Tensor of shape (num_atoms,) containing the predicted charges.
        """
        if not self.atomic_mean_charges:
            raise RuntimeError(
                "Model has not been fitted. Call .fit() with a data loader first."
            )

        atomic_numbers = batch.x
        # Create a tensor for predictions initialized to 0.0
        # Using the same device and dtype as the input charges (usually float)
        predictions = torch.zeros_like(atomic_numbers, dtype=torch.float32)

        # Vectorized lookup would require a large embedding table, 
        # but since atomic numbers are sparse and small, a loop or 
        # mapping is acceptable. For efficiency, we can map Z to index.
        
        # We will iterate over unique atomic numbers in the batch
        unique_z = torch.unique(atomic_numbers)
        
        for z in unique_z:
            z_int = int(z.item())
            mean_charge = self.atomic_mean_charges.get(z_int, 0.0)
            
            # Create a mask for this atomic number
            mask = (atomic_numbers == z_int)
            predictions[mask] = mean_charge

        return predictions

    def get_state_dict(self) -> Dict[str, any]:
        """Returns a dictionary containing the model's state."""
        return {"atomic_mean_charges": self.atomic_mean_charges}

    def load_state_dict(self, state_dict: Dict[str, any]) -> None:
        """Loads the model's state from a dictionary."""
        if "atomic_mean_charges" in state_dict:
            self.atomic_mean_charges = state_dict["atomic_mean_charges"]


def create_atom_baseline_model(
    atomic_mean_charges: Optional[Dict[int, float]] = None
) -> AtomTypeAverageBaseline:
    """
    Factory function to create an AtomTypeAverageBaseline model.

    Args:
        atomic_mean_charges: Optional pre-computed mean charges.

    Returns:
        An instance of AtomTypeAverageBaseline.
    """
    return AtomTypeAverageBaseline(atomic_mean_charges=atomic_mean_charges)
