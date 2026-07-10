"""
Rule-based model implementation for molecular toxicity prediction.

This model scores molecules based on the presence of structural alerts
defined in the configuration file, weighted by their toxicity potential.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
except ImportError:
    Chem = None
    rdMolDescriptors = None


class RuleBasedModel:
    """
    A rule-based model that scores molecules based on structural alerts.

    The model loads SMARTS patterns and weights from a configuration file
    and calculates a toxicity score for each molecule based on the presence
    of these alerts.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the rule-based model.

        Args:
            config_path: Path to the structural alerts configuration file.
                        If None, uses the default path from the project structure.
        """
        self.alerts: List[Dict[str, Any]] = []
        self.patterns: List[Any] = []
        self.weights: List[float] = []
        self.config_path = config_path
        self._load_alerts()

    def _load_alerts(self) -> None:
        """Load structural alerts from the configuration file."""
        if Chem is None:
            raise ImportError(
                "RDKit is required for rule-based model. "
                "Install with: pip install rdkit"
            )

        # Determine config path
        if self.config_path is None:
            # Try to find the config file in the project structure
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "code" / "config" / "structural_alerts.json"
            if not config_path.exists():
                # Fallback to relative path from current directory
                config_path = Path("config/structural_alerts.json")
        else:
            config_path = Path(self.config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_path, 'r') as f:
            config = json.load(f)

        self.alerts = config.get("alerts", [])

        if not self.alerts:
            raise ValueError("No alerts found in configuration file")

        # Compile SMARTS patterns
        for alert in self.alerts:
            smarts = alert.get("smarts")
            weight = alert.get("weight", 1.0)

            if not smarts:
                raise ValueError(f"Alert missing SMARTS pattern: {alert}")

            try:
                pattern = Chem.MolFromSmarts(smarts)
                if pattern is None:
                    raise ValueError(f"Invalid SMARTS pattern: {smarts}")
                self.patterns.append(pattern)
                self.weights.append(float(weight))
            except Exception as e:
                raise ValueError(f"Error compiling SMARTS pattern '{smarts}': {e}")

    def predict_score(self, smiles: str) -> float:
        """
        Calculate the toxicity score for a single molecule.

        Args:
            smiles: SMILES string of the molecule.

        Returns:
            Toxicity score based on structural alerts.
        """
        if Chem is None:
            raise ImportError("RDKit is required for scoring")

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.0

        score = 0.0
        for pattern, weight in zip(self.patterns, self.weights):
            if mol.HasSubstructMatch(pattern):
                score += weight

        return score

    def predict_scores(self, smiles_list: List[str]) -> List[float]:
        """
        Calculate toxicity scores for multiple molecules.

        Args:
            smiles_list: List of SMILES strings.

        Returns:
            List of toxicity scores.
        """
        return [self.predict_score(smiles) for smiles in smiles_list]

    def predict_binary(self, smiles_list: List[str], threshold: float = 0.0) -> List[int]:
        """
        Predict binary toxicity labels based on a threshold.

        Args:
            smiles_list: List of SMILES strings.
            threshold: Score threshold for positive prediction.

        Returns:
            List of binary predictions (0 or 1).
        """
        scores = self.predict_scores(smiles_list)
        return [1 if score > threshold else 0 for score in scores]

    def get_alerts_info(self) -> List[Dict[str, Any]]:
        """
        Get information about loaded alerts.

        Returns:
            List of dictionaries containing alert information.
        """
        info = []
        for i, alert in enumerate(self.alerts):
            info.append({
                "name": alert.get("name", f"Alert_{i}"),
                "smarts": alert.get("smarts"),
                "weight": alert.get("weight", 1.0),
                "description": alert.get("description", "")
            })
        return info

    def __repr__(self) -> str:
        return f"RuleBasedModel(alerts={len(self.alerts)})"


def load_rule_based_model(config_path: Optional[str] = None) -> RuleBasedModel:
    """
    Factory function to load a rule-based model.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Initialized RuleBasedModel instance.
    """
    return RuleBasedModel(config_path=config_path)
