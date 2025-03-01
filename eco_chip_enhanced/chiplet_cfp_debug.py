import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os, sys, argparse
from eco_chip_func import *



chiplet_processors = pd.read_csv("../dataset/chiplet_processors.csv")

# Generate the probabilistic modeled parameters for Carbon Footprint calculation
# Assume 10k sample size for each parameter
sample_size = 10000
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
epa_reference =  {"7": 1.667, "10": 1.475, "14":1.2, "22": 1.2, "28":0.9}

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
    defect_distribution = dict()
    for node in reference:
        defect_bench = defective_density_reference[node]
        start = defect_bench - d1
        end = defect_bench + d2
        step = (end - start) / stride
        defect_distribution[node] = np.random.choice(np.arange(start, end, step), size=sample_size, replace=True, p=p)
    return defect_distribution


def highest_probability(result):
    unique_values, counts = np.unique(result, return_counts=True)
    probabilities = counts / len(result)  # Convert frequency models to probabilities
    # Find the maximum probability and its corresponding value
    max_prob_index = np.argmax(probabilities)
    max_prob_value = unique_values[max_prob_index]
    max_prob = probabilities[max_prob_index]

    return max_prob_value, max_prob


# lets plot the actual modeled distribution of all the parameters mentioned above with sample process node = 7nm
defective_density_sequence = probabilistic_model(defective_density_reference, defective_density_distribution)
epa_sequence = probabilistic_model(epa_reference, epa_distribution, stride = 13, d1 = 0.575, d2 = 0.025)


# Add the eco_chip_enhanced folder to the system path
# sys.path.append(os.path.join(os.getcwd(), "../eco_chip_enhanced/"))

# Import the eco_chip function from the eco_chip_func module

def get_cfp(process_node, power, area, defective_density, gpa, carbon_intensity, epa, dir = None):
    # Calculate the Carbon Footprint (CFP) for the given processor
    if dir is None:
        dir = 'testcases/CFP_survey/'
    args = argparse.Namespace(
        design_dir = dir,
        chip_area = area,
        chip_power = power,
        node = process_node,
        defect_density = defective_density,
        gpa = gpa, 
        epa = epa,
        num_lifetime=None,
        tech_scaling_path='../eco_chip_enhanced/',
        carbon_intensity = carbon_intensity
    )
    # we have design carbon, manufacturing carbon, operational carbon and total carbon
    design_carbon, mfg_carbon, ope_carbon, total_carbon = eco_chip(args)
    embodied_carbon = float(design_carbon) + float(mfg_carbon)
    operational_carbon = float(ope_carbon)
    total_carbon = float(total_carbon)
    
    return embodied_carbon, operational_carbon, total_carbon


# this function will calculate the mean CFP value of every processor
def calculate_mean_cfp(idx, proc, dir = None, debug = False):
    node = int(proc['Process Size (nm)'])
    power = int(proc['TDP (W)'])
    area = int(proc['DieSizeValue'])

    # area = int(proc['DieSizeValue'])
    print(f"calculate_mean_cfp:{dir}")
    if debug:
        sample_size = 1

    embodied_carbon_list = np.zeros(sample_size)
    operational_carbon_list = np.zeros(sample_size)

    for i in range(sample_size):
        emb_c, ope_c, tot_c = get_cfp(node, power, area, defective_density_sequence[str(node)][i],
                                        gpa_sequence[i], carbon_intensity_sequence[i], epa_sequence[str(node)][i], dir = dir)
        embodied_carbon_list[i] = emb_c
        operational_carbon_list[i] = ope_c
        
        
    embodied_carbon_mean = embodied_carbon_list.mean()
    operational_carbon_mean = operational_carbon_list.mean()
    total_carbon_mean = embodied_carbon_mean + operational_carbon_mean
    
    
    return idx, embodied_carbon_mean, operational_carbon_mean, total_carbon_mean

def generate_die_json(num_of_dies: int, die_area: int, file_path: str) -> None:
    data = dict()
    # Add CPU dies based on num_of_dies
    for i in range(int(num_of_dies)):
        data[f"CPU_{i}"] = {
            "type": "logic",
            "area": int(die_area)
        }
    data["pkg_type"] = "RDL"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as json_file:
        json_file.write(json.dumps(data, indent=4))
        

def get_chiplet_cfp(idx, proc, debug = False):
    dir = "../eco_chip_enhanced/chiplet_dir/"
    json_file = f"{dir}architecture.json"
    print(f"get_chiplet_cfp:{dir}")
    generate_die_json(proc['#dies'], proc['Avg Die Area'], json_file)
    idx, embodied_carbon_mean, operational_carbon_mean, total_carbon_mean  = calculate_mean_cfp(idx, proc, dir = dir, debug = debug)
    return idx, embodied_carbon_mean, operational_carbon_mean, total_carbon_mean   


key = 10
cfp_res = get_chiplet_cfp(key, chiplet_processors.iloc[key], debug = True)
print(f"chiplet_cfp_debug {cfp_res}")

