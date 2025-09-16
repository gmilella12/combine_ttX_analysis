import os, re
import sys
import math

from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np
from array import array

import math

import ROOT

ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)

import utils as utils

# LEPTON_SELECTIONS = ['single_muon'] 
CHANNELS = [
    'ee_1b',
    'ee_2b',
    'mumu_1b',
    'mumu_2b', 
    'emu_1b',
    'emu_2b'
    # 'ee_',
    # 'mumu_'
]
MASSES_SELECTED = ['3000'] #, '1750'] #'500', '1000', '2000']
ERAS = [
    'all_years_Run2',
    'all_years_Run3'
]

def hex_to_root_color(hex_color):
    h = hex_color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return ROOT.TColor.GetColor(*rgb)
HIST_COLOR = {
    'tt_hadronic_top': hex_to_root_color("#964a8b"),
    'ttX_hadronic_top': hex_to_root_color("#f89c20"),
    'multitop_hadronic_top': hex_to_root_color("#7a21dd"), 
}

MASS_VALUES = ['500'] #, '1750'
WIDTH_VALUES = ['4']#, '50']

BKG_SCALE = 10

BINNING = {
    'all_years_Run2': array('d', [0., 600, 800, 1000, 1240, 1500, 2000, 5100]),
    'all_years_Run3': array('d', [0., 650, 800, 1100, 1500, 1900, 5100, 5105]), #5105 combine bug -> even if Run 3 template has less bin, it shows same nBins as Run 2
}

class Processor:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self._creation_output_dir()

        self.all_bkg = {}
        self.all_sgn = {}
        self.all_data = {}

        self.stack = ROOT.THStack()
        self.tot_bkg = ROOT.TH1F()
        self.tot_bkg_without = ROOT.TH1F()
        self.tot_bkg_with = ROOT.TH1F()
        self.ratio_hist = ROOT.TH1F()
        self.ratio_hist_dict = {}

        self.ratio_hist_without = ROOT.TH1F()
        self.list_bkg = []
        
        self.line = ROOT.TLine()
        self.all_bkg_total_unc = ROOT.TH1F()
        self.all_bkg_total_unc_ratio = ROOT.TH1F()

        self.data_rebinned = ROOT.TH1F()
        self.nominal_rebinned = ROOT.TH1F()
        self.up_rebinned = ROOT.TH1F()
        self.down_rebinned = ROOT.TH1F()

        self.tot_sys_up, self.tot_sys_down = {}, {}
        self.sys_up = ROOT.TH1F()
        self.sys_down = ROOT.TH1F()

        self.all_bkg_total_unc = ROOT.TH1F()

        self.tot_sgn = []

    def _creation_output_dir(self):
        # check if dir exist
        for year in ERAS:
            if not os.path.exists(self.output_dir + f'/{year}/prefit_plots'):
                os.makedirs(self.output_dir + f'/{year}/prefit_plots')

            if not os.path.exists(self.output_dir + f'/{year}/postfit_plots'):
                os.makedirs(self.output_dir + f'/{year}/postfit_plots')
        return self.output_dir

    def _plotting_variable(self, channel, type="", mass="", year=''):  
        canvas = utils.makeCanvas(name='canvas_{}_{}_{}_{}'.format(channel, type, mass, year))
        # canvas.SetBottomMargin(0.12)
        canvas.SetLeftMargin(0.135)
        canvas.Draw("")

        pad_up = utils.makePad(0, 0., 1, 1.0, name='pad_up_{}'.format(channel))
        # pad_up.SetLeftMargin(0.135)
        # pad_up.SetBottomMargin(0)
        # # pad_up.SetBottomMargin(0.12)
        pad_up.Draw()
        pad_down = utils.makePad(0, 0, 1, 0.3, name='pad_down_{}'.format(channel))
        # pad_down.SetTopMargin(0)
        # pad_down.SetLeftMargin(0.135)
        # pad_down.SetBottomMargin(0.4)
        pad_down.Draw()

        legend_bkg = utils.makeLegend(0.51, 0.60, 0.62, 0.87)
        legend_bkg.SetTextSize(23)

        legend_sgn = utils.makeLegend(0.52, 0.67, 0.7, 0.87)
        legend_sgn.SetTextSize(21)

        #creating the frame_up in the canvashotvr_scoreBDT_leading
        pad_up.cd()
        binx = max(BINNING[year])
        nbins = len(BINNING[year]) - 1
        frame_up = ROOT.TH1F(f"frame_up_{channel}", "", nbins, BINNING[year])
        # frame_up.SetMinimum(0)
        # frame_up.SetMaximum(self.all_bkg[f'nominal_{channel}'].GetMaximum() * 2.5)
        ymax = max(self.all_bkg[f'nominal_{channel}_prediction'].GetMaximum() * 2, self.all_data[channel].GetMaximum() * 2)
        ymin = 0.  # Or 0.01 if log is needed

        frame_up = pad_up.DrawFrame(min(BINNING[year]), ymin, max(BINNING[year]), ymax)
        frame_up.GetYaxis().SetTitle("Events")
        frame_up.GetXaxis().SetTitle("M_{JJ} [GeV]")
        frame_up.GetXaxis().SetNoExponent(ROOT.kTRUE)
        frame_up.GetYaxis().SetNdivisions(510)
        frame_up.GetXaxis().SetTitleOffset(0.9)

        # Fill with tiny content to make it drawable
        for i in range(1, nbins + 1):
            frame_up.SetBinContent(i, 1e-6)

        frame_up.Draw("HIST")
        print("Frame y-range:", frame_up.GetMinimum(), frame_up.GetMaximum())

        # --- BKG
        self.all_bkg[f'nominal_{channel}_prediction'].SetLineColor(ROOT.kRed)
        self.all_bkg[f'nominal_{channel}_prediction'].SetLineWidth(2)

        for bkg in ['tt_hadronic_top', 'ttX_hadronic_top', 'multitop_hadronic_top']:
            if self.all_bkg[f'nominal_{channel}_{bkg}']:
                self.all_bkg[f'nominal_{channel}_{bkg}'].SetFillColor(HIST_COLOR[bkg])

        # legend_sgn.AddEntry(self.all_bkg[f'nominal_{channel}'], f'{type} Background', 'l')
        # ---
        pad_up.Update()
        # self.all_bkg[f'nominal_{channel}'].GetYaxis().SetRangeUser(
        #     0, 
        #     self.all_bkg[f'nominal_{channel}'].GetMaximum() * 3
        #     # 10
        # )
        # self.all_bkg[f'nominal_{channel}'].Draw('hist same')
        ROOT.gPad.Modified()
        ROOT.gPad.Update()

        # --- SIGNAL
        # self.all_sgn.SetLineWidth(2)
        # self.all_sgn.SetLineStyle(2)
        # self.all_sgn.Scale(BKG_SCALE)
        # self.all_sgn.Draw('hist same')
        legend_sgn.AddEntry(self.all_sgn[channel], f"ttZ' (x{BKG_SCALE}), M_{{Z'}}={mass} GeV, #Gamma/M_{{Z'}} = 4%", 'l')
        # ---

        # --- treating systematics/stats unc BKG
        # --- UP/DOWN SYSTEMATIC
        n_bins = self.all_bkg[f'nominal_{channel}_prediction'].GetNbinsX()
        self.tot_sys_down = []
        self.tot_sys_up = []

        x = array('d', [self.all_bkg[f'nominal_{channel}_prediction'].GetBinCenter(i) for i in range(1, n_bins + 1)])
        ex = array('d', [self.all_bkg[f'nominal_{channel}_prediction'].GetBinWidth(i)/2 for i in range(1, n_bins + 1)])
        y = array('d', [self.all_bkg[f'nominal_{channel}_prediction'].GetBinContent(i) for i in range(1, n_bins + 1)])
        ey_up = array('d', [self.all_bkg[f'tot_unc_{channel}'].GetBinError(i+1) for i in range(n_bins)])
        ey_down = array('d', [self.all_bkg[f'tot_unc_{channel}'].GetBinError(i+1) for i in range(n_bins)])

        self.all_bkg_total_unc = ROOT.TGraphAsymmErrors(n_bins, x, y, ex, ex, ey_down, ey_up)

        self.all_bkg_total_unc.SetFillColor(ROOT.kBlack) 
        self.all_bkg_total_unc.SetFillStyle(3005)

        self.all_bkg_total_unc.Draw('2 SAME')
        legend_sgn.AddEntry(self.all_bkg_total_unc, 'Total Unc.', 'f')
        # --- 

        # --- DATA
        if self.all_data != None:
            self.all_data[channel].SetBinErrorOption(1) #equivalent to SetBinErrorOption(TH1::kPoisson)
            self.all_data[channel].SetMarkerStyle(20)
            self.all_data[channel].SetLineColor(ROOT.kBlack)
            self.all_data[channel].Draw('pE same')
        # ---

        legend_bkg.Draw("SAME")
        legend_sgn.Draw('SAME')

        utils.additional_text(channel, year)

        # pad_up.SetLogy()
        ROOT.gPad.RedrawAxis()
        pad_up.Update()
        pad_up.Modified()

        pad_down.cd()
        # pad_down.SetGrid()
        frame_down = ROOT.TH1D(
            f"dummy_{channel}_{type}_{mass}_{year}", 
            "", 
            len(BINNING[year]) - 1,
            array('d', BINNING[year])
        )
        frame_down.GetYaxis().SetTitle('Data/Sim.')
        frame_down.GetXaxis().SetTitle("M_{JJ} [GeV]")
        frame_down.SetMinimum(0.)
        frame_down.SetMaximum(1.9)
        # frame_down.GetXaxis().SetRangeUser(0, binx)
        # bin_laframe_down.bels = ["600", "800", "1000", "1240", "1500", "2000", "5100"]
        # print("N bins in frame_down:", frame_down.GetNbinsX())
        # print("N bin_labels:", len(bin_labels) - 1)
        # for i in range(1, n_bins + 1):
        #     frame_down.GetXaxis().SetBinLabel(i, bin_labels[i - 1])
        # frame_down.GetXaxis().SetLabelSize(0.08)
        frame_down.GetXaxis().SetTitleOffset(0.9)
        frame_down.GetXaxis().SetNoExponent(ROOT.kTRUE)
        # frame_down.SetMinimum(0.)
        # frame_down.SetMaximum(1.9)
        # frame_down.GetXaxis().SetTitleOffset(1.5)
        # frame_down.GetYaxis().SetTitleOffset(1.5)
        frame_down.Draw("")

        if self.all_data != None:
            self.ratio_hist = self.all_data[channel].Clone(f"data_over_mc_{channel}_{year}")
            ROOT.SetOwnership(self.ratio_hist, False)

            dummy_bkg = self.all_bkg[f'nominal_{channel}_prediction'].Clone(f"dummy_mc_{channel}_{year}")
            ROOT.SetOwnership(dummy_bkg, False)

            # def print_bin_edges(hist):
            #     print(f"Histogram: {hist.GetName()}")
            #     for i in range(1, hist.GetNbinsX() + 2):  # +2 to include upper edge
            #         print(f"  Bin {i-1}: {hist.GetBinLowEdge(i)}")

            # print_bin_edges(dummy_bkg)
            # print_bin_edges(self.all_data)

            for bin in range(1, dummy_bkg.GetNbinsX()):
                dummy_bkg.SetBinError(bin, 0)
            self.ratio_hist.Divide(dummy_bkg)
            self.ratio_hist.Draw('E same')

        ratio_y = array('d', [1.0 for i in range(n_bins)])
        ratio_ey_up = array('d', [(ey_up[i]) / y[i] if y[i] > 0 else 0 for i in range(n_bins)])
        ratio_ey_down = array('d', [(ey_down[i]) / y[i] if y[i] > 0 else 0 for i in range(n_bins)])

        self.all_bkg_total_unc_ratio = ROOT.TGraphAsymmErrors(n_bins, x, ratio_y, ex, ex, ratio_ey_down, ratio_ey_up)
        self.all_bkg_total_unc_ratio.SetFillColor(ROOT.kBlack)
        self.all_bkg_total_unc_ratio.SetFillStyle(3005)

        self.all_bkg_total_unc_ratio.Draw('2 SAME')

        self.line = ROOT.TLine(
            0, 
            1 , 
            binx, 
            1
        )
        self.line.SetLineWidth(2)
        self.line.SetLineColor(ROOT.kRed + 2)
        self.line.Draw('same')

        # pad_down.SetLogy()
        ROOT.gPad.RedrawAxis()
        pad_down.Update()

        canvas.cd()
        pad_up.cd()
        ROOT.gPad.Modified()
        ROOT.gPad.Update()

        canvas.Update()

        # print("Canvas Y axis range:", pad_up.GetUymin(), "-", pad_up.GetUymax())

        # canvas.S÷etLogy()
        # ROOT.gPad.RedrawAxis()

        return canvas

    def process(self):
        self.all_bkg = {}
        self.all_sgn = {}
        self.all_data = {}

        for mass in MASS_VALUES:
            for width in WIDTH_VALUES:
                # if width == '50' and mass != '3000':
                #     continue

                fpath = f'{self.input_dir}/Run2_Run3/fitDiagnostics_M{mass}_Width{width}.root'
                if os.path.exists(fpath):
                    input_root_file = ROOT.TFile(fpath, 'READ') #_with_btagSF
                else: 
                    print('File {} does not exist'.format(fpath))
                    sys.exit()
                print("Analyzing file: {}".format(fpath)) #_with_btagSF
                
                for year in ERAS:
                    print(f"\nYear: {year}")
                    # --- prefit
                    for channel in CHANNELS:
                        print(f"Channel: {channel}")
                        # --- background
                        for bkg in ['prediction', 'multitop_hadronic_top', 'ttX_hadronic_top', 'tt_hadronic_top']:
                            self.all_bkg[f'nominal_{channel}_{bkg}'] = input_root_file.Get(f'shapes_prefit/yr_{year}_{channel}/{bkg}')
                            if not self.all_bkg[f'nominal_{channel}_{bkg}']:
                                print(f"Bkg histo (shapes_prefit/yr_{year}_{channel}/{bkg}) not found!")
                            else:
                                self.all_bkg[f'nominal_{channel}_{bkg}'] = utils.convert_index_hist_to_mjj(
                                    self.all_bkg[f'nominal_{channel}_{bkg}'], 
                                    BINNING[year], 
                                    name=f"{self.all_bkg[f'nominal_{channel}_{bkg}'].GetName()}_mjj_{channel}"
                                )
                        
                        self.all_bkg[f'tot_unc_{channel}'] = input_root_file.Get(f'shapes_prefit/yr_{year}_{channel}/total')
                        self.all_bkg[f'tot_unc_{channel}'] = utils.convert_index_hist_to_mjj(
                            self.all_bkg[f'tot_unc_{channel}'], 
                            BINNING[year],
                            name=f"{self.all_bkg[f'tot_unc_{channel}'].GetName()}_mjj_{channel}"
                            )
                        # ---

                        # --- signal
                        self.all_sgn[channel] = input_root_file.Get(
                            f'shapes_prefit/yr_{year}_{channel}/ttZprime_M-{mass}_Width{width}'
                        )
                        if not self.all_sgn:
                            print(f"Signal histo (shapes_prefit/yr_{year}_{channel}/ttZprime_M-{mass}_Width{width}) not found!")
                        else:
                            self.all_sgn[channel] = utils.convert_index_hist_to_mjj(self.all_sgn[channel], BINNING[year]) # recreating MJJ distribution from bins of combine
                        # ---

                        # --- data
                        data_r2 = input_root_file.Get(f'shapes_prefit/yr_{year}_{channel}/data')
                        hist1 = utils.graph_to_hist(data_r2, f"prefit_{channel}_{year}")
                        self.all_data[channel] = utils.convert_index_hist_to_mjj(hist1, BINNING[year]) # recreating MJJ distribution from bins of combine
                        # ---

                        canvas = self._plotting_variable(
                            channel,
                            type="Pre-fit",
                            mass=mass,
                            year=year
                        )
                        
                        output_filename = f"{self.output_dir}/{year}/prefit_plots/prefit_M-{mass}_Width{width}_channel_{channel}"
                        canvas.SaveAs(f"{output_filename}.png")
                        canvas.SaveAs(f"{output_filename}.pdf")

                        debug_outfile = ROOT.TFile(f"{self.output_dir}/{year}/prefit_plots/debug_hist_{channel}_M-{mass}_Width{width}_{year}.root", "RECREATE")
                        for bkg in ['prediction', 'multitop_hadronic_top', 'ttX_hadronic_top', 'tt_hadronic_top']:
                            if self.all_bkg[f'nominal_{channel}_{bkg}']:
                                self.all_bkg[f'nominal_{channel}_{bkg}'].SetName(bkg)
                                self.all_bkg[f'nominal_{channel}_{bkg}'].Write()
                        self.all_data[channel].SetName("data_obs")
                        self.all_data[channel].Write()
                        if self.all_sgn.get(channel):
                            self.all_sgn[channel].SetName("signal")
                            self.all_sgn[channel].Write()
                        print(f'Saving distributions for debugging: {self.output_dir}/{year}/prefit_plots/debug_hist_{channel}_M-{mass}_Width{width}_{year}.root')
                        debug_outfile.Close()
                    # ---

                    # --- postfit
                    for channel in CHANNELS:
                        for bkg in ['prediction', 'multitop_hadronic_top', 'ttX_hadronic_top', 'tt_hadronic_top']:
                            self.all_bkg[f'nominal_{channel}_{bkg}'] = input_root_file.Get(
                                f'shapes_fit_b/yr_{year}_{channel}/{bkg}'
                            )
                            if self.all_bkg[f'nominal_{channel}_{bkg}']:
                                self.all_bkg[f'nominal_{channel}_{bkg}'] = utils.convert_index_hist_to_mjj(
                                    self.all_bkg[f'nominal_{channel}_{bkg}'], BINNING[year]
                                )
                        self.all_bkg[f'tot_unc_{channel}'] = input_root_file.Get(
                            f'shapes_fit_b/yr_{year}_{channel}/total'
                        )
                        self.all_bkg[f'tot_unc_{channel}'] = utils.convert_index_hist_to_mjj(self.all_bkg[f'tot_unc_{channel}'], BINNING[year])

                        # self.all_sgn = input_root_file.Get(
                        #     f'shapes_prefit/yr_{year}_{channel}/ttZprime_M-{mass}_Width4'
                        # )
                        # if not self.all_sgn:
                        #     print(f"Signal histo (shapes_prefit/yr_{year}_{channel}/ttZprime_M-{mass}_Width4) not found!")

                        data_r2 = input_root_file.Get(f'shapes_fit_b/yr_{year}_{channel}/data')
                        hist1 = utils.graph_to_hist(data_r2, f"postfit_{channel}_{year}")
                        self.all_data[channel] = utils.convert_index_hist_to_mjj(hist1, BINNING[year])
                        # self.all_data = None

                        canvas = self._plotting_variable(
                            channel,
                            type="Post-fit",
                            mass=mass,
                            year=year
                        )
                        output_filename = f"{self.output_dir}/{year}/postfit_plots/postfit_M-{mass}_Width{width}_channel_{channel}"
                        canvas.SaveAs(f"{output_filename}.png")
                        canvas.SaveAs(f"{output_filename}.pdf")

                        debug_outfile = ROOT.TFile(f"{self.output_dir}/{year}/postfit_plots/debug_hist_{channel}_M-{mass}_Width{width}_{year}.root", "RECREATE")
                        for bkg in ['prediction', 'multitop_hadronic_top', 'ttX_hadronic_top', 'tt_hadronic_top']:
                            if self.all_bkg[f'nominal_{channel}_{bkg}']:
                                self.all_bkg[f'nominal_{channel}_{bkg}'].SetName(bkg)
                                self.all_bkg[f'nominal_{channel}_{bkg}'].Write()
                        self.all_data[channel].SetName("data_obs")
                        self.all_data[channel].Write()
                        if self.all_sgn.get(channel):
                            self.all_sgn[channel].SetName("signal")
                            self.all_sgn[channel].Write()
                        print(f'Saving distributions for debugging: {self.output_dir}/{year}/postfit_plots/debug_hist_{channel}_M-{mass}_Width{width}_{year}.root')
                        debug_outfile.Close()
                    # ---
                input_root_file.Close()

def main(
        input_dir, output_dir):

    print("Analyzing file: {}".format(input_dir))

    processor = Processor(input_dir, output_dir)
    processor.process()


#################################################

def parse_args(argv=None):
    parser = ArgumentParser()

    parser.add_argument('--input_dir', type=str,
        help="Input file, where to find the h5 files")
    parser.add_argument('--output_dir', type=str,
        help="Top-level output directory. "
             "Will be created if not existing. "
             "If not provided, takes the input dir.")

    args = parser.parse_args(argv)

    # If output directory is not provided, assume we want the output to be
    # alongside the input directory.
    if args.input_dir is None: 
        args.input_dir = os.getcwd()
    if args.output_dir is None:
        args.output_dir = args.input_dir

    # Return the options as a dictionary.
    return vars(args)

if __name__ == "__main__":
    args = parse_args()
    main(**args)
