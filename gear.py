import sys
import numpy as np
import argparse
import itertools

import backends.dxf
import backends.text

from shapely.ops import unary_union
from shapely.geometry import Point, MultiPoint, Polygon, box
from shapely.affinity import rotate, scale, translate


def rot_matrix(x):
    """Creates a 2D rotation matrix."""
    c, s = np.cos(x), np.sin(x)
    return np.array([[c, -s], [s, c]])


def rotation(X, angle, center=None):
    """Applies rotation transformation to points."""
    if center is None:
        return np.dot(X, rot_matrix(angle))
    else:
        return np.dot(X - center, rot_matrix(angle)) + center


def deg2rad(x):
    """Converts degrees to radians."""
    return (np.pi / 180) * x


def generate(teeth_count=8, module=2.0, pressure_angle=deg2rad(20.0), backlash=0.0, frame_count=16, profile_shift=0.5, clearance_factor=0.167):
    """
    Generates a 2D gear profile using rack cutting principles, now with:
    - Profile shifting (x)
    - Adjustable clearance

    Args:
    - teeth_count: Number of teeth
    - module: Defines gear size
    - pressure_angle: Standardized pressure angle (default 20°)
    - backlash: Space left between meshing teeth
    - frame_count: Number of interpolation steps for smooth transition
    - profile_shift: Amount of profile shift (x), default = 0 (standard gear)
    - clearance_factor: Factor for clearance (default 0.167m)
    """

    # Step 1: Compute Correct Gear Parameters (Profile Shift Considered)
    pitch_diameter = module * (teeth_count + 2 * profile_shift)  # Corrected formula with profile shift
    pitch_radius = pitch_diameter / 2
    circular_pitch = np.pi * module
    base_radius = pitch_radius * np.cos(pressure_angle)

    # Compute correct Tooth Thickness
    tooth_thickness = (circular_pitch / 2) - backlash  # 1/2 of circular pitch

    # Compute Addendum & Dedendum with adjustable clearance
    addendum = module
    clearance = clearance_factor * module  # User-defined or default 0.167m
    dedendum = module + clearance  # Standard depth

    # Compute Outer and Root Radii
    outer_radius = pitch_radius + addendum
    root_radius = pitch_radius - dedendum

    print(f"[DEBUG] Pitch Diameter: {pitch_diameter:.3f}")
    print(f"[DEBUG] Pitch Radius: {pitch_radius:.3f}")
    print(f"[DEBUG] Base Radius: {base_radius:.3f}")
    print(f"[DEBUG] Addendum Radius: {outer_radius:.3f}")
    print(f"[DEBUG] Dedendum Radius: {root_radius:.3f}")
    print(f"[DEBUG] Tooth Thickness: {tooth_thickness:.3f}")
    print(f"[DEBUG] Profile Shift: {profile_shift:.3f}")

    # Step 2: Define the Tooth Profile
    profile = np.array([
        [-(0.5 * tooth_thickness + addendum * np.tan(pressure_angle)),  addendum],
        [-(0.5 * tooth_thickness - dedendum * np.tan(pressure_angle)), -dedendum],
        [ (0.5 * tooth_thickness - dedendum * np.tan(pressure_angle)), -dedendum],
        [ (0.5 * tooth_thickness + addendum * np.tan(pressure_angle)),  addendum]
    ])

    # Step 3: Generate Full Gear Using Rotation & Rack Cutting
    poly_list = []
    prev_X = None
    l = 2 * tooth_thickness / pitch_radius  # Small angular movement per frame

    for theta in np.linspace(0, l, frame_count):
        X = rotation(profile + np.array([-theta * pitch_radius, pitch_radius]), theta)
        if prev_X is not None:
            poly_list.append(MultiPoint([x for x in X] + [x for x in prev_X]).convex_hull)
        prev_X = X

    # Step 4: Assemble the Full Gear
    tooth_poly = unary_union(poly_list)
    tooth_poly = tooth_poly.union(scale(tooth_poly, -1, 1, 1, Point(0., 0.)))

    gear_poly = Point(0., 0.).buffer(outer_radius)
    for i in range(teeth_count):
        gear_poly = rotate(gear_poly.difference(tooth_poly), (2 * np.pi) / teeth_count, Point(0., 0.), use_radians=True)

    return gear_poly, pitch_radius


def main():
    """Main function to handle CLI arguments and generate the gear profile."""
    parser = argparse.ArgumentParser(description="Generate 2D spur gear profiles with profile shifting and clearance.")
    parser.add_argument('-c', '--teeth-count', type=int, default=20, help="Number of teeth")
    parser.add_argument('-m', '--module', type=float, default=2.0, help="Module (Defines size of the gear)")
    parser.add_argument('-p', '--pressure-angle', type=float, default=20.0, help="Pressure angle in degrees")
    parser.add_argument('-b', '--backlash', type=float, default=0.1, help="Backlash")
    parser.add_argument('-x', '--profile-shift', type=float, default=0.0, help="Profile shift coefficient (x)")
    parser.add_argument('-cf', '--clearance-factor', type=float, default=0.167, help="Clearance factor (default 0.167m)")
    parser.add_argument('-n', '--frame-count', type=int, default=16, help="Number of frames for interpolation")
    parser.add_argument('-t', '--output-type', choices=['dxf', 'text'], default='dxf', help="Output file format")
    parser.add_argument('-o', '--output-path', default='out', help="Output file name")

    args = parser.parse_args()

    # Generate the gear
    gear_poly, pitch_radius = generate(
        args.teeth_count, args.module, deg2rad(args.pressure_angle),
        args.backlash, args.frame_count, args.profile_shift, args.clearance_factor
    )

    print(f'Generated gear with pitch radius = {pitch_radius:.3f}')

    # Write the shape to the output file
    with open(args.output_path, 'w') as f:
        if args.output_type == 'dxf':
            backends.dxf.write(f, gear_poly)
        elif args.output_type == 'text':
            backends.text.write(f, gear_poly)


if __name__ == "__main__":
    main()