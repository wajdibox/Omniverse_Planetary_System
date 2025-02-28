import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from shapely.geometry import MultiPoint
from shapely.affinity import rotate
from gear import rotation, generate  # Import from main gear script
import matplotlib.widgets as widgets

# ===========================
# CONFIGURATION
# ===========================
teeth_count = 20  # Number of teeth
module = 2.0  # Module (size factor)
pressure_angle_deg = 20.0  # Pressure angle in degrees
backlash = 0.1  # Backlash
frame_count = 16  # Number of steps for smoother interpolation
profile_shift = 0.0  # Profile shift coefficient
clearance_factor = 0.167  # Clearance factor

# ===========================
# COMPUTE GEAR PARAMETERS
# ===========================
pressure_angle = np.radians(pressure_angle_deg)
pitch_radius = (teeth_count * module) / 2
circular_pitch = np.pi * module
base_radius = pitch_radius * np.cos(pressure_angle)
tooth_thickness = (circular_pitch / 2) - backlash
addendum = module
clearance = clearance_factor * module
dedendum = module + clearance
outer_radius = pitch_radius + addendum
root_radius = pitch_radius - dedendum

# ===========================
# DEFINE TRAPEZOID CUTTER PROFILE
# ===========================
profile = np.array([
    [-(0.5 * tooth_thickness + addendum * np.tan(pressure_angle)),  addendum],
    [-(0.5 * tooth_thickness - dedendum * np.tan(pressure_angle)), -dedendum],
    [(0.5 * tooth_thickness - dedendum * np.tan(pressure_angle)), -dedendum],
    [(0.5 * tooth_thickness + addendum * np.tan(pressure_angle)),  addendum]
])

l = 2 * tooth_thickness / pitch_radius  # Small angular step per frame
angles = np.linspace(0, l, frame_count)

# ===========================
# PLOTTING SETUP
# ===========================
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(-pitch_radius * 1.5, pitch_radius * 1.5)
ax.set_ylim(-pitch_radius * 1.5, pitch_radius * 1.5)
ax.set_aspect('equal')
ax.set_title("Step-by-Step Gear Cutting Process")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.grid(True)

# Store cutter shapes for animation
trapezes = []
prev_X = None

for theta in angles:
    X = rotation(profile + np.array([-theta * pitch_radius, pitch_radius]), theta)
    if prev_X is not None:
        trapezes.append(MultiPoint([x for x in X] + [x for x in prev_X]).convex_hull)
    prev_X = X

# ===========================
# ANIMATION FUNCTION
# ===========================
trapeze_patches = []
paused = False  # Pause flag


def update(frame):
    """Draws each step of the cutting process."""
    ax.clear()
    ax.set_xlim(-pitch_radius * 1.5, pitch_radius * 1.5)
    ax.set_ylim(-pitch_radius * 1.5, pitch_radius * 1.5)
    ax.set_aspect('equal')
    ax.set_title("Step-by-Step Gear Cutting Process")
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.grid(True)

    for i in range(frame + 1):  # Draw each trapeze up to current step
        patch = plt.Polygon(np.array(trapezes[i].exterior.coords), edgecolor='black', facecolor='gray', alpha=0.6)
        ax.add_patch(patch)

    # Draw base gear blank (circle)
    circle = plt.Circle((0, 0), outer_radius, color='lightblue', fill=False, linestyle='dashed')
    ax.add_patch(circle)

    return trapeze_patches


def toggle_animation(event):
    """Pauses and resumes the animation."""
    global paused
    if paused:
        ani.event_source.start()  # Resume animation
        paused = False
        pause_button.label.set_text("Pause")
    else:
        ani.event_source.stop()  # Pause animation
        paused = True
        pause_button.label.set_text("Resume")


def restart_animation(event):
    """Restarts the animation from the beginning."""
    global paused
    paused = False
    ani.event_source.stop()
    ani.frame_seq = ani.new_frame_seq()  # Reset frames
    ani.event_source.start()
    pause_button.label.set_text("Pause")


# ===========================
# ADDING UI CONTROLS
# ===========================
ax_pause = plt.axes([0.7, 0.02, 0.1, 0.05])
pause_button = widgets.Button(ax_pause, "Pause")
pause_button.on_clicked(toggle_animation)

ax_restart = plt.axes([0.81, 0.02, 0.1, 0.05])
restart_button = widgets.Button(ax_restart, "Restart")
restart_button.on_clicked(restart_animation)

# ===========================
# RUN ANIMATION
# ===========================
ani = animation.FuncAnimation(fig, update, frames=len(trapezes), repeat=False, interval=500)
plt.show()