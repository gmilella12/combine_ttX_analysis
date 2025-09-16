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

R_INJ_NAME = '0' #options are: Exp, 0
R_INJ = {
    500: 0,
    1750: 0
}
if R_INJ_NAME == 'Exp':
    R_INJ = {
    # 500: 1.5,
    500: 2.5,
    # 1750: 40,
    1750: 77,
}

R_RANGES = {
    # 'min_500': -10,
    # 'max_500': 10,
    'min_500': -20,
    'max_500': 20,
    # 'min_1750': -200,
    # 'max_1750': 200,
    'min_1750': -2000,
    'max_1750': 2000,
}
TRACK_PARAMETER = ""

def setup_logger(mass, output_dir):
    """Set up a logger for a specific mass."""
    log_file = os.path.join(output_dir, f'log_bias_test_r{R_INJ_NAME}_M{mass}.log')
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

def toys_generation(input_dir, output_dir, mass, width, logger):
    logger.info(f'Toys generation for mass: {mass}')
    command = (
        f"combine -M GenerateOnly -d {input_dir}/workspace_TTZprimeToTT_M{mass}_Width{width}_Run2_Run3.root --expectSignal={R_INJ[mass]} "
        f"--saveToys --toysFrequentist --bypassFrequentistFit -t 1000 -n _M{mass}_Width{width}_r{R_INJ_NAME} --rMax {R_RANGES[f'max_{mass}']} --rMin {R_RANGES[f'min_{mass}']}"
    )
    run_command(command, logger)
    run_command(f"mv higgsCombine_M{mass}_Width{width}_r{R_INJ_NAME}.GenerateOnly* {output_dir}/", logger)

def toys_fit(input_dir, output_dir, mass, width, logger):
    logger.info(f'Toys fit for mass: {mass}')
    command = (
        f"combine -M MultiDimFit -d {input_dir}/workspace_TTZprimeToTT_M{mass}_Width{width}_Run2_Run3.root -t 1000 -n _M{mass}_Width{width}_r{R_INJ_NAME} "
        f" --toysFile {input_dir}/higgsCombine_M{mass}_Width{width}_r{R_INJ_NAME}.GenerateOnly.mH120.123456.root --algo singles --toysFrequentist "
        f"--rMax {R_RANGES[f'max_{mass}']} --rMin {R_RANGES[f'min_{mass}']} "
    )
    if TRACK_PARAMETER:
        command += (
            f"--trackParameters {TRACK_PARAMETER} --trackErrors {TRACK_PARAMETER}"
        )
    run_command(command, logger)
    run_command(f"mv higgsCombine_M{mass}_Width{width}_r{R_INJ_NAME}.MultiDimFit* {output_dir}/", logger)


if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir 
    masses = [500]#, 1750]#, 2500]#500, 1000, 
    widths = [4]#, 10, 20, 50]

    for mass in masses:
        for width in widths:
            # Set up logger for the current mass point
            logger = setup_logger(mass, output_dir)

            try:
                toys_generation(input_dir, output_dir, mass=mass, width=width, logger=logger)
                toys_fit(input_dir, output_dir, mass=mass, width=width, logger=logger)
            except RuntimeError as e:
                logger.error(f"An error occurred for mass {mass}: {e}")
