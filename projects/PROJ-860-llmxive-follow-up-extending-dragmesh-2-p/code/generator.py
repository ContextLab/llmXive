"""
Novel Object Set Generator for Virtual Tactile Zero-Shot Adaptation.

This module implements the `NovelObjectSet` class to generate randomized
articulated geometries with varying friction coefficients for zero-shot
evaluation (FR-003).
"""

import os
import math
import random
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Import existing utilities from the project
from seed_config import set_seeds


class NovelObjectSet:
    """
    Generates a set of randomized articulated geometries with friction coefficients
    uniformly distributed across a specified range.

    The generated objects are saved as URDF/XML files to the specified output directory.
    Each object represents a simple articulated mechanism (e.g., a hinge or slider)
    with randomized physical properties to simulate diverse tactile interactions.

    Attributes:
        count (int): Number of objects to generate.
        seed (int): Random seed for reproducibility.
        friction_min (float): Minimum friction coefficient.
        friction_max (float): Maximum friction coefficient.
        output_dir (str): Directory to save generated files.
    """

    def __init__(
        self,
        count: int,
        seed: int,
        friction_min: float,
        friction_max: float,
        output_dir: str = "data/generated"
    ):
        """
        Initialize the NovelObjectSet generator.

        Args:
            count: Number of objects to generate.
            seed: Random seed for reproducibility.
            friction_min: Minimum friction coefficient (0.0 to 2.5).
            friction_max: Maximum friction coefficient (0.0 to 2.5).
            output_dir: Directory to save generated URDF/XML files.
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("Count must be a positive integer.")
        if friction_min < 0.0 or friction_max > 2.5 or friction_min > friction_max:
            raise ValueError(f"Friction must be in [0.0, 2.5] and min <= max. Got [{friction_min}, {friction_max}].")

        self.count = count
        self.seed = seed
        self.friction_min = friction_min
        self.friction_max = friction_max
        self.output_dir = output_dir

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Set random seeds for reproducibility
        set_seeds(seed)

    def _generate_friction(self) -> float:
        """
        Generate a random friction coefficient uniformly distributed
        between friction_min and friction_max.

        Returns:
            float: Random friction coefficient.
        """
        return random.uniform(self.friction_min, self.friction_max)

    def _generate_geometry_params(self, object_id: int) -> Dict[str, Any]:
        """
        Generate randomized geometric parameters for an object.

        Args:
            object_id: Unique identifier for the object.

        Returns:
            Dict containing geometry parameters (dimensions, masses, etc.).
        """
        # Randomize dimensions within reasonable physical bounds
        base_size = random.uniform(0.05, 0.15)  # 5cm to 15cm
        mass = random.uniform(0.1, 1.0)  # 100g to 1kg

        return {
            "base_size": base_size,
            "link_size": base_size * random.uniform(0.8, 1.2),
            "mass": mass,
            "link_mass": mass * random.uniform(0.5, 1.5),
            "joint_type": random.choice(["hinge", "slider"]),
            "object_id": object_id
        }

    def _create_urdf(self, params: Dict[str, Any], friction: float) -> str:
        """
        Create a URDF string for a simple articulated object.

        Args:
            params: Geometry parameters.
            friction: Friction coefficient for contact materials.

        Returns:
            str: URDF XML content.
        """
        base_size = params["base_size"]
        link_size = params["link_size"]
        mass = params["mass"]
        link_mass = params["link_mass"]
        joint_type = params["joint_type"]
        object_id = params["object_id"]

        # Material definition with friction
        material_xml = f"""
<material name="tactile_material_{object_id}">
    <color rgba="0.8 0.8 0.8 1.0"/>
    <friction>{friction}</friction>
</material>
        """

        # Base link
        base_link = f"""
<link name="base_link">
    <visual>
        <geometry>
            <box size="{base_size} {base_size} {base_size}"/>
        </geometry>
        <material name="tactile_material_{object_id}"/>
    </visual>
    <collision>
        <geometry>
            <box size="{base_size} {base_size} {base_size}"/>
        </geometry>
    </collision>
    <inertial>
        <mass value="{mass}"/>
        <inertia ixx="{mass * base_size**2 / 12}" ixy="0.0" ixz="0.0"
                 iyy="{mass * base_size**2 / 12}" iyz="0.0"
                 izz="{mass * base_size**2 / 12}"/>
    </inertial>
</link>
        """

        # Joint definition
        if joint_type == "hinge":
            joint_xml = f"""
<joint name="joint_{object_id}" type="continuous">
    <parent link="base_link"/>
    <child link="link_{object_id}"/>
    <origin xyz="{base_size/2} 0 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="10.0" velocity="1.0"/>
    <dynamics damping="0.1" friction="{friction}"/>
</joint>
            """
            link_size_z = link_size
            link_size_x = link_size
            link_size_y = link_size
        else:  # slider
            joint_xml = f"""
<joint name="joint_{object_id}" type="prismatic">
    <parent link="base_link"/>
    <child link="link_{object_id}"/>
    <origin xyz="{base_size/2} 0 0" rpy="0 0 0"/>
    <axis xyz="1 0 0"/>
    <limit lower="-0.5" upper="0.5" effort="10.0" velocity="1.0"/>
    <dynamics damping="0.1" friction="{friction}"/>
</joint>
            """
            link_size_z = link_size
            link_size_x = link_size
            link_size_y = link_size

        # Moving link
        link_xml = f"""
<link name="link_{object_id}">
    <visual>
        <geometry>
            <box size="{link_size_x} {link_size_y} {link_size_z}"/>
        </geometry>
        <material name="tactile_material_{object_id}"/>
    </visual>
    <collision>
        <geometry>
            <box size="{link_size_x} {link_size_y} {link_size_z}"/>
        </geometry>
    </collision>
    <inertial>
        <mass value="{link_mass}"/>
        <inertia ixx="{link_mass * link_size_x**2 / 12}" ixy="0.0" ixz="0.0"
                 iyy="{link_mass * link_size_y**2 / 12}" iyz="0.0"
                 izz="{link_mass * link_size_z**2 / 12}"/>
    </inertial>
</link>
        """

        # Assemble URDF
        urdf_content = f"""<?xml version="1.0"?>
<robot name="novel_object_{object_id}">
    {material_xml.strip()}
    {base_link.strip()}
    {joint_xml.strip()}
    {link_xml.strip()}
</robot>
"""
        return urdf_content

    def generate(self) -> List[str]:
        """
        Generate the set of novel objects and save them to disk.

        Returns:
            List[str]: Paths to the generated URDF files.
        """
        generated_files = []

        for i in range(self.count):
            # Generate random parameters
            friction = self._generate_friction()
            params = self._generate_geometry_params(i)

            # Create URDF content
            urdf_content = self._create_urdf(params, friction)

            # Save to file
            filename = f"novel_object_{params['object_id']:03d}.urdf"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w') as f:
                f.write(urdf_content)

            generated_files.append(filepath)

        return generated_files


def main():
    """
    Command-line entry point for generating novel object sets.

    Usage:
        python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 1.2 --output data/generated/
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a set of randomized articulated geometries for zero-shot evaluation."
    )
    parser.add_argument(
        "--count", type=int, required=True,
        help="Number of objects to generate."
    )
    parser.add_argument(
        "--seed", type=int, required=True,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--friction-min", type=float, required=True,
        help="Minimum friction coefficient (0.0 to 2.5)."
    )
    parser.add_argument(
        "--friction-max", type=float, required=True,
        help="Maximum friction coefficient (0.0 to 2.5)."
    )
    parser.add_argument(
        "--output", type=str, default="data/generated",
        help="Output directory for generated files."
    )

    args = parser.parse_args()

    # Validate arguments
    if args.friction_min < 0.0 or args.friction_max > 2.5:
        parser.error("Friction coefficients must be between 0.0 and 2.5.")
    if args.friction_min > args.friction_max:
        parser.error("friction-min must be less than or equal to friction-max.")

    # Initialize generator
    generator = NovelObjectSet(
        count=args.count,
        seed=args.seed,
        friction_min=args.friction_min,
        friction_max=args.friction_max,
        output_dir=args.output
    )

    # Generate objects
    print(f"Generating {args.count} novel objects with friction in [{args.friction_min}, {args.friction_max}]...")
    files = generator.generate()

    print(f"Successfully generated {len(files)} objects:")
    for f in files:
        print(f"  - {f}")

    print(f"Generation complete. Files saved to: {args.output}")


if __name__ == "__main__":
    main()
