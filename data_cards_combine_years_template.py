import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--output_dir', help="""Subdirectory of ./output/ where the workspace are written out to""")
parser.add_argument(
    '--input_dir', required=True, help="""Input directory where datacards are""")
args = parser.parse_args()

if args.output_dir is None:
    args.output_dir = args.input_dir
if not os.path.exists(args.output_dir + '/Run2_Run3'):
    os.makedirs(args.output_dir + '/Run2_Run3')

# --- 
# for mass in ['500', '750', '1000', '1250', '1500', '1750', '2000', '2500', '3000', '4000']:
#     for width in ['4', '10', '20', '50']:
#         if mass == '1500' and width == '20': continue
#         cmd = ''
#         for year in ['2017', '2018', '2016preVFP', '2016']:
#             cmd += ' yr_{}={}/{}/TTZprimeToTT_M{}_{}.txt'.format(year, args.input_dir, year, mass, year)

#         cmd += " > {}/TTZprimeToTT_M{}_Run2.txt".format(args.output_dir, mass)

#         # print(cmd)
#         print('Combined card: {}'.format("{}/TTZprimeToTT_M{}_Run2.txt".format(args.output_dir, mass)))
#         os.system('combineCards.py ' + cmd)
# --- 

# sgn = 'TTZprimeToTT'
sgn = 'TTZprimeToTT'
# sgn = 'TTZprimeToTT'

# --- Run 2 + Run 3
for mass in ['500', '750', '1000', '1250', '1500', '1750', '2000', '2500', '3000', '4000']:
    for width in ['4', '10', '20', '50']:
        # if mass == '1500' and width == '20': continue
        cmd = ''
        for year in ['all_years_Run2', 'all_years_Run3']:
            cmd += f' yr_{year}={args.input_dir}/{year}/{sgn}_M{mass}_Width{width}_{year}.txt'

        cmd += f" > {args.output_dir}/Run2_Run3/{sgn}_M{mass}_Width{width}_Run2_Run3.txt"

        # print(cmd)
        print(f'Combined card: {args.output_dir}/Run2_Run3/{sgn}_M{mass}_Width{width}_Run2_Run3.txt')
        os.system('combineCards.py ' + cmd)
