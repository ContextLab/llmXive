"""
Novel Object Set Generator for Virtual Tactile Adaptation.

Generates a diverse set of randomized articulated geometries with friction
coefficients uniformly distributed across a broad range.
"""
import os
import math
import random
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class NovelObjectSet:
    """
    Generates articulated mesh assets (URDF/MJCF style) with randomized
    geometry and friction properties for zero-shot adaptation testing.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with a specific seed for reproducibility.

        Args:
            seed: Random seed. If None, uses system randomness.
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.seed = seed

    def _create_box_mesh(self, size: Tuple[float, float, float], color: List[float]) -> ET.Element:
        """Create a box mesh element for the URDF."""
        mesh = ET.Element("mesh")
        mesh.set("filename", "package://data/generated/box.stl") # Placeholder for actual mesh gen or reuse
        mesh.set("scale", f"{size[0]} {size[1]} {size[2]}")
        return mesh

    def _create_visual(self, position: Tuple[float, float, float], rotation: Tuple[float, float, float], color: List[float], size: Tuple[float, float, float]) -> ET.Element:
        """Create a visual element."""
        visual = ET.Element("visual")
        if position:
            origin = ET.SubElement(visual, "origin")
            origin.set("xyz", f"{position[0]} {position[1]} {position[2]}")
            origin.set("rpy", f"{rotation[0]} {rotation[1]} {rotation[2]}")

        geometry = ET.SubElement(visual, "geometry")
        box = ET.SubElement(geometry, "box")
        box.set("size", f"{size[0]} {size[1]} {size[2]}")

        material = ET.SubElement(visual, "material")
        material.set("name", "random_material")
        color_elem = ET.SubElement(material, "color")
        color_elem.set("rgba", f"{color[0]} {color[1]} {color[2]} {color[3]}")

        return visual

    def _create_collision(self, position: Tuple[float, float, float], rotation: Tuple[float, float, float], size: Tuple[float, float, float]) -> ET.Element:
        """Create a collision element."""
        collision = ET.Element("collision")
        if position:
            origin = ET.SubElement(collision, "origin")
            origin.set("xyz", f"{position[0]} {position[1]} {position[2]}")
            origin.set("rpy", f"{rotation[0]} {rotation[1]} {rotation[2]}")

        geometry = ET.SubElement(collision, "geometry")
        box = ET.SubElement(geometry, "box")
        box.set("size", f"{size[0]} {size[1]} {size[2]}")

        return collision

    def _create_joint(self, name: str, parent: str, child: str, joint_type: str, axis: Tuple[float, float, float], limit: Tuple[float, float]) -> ET.Element:
        """Create a joint element."""
        joint = ET.Element("joint")
        joint.set("name", name)
        joint.set("type", joint_type)

        parent_elem = ET.SubElement(joint, "parent")
        parent_elem.set("link", parent)

        child_elem = ET.SubElement(joint, "child")
        child_elem.set("link", child)

        origin = ET.SubElement(joint, "origin")
        origin.set("xyz", "0 0 0")
        origin.set("rpy", "0 0 0")

        axis_elem = ET.SubElement(joint, "axis")
        axis_elem.set("xyz", f"{axis[0]} {axis[1]} {axis[2]}")

        if joint_type != "fixed":
            limit_elem = ET.SubElement(joint, "limit")
            limit_elem.set("lower", f"{limit[0]}")
            limit_elem.set("upper", f"{limit[1]}")
            limit_elem.set("effort", "100.0")
            limit_elem.set("velocity", "5.0")

        return joint

    def generate_object(self, object_id: int, friction_coef: float, seed_offset: int = 0) -> str:
        """
        Generate a single URDF string for a novel object.

        Args:
            object_id: Unique identifier for the object.
            friction_coef: Friction coefficient for the material.
            seed_offset: Offset to randomize geometry for this specific object.

        Returns:
            URDF string content.
        """
        # Use a local random state to ensure reproducibility per object_id
        local_random = random.Random(self.seed + object_id + seed_offset if self.seed else object_id + seed_offset)
        np_local = np.random.RandomState(self.seed + object_id + seed_offset if self.seed else object_id + seed_offset)

        # Generate randomized geometry parameters
        # Base link (static)
        base_size = (
            local_random.uniform(0.1, 0.3),
            local_random.uniform(0.1, 0.3),
            local_random.uniform(0.05, 0.15)
        )

        # Mobile link
        mobile_size = (
            local_random.uniform(0.05, 0.2),
            local_random.uniform(0.05, 0.2),
            local_random.uniform(0.05, 0.15)
        )

        # Joint configuration (prismatic for drag simulation)
        joint_type = "prismatic"
        joint_axis = (1.0, 0.0, 0.0) # Drag along X
        limit_range = (-0.2, 0.2)

        # Colors
        base_color = [
            local_random.uniform(0.2, 0.8),
            local_random.uniform(0.2, 0.8),
            local_random.uniform(0.2, 0.8),
            1.0
        ]
        mobile_color = [
            local_random.uniform(0.2, 0.8),
            local_random.uniform(0.2, 0.8),
            local_random.uniform(0.2, 0.8),
            1.0
        ]

        # Construct URDF
        robot = ET.Element("robot", name=f"novel_object_{object_id}")

        # Material definition with friction
        material = ET.SubElement(robot, "material")
        material.set("name", f"friction_{friction_coef:.2f}")
        # Note: URDF friction is often handled in the contact tag or via a specific plugin.
        # For this simulation, we embed the friction value in a custom property or rely on the
        # environment's friction map. Here we add a custom attribute for the environment to read.
        prop = ET.SubElement(material, "parameter")
        prop.set("name", "mu")
        prop.set("value", str(friction_coef))

        # Base Link
        base_link = ET.SubElement(robot, "link", name="base_link")
        base_inertial = ET.SubElement(base_link, "inertial")
        ET.SubElement(base_inertial, "origin", xyz="0 0 0", rpy="0 0 0")
        ET.SubElement(base_inertial, "mass", value="1.0")
        ET.SubElement(base_inertial, "inertia", ixx="0.1", ixy="0", ixz="0", iyy="0.1", iyz="0", izz="0.1")

        base_vis = ET.SubElement(base_link, "visual")
        ET.SubElement(base_vis, "origin", xyz="0 0 0", rpy="0 0 0")
        base_geom = ET.SubElement(base_vis, "geometry")
        ET.SubElement(base_geom, "box", size=f"{base_size[0]} {base_size[1]} {base_size[2]}")
        base_mat = ET.SubElement(base_vis, "material", name="base_mat")
        ET.SubElement(base_mat, "color", rgba=f"{base_color[0]} {base_color[1]} {base_color[2]} {base_color[3]}")

        base_coll = ET.SubElement(base_link, "collision")
        ET.SubElement(base_coll, "origin", xyz="0 0 0", rpy="0 0 0")
        base_coll_geom = ET.SubElement(base_coll, "geometry")
        ET.SubElement(base_coll_geom, "box", size=f"{base_size[0]} {base_size[1]} {base_size[2]}")

        # Mobile Link
        mobile_link = ET.SubElement(robot, "link", name="mobile_link")
        mobile_inertial = ET.SubElement(mobile_link, "inertial")
        ET.SubElement(mobile_inertial, "origin", xyz="0 0 0", rpy="0 0 0")
        ET.SubElement(mobile_inertial, "mass", value="0.5")
        ET.SubElement(mobile_inertial, "inertia", ixx="0.05", ixy="0", ixz="0", iyy="0.05", iyz="0", izz="0.05")

        mobile_vis = ET.SubElement(mobile_link, "visual")
        ET.SubElement(mobile_vis, "origin", xyz="0 0 0", rpy="0 0 0")
        mobile_geom = ET.SubElement(mobile_vis, "geometry")
        ET.SubElement(mobile_geom, "box", size=f"{mobile_size[0]} {mobile_size[1]} {mobile_size[2]}")
        mobile_mat = ET.SubElement(mobile_vis, "material", name="mobile_mat")
        ET.SubElement(mobile_mat, "color", rgba=f"{mobile_color[0]} {mobile_color[1]} {mobile_color[2]} {mobile_color[3]}")

        mobile_coll = ET.SubElement(mobile_link, "collision")
        ET.SubElement(mobile_coll, "origin", xyz="0 0 0", rpy="0 0 0")
        mobile_coll_geom = ET.SubElement(mobile_coll, "geometry")
        ET.SubElement(mobile_coll_geom, "box", size=f"{mobile_size[0]} {mobile_size[1]} {mobile_size[2]}")

        # Contact properties for friction (PyBullet specific handling often requires setting friction in contact)
        # We add a contact tag if the environment supports it, otherwise friction is set globally.
        # Here we define the contact surface.
        contact = ET.SubElement(mobile_link, "contact")
        ET.SubElement(contact, "lateral_friction", value=str(friction_coef))
        ET.SubElement(contact, "rolling_friction", value=str(friction_coef * 0.1))
        ET.SubElement(contact, "spinning_friction", value=str(friction_coef * 0.1))

        # Joint
        joint = ET.SubElement(robot, "joint", name="drag_joint", type=joint_type)
        ET.SubElement(joint, "parent", link="base_link")
        ET.SubElement(joint, "child", link="mobile_link")
        ET.SubElement(joint, "origin", xyz="0 0 0", rpy="0 0 0")
        ET.SubElement(joint, "axis", xyz="1 0 0")
        limit = ET.SubElement(joint, "limit")
        limit.set("lower", str(limit_range[0]))
        limit.set("upper", str(limit_range[1]))
        limit.set("effort", "100.0")
        limit.set("velocity", "5.0")

        # Serialize to string
        ET.indent(robot, space="  ")
        return ET.tostring(robot, encoding="unicode")

    def generate_set(self, count: int, friction_min: float, friction_max: float, output_dir: str, seed_offset: int = 0) -> List[str]:
        """
        Generate a set of novel objects and save them to disk.

        Args:
            count: Number of objects to generate.
            friction_min: Minimum friction coefficient.
            friction_max: Maximum friction coefficient.
            output_dir: Directory to save the URDF files.
            seed_offset: Offset for the random seed to ensure diversity across runs.

        Returns:
            List of paths to the generated URDF files.
        """
        os.makedirs(output_dir, exist_ok=True)
        generated_files = []

        # Generate friction coefficients uniformly distributed
        friction_values = np.linspace(friction_min, friction_max, count)
        # Add slight random jitter to ensure uniqueness and broad range coverage
        jitter = (friction_max - friction_min) * 0.05
        friction_values = friction_values + np.random.uniform(-jitter, jitter, count)
        friction_values = np.clip(friction_values, friction_min, friction_max)

        for i, mu in enumerate(friction_values):
            object_id = i + 1
            urdf_content = self.generate_object(object_id, mu, seed_offset=seed_offset)
            filename = f"object_{object_id:03d}_mu_{mu:.2f}.urdf"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                f.write(urdf_content)

            generated_files.append(filepath)

        return generated_files

def main():
    """
    CLI entry point for generating the novel object set.
    Usage: python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 2.0 --output data/generated/
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate novel object set for zero-shot adaptation.")
    parser.add_argument("--count", type=int, default=30, help="Number of objects to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--friction-min", type=float, default=0.1, help="Minimum friction coefficient.")
    parser.add_argument("--friction-max", type=float, default=2.0, help="Maximum friction coefficient.")
    parser.add_argument("--output", type=str, default="data/generated/", help="Output directory for URDF files.")

    args = parser.parse_args()

    print(f"Generating {args.count} novel objects with friction in [{args.friction_min}, {args.friction_max}]...")
    print(f"Seed: {args.seed}, Output: {args.output}")

    generator = NovelObjectSet(seed=args.seed)
    files = generator.generate_set(
        count=args.count,
        friction_min=args.friction_min,
        friction_max=args.friction_max,
        output_dir=args.output
    )

    print(f"Successfully generated {len(files)} objects:")
    for f in files:
        print(f"  - {f}")

if __name__ == "__main__":
    main()
