#!/usr/bin/env python

import CombineHarvester.CombineTools.ch as ch
import ROOT
import math
import glob
import numpy as np
import os
import sys
import argparse
from array import array

import utils as utils

parser = argparse.ArgumentParser()
parser.add_argument(
 '--output_dir', default='vhbb', help="""Subdirectory of ./output/ where the cards are written out to""")
parser.add_argument(
 '--year', default='2018', help="""Year to produce datacards for (2017 or 2016)""")

args = parser.parse_args()

BKG_PREDICTION = True
BKG_SCALING = False
CONTROL_REGIONS = False

# NFS_PATH = os.environ.get('NFS', '/data/dust/user/gmilella')
AFS_PATH = os.environ.get('AFS', '/afs/desy.de/user/g/gmilella/public/combine_inputs')

PREDICTION_REGION = '2T'

SIGNAL_SHAPES = f'{AFS_PATH}/{args.year}/signal_shapes/hotvr_variables_SRREGION{PREDICTION_REGION}/hotvr_invariant_mass_leading_subleading/'
BKG_ESTIMATION_DIR = f'{AFS_PATH}/{args.year}/bkg_prediction/prediction_analysis_source_SRREGION0T_prediction_SRREGION{PREDICTION_REGION}/'
SMOOTHING_DIR = f'{AFS_PATH}/{args.year}/smoothing/check_systematics_variation_SRREGION{PREDICTION_REGION}/hotvr_invariant_mass_leading_subleading/'

if CONTROL_REGIONS:
    SIGNAL_SHAPES = f'{AFS_PATH}/{args.year}/signal_shapes/hotvr_variables_CR2J{PREDICTION_REGION}/hotvr_invariant_mass_leading_subleading/'
    BKG_ESTIMATION_DIR = f'{AFS_PATH}/{args.year}/bkg_prediction/prediction_analysis_source_CR2J0T_prediction_CR2J{PREDICTION_REGION}/'
    SMOOTHING_DIR = f'{AFS_PATH}/{args.year}/smoothing/check_systematics_variation_CR2J{PREDICTION_REGION}/hotvr_invariant_mass_leading_subleading/'

def get_hist(file_name, hist_name):
    rootFile = ROOT.TFile(file_name)
    hist = rootFile.Get(hist_name)
    try:
        hist = hist.Clone()
        hist.SetDirectory(0)
    except:
        print(f"Could not read {hist_name} from file {file_name}")
        return -1
    else:
        rootFile.Close()
        return hist

def rename_bins(combine_harvester):
    bins = combine_harvester.bin_set()
    for b in bins:
        new_name = b #+ '_' + args.year
        combine_harvester.cp().bin([b]).ForEachObj(lambda obj: obj.set_bin(new_name))

def smoothing_systematic(root_infile, systematic_name, chn, region, sgn_procs):
    histos = []

    histo_d = get_hist(
        root_infile,
        f"{systematic_name}Down{year}/{chn}/{sgn_procs}_hotvr_invariant_mass_leading_subleading"
    )
    histo_u = get_hist(
        root_infile,
        f"{systematic_name}Up{year}/{chn}/{sgn_procs}_hotvr_invariant_mass_leading_subleading"
    )
    histo_nom = get_hist(
        root_infile,
        f"nominal/{chn}/{sgn_procs}_hotvr_invariant_mass_leading_subleading"
    )

    fpath = f'{SMOOTHING_DIR.replace("REGION", region)}/{sgn_procs}/{chn}/smoothing_ratios/{sgn_procs}.root'
    fsmooth = ROOT.TFile(fpath, "READ")
    if not os.path.exists(fpath):
        print(f'File for systematic smoothing not found -> {fpath}')
        sys.exit()
    else:
        print(f'Smoothing procedure for {systematic_name}. Extracting smoothed ratio from: {fpath}')

    fsmooth = ROOT.TFile(fpath, "READ")
    h_down_path = f"{systematic_name}Down/{chn}/smoothed"
    h_up_path = f"{systematic_name}Up/{chn}/smoothed"

    h_ratio_down = fsmooth.Get(h_down_path)
    h_ratio_up = fsmooth.Get(h_up_path)

    if h_ratio_down:
        h_ratio_down = h_ratio_down.Clone(f"{systematic_name}_down_ratio_clone")
        h_ratio_down.SetDirectory(0)
    else:
        print(f"[WARNING] Could not find smoothed down histogram: {h_down_path}")

    if h_ratio_up:
        h_ratio_up = h_ratio_up.Clone(f"{systematic_name}_up_ratio_clone")
        h_ratio_up.SetDirectory(0)
    else:
        print(f"[WARNING] Could not find smoothed up histogram: {h_up_path}")

    fsmooth.Close()

    # Multiply nominal with smoothed ratio to get final histograms
    if h_ratio_down:
        histo_down = histo_nom.Clone(f"{sgn_procs}_{systematic_name}Down")
        histo_down.Multiply(h_ratio_down)
        histos.append(histo_down)
    else:
        histos.append(histo_d)

    if h_ratio_up:
        histo_up = histo_nom.Clone(f"{sgn_procs}_{systematic_name}Up")
        histo_up.Multiply(h_ratio_up)
        histos.append(histo_up)
    else:
        histos.append(histo_u)

    return histos

def normalization_systematic(root_infile, systematic_name, chn, region, sgn_procs):
    fpath = f'{SMOOTHING_DIR.replace("REGION", region)}/{sgn_procs}/{chn}/normalization/{sgn_procs}.root'
    fsmooth = ROOT.TFile(fpath, "READ")
    if not os.path.exists(fpath):
        print(f'File for normalization not found -> {fpath}')
        sys.exit()
    else:
        print(f'Normalization procedure for {systematic_name}. Extracting value from: {fpath}')

    fsmooth = ROOT.TFile(fpath, "READ")
    h_down_path = f"{systematic_name}Down/{chn}/normalization_down"
    h_up_path = f"{systematic_name}Up/{chn}/normalization_up"

    h_ratio_down = fsmooth.Get(h_down_path)
    h_ratio_up = fsmooth.Get(h_up_path)

    norm_factor = 1.

    if h_ratio_down:
        h_ratio_down = h_ratio_down.Clone(f"{systematic_name}_down_ratio_clone")
        h_ratio_down.SetDirectory(0)
    else:
        print(f"[WARNING] Could not find down histogram: {h_down_path}")
        sys.exit()

    if h_ratio_up:
        h_ratio_up = h_ratio_up.Clone(f"{systematic_name}_up_ratio_clone")
        h_ratio_up.SetDirectory(0)
        norm_factor = h_ratio_up.GetBinContent(2)
    else:
        print(f"[WARNING] Could not find smoothed up histogram: {h_up_path}")

    fsmooth.Close()

    return norm_factor

def rename_systematics(combine_harvester):
    to_rename = [
        # 'trigger', 
        'muonID', 
        'muonISO',
        'electronID', 
        'electronPt', 
        # 'bTaggingBC', 
        # 'bTaggingLight', 
        # 'ak4JESTotal', 
        # 'ak4JER', 
        # 'hotvrJESTotal', 
        # 'hotvrJER', 
        # 'BDT'
        'bTaggingLightCorrelated',
        'bTaggingBCCorrelated'
    ]
    for syst in to_rename:
        combine_harvester.cp().syst_name([syst]).ForEachSyst(lambda syst_obj: syst_obj.set_name("{}_{}".format(syst, args.year)))

CHANNELS = ['ee', 'mumu', 'emu']
REGIONS = ['2b', '1b']
if CONTROL_REGIONS:
    CHANNELS = ['ee', 'mumu']
    REGIONS = ['']
cats = []

IS_BSM_FOUR_TOP = True
IS_BSM_THREE_TOP = False
IS_BSM_TTA = False
IS_BSM_TTH = False
MC_ONLY = False

new_bin_edges_dict = {} # for rebinning

for ichn, chn in enumerate(CHANNELS): 
    for ireg, region in enumerate(REGIONS):
        cats.append(( ichn*len(REGIONS) + ireg , chn+'_'+region))

        new_bin_edges_dict[chn+'_'+region] = array('d')

MASSES = ['500', '750', '1000', '1250', '1500', '1750', '2000', '2500', '3000', '4000']
WIDTHS = ['4', '10', '20', '50']
if IS_BSM_FOUR_TOP:
    XSEC_UNC_SIGNALS = {
        # ttZ
        '500': (1.-0.258, 1.+0.475), 
        '750': (1.-0.266, 1.+0.398), 
        '1000': (1.-0.271, 1.+0.414), 
        '1250': (1.-0.277, 1.+0.442), 
        '1500': (1.-0.282, 1.+0.432), 
        '1750': (1.-0.287, 1.+0.444), 
        '2000': (1.-0.292, 1.+0.454),
        '2500': (1.-0.301, 1.+0.475), 
        '3000': (1.-0.31, 1.+0.497), 
        '4000': (1.-0.328, 1.+0.542)
    }
if IS_BSM_THREE_TOP:
    XSEC_UNC_SIGNALS = {
        # S-tZ
        '500': (1.-0.077, 1.+0.086), 
        '750': (1.-0.09, 1.+0.111), 
        '1000': (1.-0.1, 1.+0.13), 
        '1250': (1.-0.12, 1.+0.145), 
        '1500': (1.-0.129, 1.+0.158), 
        '1750': (1.-0.138, 1.+0.172), 
        '2000': (1.-0.145, 1.+0.183),
        '2500': (1.-0.16, 1.+0.206), 
        '3000': (1.-0.172, 1.+0.22), 
        '4000': (1.-0.195, 1.+0.269)
    }

XSEC_UNC = {
    'tt_hadronic_top': 1.05, 
    'ttX_hadronic_top': 1.2, 
    'multitop_hadronic_top': 1.15,
}

# from https://twiki.cern.ch/twiki/bin/viewauth/CMS/LumiRecommendationsRun2
LUMI_UNC = {
    # '2016preVFP': 1.012, 
    # '2016': 1.012,
    # '2016': 1.0026, # considering merged Run 2 histograms
    # '2017': 1.023,
    # '2017': 1.006, # considering merged Run 2 histograms
    # '2018': 1.025,
    # '2018': 1.0065, # considering merged Run 2 histograms
    'all_years_Run2': 1.016, # it takes into account the fact that the templates for Run 2 are merged together already 
    # 'all_years_Run2': 1.0130,
    # '2017_2018': 1.0027,
    # '2022': 1.014,
    # '2022EE': 1.014,
    'all_years_Run3': 1.014, # it takes into account the fact that the templates for Run 3 are merged together already 
}
LUMI_CORR_YEARS = ['2016', '2017', '2017_2018']

SYSTEMATICS = [
    'trigger', 
    'muonID',
    'muonISO',
    'electronID', 
    'electronPt', 
    'PU',
    'bTaggingBC', 
    'bTaggingLight',
    'bTaggingBCCorrelated', 
    'bTaggingLightCorrelated',

    'hotvrJESTotal', 
    'hotvrJER', 
    'ISR', 
    'FSR',
    'QCDScale',
    # 'MEfac', 
    # 'MEren',
    # 'MEenv',
    'PDF',
    'BDT',
]
if args.year == '2016preVFP' or args.year == '2016' or args.year == '2017' or args.year == 'all_years_Run2':
    SYSTEMATICS.append('L1preFiring')
if args.year == 'all_years_Run2':
    SYSTEMATICS.append('PUID')

UNCORRELATED_SYSTEMATICS = [
    'trigger', 
    'bTaggingBC', 
    'bTaggingLight', 
    'ak4JESTotal', 
    'ak4JER', 
    'hotvrJESTotal', 
    'hotvrJER', 
    'BDT', 
    'L1preFiring',
    'PUID'
]

# these values are calculated in different scripts
LOGN_OFFSET = {
    "NORM_CR_OFFSET": {
        "2T": {
            "all_years_Run2": {
                "ee": 1.115, "mumu": 1.095, "emu": 1.073,
            },
            "all_years_Run3": {
                "ee": 1.25, "mumu": 1.233, "emu": 1.178,
            },
        },
        "1T": {
            "all_years_Run2": {
                "ee": 1.041, "mumu": 1.035, "emu": 1.029,
            },
            "all_years_Run3": {
                "ee": 0.996, "mumu": 0.98, "emu": 1.073,
            },
        },
    },
    "FLAVOR_COMPOSITION_OFFSET": {
        "2T": {
            "all_years_Run2": {
                "ee_1b": 1.23, "ee_2b": 1.46,
                "mumu_1b": 1.20, "mumu_2b": 1.39,
                "emu_1b": 1.27, "emu_2b": 1.24,
                "ee_": 1.345, "mumu_": 1.295,
            },
            "all_years_Run3": {
                "ee_1b": 1.23, "ee_2b": 1.46,
                "mumu_1b": 1.20, "mumu_2b": 1.39,
                "emu_1b": 1.27, "emu_2b": 1.24,
                "ee_": 1.345, "mumu_": 1.295,
            },
        },
        "1T": {
            "all_years_Run2": {
                "ee_1b": 1.16, "ee_2b": 1.29,
                "mumu_1b": 1.14, "mumu_2b": 1.24,
                "emu_1b": 1.21, "emu_2b": 1.18,
                # "ee_": 1.4, "mumu_": 1.32,
            },
            "all_years_Run3": {
                "ee_1b": 1.16, "ee_2b": 1.29,
                "mumu_1b": 1.14, "mumu_2b": 1.24,
                "emu_1b": 1.21, "emu_2b": 1.18,
                # "ee_": 1.4, "mumu_": 1.32,
            },
        },
    },
    "NORM_FSR_BKG": {
        "2T": {
            "all_years_Run2": {
                # "ee_": 1.041, "mumu_": 1.048,
                "ee_1b": 1.05, "ee_2b": 1.19,
                "mumu_1b": 1.027, "mumu_2b": 1.028,
                "emu_1b": 1.062, "emu_2b": 1.025,
            },
            "all_years_Run3": {
                # "ee_": 1.111, "mumu_": 1.03,
                "ee_1b": 1.12, "ee_2b": 1.16,
                "mumu_1b": 1.05, "mumu_2b": 1.06,
                "emu_1b": 1.06, "emu_2b": 1.06,
            },
        },
        "1T": {
            "all_years_Run2": {
                # "ee_": 1.041, "mumu_": 1.048,
                "ee_1b": 1.028, "ee_2b": 1.012,
                "mumu_1b": 1.02, "mumu_2b": 1.029,
                "emu_1b": 1.028, "emu_2b": 1.021,
            },
            "all_years_Run3": {
                # "ee_": 1.111, "mumu_": 1.03,
                "ee_1b": 1.042, "ee_2b": 1.024,
                "mumu_1b": 1.063, "mumu_2b": 1.073,
                "emu_1b": 1.02, "emu_2b": 1.03,
            },
        },
    },
}
offset_mode = "1T" if "1T" in PREDICTION_REGION else "2T"

EXCLUDING_BINS = False #helpful for GoF in Run3 (first bin exclusion)
# ---

####################################################
####################################################

# creating data card per each mass/width point
bkg_list = ['prediction', 'tt_hadronic_top', 'ttX_hadronic_top', 'multitop_hadronic_top']
for width in WIDTHS:
    for mass in MASSES:
        print(f"\nttZ', m={mass}, width={width}")
        cb = ch.CombineHarvester()
        
        # --- backgrounds
        for bkg in bkg_list:
            for ichn, chn in enumerate(CHANNELS):
                for ireg, region in enumerate(REGIONS):
                    category_name = chn+'_'+region

                    print(f'\nRegion: {region}, chn: {chn}, {bkg}')

                    process = ch.Process()
                    process.set_process(bkg)
                    process.set_bin(category_name)
                    process.set_era(args.year)

                    root_infile = f"{BKG_ESTIMATION_DIR}/distributions_hadronic_t_removed.root"
                    root_infile = root_infile.replace("REGION", region)
                    print(f'Reading from: {root_infile}')

                    histo_name = f"nominal/{chn}/{bkg}"

                    bkg_hist_nominal = get_hist(
                        root_infile,
                        histo_name
                    )
                    if not bkg_hist_nominal:
                        print(f"{histo_name} does not exist in {root_infile}")
                        sys.exit()
                    if bkg_hist_nominal.Integral() == 0.0: #skipping empty histograms
                        continue

                    # --- rebinning procedure to avoid empty bins in the prediction template!
                    if bkg == 'prediction': 
                        bkg_hist_nominal, new_bin_edges = utils.auto_rebin(bkg_hist_nominal)
                        if BKG_SCALING:
                            bkg_hist_nominal.Scale(10)
                        if EXCLUDING_BINS and chn == 'ee' and CONTROL_REGIONS:
                            bkg_hist_nominal = utils.bin_exclusion(bkg_hist_nominal)

                    # saving the new binning edges to rebin other histograms
                    if len(new_bin_edges) != 0:
                        new_bin_edges_dict[category_name] = new_bin_edges
                    # ---

                    # --- NORMALIZATION AND JET FLAVOR OFFSETS
                    if bkg == 'prediction':
                        systematic = ch.Systematic()
                        systematic.set_name(f'norm_CR_offset_unc_{chn}_{args.year}')
                        systematic.set_bin(category_name)
                        systematic.set_type('lnN')
                        systematic.set_era(args.year)
                        systematic.set_value_u(LOGN_OFFSET["NORM_CR_OFFSET"][offset_mode][args.year][chn])
                        systematic.set_process(bkg)

                        cb.InsertSystematic(systematic)

                        systematic = ch.Systematic()
                        systematic.set_name(f'jet_flavor_difference_{chn}_{region}')
                        systematic.set_bin(category_name)
                        systematic.set_type('lnN')
                        systematic.set_era(args.year)
                        systematic.set_value_u(LOGN_OFFSET["FLAVOR_COMPOSITION_OFFSET"][offset_mode][args.year][chn+'_'+region])
                        systematic.set_process(bkg)

                        cb.InsertSystematic(systematic)
                    # ---

                    for systematic_name in SYSTEMATICS:
                        # templates to be fixed
                        if args.year == 'all_years_Run3' and 'bTaggingLight' in systematic_name:
                            continue 

                        years = ['_2016', '_2016preVFP', '_2017', '_2018'] if systematic_name in UNCORRELATED_SYSTEMATICS else ['']
                        if args.year == 'all_years_Run3':
                            years = ['_2022', '_2022EE'] if systematic_name in UNCORRELATED_SYSTEMATICS else ['']

                        for year in years:
                            if year == '_2018' and 'L1preFiring' in systematic_name:
                                continue

                            systematic = ch.Systematic()
                            systematic.set_name(f'{systematic_name}{year}')
                            systematic.set_bin(category_name)
                            systematic.set_type('shape')
                            systematic.set_era(args.year)

                            # envelope method for MEren/env/fac
                            if systematic_name == 'QCDScale':
                                histos_qcd = []
                                for qcd_sys in ['MEenv', 'MEfac', "MEren"]:
                                    for variation in ['Up', 'Down']:
                                        histo = get_hist(
                                            root_infile,
                                            f"{qcd_sys}{variation}{year}/{chn}/{bkg}"
                                        )
                                        if histo:
                                            if new_bin_edges_dict[category_name]:
                                                histo = histo.Rebin(
                                                    len(new_bin_edges_dict[category_name]) - 1, 
                                                    histo.GetName(),
                                                    new_bin_edges_dict[category_name]
                                                )
                                            histos_qcd.append(histo)
                                        else:
                                            # print(f"{qcd_sys}{variation}{year}/{chn}/{bkg} not available!")
                                            continue
                                
                                if len(histos_qcd) == 0:
                                    continue

                                bkg_hist_down = bkg_hist_nominal.Clone(f"{bkg}_data_hotvr_invariant_mass_leading_subleading_down")
                                bkg_hist_up = bkg_hist_nominal.Clone(f"{bkg}_data_hotvr_invariant_mass_leading_subleading_up")

                                for ibin in range(1, bkg_hist_nominal.GetNbinsX()+1):
                                    nominal = bkg_hist_nominal.GetBinContent(ibin)
                                    if nominal == 0:
                                        # Handle zero-nominal case safely
                                        bin_values = [h.GetBinContent(ibin) for h in histos_qcd if h != -1]
                                        if len(bin_values) == 0:
                                            continue
                                        bkg_hist_up.SetBinContent(ibin, max(bin_values))
                                        bkg_hist_down.SetBinContent(ibin, min(bin_values))
                                    else:
                                        deviations = [h.GetBinContent(ibin) - nominal for h in histos_qcd if h != -1]
                                        if len(deviations) == 0:
                                            continue

                                        up_deviation = max(deviations)
                                        down_deviation = min(deviations)

                                        bkg_hist_up.SetBinContent(ibin, nominal + up_deviation)
                                        bkg_hist_down.SetBinContent(ibin, nominal + down_deviation)
                            
                            else:
                                bkg_hist_down = get_hist(
                                    root_infile,
                                    f"{systematic_name}Down{year}/{chn}/{bkg}" #histo_name
                                )
                                bkg_hist_up = get_hist(
                                    root_infile,
                                    f"{systematic_name}Up{year}/{chn}/{bkg}"
                                )

                                # FSR is taken as normalization uncertainty
                                if systematic_name == 'FSR' and bkg == 'prediction':
                                    norm_factor = LOGN_OFFSET["NORM_FSR_BKG"][offset_mode][args.year][f'{chn}_{region}']
                                    systematic.set_type('lnN')
                                    systematic.set_value_u(norm_factor)

                                if not isinstance(bkg_hist_nominal, ROOT.TH1):
                                    # raise TypeError(f"Expected TH1 object, got {type(bkg_hist_nominal)} instead.")
                                    continue
                                if not isinstance(bkg_hist_down, ROOT.TH1):
                                    # print(f"Expected cloned TH1 object for up bin, got {type(bkg_hist_down)}")
                                    continue
                                if not isinstance(bkg_hist_up, ROOT.TH1):
                                    # print(f'Expected cloned TH1 object for down bin, got {type(bkg_hist_up)}')
                                    continue
                                if bkg_hist_down.Integral() == 0.0 or bkg_hist_up.Integral() == 0.0: #skipping empty histograms
                                    continue

                            if BKG_SCALING:
                                bkg_hist_up.Scale(10)
                                bkg_hist_down.Scale(10)

                            if new_bin_edges_dict[category_name] != array('d'): # in case of rebinning!
                                bkg_hist_up = bkg_hist_up.Rebin(
                                    len(new_bin_edges_dict[category_name]) - 1, 
                                    bkg_hist_up.GetName(),
                                    new_bin_edges_dict[category_name]
                                )
                                bkg_hist_down = bkg_hist_down.Rebin(
                                    len(new_bin_edges_dict[category_name]) - 1, 
                                    bkg_hist_down.GetName(),
                                    new_bin_edges_dict[category_name]
                                )
                            if EXCLUDING_BINS and chn == 'ee' and CONTROL_REGIONS:
                                bkg_hist_up = utils.bin_exclusion(bkg_hist_up)
                                kg_hist_down = utils.bin_exclusion(bkg_hist_down)

                            # switching up/down variation in case they are swapped
                            if bkg_hist_up.Integral() < bkg_hist_down.Integral(): 
                                print(
                                    f"\nSystematic: {systematic_name} -> "
                                    f"integral up: {bkg_hist_up.Integral()}, down: {bkg_hist_down.Integral()}"
                                )
                                print("Switching up/down uncertainties!!!")
                                
                                systematic.set_shapes(
                                    bkg_hist_down,
                                    bkg_hist_up,
                                    bkg_hist_nominal,
                                )
                                if bkg_hist_up.Integral() > bkg_hist_nominal.Integral() or bkg_hist_nominal.Integral() > bkg_hist_down.Integral():
                                    print(f'WARNING!! integral nominal: {bkg_hist_nominal.Integral()} outside up/down variation!!')
                            
                            else:
                                systematic.set_shapes(
                                    bkg_hist_up,
                                    bkg_hist_down,
                                    bkg_hist_nominal,
                                )
                                if bkg_hist_up.Integral() < bkg_hist_nominal.Integral() or bkg_hist_nominal.Integral() < bkg_hist_down.Integral():
                                    print(f"\nSystematic: {systematic_name}")
                                    print(f'WARNING!! integral nominal: {bkg_hist_nominal.Integral()} outside up/down variation!!')

                            systematic.set_process(bkg)
                            systematic.set_signal(False)

                            cb.InsertSystematic(systematic)

                    process.set_shape(bkg_hist_nominal, True)
                    cb.InsertProcess(process)

                # cross section uncertainties
                if bkg != 'prediction':
                    systematic = ch.Systematic()
                    systematic.set_name(f'xsec_unc_{bkg}')
                    systematic.set_bin(category_name)
                    systematic.set_type('lnN')
                    systematic.set_era(args.year)
                    systematic.set_value_u(XSEC_UNC[bkg])
                    systematic.set_process(bkg)

                    cb.InsertSystematic(systematic)

        cb.cp().backgrounds().AddSyst( cb, "lumi_$ERA", "lnN", ch.SystMap()
            ((LUMI_UNC[args.year]))
        )

        # --- dealing with partial lumi correlation in Run2
        # if args.year == 'all_years_Run2':
        #     for year in LUMI_CORR_YEARS:
        #         cb.cp().backgrounds().AddSyst( cb, f"lumi_{year}", "lnN", ch.SystMap()
        #             ((LUMI_UNC[year]))
        #         )

        # --- observation (if BLINDED -> constructing Asimov data using prediction)
        for ichn, chn in enumerate(CHANNELS): 
            for ireg, region in enumerate(REGIONS):
                category_name = chn+'_'+region

                root_infile = f'{BKG_ESTIMATION_DIR}/distributions_hadronic_t_removed.root'
                root_infile = root_infile.replace("REGION", region)

                obs = ch.Observation()
                histo_name = f"nominal/{chn}/data_prediction_region"
                obs_hist = get_hist(
                    root_infile,
                    histo_name
                )
                if not obs_hist:
                    print(f"{histo_name} does not exist in {root_infile}")
                    sys.exit()

                if new_bin_edges_dict[category_name]:
                    obs_hist = obs_hist.Rebin(
                        len(new_bin_edges_dict[category_name] ) - 1, 
                        obs_hist.GetName(),
                        new_bin_edges_dict[category_name] 
                    ) # rebinning accordingly to the bkg prediction
                if BKG_SCALING:
                    obs_hist.Scale(10)
                # if EXCLUDING_BINS and chn == 'ee' and CONTROL_REGIONS: #excluding first bin of Run3 for GoF 
                #     obs_hist = utils.bin_exclusion(obs_hist)

                obs_hist.SetDirectory(0)
                obs.set_shape(obs_hist, True)
                obs.set_bin(category_name)
                obs.set_era(args.year)
                cb.InsertObservation(obs)
        # --- 

        # --- signals
        sgn_procs = [f'ttZprime_M-{mass}_Width{width}']
        if IS_BSM_TTA:
            sgn_procs = [f'tta_M-{mass}_Width{width}']
        if IS_BSM_TTH:
            sgn_procs = [f'tth_M-{mass}_Width{width}']

        process = ch.Process()
        process.set_process(sgn_procs[0])
        for ichn, chn in enumerate(CHANNELS): 
            for ireg, region in enumerate(REGIONS):
                category_name = chn+'_'+region
                
                process.set_bin(category_name)
                process.set_era(args.year)

                root_infile = f'{SIGNAL_SHAPES}/distributions.root'
                if IS_BSM_TTA:
                    root_infile = f'{SIGNAL_SHAPES}/distributions_tta.root'
                if IS_BSM_TTH:
                    root_infile = f'{SIGNAL_SHAPES}/distributions_tth.root'

                root_infile = root_infile.replace("REGION", region)

                bkg_hist_nominal = get_hist(
                        root_infile,
                        f"nominal/{chn}/{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading"
                )
                if not isinstance(bkg_hist_nominal, ROOT.TH1):
                    # raise TypeError(f"Expected TH1 object, got {type(bkg_hist_nominal)} instead.")
                    continue

                # signal histogram to be rebinned accordingly to the background bins
                if new_bin_edges_dict[category_name] != array('d'):
                    bkg_hist_nominal = bkg_hist_nominal.Rebin(
                        len(new_bin_edges_dict[category_name] ) - 1, 
                        bkg_hist_nominal.GetName(),
                        new_bin_edges_dict[category_name] 
                    )
                    if EXCLUDING_BINS and chn == 'ee' and CONTROL_REGIONS:
                        bkg_hist_nominal = utils.bin_exclusion(bkg_hist_nominal)

                process.set_shape(bkg_hist_nominal, True)
                process.set_signal(True)

                cb.InsertProcess(process)

                for systematic_name in SYSTEMATICS:
                    # --- bug in bTaggingLightCorrelated Run3 templates (TO BE FIXED!!!!)
                    if args.year == 'all_years_Run3' and 'bTaggingLight' in systematic_name:
                        continue 

                    years = ['_2016', '_2016preVFP', '_2017', '_2018'] if systematic_name in UNCORRELATED_SYSTEMATICS else ['']
                    if args.year == 'all_years_Run3':
                        years = ['_2022', '_2022EE'] if systematic_name in UNCORRELATED_SYSTEMATICS else ['']

                    for year in years:
                        if year == '_2018' and 'L1preFiring' in systematic_name:
                            continue

                        systematic = ch.Systematic()
                        systematic.set_name(f'{systematic_name}{year}')
                        systematic.set_bin(category_name)
                        systematic.set_type('shape')
                        systematic.set_era(args.year)

                        # --- envelope method for MEren/fac/env
                        if systematic_name == 'QCDScale':
                            histos_qcd = []
                            for qcd_sys in ['MEenv', 'MEfac', "MEren"]:
                                for variation in ['Up', 'Down']:
                                    histo = get_hist(
                                            root_infile,
                                            f"{qcd_sys}{variation}{year}/{chn}/{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading"
                                        )
                                    if histo:
                                        if new_bin_edges_dict[category_name]:
                                            histo = histo.Rebin(
                                                len(new_bin_edges_dict[category_name]) - 1, 
                                                histo.GetName(),
                                                new_bin_edges_dict[category_name]
                                            )
                                        histos_qcd.append(histo)
                                    else:
                                        print(f'{qcd_sys}{variation}{year}/{chn}/{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading not available!')

                            bkg_hist_down = bkg_hist_nominal.Clone(f"{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading_down")
                            bkg_hist_up = bkg_hist_nominal.Clone(f"{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading_up")

                            for ibin in range(1, bkg_hist_nominal.GetNbinsX()+1):
                                nominal = bkg_hist_nominal.GetBinContent(ibin)
                                if nominal == 0:
                                    # Handle zero-nominal case safely
                                    # print(f'zero nominal {nominal} {[h.GetBinContent(ibin) for h in histos_qcd]}')

                                    bin_values = [h.GetBinContent(ibin) for h in histos_qcd if h!=-1]
                                    if len(bin_values) == 0:
                                        continue
                                    bkg_hist_up.SetBinContent(ibin, max(bin_values))
                                    bkg_hist_down.SetBinContent(ibin, min(bin_values))
                                else:
                                    # print(f'non-zero nominal {nominal} {[h.GetBinContent(ibin) - nominal for h in histos_qcd]}')
                                    # print([h.GetBinContent(ibin) for h in histos_qcd], [h.GetName() for h in histos_qcd])
                                    # print(bkg_hist_nominal.GetNbinsX(), histos_qcd[0].GetNbinsX())

                                    deviations = [h.GetBinContent(ibin) - nominal for h in histos_qcd if h!=-1]
                                    if len(deviations) == 0:
                                        continue
                                    if deviations:
                                        up_deviation = max(deviations)
                                        down_deviation = min(deviations)
                                    else:
                                        up_deviation = 0.0
                                        down_deviation = 0.0

                                    bkg_hist_up.SetBinContent(ibin, nominal + up_deviation)
                                    bkg_hist_down.SetBinContent(ibin, nominal + down_deviation)
                        else:
                            bkg_hist_down = get_hist(
                                root_infile,
                                f"{systematic_name}Down{year}/{chn}/{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading"
                            )
                            bkg_hist_up = get_hist(
                                root_infile,
                                f"{systematic_name}Up{year}/{chn}/{sgn_procs[0]}_hotvr_invariant_mass_leading_subleading"
                            )

                        # normalization uncertainty for FSR (from root files)
                        if systematic_name == 'FSR':
                            norm_factor = normalization_systematic(root_infile, systematic_name, chn, region, sgn_procs[0])
                            systematic.set_type('lnN')
                            systematic.set_value_u(norm_factor)

                        if not isinstance(bkg_hist_nominal, ROOT.TH1):
                            raise TypeError(f"Expected TH1 object, got {type(bkg_hist_nominal)} instead.")
                        if not isinstance(bkg_hist_down, ROOT.TH1):
                            # raise TypeError(f"Expected cloned TH1 object for up bin, got {type(bkg_hist_down)}")
                            # print(f"Expected cloned TH1 object for up bin, got {type(bkg_hist_down)}")
                            continue
                        if not isinstance(bkg_hist_up, ROOT.TH1):
                            # raise TypeError(f"Expected cloned TH1 object for down bin, got {type(bkg_hist_up)}")
                            # print(f'Expected cloned TH1 object for down bin, got {type(bkg_hist_up)}')
                            continue

                        if new_bin_edges_dict[category_name] != array('d'):
                            bkg_hist_up = bkg_hist_up.Rebin(
                                len(new_bin_edges_dict[category_name]) - 1, 
                                bkg_hist_up.GetName(),
                                new_bin_edges_dict[category_name]
                            )
                            bkg_hist_down = bkg_hist_down.Rebin(
                                len(new_bin_edges_dict[category_name]) - 1, 
                                bkg_hist_down.GetName(),
                                new_bin_edges_dict[category_name]
                            )
                            if EXCLUDING_BINS and chn == 'ee' and CONTROL_REGIONS:
                                bkg_hist_up = utils.bin_exclusion(bkg_hist_up)
                                bkg_hist_down = utils.bin_exclusion(bkg_hist_down)

                        if bkg_hist_up.Integral() < bkg_hist_down.Integral(): 
                            print(f"\nSystematic: {systematic_name} -> integral up: {bkg_hist_up.Integral()}, down: {bkg_hist_down.Integral()}")
                            print("Switching up/down uncertainties!!!")
                            systematic.set_shapes(
                                bkg_hist_down,
                                bkg_hist_up,
                                bkg_hist_nominal,
                            )
                            if bkg_hist_up.Integral() > bkg_hist_nominal.Integral() or bkg_hist_nominal.Integral() > bkg_hist_down.Integral():
                                print(f'WARNING!! integral nominal: {bkg_hist_nominal.Integral()} outside up/down variation!!')
                        else:
                            systematic.set_shapes(
                                bkg_hist_up,
                                bkg_hist_down,
                                bkg_hist_nominal,
                            )
                            if bkg_hist_up.Integral() < bkg_hist_nominal.Integral() or bkg_hist_nominal.Integral() < bkg_hist_down.Integral():
                                print(f"\nSystematic: {systematic_name}")
                                print(f'WARNING!! integral nominal: {bkg_hist_nominal.Integral()} outside up/down variation!!')

                        systematic.set_process(sgn_procs[0])
                        systematic.set_signal(True)

                        cb.InsertSystematic(systematic)

        # --- sgn cross-section 
        # if IS_BSM_FOUR_TOP:
        #     cb.cp().signals().AddSyst(
        #         cb, 'xsec_TTZprimeToTT_Width4_M{}'.format(mass), "lnN", ch.SystMap()((XSEC_UNC_SIGNALS[mass])) )
        # if IS_BSM_THREE_TOP:
        #     cb.cp().signals().AddSyst(
        #         cb, 'xsec_S-TZprimeToTT_Width4_M{}'.format(mass), "lnN", ch.SystMap()((XSEC_UNC_SIGNALS[mass])) )
        # ---

        cb.cp().signals().AddSyst(
            cb, "lumi_$ERA", "lnN", ch.SystMap()(LUMI_UNC[args.year])
        )
        # if args.year == 'all_years_Run2':
        #     for year in LUMI_CORR_YEARS:
        #         cb.cp().signals().AddSyst( cb, f"lumi_{year}", "lnN", ch.SystMap()
        #             ((LUMI_UNC[year]))
        #         )

        # cb.AddDatacardLineAtEnd("lumiscale rateParam * * 3.31")
        cb.AddDatacardLineAtEnd("* autoMCStats 10 0 1")
        # cb.PrintAll()

        rename_bins(cb)
        rename_systematics(cb)

        if not os.path.isdir(args.output_dir):
            os.makedirs(args.output_dir)
        output_path = "{}/{}/".format(args.output_dir, args.year)
        if not os.path.isdir(output_path):
            os.makedirs(output_path)

        if IS_BSM_FOUR_TOP:
            output_string = f"TTZprimeToTT_M{mass}_Width{width}_{args.year}.txt"
        if IS_BSM_THREE_TOP:
            output_string = f"S-TZprimeToTT_M{mass}_Width{width}_{args.year}.txt"
        if IS_BSM_TTA:
            output_string = f"tta_M{mass}_Width{width}_{args.year}.txt"
        if IS_BSM_TTH:
            output_string = f"tth_M{mass}_Width{width}_{args.year}.txt"
        print('Saving datacard in: {}'.format(output_path + output_string))

        root_output = ROOT.TFile.Open(output_path + output_string.replace('txt', 'root'), "RECREATE")
        cb.cp().WriteDatacard(
            output_path + output_string.format(mass, args.year),
            root_output
        )
        root_output.Close()

        print('Saving datacard in: {}'.format(output_path + output_string.format(mass, args.year)))