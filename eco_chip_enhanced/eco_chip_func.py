import numpy as np
import pandas as pd

from .CO2_func import * 
from .tech_scaling import *

import utils
import argparse
import json
import ast



def eco_chip(args):



    if args == None:
        print("Please provide the arguments")
        exit(-1)

        
    # Ensure tech_scaling_path is a string, not a tuple
    if isinstance(args.tech_scaling_path, tuple):
        args.tech_scaling_path = args.tech_scaling_path[0]

    # Ensure design_dir is a string, not a tuple
    if isinstance(args.design_dir, tuple):
        args.design_dir = args.design_dir[0]

    # Default paths (relative to `eco_chip_enhanced/`)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory

    # print(f"eco_chip_func: base_dir: {base_dir}")
    # print(f"eco_chip_func: tech_scaling_path: {args.tech_scaling_path}")
    # print(f"eco_chip_func: design_dir: {args.design_dir}")
    

    tech_path = args.tech_scaling_path if args.tech_scaling_path else os.path.join(base_dir,"tech_params/")
    design_dir = args.design_dir if args.design_dir else os.path.join(base_dir, "arch_params/")

    scaling_factors =  load_tables(tech_path)



    # Ensure design_dir always ends with "/"
    if not design_dir.endswith("/"):
        design_dir += "/"

    # Ensure tech_path always ends with "/"
    if not tech_path.endswith("/"):
        tech_path += "/"

    architecture_file = design_dir+'architecture.json'
    node_list_file = design_dir+'node_list.txt'
    designC_file = design_dir+'designC.json'
    operationalC_file = design_dir+'operationalC.json'
    packageC_file = design_dir+'packageC.json'


    if args.chip_area is not None:
        chip_area = float(args.chip_area)
    if args.chip_power is not None:
        chip_power = float(args.chip_power)
    if args.node is not None:
        node_val = int(args.node)
    if args.num_lifetime is not None:
        NUM_Life = float(args.num_lifetime)
        NUM_Life = NUM_Life*24*365 #in hrs     


    with open(architecture_file,'r') as json_file:
        config_json = json.load(json_file)
    

    with open(node_list_file , 'r') as file:
        nodes=file.readlines()
    nodes = [ast.literal_eval(node_item) for node_item in nodes]
    nodes = [data for inside_node in nodes for data in inside_node]

    design = pd.DataFrame(config_json).T
    # print(f"*** read from json *** \n{design}")    


    package_type = design.loc['pkg_type'].iloc[0]
    # package_type = package_type.iloc[0]
        
    design = design.drop(index='pkg_type')


    # inp_des = pd.DataFrame()
    # inp_des.at['Logic','type'] = 'logic'
    # inp_des.at['Logic','area'] = chip_area
    # design=inp_des

    # print(f"*** reset design=inp_des *** \n{design}")    


    #Area knob

    # if args.chip_area is not None:
    #     design.at['Logic','area'] = chip_area
    # else : 
    #     design = design
    with open(designC_file, 'r') as f:
        designC_values = json.load(f)

    #Power knob
    if args.chip_power is not None: 
        power =chip_power
    else : 
        power = float(designC_values['power'])
    powers = design.area.values * power / design.area.values.sum()

    num_iter = designC_values['num_iter']
    num_prt_mfg = designC_values['num_prt_mfg']
    transistors_per_gate = designC_values['Transistors_per_gate']
    power_per_core = designC_values['Power_per_core']
    carbon_per_kWh = designC_values['Carbon_per_kWh']


    design.insert(loc=2,column='power',value=powers)
        
    with open(operationalC_file,'r') as f:
        operationalC_values = json.load(f)
    #Lifetime knob
    if args.num_lifetime is not None:
        lifetime = NUM_Life
    else :
        lifetime = operationalC_values['lifetime']
        
        
    with open(packageC_file,'r') as f:
        packageC_values = json.load(f)
    interposer_node = packageC_values['interposer_node']
    rdl_layer = packageC_values['rdl_layers']
    emib_layers = packageC_values['emib_layers']
    emib_pitch = packageC_values['emib_pitch']
    tsv_pitch = packageC_values['tsv_pitch']
    tsv_size = packageC_values['tsv_size']
    numBEOL = packageC_values['num_beol']
    
    epa_dict = {
        "28" : 0.417,
        "22" : 0.763,
        "14" : 0.763,
        "10" : 1.038,
        "7"  : 1.667,
    }

    #Node knob
    if args.node is not None:
        nodes[0] = node_val
    if args.epa is not None:
        epa = float(args.epa)
    else:
        epa = epa_dict[str(node_val)]
    

    

    # tuning carbon intensity, defective density and CFP per unit area
    if args.gpa is not None:
        gpa = float(args.gpa)
    if args.carbon_intensity is not None:
        carbon_per_kWh = float(args.carbon_intensity)
    if args.defect_density is not None:
        defect_density = float(args.defect_density)
        yield_val = (1+(defect_density*1e4)*(0.01*1e-6)/10)**-10
        cpa_values = (carbon_per_kWh*epa)+gpa+500 / yield_val # MPA
        cpa_values = cpa_values*0.01
        scaling_factors['defect_den'].loc[nodes[0], 'defect_density'] = float(args.defect_density)
        scaling_factors['cpa'].loc[nodes[0], 'cpa'] = cpa_values

    #Update packaging 65nm parameters with probabilistic modeling 
    epa_packaging = float(args.epa_pack)
    defect_density_packaging = float(args.defect_density_pack)
    yield_val_packaging = (1+(defect_density_packaging*1e4)*(0.01*1e-6)/10)**-10
    cpa_values_packaging = (carbon_per_kWh*epa_packaging)+gpa+500 / yield_val_packaging 
    cpa_values_packaging = cpa_values_packaging*0.01
    scaling_factors['cpa'].loc[65, 'cpa'] = cpa_values_packaging


    # print(f"--- Packaging 65----")
    # print(f"carbon_per_kWh: {carbon_per_kWh}")
    # print(f"epa_packaging: {epa_packaging}")
    # print(f"defect_density_packaging: {defect_density_packaging}")
    # print(f"yield_val_packaging: {yield_val_packaging}")
    # print(f"cpa_values_packaging: {cpa_values_packaging} {scaling_factors['cpa'].loc[65, 'cpa']}")


    # print(f"--- Chip {node_val}----")
    # print(f"epa: {epa}")
    # print(f"defect_density: {defect_density}")
    # print(f"yield_val: {yield_val}")
    # print(f"cpa_values: {cpa_values}")


    # print(f"Scaling factors {scaling_factors}")
    result = calculate_CO2(design,scaling_factors, 'Tiger Lake',
                       num_iter,package_type=package_type ,Ns=num_prt_mfg,lifetime=lifetime,
                       carbon_per_kWh=carbon_per_kWh,transistors_per_gate=transistors_per_gate,
                       power_per_core=power_per_core,interposer_node = interposer_node, rdl_layer=rdl_layer, emib_layers=emib_layers,
                       emib_pitch=emib_pitch, tsv_pitch=tsv_pitch, tsv_size=tsv_size, num_beol=numBEOL)

    ###############################
    c_des = result[1].sum(axis=1)/1000
    c_mfg = result[0].sum(axis=1)/1000
    c_ope = result[3].sum(axis=1)/1000
    c_tot = c_des + c_mfg + c_ope

    str_c_des = np.array2string(c_des.values)
    str_c_mfg = np.array2string(c_mfg.values)
    str_c_ope = np.array2string(c_ope.values)
    str_c_tot = np.array2string(c_tot.values)
    c_des = str_c_des.strip('[]')
    c_mfg = str_c_mfg.strip('[]')
    c_ope = str_c_ope.strip('[]')
    c_tot = str_c_tot.strip('[]')

    return c_des, c_mfg, c_ope, c_tot
    # return result


if __name__ == '__main__':
    # print("utils: eco_chip_fun.py Running as __main__")

    # parser = argparse.ArgumentParser(description='Provide a Carbon Foot Print(CFP) estimate ')
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #         '--design_dir',
    #         default=None,
    #         help='use existing template for design_dir "--design_dir config/example/architecture.json"'
    #         )

    # parser.add_argument(
    #         '--num_lifetime',
    #         default=None,
    #         help='Lifetime of the chip'
    # )
    # parser.add_argument(
    #         '--chip_area',
    #         default=None,
    #         help='Chip area'
    # )
    # parser.add_argument(
    #         '--node',
    #         default=None,
    #         help='Node of design'
    # )
    # parser.add_argument(
    #         '--chip_power',
    #         default=None,
    #         help='Chip Power'
    # )
    # parser.add_argument(
    #         '--carbon_intensity',
    #         default=None,
    #         help='carbon_per_kWh'
    # )
    # parser.add_argument(
    #         '--cfpa',
    #         default=None,
    #         help='CFP_per_unit_area'
    # )
    # parser.add_argument(
    #         '--defect_density',
    #         default=None,
    #         help='defective_density'
    # )

    # parser.add_argument(
    #         '--gpa',
    #         default=None,
    #         help='GPA'
    # )

    # parser.add_argument(
    #         '--epa',
    #         default=None,
    #         help='EPA'
    # )

    # parser.add_argument(
    #         '--tech_scaling_path',
    #         default=None,
    #         help='tech_scaling_path'
    # )

    # args = parser.parse_args()
    # c_des, c_mfg, c_ope, c_tot = eco_chip(args)



    sample_size = 100
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
        defect_distribution = dict()
        for node in reference:
            defect_bench = defective_density_reference[node]
            start = defect_bench - d1
            end = defect_bench + d2
            step = (end - start) / stride
            defect_distribution[node] = np.random.choice(np.arange(start, end, step), size=sample_size, replace=True, p=p)
        return defect_distribution
    
    defective_density_sequence = probabilistic_model(defective_density_reference, defective_density_distribution)
    epa_sequence = probabilistic_model(epa_reference, epa_distribution, stride = 13, d1 = 0.575, d2 = 0.025)
    
    def run_eco_chip_sample(area, power, node, dies = 1):
        # lets plot the actual modeled distribution of all the parameters mentioned above with sample process node = 7nm

        des_carbon = []
        mfg_carbon = []
        ope_carbon = []
        current_file = os.path.abspath(__file__)
        parent_dir = os.path.dirname(current_file)
        # print(parent_dir, os.getcwd())
        arch_param_path = parent_dir + "/arch_params/"
        print(arch_param_path)
        utils.generate_node_arch(dies, node, area, arch_param_path)
        for i in range(sample_size):

            args = argparse.Namespace(
                design_dir = None,
                chip_area = area,
                chip_power = power,
                node = node,
                defect_density = defective_density_sequence[str(node)][i],
                gpa = gpa_sequence[i], 
                epa = epa_sequence[str(node)][i],
                epa_pack = epa_sequence['65'][i],
                defect_density_pack = defective_density_sequence['65'][i],
                num_lifetime=None,
                tech_scaling_path= None,
                carbon_intensity = carbon_intensity_sequence[i]
            )

            c_des, c_mfg, c_ope, c_tot = eco_chip(args)
            des_carbon.append(float(c_des))
            mfg_carbon.append(float(c_mfg))
            ope_carbon.append(float(c_ope))

        # print(np.mean(des_carbon), np.mean(mfg_carbon), np.mean(ope_carbon))
        return np.mean(des_carbon), np.mean(mfg_carbon), np.mean(ope_carbon)


    gpu = pd.read_csv("flagship_trend/dataset/NVIDIA-Desktop-GPU.csv")
    for idx, proc in gpu.iterrows():
        node = int(proc['Process Size (nm)'])
        power = float(proc['TDP (W)'])
        area = float(proc['DieSizeValue'])
        des_carbon, mfg_carbon, ope_carbon = run_eco_chip_sample(area=area, node=node, power=power)
        print(f"{proc['Product']} {node}nm {area}mm^2")
        print(f"Old: {proc['Emb CFP']} - {proc['Ope CFP']}")
        print(f"New: {des_carbon + mfg_carbon} - {ope_carbon}")
        print(f"Detailed: des_carbon: {des_carbon} mfg_carbon: {mfg_carbon}  ope_carbon: {ope_carbon}\n")






