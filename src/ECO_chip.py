import numpy as np
import pandas as pd 
from  matplotlib import pyplot as plt

#Importing all functions from CO2_func files
from CO2_func import * 
from tech_scaling import *

import argparse
import json
import ast

def eco_chip():


    scaling_factors = load_tables()
    #print(scaling_factors)


    parser = argparse.ArgumentParser(description='Provide a Carbon Foot Print(CFP) estimate ')
    parser.add_argument(
            '--design_dir',
            default=None,
            help='use existing template for design_dir "--design_dir config/example/architecture.json"'
            )

    parser.add_argument(
            '--num_lifetime',
            default=None,
            help='Lifetime of the chip'
    )
    parser.add_argument(
            '--chip_area',
            default=None,
            help='Chip area'
    )
    parser.add_argument(
            '--node',
            default=None,
            help='Node of design'
    )
    parser.add_argument(
            '--chip_power',
            default=None,
            help='Chip Power'
    )
    parser.add_argument(
            '--carbon_intensity',
            default=None,
            help='carbon_per_kWh'
    )
    parser.add_argument(
            '--cfpa',
            default=None,
            help='CFP_per_unit_area'
    )


    ##
    args = parser.parse_args()
    design_dir = args.design_dir
    ##

    if args.chip_area is not None:
        chip_area = float(args.chip_area)
    if args.chip_power is not None:
        chip_power = float(args.chip_power)
    if args.node is not None:
        node_val = int(args.node)
    if args.num_lifetime is not None:
        NUM_Life = float(args.num_lifetime)
        NUM_Life = NUM_Life*24*365 #in hrs     


        
    architecture_file = design_dir+'architecture.json'
    node_list_file = design_dir+'node_list.txt'
    designC_file = design_dir+'designC.json'
    operationalC_file = design_dir+'operationalC.json'
    packageC_file = design_dir+'packageC.json'
    #print(" ---------------------------------------------------------")
    #print("Using below files for CFP estimations : \n")
    #print(architecture_file)
    #print(node_list_file)
    #print(designC_file)
    #print(operationalC_file)
    #print(packageC_file)
    #print(" ---------------------------------------------------------")


    with open(architecture_file,'r') as json_file:
        config_json = json.load(json_file)

    with open(node_list_file , 'r') as file:
        nodes=file.readlines()
    nodes = [ast.literal_eval(node_item) for node_item in nodes]
    nodes = [data for inside_node in nodes for data in inside_node]
    #print("Nodes from node_list.txt file ",nodes)

    #print(config_json)
    #print(type(config_json))
    #print("start") #TODO CCS remove
    design = pd.DataFrame(config_json).T
    #print(type(design))
    #print(design)
    #print("done")   #TODO CCS remove
    package_type = design.loc['pkg_type']
    package_type = package_type[0]
        
    design = design.drop(index='pkg_type')
    #print(design)

    #power = 450
    #powers = design.area.values * power / design.area.values.sum()
    #design.insert(loc=2,column='power',value=powers)
    #print(design)

    inp_des = pd.DataFrame()
    inp_des.at['Logic','type'] = 'logic'
    inp_des.at['Logic','area'] = chip_area
    design=inp_des

    #Area knob
    if args.chip_area is not None:
        design.at['Logic','area'] = chip_area
    else : 
        design = design

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
    #print(design)
    print(" ")
        
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
        


    #Node knob
    if args.node is not None:
        nodes[0] = node_val

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
    # if args.epa is not None:
    #     epa = float(args.epa)
    # else:
    #     epa = epa_dict[str(node_val)]

    # tuning carbon intensity, defective density and CFP per unit area
    if args.carbon_intensity is not None:
        carbon_per_kWh = float(args.carbon_intensity)
    # if args.defect_density is not None:
    #     scaling_factors['defect_den'].loc[nodes[0], 'defect_density'] = float(args.defect_density)

    if args.cfpa is not None:
        scaling_factors['cpa'].loc[nodes[0], 'cpa'] = float(args.cfpa)



    ##Debug print 
    #print("Lifetime",lifetime)
    #print("design ",design.values)
    #print('Nodes ',nodes)

    # print(f"{scaling_factors['defect_den'],scaling_factors['cpa']}")
    #result = calculate_CO2(design,scaling_factors, nodes, 'Tiger Lake')
    result = calculate_CO2(design,scaling_factors, nodes, 'Tiger Lake',
                        num_iter,package_type=package_type ,Ns=num_prt_mfg,lifetime=lifetime,
                        carbon_per_kWh=carbon_per_kWh,transistors_per_gate=transistors_per_gate,
                        power_per_core=power_per_core,interposer_node = interposer_node, rdl_layer=rdl_layer, emib_layers=emib_layers,
                        emib_pitch=emib_pitch, tsv_pitch=tsv_pitch, tsv_size=tsv_size, num_beol=numBEOL)

    #print("'"+design_dir+"' Example testcase")
    #print(" ---------------------------------------------------------")
    #print("Manufacture Carbon in Kgs ")
    #print(result[0]/1000) #Converting to Kgs
    #print(" ---------------------------------------------------------")
    #print("Design Carbon in Kgs ")
    #print(result[1]/1000) #Converting to Kgs
    #print(" ---------------------------------------------------------")
    #print("Operational Carbon in Kgs ")
    #print(result[3]/1000) #Converting to Kgs
    #print(" ---------------------------------------------------------")
    #print("Total Carbon in Kgs ")
    #print(result[2]/1000) #Converting to Kgs
    #print(" ---------------------------------------------------------")

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

    print("Des CFP : ",c_des)
    print("Mfg CFP : ",c_mfg)
    print("Ope CFP : ",c_ope)
    print("Tot CFP : ",c_tot)
