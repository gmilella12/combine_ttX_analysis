import os
import subprocess
import argparse
import logging

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

BKG_ONLY = False
CONTROL_REGION = False
if CONTROL_REGION:
    BKG_ONLY = True

UNBLIND = True

SGN = 'TTZprimeToTT' #tth tta

#from AsymptoticLimits calculation on 4%
EXPECT_SGN = {
    500: 4.29, #1T # 2T: 2.4891,
    750: 3.9101,
    1000: 18.15, #1T # 2T: 8.6975,
    1250: 18.2343,
    1500: 35.7056,
    1750: 77.8198,
    2000: 394.28, #1T # 2T: 163.5742,
    2500: 578.6133,
    3000: 2158.2031,
    4000: 44218.7500,
}
if SGN == 'tta' or SGN == 'tth':
    EXPECT_SGN = {
        500: 15.6,
        750: 26.09,
        1000: 50.5,
        1250: 113.5,
        1500: 177.6,
        1750: 314.9,
        2000: 612.7,
        2500: 2021.4,
        3000: 7695.3,
        4000: 135625.0,
    }
if BKG_ONLY:
    EXPECT_SGN = {
        500: 0,
        1750: 0
    }

def setup_logger(mass, output_dir):
    """Set up a logger for a specific mass."""
    log_file = os.path.join(output_dir, f'log_impacts_M{mass}.log')
    logger = logging.getLogger(f'M{mass}')
    logger.setLevel(logging.DEBUG)

    # Create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create formatter and add to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def run_command(command, logger):
    """Run a shell command and log the output."""
    logger.info(f"Running command: {command}")
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    logger.info(stdout)
    if stderr:
        logger.error(stderr)
    if process.returncode != 0:
        logger.error(f"Command failed with return code {process.returncode}")
        raise RuntimeError(f"Command failed: {command}")

def initial_fit(input_dir, output_dir, mass, width, logger):
    logger.info(f'Initial fit for mass: {mass}')

    command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root -t -1 --expectSignal={EXPECT_SGN[mass]} -m 125 --doInitialFit --rMin -20 --rMax 20 "
    if CONTROL_REGION:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root  --expectSignal=0 -m 125 --doInitialFit --rMin -2 --rMax 2 "
    if mass >= 1000:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root -t -1 --expectSignal={EXPECT_SGN[mass]} -m 125 --doInitialFit --rMin -2000 --rMax 2000 "
        if CONTROL_REGION:
            command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root  --expectSignal=0 -m 125 --doInitialFit --rMin -2000 --rMax 2000 "
    if UNBLIND:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root -m 125 --doInitialFit --rMin -200 --rMax 200"
    run_command(command, logger)

def param_fit(input_dir, output_dir, mass, width, logger):
    logger.info(f'Param fit for mass: {mass}')
    command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root --doFits -t -1 --expectSignal={EXPECT_SGN[mass]} -m 125 --parallel 10 --rMin -2 --rMax 2 "
    if CONTROL_REGION:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root --doFits  --expectSignal=0 -m 125 --parallel 10 --rMin -2 --rMax 2 "
    if mass >= 20:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root --doFits -t -1 --expectSignal={EXPECT_SGN[mass]} -m 125 --parallel 10 --rMin -2000 --rMax 2000 "
        if CONTROL_REGION:
            command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root --doFits  --expectSignal=0 -m 125 --parallel 10 --rMin -2000 --rMax 2000 "
    if UNBLIND:
        command = f"combineTool.py -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root --doFits  -m 125 --parallel 10 --rMin -200 --rMax 200"
    run_command(command, logger)

def json_creation(input_dir, output_dir, mass, width, logger):
    logger.info(f'JSON creation for mass: {mass}')
    additional_text = ''
    if BKG_ONLY:
        additional_text = '_bkgOnly'
    
    command = f"combineTool.py -m 125 -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root -o impacts_asimov_M{mass}_Width{width}{additional_text}.json "
    if UNBLIND:
        command = f"combineTool.py -m 125 -M Impacts -d {input_dir}/workspace_{SGN}_M{mass}_Width{width}_Run2_Run3.root -o impacts_M{mass}_Width{width}{additional_text}.json "
    run_command(command, logger)
    run_command(f"mv *impacts_* {output_dir}/", logger)
    run_command(f"rm *initialFit*", logger)
    run_command(f"rm *paramFit*", logger)

def plotting(input_dir, output_dir, mass, width, logger):
    logger.info(f'Plotting impacts for mass, width: {mass} {width}')
    additional_text = ''
    if BKG_ONLY:
        additional_text = '_bkgOnly'
    command = f"plotImpacts.py -i {output_dir}/impacts_asimov_M{mass}_Width{width}{additional_text}.json -o {output_dir}/impacts_asimov_M{mass}_Width{width}{additional_text}"
    if UNBLIND:
        command = f"plotImpacts.py -i {output_dir}/impacts_M{mass}_Width{width}{additional_text}.json -o {output_dir}/impacts_M{mass}_Width{width}{additional_text} --blind"
    run_command(command, logger)

if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir 
    masses = [2000]#, 2000]#500, 1000, 
    widths = [4]#, 10, 20, 50]

    for mass in masses:
        for width in widths:
            # Set up logger for the current mass point
            logger = setup_logger(mass, output_dir)

            try:
                initial_fit(input_dir, output_dir, mass=mass, width=width, logger=logger)
                param_fit(input_dir, output_dir, mass=mass, width=width, logger=logger)
                json_creation(input_dir, output_dir, mass=mass, width=width, logger=logger)
                plotting(input_dir, output_dir, mass=mass, width=width, logger=logger)
            except RuntimeError as e:
                logger.error(f"An error occurred for mass {mass}: {e}")
