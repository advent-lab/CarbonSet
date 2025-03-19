import re
import pandas as pd
import numpy as np
import os, sys, json
import shutil
# ---------------------------
# Usage example:
# ---------------------------
# Assuming your original DataFrame is named `df` and has columns:
#    DieSizeValue (float)
#    Die Size (mm^2) (string)
#
# df_monolithic, df_chiplet = separate_monolithic_and_chiplets(df)
#
# Now each of df_monolithic and df_chiplet has:
#  - the original columns,
#  - plus two new columns: "#dies" and "Avg Die Area"
#
# df_monolithic: will have #dies = 1, Avg Die Area = DieSizeValue
# df_chiplet:    will have #dies = a, Avg Die Area = b (from the "a x b" text)

def separate_monolithic_and_chiplets(df):
    # Prepare empty lists to store rows for each category
    monolithic_rows = []
    chiplet_rows = []
    
    for idx, row in df.iterrows():
        die_size_value = row['DieSizeValue']           # numeric
        die_size_str = str(row['Die Size (mm^2)'])     # string from the DataFrame

        # Attempt to parse the string as a float
        try:
            as_float = float(die_size_str)
            # If it exactly matches the numeric DieSizeValue, treat as monolithic
            if abs(as_float - die_size_value) < 1e-9:
                monolithic_rows.append({
                    **row,
                    '#dies': 1,
                    'Avg Die Area': die_size_value
                })
            else:
                # If it's a float but doesn't match exactly, treat as chiplet?
                # Or skip? This depends on your data's structure.
                # Typically, "chiplet" lines won't be float-castable, 
                # so adjust as needed.
                pass

        except ValueError:
            # Not float-castable -> likely "a x b" format for chiplet
            # Use regex to extract a and b
            match = re.match(r'^\s*(\d+)\s*x\s*([\d\.]+)\s*$', die_size_str)
            if match:
                a = int(match.group(1))            # number of dies
                b = float(match.group(2))          # average die area
                
                chiplet_rows.append({
                    **row,
                    '#dies': a,
                    'Avg Die Area': b
                })
            else:
                # If it doesn't match either pattern, handle or skip as needed
                pass

    # Convert the collected rows back to DataFrames
    df_monolithic = pd.DataFrame(monolithic_rows)
    df_chiplet = pd.DataFrame(chiplet_rows)
    
    return df_monolithic, df_chiplet


def generate_node_arch(num_of_dies: int, node: int,die_area: int, file_path: str) -> None:
    """
    Generates architecture.json and node_list.txt files based on the provided parameters.

    Args:
        num_of_dies (int): The number of dies to include in the architecture.
        node (int): The node value to be included in the architecture and node list.
        die_area (int): The area of each die.
        file_path (str): The directory path where the files will be saved.

    Returns:
        None
    """
    data = dict()
    # generate architecture.json
    for i in range(int(num_of_dies)):
        data[f"CPU_{i}"] = {
            "type": "logic",
            "area": int(die_area),
            "node": node
        }
    data["pkg_type"] = "RDL"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    arch_path = os.path.join(os.path.dirname(file_path), "architecture.json")

    with open(arch_path, "w") as json_file:
        json_file.write(json.dumps(data, indent=4))

    # Generate node_list.txt
    node_list_path = os.path.join(os.path.dirname(file_path), "node_list.txt")
    with open(node_list_path, "w") as node_file:
        node_file.write(f"[{node}]\n")

    

def copy_design_operation_package(src: str, dest: str) -> None:
    """
    Copies specific design and operation package files from the source directory to the destination directory.

    This function creates the destination directory if it does not exist and copies the following files from the source
    directory to the destination directory:
    - operationalC.json
    - packageC.json
    - designC.json

    Args:
        src (str): The source directory path where the files are located.
        dest (str): The destination directory path where the files will be copied.

    Returns:
        None
    """

    os.makedirs(dest, exist_ok=True)
    files_to_copy = ['operationalC.json', 'packageC.json', 'designC.json']
    for file_name in files_to_copy:
        src_file = os.path.join(src, file_name)
        des_file = os.path.join(dest, file_name)
        if os.path.exists(src_file):
            shutil.copy(src_file, des_file)



def generate_probabilistic_sequences(sample_size: int = 10000) -> tuple[dict, dict, np.ndarray, np.ndarray]:
    def generate_probabilistic_sequences(sample_size: int = 10000):
        """
        Generates probabilistic sequences for defective density, EPA, GPA, and carbon intensity.

        Parameters:
        sample_size (int): The number of samples to generate for each sequence. Default is 10000.

        Returns:
        tuple: A tuple containing the following sequences:
            - defective_density_sequence (dict): A dictionary where keys are process nodes and values are arrays of defective density values.
            - epa_sequence (dict): A dictionary where keys are process nodes and values are arrays of EPA values.
            - gpa_sequence (numpy.ndarray): An array of GPA values.
            - carbon_intensity_sequence (numpy.ndarray): An array of carbon intensity values.
        """

    carbon_intensity_distribution = [0.03125,0.03125,0.03125,0.03125,0.01041667,0.01041667,0.01041667,0.01041663,0.01041667,
                        0.01041667,0.01041667,0.01041667,0.01041667,0.01041667,0.01041667,
                        0.01041667,0.04166667,0.04166667,0.04166667,0.04166667,
                        0.02083333,0.02083333,0.02083333,0.02083333,0.0625,0.0625,
                        0.0625,0.0625,0.0625,0.0625,0.0625,0.0625]
    carbon_intensity_sequence = np.random.choice(np.arange(480.8486,546.7014,2.057901), size=sample_size, replace=True, p = carbon_intensity_distribution)

    gpa_mean=150
    gpa_std=30

    gpa_sequence = np.random.normal(gpa_mean, gpa_std, sample_size)
    gpa_sequence = np.clip(gpa_sequence,50,300)


    # We use the estimated reference values of defective density and EPA in very process node to model the complete sequence 
    defective_density_reference =  {"7": 0.2, "10": 0.11, "14":0.09, "22": 0.08, "28":0.07, "65":0.05}
    # epa_reference =  {"7": 1.667, "10": 1.475, "14":1.2, "22": 1.2, "28":0.9}
    epa_reference =  {"7": 1.667, "10": 1.475, "14":1.2, "22": 1.2, "28":0.9, "65": 0.65}


    epa_distribution = [0.092478422,0.09864365,
                        0.101726264,0.103575832,0.101726264,0.097410604,
                        0.091245376,0.08323058,0.073982737,0.061652281,
                        0.048088779,0.033908755,0.012330456,]

    defective_density_distribution=[0.1125,0.1125,0.1125,0.1125,0.1125,0.05,0.05,0.05,0.05,0.05,
        0.0125,0.0125,0.0125,0.0125,0.0125,0.0125,0.0125,0.0125,
        0.0125,0.0125,0.0125,0.0125,0.0125,0.0125,0.0125,]

    def probabilistic_model(reference, p, stride = 25, d1 = None, d2 = None):
        d1 = 0.11 - 0.095
        d2 = 0.42 - 0.11
        distribution = dict()
        for node in reference:
            defect_bench = defective_density_reference[node]
            start = defect_bench - d1
            end = defect_bench + d2
            step = (end - start) / stride
            distribution[node] = np.random.choice(np.arange(start, end, step), size=sample_size, replace=True, p=p)
        return distribution

    defective_density_sequence = probabilistic_model(defective_density_reference, defective_density_distribution)
    epa_sequence = probabilistic_model(epa_reference, epa_distribution, stride = 13, d1 = 0.575, d2 = 0.025)

    return defective_density_sequence, epa_sequence, gpa_sequence, carbon_intensity_sequence


if __name__ == '__main__':
    print("")