import sys
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shapely.affinity import scale
from gear import generate  # Assuming gear_generator.py contains the gear generation function
import pyperclip

class GearGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gear Generator")
        self.root.geometry("1000x600")
        
        self.units = tk.StringVar(value="mm")
        self.teeth_count = tk.IntVar(value=20)
        self.module = tk.DoubleVar(value=2.0)
        self.pressure_angle = tk.DoubleVar(value=20.0)
        self.backlash = tk.DoubleVar(value=0.1)
        self.profile_shift = tk.DoubleVar(value=0.0)
        self.clearance_factor = tk.DoubleVar(value=0.167)

        self.create_ui()
        self.update_gear()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle graceful exit
    
    def create_ui(self):
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Unit Selection
        tk.Label(control_frame, text="Select Units:").grid(row=0, column=0, sticky=tk.W)
        unit_menu = ttk.Combobox(control_frame, textvariable=self.units, values=["mm", "cm", "m"], state="readonly")
        unit_menu.grid(row=0, column=1, padx=5, pady=2)

        # Parameter Inputs
        parameters = [
            ("Teeth Count", self.teeth_count, 10, 200, 1),
            ("Module", self.module, 0.5, 10, 0.1),
            ("Pressure Angle", self.pressure_angle, 10, 30, 0.1),
            ("Backlash", self.backlash, 0.0, 1.0, 0.01),
            ("Profile Shift", self.profile_shift, -1.0, 1.0, 0.01),
            ("Clearance Factor", self.clearance_factor, 0.0, 0.5, 0.01)
        ]

        self.sliders = []
        for i, (label, var, min_val, max_val, step) in enumerate(parameters):
            tk.Label(control_frame, text=label).grid(row=i+1, column=0, sticky=tk.W)
            entry = tk.Entry(control_frame, textvariable=var, width=5)
            entry.grid(row=i+1, column=1, padx=5)
            slider = tk.Scale(control_frame, variable=var, from_=min_val, to=max_val, resolution=step, orient=tk.HORIZONTAL, length=200, command=lambda val, v=var: v.set(float(val)))
            slider.grid(row=i+1, column=2, padx=5)
            self.sliders.append(slider)
            
        # Gear Visualization Frame
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Data Display Frame
        self.data_frame = ttk.Treeview(self.root, columns=("Parameter", "Value"), show="headings", height=6)
        self.data_frame.heading("Parameter", text="Parameter")
        self.data_frame.heading("Value", text="Value")
        self.data_frame.column("Parameter", width=150)
        self.data_frame.column("Value", width=80)
        self.data_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)
        
        # Copy CLI Command Button
        self.cli_command = tk.StringVar()
        self.copy_button = tk.Button(self.root, text="Copy CLI Command", command=self.copy_command)
        self.copy_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Update Button
        self.update_button = tk.Button(control_frame, text="Update Gear", command=self.update_gear)
        self.update_button.grid(row=len(parameters)+1, column=0, columnspan=3, pady=10)
        
    def update_gear(self):
        self.ax.clear()
        
        # Generate Gear
        gear, pitch_radius = generate(
            self.teeth_count.get(), self.module.get(), np.radians(self.pressure_angle.get()),
            self.backlash.get(), 16, self.profile_shift.get(), self.clearance_factor.get()
        )
        
        scaled_gear = scale(gear, xfact=1, yfact=1, origin=(0, 0))
        x, y = scaled_gear.exterior.xy
        self.ax.plot(x, y, "b-")
        self.ax.set_title("Gear Visualization")
        self.ax.set_xlim(-pitch_radius * 1.2, pitch_radius * 1.2)
        self.ax.set_ylim(-pitch_radius * 1.2, pitch_radius * 1.2)
        self.ax.set_aspect("equal")
        self.canvas.draw()

        # Update Data Table
        self.data_frame.delete(*self.data_frame.get_children())
        gear_data = [
            ("Teeth Count", self.teeth_count.get()),
            ("Module (mm per tooth)", self.module.get()),
            ("Pressure Angle (deg)", self.pressure_angle.get()),
            ("Backlash (mm)", self.backlash.get()),
            ("Profile Shift", self.profile_shift.get()),
            ("Clearance Factor", self.clearance_factor.get()),
            ("Pitch Radius (mm)", pitch_radius)
        ]
        for param, value in gear_data:
            self.data_frame.insert("", "end", values=(param, round(value, 3)))
        
        # Generate CLI Command
        self.cli_command.set(
            f"python gear_generator.py -c {self.teeth_count.get()} -m {self.module.get()} "
            f"-p {self.pressure_angle.get()} -b {self.backlash.get()} "
            f"-x {self.profile_shift.get()} -cf {self.clearance_factor.get()} -n 16 "
            f"-t dxf -o generated_gear.dxf"
        )
    
    def copy_command(self):
        pyperclip.copy(self.cli_command.get())
        messagebox.showinfo("CLI Command", "Copied to clipboard!")
    
    def on_closing(self):
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GearGeneratorApp(root)
    root.mainloop()