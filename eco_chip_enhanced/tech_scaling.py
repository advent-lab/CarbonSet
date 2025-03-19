import pandas as pd
import json
import os

tech_indices = [7, 10, 14, 22, 28]

def load_tables(dir_name=None):
    """Load the scaling tables from the JSON files with correct path handling."""
    
    
    if isinstance(dir_name, tuple):
        dir_name = dir_name[0]  # Extract first element of the tuple

    # Validate directory existence
    if not os.path.exists(dir_name):
        raise FileNotFoundError(f"Tech scaling directory not found: {dir_name}")
    

    # Load JSON files safely
    def load_json_file(file_name):
        file_path = dir_name + file_name  # Use relative path directly
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r') as f:
            return json.load(f)

    # Load scaling data
    logic_scaling = pd.DataFrame(data=load_json_file("logic_scaling.json"), index=tech_indices)
    analog_scaling = pd.DataFrame(data=load_json_file("analog_scaling.json"), index=tech_indices)
    sram_scaling = pd.DataFrame(data=load_json_file("sram_scaling.json"), index=tech_indices)
    
    tech_indices_package = tech_indices + [65]
    defect_density = pd.DataFrame(data=load_json_file("defect_density.json"), index=tech_indices_package)
    cpa = pd.DataFrame(data=load_json_file("cpa_scaling.json"), index=tech_indices_package)
    
    transistors_per_mm2 = pd.DataFrame(data=load_json_file("transistors_scaling.json"), index=tech_indices)
    gates_per_hr_per_core = pd.DataFrame(data=load_json_file("gates_perhr_scaling.json"), index=tech_indices)
    beolVfeol = pd.DataFrame(data=load_json_file("beol_feol_scaling.json"), index=tech_indices_package)
    dyn_pwr_ratio = pd.DataFrame(data=load_json_file("dyn_pwr_scaling.json"), index=tech_indices_package)

    return {
        "logic": logic_scaling,
        "analog": analog_scaling,
        "sram": sram_scaling, 
        "cpa": cpa,
        "defect_den": defect_density,
        "transistors_per_mm2": transistors_per_mm2,
        "gates_per_hr_per_core": gates_per_hr_per_core,
        "beolVfeol": beolVfeol,
        "dyn_pwr_ratio": dyn_pwr_ratio
    }
