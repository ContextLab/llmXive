"""
Novel Object Set Generator for Virtual Tactile Zero-Shot Adaptation.

This module implements the NovelObjectSet class to generate randomized
articulated geometries with varying friction coefficients for zero-shot
evaluation.
"""

import os
import math
import random
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Ensure we can import from the project root if running as script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

class NovelObjectSet:
    """
    Generates a set of randomized articulated geometries with friction
    coefficients uniformly distributed across a broad range.

    This class satisfies FR-003 by producing diverse object geometries
    with controlled physical properties for zero-shot evaluation.
    """

    def __init__(self, count: int, seed: int, friction_min: float, friction_max: float):
        """
        Initialize the Novel Object Set generator.

        Args:
            count: Number of objects to generate.
            seed: Random seed for reproducibility.
            friction_min: Minimum friction coefficient (inclusive).
            friction_max: Maximum friction coefficient (inclusive).

        Raises:
            ValueError: If parameters are invalid (count <= 0, seed < 0, friction_min > friction_max).
        """
        if count <= 0:
            raise ValueError(f"count must be positive, got {count}")
        if seed < 0:
            raise ValueError(f"seed must be non-negative, got {seed}")
        if friction_min > friction_max:
            raise ValueError(f"friction_min ({friction_min}) must be <= friction_max ({friction_max})")
        if friction_min < 0:
            raise ValueError(f"friction_min must be non-negative, got {friction_min}")

        self.count = count
        self.seed = seed
        self.friction_min = friction_min
        self.friction_max = friction_max
        
        # Initialize random state
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

    def _generate_box_geometries(self, obj_id: int) -> Dict[str, Any]:
        """
        Generate a simple articulated box geometry definition.

        Args:
            obj_id: Unique identifier for the object.

        Returns:
            Dictionary containing URDF-like geometry parameters.
        """
        # Generate random dimensions for base and link
        base_size = self.rng.uniform(0.05, 0.15, 3)
        link_size = self.rng.uniform(0.03, 0.10, 3)
        
        # Generate random joint parameters
        joint_pos = self.rng.uniform(0.0, 0.1, 3)
        joint_axis = self.rng.choice([
            [1, 0, 0], [0, 1, 0], [0, 0, 1]
        ])
        
        # Generate random mass properties
        base_mass = self.rng.uniform(0.1, 0.5)
        link_mass = self.rng.uniform(0.05, 0.3)
        
        # Generate friction coefficient from uniform distribution
        friction = self.rng.uniform(self.friction_min, self.friction_max)
        
        return {
            "id": obj_id,
            "base": {
                "size": base_size.tolist(),
                "mass": base_mass
            },
            "link": {
                "size": link_size.tolist(),
                "mass": link_mass
            },
            "joint": {
                "position": joint_pos.tolist(),
                "axis": joint_axis.tolist()
            },
            "friction": friction
        }

    def _create_urdf_string(self, obj_data: Dict[str, Any]) -> str:
        """
        Create a minimal URDF string from object data.

        Args:
            obj_data: Dictionary containing object geometry parameters.

        Returns:
            Valid URDF string representation.
        """
        base_size = obj_data["base"]["size"]
        link_size = obj_data["link"]["size"]
        joint_pos = obj_data["joint"]["position"]
        joint_axis = obj_data["joint"]["axis"]
        base_mass = obj_data["base"]["mass"]
        link_mass = obj_data["link"]["mass"]
        friction = obj_data["friction"]

        # Create URDF structure
        urdf = f"""<?xml version="1.0"?>
<robot name="novel_object_{obj_data['id']}">
  <link name="base_link">
    <inertial>
<mass value="{base_mass:.4f}"/>
<inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>
    </inertial>
    <visual>
<geometry>
  <box size="{base_size[0]:.4f} {base_size[1]:.4f} {base_size[2]:.4f}"/>
</geometry>
<material name="blue">
  <color rgba="0.2 0.2 0.8 1.0"/>
</material>
    </visual>
    <collision>
<geometry>
  <box size="{base_size[0]:.4f} {base_size[1]:.4f} {base_size[2]:.4f}"/>
</geometry>
    </collision>
    <surface>
<friction>
  <ode>
    <mu>{friction:.4f}</mu>
    <mu2>{friction:.4f}</mu2>
  </ode>
</friction>
    </surface>
  </link>

  <link name="moving_link">
    <inertial>
<mass value="{link_mass:.4f}"/>
<inertia ixx="0.0005" ixy="0.0" ixz="0.0" iyy="0.0005" iyz="0.0" izz="0.0005"/>
    </inertial>
    <visual>
<geometry>
  <box size="{link_size[0]:.4f} {link_size[1]:.4f} {link_size[2]:.4f}"/>
</geometry>
<material name="red">
  <color rgba="0.8 0.2 0.2 1.0"/>
</material>
    </visual>
    <collision>
<geometry>
  <box size="{link_size[0]:.4f} {link_size[1]:.4f} {link_size[2]:.4f}"/>
</geometry>
    </collision>
    <surface>
<friction>
  <ode>
    <mu>{friction:.4f}</mu>
    <mu2>{friction:.4f}</mu2>
  </ode>
</friction>
    </surface>
  </link>

  <joint name="prismatic_joint" type="prismatic">
    <parent link="base_link"/>
    <child link="moving_link"/>
    <origin xyz="{joint_pos[0]:.4f} {joint_pos[1]:.4f} {joint_pos[2]:.4f}" rpy="0 0 0"/>
    <axis xyz="{joint_axis[0]} {joint_axis[1]} {joint_axis[2]}"/>
    <limit lower="-0.1" upper="0.1" effort="10.0" velocity="1.0"/>
  </joint>
</robot>"""
        return urdf

    def generate(self, output_dir: str) -> List[str]:
        """
        Generate the novel object set and save to disk.

        Args:
            output_dir: Directory path where object files will be saved.

        Returns:
            List of file paths to the generated URDF files.

        Raises:
            ValueError: If output_dir is invalid or not writable.
            IOError: If file writing fails.
        """
        if not output_dir:
            raise ValueError("output_dir cannot be empty")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        
        for i in range(self.count):
            obj_id = f"obj_{i:04d}"
            
            # Generate geometry data
            obj_data = self._generate_box_geometries(obj_id)
            
            # Create URDF string
            urdf_content = self._create_urdf_string(obj_data)
            
            # Write to file
            file_path = os.path.join(output_dir, f"{obj_id}.urdf")
            with open(file_path, 'w') as f:
                f.write(urdf_content)
            
            generated_files.append(file_path)
        
        return generated_files

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the generated object set.

        Returns:
            Dictionary containing generation parameters and statistics.
        """
        return {
            "count": self.count,
            "seed": self.seed,
            "friction_min": self.friction_min,
            "friction_max": self.friction_max,
            "friction_range": self.friction_max - self.friction_min
        }


def main():
    """
    Command-line interface for generating novel object sets.
    
    Usage:
        python generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 1.2 --output data/generated/
    
    This script generates a set of randomized articulated geometries with
    friction coefficients uniformly distributed across the specified range.
    """
    import argparse
    import logging
    import sys
    from pathlib import Path

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description='Generate novel object set for zero-shot evaluation'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        required=True,
        help='Number of objects to generate'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        required=True,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--friction-min', 
        type=float, 
        required=True,
        help='Minimum friction coefficient'
    )
    parser.add_argument(
        '--friction-max', 
        type=float, 
        required=True,
        help='Maximum friction coefficient'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        required=True,
        help='Output directory for generated URDF files'
    )

    args = parser.parse_args()

    try:
        logger.info(f"Initializing NovelObjectSet generator with count={args.count}, "
                   f"seed={args.seed}, friction=[{args.friction_min}, {args.friction_max}]")
        
        generator = NovelObjectSet(
            count=args.count,
            seed=args.seed,
            friction_min=args.friction_min,
            friction_max=args.friction_max
        )
        
        # Ensure output directory is absolute path relative to project root
        output_path = Path(args.output)
        if not output_path.is_absolute():
            # Resolve relative to current working directory
            output_path = Path.cwd() / output_path
        
        logger.info(f"Generating objects to {output_path}")
        
        generated_files = generator.generate(str(output_path))
        
        metadata = generator.get_metadata()
        metadata_file = output_path / "metadata.json"
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Successfully generated {len(generated_files)} objects")
        logger.info(f"Metadata saved to {metadata_file}")
        
        # Print summary
        print(f"Generated {len(generated_files)} novel objects:")
        print(f"  - Friction range: [{args.friction_min}, {args.friction_max}]")
        print(f"  - Seed: {args.seed}")
        print(f"  - Output directory: {output_path}")
        print(f"  - Metadata file: {metadata_file}")
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        sys.exit(1)
    except IOError as e:
        logger.error(f"File I/O error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()