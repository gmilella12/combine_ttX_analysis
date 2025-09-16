import os
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--output_dir', help="""Subdirectory of ./output/ where the workspace are written out to""")
parser.add_argument(
    '--input_dir', required=True, help="""Input directory where datacards are""")
args = parser.parse_args()

if args.output_dir is None:
    args.output_dir = args.input_dir
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

is_tta = False
is_tth = False

UNBLIND = True

def run_combine(input_dir, output_dir, masses, widths):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for mass in masses:
        for width in widths:
            print(f'Calculating limit for mass: {mass} width: {width}')

            sgn = 'TTZprimeToTT'
            if is_tta:
                sgn = 'tta'
            if is_tth:
                sgn = 'tth'

            command = f"combine {input_dir}/Run2_Run3/workspace_{sgn}_M{mass}_Width{width}_Run2_Run3.root -M AsymptoticLimits -m 800 --run blind -t -1 --rMin -1000 --rMax 1000 -n AsymptoticLimit_AsimovSet_{sgn}_M{mass}_Width{width}_Run2_Run3"

            if UNBLIND:
                command = f"combine {input_dir}/Run2_Run3/workspace_{sgn}_M{mass}_Width{width}_Run2_Run3.root -M AsymptoticLimits -m 800 --rMin -1000 --rMax 1000 -n AsymptoticLimit_{sgn}_M{mass}_Width{width}_Run2_Run3"

            subprocess.call(command, shell=True)

            if UNBLIND:
                subprocess.call(f"mv *AsymptoticLimit_{sgn}* {output_dir}/Run2_Run3", shell=True)
            else:
                subprocess.call(f"mv *AsymptoticLimit_AsimovSet_{sgn}* {output_dir}/Run2_Run3", shell=True)

    # for year in ['2016', '2016preVFP', '2017', '2018']:
    #     for category in ['ee_1b', 'ee_2b', 'emu_1b', 'emu_2b', 'mumu_1b', 'mumu_2b']:
    #         output_subdir = f"{output_dir}/{year}/{category}" 
    #         input_subdir = f"{input_dir}/{year}/{category}"
    #         for mass in masses:
    #             print(f'Calculating limit for mass: {mass}, {year}, {category}')
    #             command = f"combine {input_subdir}/workspace_TTZprimeToTT_M{mass}_{year}.root -M AsymptoticLimits -m 800 --run blind -t -1 --rMin -10 --rMax 200 -n AsymptoticLimit_ttX_mass{mass}_{year}"
    #             subprocess.call(command, shell=True)
    #             subprocess.call(f"mv *AsymptoticLimit_ttX_mass* {output_subdir}/", shell=True)
                # subprocess.run(command, shell=True, check=True)

if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir 
    masses = [500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 4000]
    widths = [10, 20, 50]
    
    run_combine(input_dir, output_dir, masses, widths)
    print("All combine commands executed successfully.")
