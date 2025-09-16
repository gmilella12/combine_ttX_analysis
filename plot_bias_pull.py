import os
import ROOT
import numpy as np
import argparse

ROOT.gROOT.SetBatch(True)

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

N_toys = 1000
r_type = 'r0'

r_truth = {
    500: 0,
    1750: 0
}
r_ranges = {
    'min': 
    {
        500: -20,
        1750: -2000
    },
    'max':
    {
        500: 20,
        1750: 2000
    }
}
if r_type == 'rExp':
    r_truth = {
        500: 2.5,
        1750: 77
    }

def plotting(input_dir, output_dir, mass, width):
    f = ROOT.TFile(f"{input_dir}/higgsCombine_M{mass}_Width{width}_{r_type}.MultiDimFit.mH120.123456.root")
    t = f.Get("limit")

    # hist_pull = ROOT.TH1F("pull_%s" % name, "Pull distribution: truth=%s, fit=%s" % (truth_function, fit_function), 80, -4, 4)
    hist_pull = ROOT.TH1F(f"pull_{mass}_{width}", "", 80, -5, 5)
    hist_pull.SetName(f"r_{{Inj.}} = 0, M_{{Z'}} = {mass} GeV")
    if r_type == 'rExp':
        if mass == 1750:
            hist_pull.SetName(f"r_{{Inj.}} = {r_truth[mass]}, M_{{Z'}} = {mass} GeV")
        if mass == 500:
            hist_pull.SetName(f"r_{{Inj.}} = {r_truth[mass]}, M_{{Z'}} = {mass} GeV")

    hist_pull.GetXaxis().SetTitle("Pull = (r_{inj}-r_{fit})/#sigma_{fit}")
    hist_pull.GetYaxis().SetTitle("No. of Toys")
    hist_pull.GetXaxis().SetTitleSize(0.045)
    hist_pull.GetYaxis().SetTitleSize(0.045)

    sigma_values = np.array([])

    for i_toy in range(N_toys):
        # Best-fit value
        t.GetEntry(i_toy * 3)
        r_fit = getattr(t, "r")

        # -1 sigma value
        t.GetEntry(i_toy * 3 + 1)
        r_lo = getattr(t, "r")

        # +1 sigma value
        t.GetEntry(i_toy * 3 + 2)
        r_hi = getattr(t, "r")

        diff = r_truth[mass] - r_fit
        # Use uncertainty depending on where mu_truth is relative to mu_fit
        if diff > 0:
            sigma = abs(r_hi - r_fit)
        else:
            sigma = abs(r_lo - r_fit)

        if abs(r_hi-r_ranges['max'][mass])>1e-3: #Minos didn't return the rMax properly
            if abs(r_lo-r_ranges['min'][mass])>1e-3:
                if abs(sigma)>1e-3: #Errors returned by Minos too small, indicating again fit issues. If your r range is wider, you might need to level up this cut
                    hist_pull.Fill(diff / sigma)
                else:
                    print("r_fit: %f, sigma: %f is too small" % (r_fit, sigma))
            else:
                print("r: %f, r_lo: %f touches rMin" % (r_fit, r_lo))
        else:
            print("r: %f, r_hi: %f touches rMax" % (r_fit, r_hi))

        if sigma != 0:
            sigma_values = np.append(sigma_values, sigma)
        else:
            sigma = sigma_values.mean()

        if sigma != 0:
            hist_pull.Fill(diff / sigma)

    canv = ROOT.TCanvas()
    hist_pull.Draw()

    # Fit Gaussian to pull distribution
    ROOT.gStyle.SetOptFit(111)
    hist_pull.Fit("gaus")

    stats = hist_pull.GetListOfFunctions().FindObject("stats")
    if stats:
        stats.SetTextSize(0.035)
        stats.SetX1NDC(0.6)
        stats.SetX2NDC(0.9)
        stats.SetY1NDC(0.6)
        stats.SetY2NDC(0.9)

    pTextCMS = ROOT.TPaveText(0.15, 0.96, 0.15, 0.96, "NDC")
    pTextCMS.AddText("CMS Preliminary")
    pTextCMS.SetTextFont(63)
    pTextCMS.SetTextSize(28)
    pTextCMS.SetTextAlign(13)
    pTextCMS.Draw("Same")

    pText = ROOT.TPaveText(0.54, 0.96, 0.54, 0.96, "NDC")
    pText.AddText("173 fb#lower[-0.8]{#scale[0.7]{-1}} (13 + 13.6 TeV)")
    # if str(year) == '2022' or str(year) == '2022EE':
    #     pText.AddText(str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13.6 TeV)")
    # else:
    #     pText.AddText( str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13 TeV)") #str(lumi) +
    #     # pText.AddText( " (13 TeV)") #str(lumi) +
    pText.SetTextFont(63)
    pText.SetTextSize(28)
    pText.SetTextAlign(13)
    pText.Draw("Same")

    canv.SaveAs(f"{output_dir}/part4_pull_M{mass}_Width{width}_{r_type}.png")
    canv.SaveAs(f"{output_dir}/part4_pull_M{mass}_Width{width}_{r_type}.pdf")
    # canv.SaveAs("%s/part4_pull_%s.png" % (plot_dir, name))

if __name__ == "__main__":
    input_dir = args.input_dir
    output_dir = args.output_dir 
    masses = [500]#, 1750]#, 2500]#500, 1000, 
    widths = [4]#, 10, 20, 50]

    for mass in masses:
        for width in widths:
            try:
                plotting(input_dir, output_dir, mass=mass, width=width)
            except RuntimeError as e:
                print(f"An error occurred for mass {mass}: {e}")