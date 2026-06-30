"""
Heterogeneous routing layer for multi-modal model orchestration.

Implements the ModalityRouter class to route inputs to native modality-specific
models (TimeSeries, Tabular, Text) based on the modality type.

Dependencies:
    - src.models.timeseries_model (TimeSeriesModel)
    - src.models.tabular_model (TabularModel)
    - src.models.text_model (TextModel)
    - src.utils.logging (get_logger)

FR-002 Compliance:
    - Routes each modality's raw input to its native model.
    - Provides a unified predict interface for heterogeneous inputs.
"""
import logging
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from pathlib import Path

# Import modality-specific models as defined in T035-T037
# Note: Using relative imports to match project structure
try:
    from .timeseries_model import TimeSeriesModel
except ImportError:
    # Fallback for direct execution or different import context
    from src.models.timeseries_model import TimeSeriesModel

try:
    from .tabular_model import TabularModel
except ImportError:
    from src.models.tabular_model import TabularModel

try:
    from .text_model import TextModel
except ImportError:
    from src.models.text_model import TextModel

from src.utils.logging import get_logger

# Register modality model classes
MODALITY_MODEL_REGISTRY = {
    "timeseries": TimeSeriesModel,
    "tabular": TabularModel,
    "text": TextModel,
}

class ModalityRouter:
    """
    Routes heterogeneous inputs to their native modality-specific models.
    
    This class manages the lifecycle of modality-specific models and provides
    a unified interface for prediction across multiple modalities.
    
    Attributes:
        models (Dict[str, Any]): Dictionary of initialized model instances.
        logger (logging.Logger): Logger instance for routing events.
    """
    
    def __init__(self, model_configs: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the ModalityRouter with optional model configurations.
        
        Args:
            model_configs: Dictionary mapping modality types to model configuration.
                          Expected keys: 'timeseries', 'tabular', 'text'.
                          Each value should contain 'model_id' and other model-specific params.
        
        Raises:
            ValueError: If a requested modality is not supported.
        """
        self.models: Dict[str, Any] = {}
        self.model_configs = model_configs or {}
        self.logger = get_logger(__name__)
        
        self.logger.info("Initializing ModalityRouter")
        
        # Pre-load models if configs are provided
        if self.model_configs:
            self._load_models_from_config()
    
    def _load_models_from_config(self) -> None:
        """Load models based on provided configuration."""
        for modality, config in self.model_configs.items():
            if modality not in MODALITY_MODEL_REGISTRY:
                self.logger.warning(
                    f"Modality '{modality}' not in registry. Skipping auto-load."
                )
                continue
            
            model_class = MODALITY_MODEL_REGISTRY[modality]
            model_id = config.get("model_id", f"default_{modality}")
            
            self.logger.info(f"Loading {modality} model: {model_id}")
            self.models[modality] = model_class()
            # Assuming models have a load_model method that takes model_id
            if hasattr(self.models[modality], 'load_model'):
                self.models[modality].load_model(model_id)
    
    def get_model(self, modality: str) -> Any:
        """
        Retrieve or initialize a model for the specified modality.
        
        Args:
            modality: The modality type ('timeseries', 'tabular', 'text').
        
        Returns:
            The initialized model instance.
        
        Raises:
            ValueError: If the modality is not supported.
            RuntimeError: If the model fails to initialize.
        """
        if modality not in MODALITY_MODEL_REGISTRY:
            raise ValueError(
                f"Unsupported modality: '{modality}'. "
                f"Supported: {list(MODALITY_MODEL_REGISTRY.keys())}"
            )
        
        if modality not in self.models:
            model_class = MODALITY_MODEL_REGISTRY[modality]
            self.logger.info(f"Lazy-loading {modality} model")
            self.models[modality] = model_class()
            
            # Try to load with config if available, otherwise default
            if modality in self.model_configs:
                model_id = self.model_configs[modality].get("model_id", f"default_{modality}")
                if hasattr(self.models[modality], 'load_model'):
                    self.models[modality].load_model(model_id)
        
        return self.models[modality]
    
    def route(self, modality: str, input_data: Any) -> Any:
        """
        Route input data to the appropriate model and return the result.
        
        This is the core routing logic: forward each modality's raw input
        to its native model for processing.
        
        Args:
            modality: The modality type ('timeseries', 'tabular', 'text').
            input_data: The raw input data for the model.
        
        Returns:
            The model's output (prediction, embedding, etc.).
        
        Raises:
            ValueError: If the modality is unsupported.
            RuntimeError: If the model execution fails.
        """
        model = self.get_model(modality)
        self.logger.debug(f"Routing {modality} input to model")
        
        # Determine the method to call based on model capabilities
        # Prefer 'predict' for general inference, fallback to 'get_embedding' if needed
        if hasattr(model, 'predict'):
            return model.predict(input_data)
        elif hasattr(model, 'get_embedding'):
            return model.get_embedding(input_data)
        else:
            raise RuntimeError(
                f"Model for {modality} has no 'predict' or 'get_embedding' method."
            )
    
    def predict(self, modalities_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified prediction interface for heterogeneous inputs.
        
        Processes multiple modalities in a single call, routing each to its
        native model, and returns a dictionary of results.
        
        Args:
            modalities_dict: Dictionary mapping modality names to input data.
                            Example: {"timeseries": data, "text": text_str}
        
        Returns:
            Dictionary mapping modality names to their respective model outputs.
        
        Example:
            >>> router = ModalityRouter()
            >>> results = router.predict({
            ...     "timeseries": ts_data,
            ...     "tabular": df,
            ...     "text": "sample text"
            ... })
            >>> # results = {"timeseries": pred_ts, "tabular": pred_tab, "text": pred_txt}
        """
        self.logger.info(f"Executing heterogeneous prediction for {len(modalities_dict)} modalities")
        results = {}
        
        for modality, input_data in modalities_dict.items():
            try:
                output = self.route(modality, input_data)
                results[modality] = output
                self.logger.debug(f"Successfully processed {modality} modality")
            except Exception as e:
                self.logger.error(f"Failed to process {modality} modality: {e}")
                results[modality] = {"error": str(e), "success": False}
        
        return results

def main():
    """
    CLI entry point for testing the routing layer.
    
    Usage:
        python -m src.models.routing --modality timeseries --data "..."
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Test ModalityRouter")
    parser.add_argument(
        "--modality", 
        type=str, 
        choices=["timeseries", "tabular", "text"],
        help="Modality to test"
    )
    parser.add_argument(
        "--data", 
        type=str, 
        help="Input data (JSON string or file path)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.modality:
        parser.print_help()
        sys.exit(1)

    logger = get_logger(__name__)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    router = ModalityRouter()
    
    # Mock data for testing if no real data provided
    if args.data:
        try:
            # Try to parse as JSON
            input_data = json.loads(args.data)
        except json.JSONDecodeError:
            # Assume it's a file path or raw string
            if Path(args.data).exists():
                with open(args.data, 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = args.data
    else:
        # Default mock data based on modality
        if args.modality == "timeseries":
            input_data = {"values": [1.0, 2.0, 3.0, 4.0, 5.0], "label": "test"}
        elif args.modality == "tabular":
            input_data = {"feature1": 10, "feature2": 20}
        elif args.modality == "text":
            input_data = "This is a test sentence for routing."
        else:
            input_data = {}

    logger.info(f"Running route for modality: {args.modality}")
    result = router.route(args.modality, input_data)
    
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
