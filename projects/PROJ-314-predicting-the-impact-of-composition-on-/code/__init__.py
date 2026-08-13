import logging
import os
from pathlib import Path

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("llmXive")

# Import config
from .config import load_environment, initialize_config

# Initialize config on import
initialize_config()

def load_env():
    """
    Load environment variables from a .env file in the project root.
    Returns True if successful, False otherwise.
    """
    from dotenv import load_dotenv
    from pathlib import Path

    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using system environment only.")
        return False

    success = load_dotenv(dotenv_path=env_path)
    if success:
        logger.info(f"Environment variables loaded from {env_path}")
    else:
        logger.warning("Failed to load environment variables from .env")
    return True


class DescriptorSet:
    """
    Represents a set of computed elemental descriptors for a ceramic composition.
    
    This class encapsulates the feature vector derived from a chemical formula,
    including physical and chemical properties used for predictive modeling.
    
    Attributes:
        composition (str): The original chemical formula string (e.g., "Al2O3").
        mean_atomic_radius (float): Mean atomic radius of constituent elements.
        electronegativity_std (float): Standard deviation of electronegativity.
        valence_electron_concentration (float): Valence electron concentration (VEC).
        cation_size_variance (float): Variance of cation atomic radii.
        range_uncertainty (float): Uncertainty metric derived from range values.
        primary_anion_cation_group (str): Identified primary anion-cation group (e.g., "O-Al").
        is_range_flag (bool): Flag indicating if original values were ranges.
        is_imputed (bool): Flag indicating if any values were imputed.
        sample_count (int): Number of samples for this entry.
        weibull_modulus (float): The target Weibull modulus value.
        sintering_temp (float): Sintering temperature in Kelvin.
        raw_data (dict): Dictionary containing raw descriptor values before aggregation.
    """
    
    def __init__(
        self,
        composition: str,
        mean_atomic_radius: float,
        electronegativity_std: float,
        valence_electron_concentration: float,
        cation_size_variance: float = 0.0,
        range_uncertainty: float = 0.0,
        primary_anion_cation_group: str = "Unknown",
        is_range_flag: bool = False,
        is_imputed: bool = False,
        sample_count: int = 0,
        weibull_modulus: float = 0.0,
        sintering_temp: float = 0.0,
        raw_data: dict = None
    ):
        self.composition = composition
        self.mean_atomic_radius = mean_atomic_radius
        self.electronegativity_std = electronegativity_std
        self.valence_electron_concentration = valence_electron_concentration
        self.cation_size_variance = cation_size_variance
        self.range_uncertainty = range_uncertainty
        self.primary_anion_cation_group = primary_anion_cation_group
        self.is_range_flag = is_range_flag
        self.is_imputed = is_imputed
        self.sample_count = sample_count
        self.weibull_modulus = weibull_modulus
        self.sintering_temp = sintering_temp
        self.raw_data = raw_data or {}
    
    def to_dict(self) -> dict:
        """Convert the DescriptorSet to a dictionary representation."""
        return {
            "composition": self.composition,
            "mean_atomic_radius": self.mean_atomic_radius,
            "electronegativity_std": self.electronegativity_std,
            "valence_electron_concentration": self.valence_electron_concentration,
            "cation_size_variance": self.cation_size_variance,
            "range_uncertainty": self.range_uncertainty,
            "primary_anion_cation_group": self.primary_anion_cation_group,
            "is_range_flag": self.is_range_flag,
            "is_imputed": self.is_imputed,
            "sample_count": self.sample_count,
            "weibull_modulus": self.weibull_modulus,
            "sintering_temp": self.sintering_temp,
            "raw_data": self.raw_data
        }
    
    def get_feature_vector(self) -> list:
        """
        Extract the numeric feature vector for ML models.
        
        Returns:
            list: Ordered list of float features excluding metadata fields.
        """
        return [
            self.mean_atomic_radius,
            self.electronegativity_std,
            self.valence_electron_concentration,
            self.cation_size_variance,
            self.range_uncertainty,
            float(self.is_range_flag),
            float(self.is_imputed)
        ]
    
    def __repr__(self):
        return (
            f"DescriptorSet(composition={self.composition}, "
            f"weibull_modulus={self.weibull_modulus}, "
            f"group={self.primary_anion_cation_group})"
        )