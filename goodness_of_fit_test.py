import os
import subprocess
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    '--output_dir', help="""Subdirectory of ./output/ where the workspace are written out to""")
parser.add_argument(
    '--input_dir', required=True, help="""Input directory where datacards are""")
parser.add_argument(
    '--year', required=True, help="""Era""")
args = parser.parse_args()

if args.output_dir is None:
    args.output_dir = args.input_dir
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

LABELS = {
    'all_years_Run2': 'SRXb2T - 138 fb^{-1}',
    'all_years_Run3': 'SRXb2T - 35 fb^{-1}'
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

def gof_saturated_model(input_dir, output_dir, mass, width, year, logger):
    logger.info(f'Toys generation for mass: {mass}')
    command = (
        f"combine -M GoodnessOfFit -d {input_dir}/workspace_TTZprimeToTT_M{mass}_Width{width}_{year}.root --algo=saturated -n _M{mass}_Width{width}"
        f" --setParameters mask_ee_1b=0,mask_ee_2b=0,mask_emu_1b=0,mask_emu_2b=0,mask_mumu_1b=0,mask_mumu_2b=0"
        # f" --setParameters mask_*=0 --freezeParameters mask_* "
        # f" --X-rtd MINIMIZER_noOptimizeSimPdf "
    )
    run_command(command, logger)
    run_command(f"mv higgsCombine_M{mass}_Width{width}.GoodnessOfFit* {output_dir}/", logger)

def gof_with_toys(input_dir, output_dir, mass, width, year, logger):
    logger.info(f'Toys generation for mass: {mass}')
    command = (
        f"combine -M GoodnessOfFit -d {input_dir}/workspace_TTZprimeToTT_M{mass}_Width{width}_{year}.root --algo=saturated -n _M{mass}_Width{width}"
        f" --toysFrequentist  -t 500"
        f" --setParameters mask_ee_1b=0,mask_ee_2b=0,mask_emu_1b=0,mask_emu_2b=0,mask_mumu_1b=0,mask_mumu_2b=0 " #2000
        # f" --X-rtd MINIMIZER_noOptimizeSimPdf "
    )
    run_command(command, logger)
    run_command(f"mv higgsCombine_M{mass}_Width{width}.GoodnessOfFit* {output_dir}/", logger)

def p_value_evaluation(input_dir, output_dir, mass, width, year, logger):
    logger.info(f'Toys fit for mass: {mass}')
    command = (
        f"combineTool.py -M CollectGoodnessOfFit --input {input_dir}/higgsCombine_M{mass}_Width{width}.GoodnessOfFit.mH120.root {input_dir}/higgsCombine_M{mass}_Width{width}.GoodnessOfFit.mH120.123456.root "
        f"-o {output_dir}/gof_M{mass}_Width{width}.json "
    )
    run_command(command, logger)

def plotting_gof(input_dir, output_dir, mass, width, year, logger):
    logger.info(f'Plotting GOF: {mass}')
    command = (
        f'plotGof.py {output_dir}/gof_M{mass}_Width{width}.json --statistic saturated --mass 120.0 -o {output_dir}/gof_M{mass}_Width{width} --title-right="{LABELS[year]}"'
    )
    run_command(command, logger)

if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir 
    year = args.year
    masses = [1000] #, 1750]#, 2500]#500, 1000, 
    widths = [4]#, 10, 20, 50]

    for mass in masses:
        for width in widths:
            # Set up logger for the current mass point
            logger = setup_logger(mass, output_dir)

            try:
                gof_saturated_model(input_dir, output_dir, mass=mass, width=width, year=year, logger=logger)
                gof_with_toys(input_dir, output_dir, mass=mass, width=width, year=year, logger=logger)
                p_value_evaluation(input_dir, output_dir, mass=mass, width=width, year=year, logger=logger)
                plotting_gof(input_dir, output_dir, mass=mass, width=width, year=year, logger=logger)
            except RuntimeError as e:
                logger.error(f"An error occurred for mass {mass}: {e}")
