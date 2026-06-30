import os
import sys
import json
import time
import csv
import argparse

# Try to import pybullet; if missing, we cannot run physics.
# We do NOT fallback to synthetic data.
try:
    import pybullet as p
    import pybullet_data
except ImportError:
    print("ERROR: pybullet is required but not installed. Cannot run physics simulation.")
    print("Install via: pip install pybullet")
    sys.exit(1)

import numpy as np
import matplotlib.pyplot as plt

# Constants
SIMULATION_DT = 1.0 / 240.0
MAX_STEPS = 500  # Short episode to fit time budget
TARGET_ANGLE = np.radians(80.0)  # Target opening angle in radians

# Paths for outputs
DATA_DIR = "data"
FIGURES_DIR = "figures"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def create_articulated_box():
    """
    Creates a simple articulated object: a box with a hinged lid.
    This replaces the complex GAPartNet meshes with a minimal geometric proxy
    that still exhibits the physics of an articulated object.
    """
    # Load ground plane
    plane_id = p.loadURDF("plane.urdf", globalScaling=1.0)

    # Base box (the "cup")
    base_shape = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.1])
    base_mass = 1.0
    base_pos = [0, 0, 0.1]
    base_quat = [0, 0, 0, 1]
    base_id = p.createMultiBody(base_mass, base_shape, base_shape, base_pos, base_quat)
    p.changeDynamics(base_id, -1, lateralFriction=1.0)

    # Lid box (the "moving part")
    lid_shape = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.02])
    lid_mass = 0.5
    # Initial position: closed on top of base
    lid_pos = [0, 0, 0.12] 
    lid_quat = [0, 0, 0, 1]
    
    # Create joint: Revolute (hinge)
    # Axis Y (hinge along width)
    joint_axis = [0, 1, 0]
    # Pivot point: edge of the base
    pivot_pos = [0, 0.1, 0.1] 
    
    # Link index -1 means base is parent, 0 is child (lid)
    # We attach the lid to the base
    lid_id = p.createMultiBody(
        baseMass=lid_mass,
        baseInertialFramePosition=[0, 0, 0],
        baseVisualShape=lid_shape,
        basePosition=lid_pos,
        baseOrientation=lid_quat,
        parentLinkIndex=-1, # Base ID is -1 relative to the new body? No, we need to attach to base_id
        # Actually, createMultiBody creates a single body. We need to use createConstraint or load with URDF.
        # Let's use a simpler approach: Load a pre-made URDF string or use createConstraint.
        # For robustness in a single script, we will build the constraint manually.
    )
    
    # Re-doing with createMultiBody for the lid, then attaching
    lid_id = p.createMultiBody(
        baseMass=lid_mass,
        baseInertialFramePosition=[0, 0, 0],
        baseVisualShape=lid_shape,
        basePosition=lid_pos,
        baseOrientation=lid_quat
    )
    
    # Create the hinge constraint
    # Constraint type: JOINT_REVOLUTE
    # Body A: Base, Link A: -1
    # Body B: Lid, Link B: -1 (root of lid)
    # Pivot in A: [0, 0.1, 0.1]
    # Pivot in B: [0, -0.1, 0] (relative to lid center)
    # Axis: [0, 1, 0]
    
    cid = p.createConstraint(
        parentBodyUniqueId=base_id,
        parentLinkIndex=-1,
        childBodyUniqueId=lid_id,
        childLinkIndex=-1,
        jointType=p.JOINT_REVOLUTE,
        jointAxis=[0, 1, 0],
        parentFramePosition=[0, 0.1, 0.1],
        childFramePosition=[0, -0.1, 0],
        childFrameOrientation=[0, 0, 0, 1]
    )
    
    # Set initial position of lid to match the constraint
    # The constraint is created at the current position, so we just need to ensure physics starts correctly.
    # We need to enable the motor or set limits if we want control.
    p.changeConstraint(cid, maxForce=500.0) # High force to allow movement
    
    return base_id, lid_id, cid

def setup_simulation(damping_factor):
    """
    Sets up the physics engine with a specific damping value.
    Higher damping simulates higher "contact load" or friction in the joint.
    """
    p.disconnect()
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(SIMULATION_DT)
    
    # Create the object
    base_id, lid_id, cid = create_articulated_box()
    
    # Apply damping to the joint
    # We use setJointMotorControl2 to set velocity target and gain, 
    # but for damping simulation, we modify the joint dynamics.
    # In Bullet, we can set joint damping via changeDynamics on the link.
    # However, for a constraint, we often use the constraint's own damping or
    # set the joint properties if we treat it as a motor.
    
    # Simulate "contact load" by increasing the damping of the joint's rotational motion.
    # We will use the constraint's motor capabilities to control it, but add artificial damping.
    # Alternatively, simpler: Use p.setJointMotorControl2 with position control and high damping.
    
    # Let's use the constraint to hold the joint, but we will control the lid directly
    # to simulate the "hand" applying torque.
    
    # Better approach for "damping":
    # We will control the lid via a PD controller (simulating the hand).
    # The "damping" will be a force opposing the velocity of the lid.
    
    p.setRealTimeSimulation(0)
    
    # Store IDs for the loop
    return {
        "base": base_id,
        "lid": lid_id,
        "constraint": cid,
        "damping": damping_factor
    }

def get_joint_angle(lid_id):
    """Get the current angle of the lid relative to the base."""
    # We need to calculate the angle from the quaternion or position.
    # Since it's a hinge on Y, we can look at the rotation.
    pos, quat = p.getBasePositionAndOrientation(lid_id)
    # Convert quaternion to euler
    euler = p.getEulerFromQuaternion(quat)
    # The hinge is around Y.
    return euler[1]

def run_episode(env_config, damping_val):
    """
    Runs a single episode attempting to open the lid.
    The "policy" is a simple PD controller trying to reach TARGET_ANGLE.
    Returns (success, final_angle, steps).
    """
    p.resetSimulation()
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(SIMULATION_DT)
    
    # Re-create object (simpler to reset simulation and rebuild than to manage state)
    # But to save time, we can just reset the body.
    # For this small scale, rebuilding is fine.
    
    base_id, lid_id, cid = create_articulated_box()
    
    # We will control the lid directly using setJointMotorControl2
    # But wait, the lid is a separate body connected by a constraint.
    # To control it, we can apply a force or set the constraint target.
    # Let's use the constraint's motor.
    
    p.setConstraint(cid, maxForce=500.0)
    p.setConstraint(cid, jointDamping=damping_val * 10.0) # Scale damping
    
    # Initial state
    current_angle = get_joint_angle(lid_id)
    target_angle = TARGET_ANGLE
    
    success = False
    final_angle = current_angle
    
    for step in range(MAX_STEPS):
        # 1. Calculate error
        current_angle = get_joint_angle(lid_id)
        error = target_angle - current_angle
        
        # 2. PD Control (Simulating the "Hand" policy)
        # Kp and Kd are tuned for a "nominal" load.
        Kp = 10.0
        Kd = 1.0
        
        # If damping is high, the Kd term might not be enough to overcome it,
        # or the motor force is limited.
        # We simulate the "Hand" applying a torque.
        torque = Kp * error - Kd * (current_angle - (current_angle + 0.01)) # Approx velocity
        
        # Limit torque to simulate actuator limits
        torque = np.clip(torque, -50.0, 50.0)
        
        # Apply torque to the lid (as a force on the constraint or body)
        # Since it's a constraint, we can set the target velocity or force.
        # Let's use setJointMotorControl2 on the constraint if possible, 
        # or apply force to the lid body.
        # Bullet constraints don't always support direct torque application easily in this setup.
        # Alternative: Apply a force to the lid's center of mass to rotate it.
        # Force = Torque / lever_arm. Lever arm ~ 0.1m.
        force_vec = [0, 0, 0]
        if abs(error) > 0.01:
            # Apply force in Z direction to rotate around Y
            # If angle is 0 (closed), we need to lift the front.
            # This is getting complex for a proxy.
            # Let's simplify: The "Hand" applies a velocity target to the constraint.
            pass
        
        # SIMPLIFIED CONTROL:
        # We will directly set the constraint's target velocity to move the lid.
        # The "damping" will resist this.
        # p.setConstraint(cid, targetVelocity=desired_vel, maxForce=500)
        
        # Let's try a simpler physics proxy:
        # The "Hand" applies a constant force to the lid's edge.
        # High damping makes the lid move slower or not at all.
        
        # Apply a force to the lid to rotate it
        # Force at [0, 0.1, 0.12] (front edge)
        force_pos = [0, 0.1, 0.12]
        # If we push up (Z), it rotates around Y.
        force_mag = 20.0 if error > 0 else 0.0
        
        # Apply force
        p.applyExternalForce(lid_id, -1, [0, 0, force_mag], force_pos, p.WORLD_FRAME)
        
        # Simulate Damping manually if the joint damping isn't enough
        # We can apply a counter-force proportional to velocity
        # Get velocity of the lid
        vel = p.getBaseVelocity(lid_id)
        # Angular velocity
        ang_vel = vel[4] # Index 4 is angular velocity around Y? 
        # Actually getBaseVelocity returns [lin_vel, ang_vel]
        # ang_vel is a tuple (wx, wy, wz)
        # We need the Y component.
        # Let's approximate:
        # p.getLinkState is better for joint angles, but for velocity we use getBaseVelocity
        
        # Manual damping: apply opposite force to rotation
        # This is a hack to simulate "contact load" without complex joint tuning
        # But let's trust the constraint damping we set earlier.
        
        p.stepSimulation()
        
        # Check success
        current_angle = get_joint_angle(lid_id)
        if current_angle >= np.radians(70.0): # 70 degrees is "open enough"
            success = True
            final_angle = current_angle
            break
            
    return success, current_angle, step

def main():
    print("Starting DragMesh-2 CPU Adaptation: Contact Load Sensitivity Sweep")
    print("This script simulates a simplified articulated object opening task.")
    print("It sweeps damping values to demonstrate the failure of simple controllers.")
    print("-" * 60)

    # Damping sweep: 0.0 (low friction) to 5.0 (high friction/contact load)
    damping_values = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
    
    results = []
    
    for damp in damping_values:
        print(f"Running simulation with damping factor: {damp}")
        success, final_angle, steps = run_episode(None, damp)
        progress = final_angle / TARGET_ANGLE
        results.append({
            "damping": damp,
            "success": int(success),
            "final_angle_rad": final_angle,
            "progress": progress,
            "steps": steps
        })
        print(f"  -> Success: {success}, Final Angle: {np.degrees(final_angle):.1f} deg")

    # Write CSV
    csv_path = os.path.join(DATA_DIR, "sweep_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["damping", "success", "final_angle_rad", "progress", "steps"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results written to {csv_path}")

    # Plot
    plt.figure(figsize=(8, 5))
    damp_vals = [r["damping"] for r in results]
    success_vals = [r["success"] for r in results]
    progress_vals = [r["progress"] for r in results]
    
    plt.subplot(1, 2, 1)
    plt.plot(damp_vals, success_vals, 'o-', color='red', label='Success (1/0)')
    plt.xlabel('Damping Factor (Contact Load)')
    plt.ylabel('Success Rate')
    plt.title('Task Success vs Contact Load')
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.1, 1.1)
    
    plt.subplot(1, 2, 2)
    plt.plot(damp_vals, progress_vals, 'o-', color='blue', label='Progress')
    plt.xlabel('Damping Factor (Contact Load)')
    plt.ylabel('Progress (0-1)')
    plt.title('Task Progress vs Contact Load')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig_path = os.path.join(FIGURES_DIR, "damping_sensitivity.png")
    plt.savefig(fig_path)
    print(f"Figure saved to {fig_path}")
    
    print("Done.")

if __name__ == "__main__":
    main()
