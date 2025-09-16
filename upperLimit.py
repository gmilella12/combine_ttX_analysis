import ROOT
import os
import subprocess
import argparse
import math

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

ROOT.gROOT.SetBatch(True)

def hex_to_root_color(hex_color):
    h = hex_color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return ROOT.TColor.GetColor(*rgb)

QUANTILE_LABELS = {
    -1.0:   "observed",
     0.025: "exp_m2",
     0.16:  "exp_m1",
     0.50:  "exp_median",
     0.84:  "exp_p1",
     0.975: "exp_p2",
}
def read_limits_by_quantile(f):
    t = f.Get('limit')
    out = {}
    if not t:
        return out
    for entry in t:
        q = round(float(getattr(entry, 'quantileExpected')), 3)
        label = QUANTILE_LABELS.get(q)
        if label:
            out[label] = float(entry.limit)
    return out  

file_dict, limit_dict = dict(),dict()
widths = ['4']#, '10', '20', '50'] #4
masses = ["500", "750", "1000", "1250", "1500", "1750", "2000", "2500", "3000", "4000"]
N=len(masses)

is_tta = False
is_tth = False

FOR_PAS = True

UNBLIND = True

# ttZ'
xsecs = {
    '4': [75.6, 16.4, 4.6, 1.52, 0.54, 0.2, 0.08, 0.016, 0.003, 0.00016],
    '10': [189.0, 41.0, 11.5, 3.8, 1.35, 0.5, 0.2, 0.04, 0.0075, 0.0004],
    '20': [378.0, 82.0, 23.0, 7.6, 2.7, 1.0, 0.4, 0.08, 0.015, 0.0008],
    '50': [945.0, 205.0, 57.5, 19.0, 6.75, 2.5, 1.0, 0.2, 0.0375, 0.002]
}
coupling_factor = {
    '4': 1.,
    '10': math.sqrt(10/4),
    '20': math.sqrt(20/4),
    '50': math.sqrt(50/4)
}

# s-T Z'
# xsecs = [57.8, 14.3, 4.8, 1.61, 0.62, 0.26, 0.114, 0.0238, 0.0053, 0.003]
# tta
if is_tta:
    xsecs = {
        '4': [11.5, 3.1, 0.99, 0.35, 0.13, 5.682e-02, 2.429e-02, 4.943e-03, 1.086e-03, 6.019e-05],
        '10': [28.75, 7.75, 2.475, 0.875, 0.325, 0.14205, 0.060725, 0.0123575, 0.002715, 0.000150475],
        '20': [57.5, 15.5, 4.95, 1.75, 0.65, 0.2841, 0.12145, 0.024715, 0.00543, 0.00030095],
        '50': [143.75, 38.75, 12.375, 4.375, 1.625, 0.71025, 0.303625, 0.0617875, 0.013575, 0.000752375]
    } 
# tth
if is_tth:
    xsecs = {
        '4': [8.0, 2.4, 0.86, 0.32, 0.12, 5.391e-02, 2.332e-02, 4.818e-03, 1.068e-03, 5.967e-05],
        '10': [20.0, 6.0, 2.15, 0.8, 0.3, 0.134775, 0.0583, 0.012045, 0.00267, 0.000149175],
        '20': [40.0, 12.0, 4.3, 1.6, 0.6, 0.26955, 0.1166, 0.02409, 0.00534, 0.00029835],
        '50': [100.0, 30.0, 10.75, 4.0, 1.5, 0.673875, 0.2915, 0.060225, 0.01335, 0.000745875]
    }

atlas_limit = [50, 44.7, 30, 22, 19, 32]
# atlas_limit = [10.8, 29.4, 55, 275, 1187, 10000]

atlas_mass = ["1000", "1250", "1500", "2000", "2500", "3000"]
single_lepton = [2.1, 3.1, 5, 8.5, 17.6, 32.5, 67.5, 181.2, 933]

YEAR = 'Run2_Run3'

SIGNAL_STRENGTH_ONLY = False
COUPLING = False

atlas_graph = ROOT.TGraph()
for i, m in enumerate(atlas_mass):
    if float(m) <= 3000:
        atlas_graph.SetPoint(atlas_graph.GetN(), float(m), atlas_limit[i])

singlelep = ROOT.TGraph()
for i, m in enumerate(masses):
    if float(m) <= 3000:
        singlelep.SetPoint(singlelep.GetN(), float(m), single_lepton[i] * xsecs['4'][i])

for width in widths:
    print('\nWidth: ', width)
    limit_dict.clear()
    for mass in masses:
        
        sgn = f"TTZprimeToTT_M{mass}_Width{width}"
        if is_tta:
            sgn = f"tta_M{mass}_Width{width}"
        if is_tth:
            sgn = f"tth_M{mass}_Width{width}"

        # --- Asimov
        # fexp_path = f'{args.input_dir}/{YEAR}/higgsCombineAsymptoticLimit_expectedLimits_{sgn}_{YEAR}.AsymptoticLimits.mH800.root' # for Asimov
        # fexp = ROOT.TFile(fexp_path) 
        # lim_exp = read_limits_by_quantile(fexp)
        # fexp.Close()
        # if 0.5 not in lim_exp:
        #     print(f'uncorrect limit tree for mass {mass}, width {width}')
        #     continue
        # lim_exp = {round(k, 3): v for k, v in lim_exp.items()}
        # limit_dict[mass] = [
        #     lim_exp.get(0.025), lim_exp.get(0.16), lim_exp.get(0.5),
        #     lim_exp.get(0.84), lim_exp.get(0.975)
        # ]
        # ---

        fobs_path = f'{args.input_dir}/{YEAR}/higgsCombineAsymptoticLimit_{sgn}_{YEAR}.AsymptoticLimits.mH800.root'
        if not os.path.exists(fobs_path):
            print(f'missing file(s) for mass {mass}, width {width}')
            continue
        fobs = ROOT.TFile(fobs_path)
        
        lim_obs = read_limits_by_quantile(fobs)
        fobs.Close()

        if 'observed' not in lim_obs:
            print(f'uncorrect limit tree for mass {mass}, width {width}')
            continue

        # print(lim_obs)
        limit_dict[mass] = [
            lim_obs.get('exp_m2'), lim_obs.get('exp_m1'), lim_obs.get('exp_median'),
            lim_obs.get('exp_p1'), lim_obs.get('exp_p2'), lim_obs.get('observed')
        ]

    yellow = ROOT.TGraph(2*len(masses))
    green = ROOT.TGraph(2*len(masses))
    median = ROOT.TGraph(len(masses))
    blue = ROOT.TGraph(len(masses))
    obs = ROOT.TGraph(len(masses))

    up2s = [ ]
    for i, mass in enumerate(masses):
        print(
            f"Mass: {float(mass)}, r-value (exp): {limit_dict[mass][2]:.2f}, "
            f"+1sigma: {limit_dict[mass][3]:.2f}, -1sigma: {limit_dict[mass][1]:.2f}, "
            f"r-value (obs.): {limit_dict[mass][-1]:.2f}"
        )
        up2s.append(limit_dict[mass][4])
        if SIGNAL_STRENGTH_ONLY:
            yellow.SetPoint(i, float(mass), limit_dict[mass][4] ) # + 2 sigma
            green.SetPoint(i, float(mass), limit_dict[mass][3] ) # + 1 sigma
            median.SetPoint(i, float(mass), limit_dict[mass][2] ) # median
            green.SetPoint(2*N-1-i, float(mass), limit_dict[mass][1] ) # - 1 sigma
            yellow.SetPoint(2*N-1-i, float(mass), limit_dict[mass][0] ) # - 2 sigma    
        if COUPLING:
            yellow.SetPoint(i, float(mass), limit_dict[mass][4]**2 ) # + 2 sigma
            green.SetPoint(i, float(mass), limit_dict[mass][3]**2 ) # + 1 sigma
            median.SetPoint(i, float(mass), limit_dict[mass][2]**2 ) # median
            green.SetPoint(2*N-1-i, float(mass), limit_dict[mass][1]**2 ) # - 1 sigma
            yellow.SetPoint(2*N-1-i, float(mass), limit_dict[mass][0]**2 ) # - 2 sigma  
            blue.SetPoint(i, float(mass), coupling_factor[width])
        else:
            yellow.SetPoint(i, float(mass), limit_dict[mass][4] * xsecs['4'][i]) # + 2 sigma
            green.SetPoint(i, float(mass), limit_dict[mass][3] * xsecs['4'][i]) # + 1 sigma
            median.SetPoint(i, float(mass), limit_dict[mass][2] * xsecs['4'][i]) # median
            green.SetPoint(2*N-1-i, float(mass), limit_dict[mass][1] * xsecs['4'][i]) # - 1 sigma
            yellow.SetPoint(2*N-1-i, float(mass), limit_dict[mass][0] * xsecs['4'][i]) # - 2 sigma    
            blue.SetPoint(i, float(mass), xsecs[width][i] )

            obs.SetPoint(i, float(mass), limit_dict[mass][-1] * xsecs['4'][i]) # median

    print(median)
    # import sys
    # sys.exit()

    W = 800
    H  = 800
    T = 0.08*H
    B = 0.12*H
    L = 0.14*W
    R = 0.055*W

    c = ROOT.TCanvas("c"+width,"c",100,100,W,H)
    c.SetLogy()
    c.SetFillColor(0)
    c.SetBorderMode(0)
    c.SetFrameFillStyle(0)
    c.SetFrameBorderMode(0)
    c.SetLeftMargin( L/W )
    c.SetRightMargin( R/W )
    c.SetTopMargin( T/H )
    c.SetBottomMargin( B/H )
    c.SetTickx(0)
    c.SetTicky(0)
    c.SetGrid()
    c.cd()
    frame = c.DrawFrame(1000,0.001, 4000, 10)
    # frame = c.DrawFrame(1000, 0.1, 100000, 10)
    frame.GetYaxis().CenterTitle()
    frame.GetYaxis().SetTitleSize(0.05)
    frame.GetXaxis().SetTitleSize(0.05)
    frame.GetXaxis().SetLabelSize(0.04)
    frame.GetYaxis().SetLabelSize(0.04)
    frame.GetYaxis().SetTitleOffset(1.35)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetYaxis().CenterTitle(True)
    # frame.GetYaxis().SetTitle("#sigma(pp#rightarrowZ't#bar{t}) X BR(Z'#rightarrowt#bar{t})  [fb]")
    if SIGNAL_STRENGTH_ONLY:
        frame.GetYaxis().SetTitle("#it{r} (pp #rightarrow t#bar{t}Z')")
    if COUPLING:
        frame.GetYaxis().SetTitle("#it{c_{t}} (pp #rightarrow t#bar{t}Z')")
        if is_tta:
            frame.GetYaxis().SetTitle("#it{c_{t}} (pp #rightarrow t#bar{t}a)")
        if is_tth:
            frame.GetYaxis().SetTitle("#it{c_{t}} (pp #rightarrow t#bar{t}#phi)")
    else:
        frame.GetYaxis().SetTitle("#sigma_{@13.6 TeV}(pp #rightarrow t#bar{t}Z') #times BR(Z' #rightarrow t#bar{t}) [fb]")
        if is_tta:
            frame.GetYaxis().SetTitle("#sigma_{@13 TeV}(pp #rightarrow t#bar{t}a) #times BR(a #rightarrow t#bar{t}) [fb]")
        if is_tth:
            frame.GetYaxis().SetTitle("#sigma_{@13 TeV}(pp #rightarrow t#bar{t}#phi) #times BR(#phi #rightarrow t#bar{t}) [fb]")
    
    frame.GetXaxis().SetTitle("#it{m}_{Z'} [GeV]")
    if is_tta:
        frame.GetXaxis().SetTitle("#it{m}_{a} [GeV]")
    if is_tth:
        frame.GetXaxis().SetTitle("#it{m}_{#phi} [GeV]")

    frame.SetMinimum(0.001)
    if COUPLING:
        frame.SetMinimum(0.5)
    frame.SetMaximum(1000)
    if SIGNAL_STRENGTH_ONLY or COUPLING:
        frame.SetMaximum(100000)
    frame.GetXaxis().SetLimits(500, 4000)
            
    yellow.SetFillColor(hex_to_root_color('#F5BB54'))
    yellow.SetLineColor(hex_to_root_color('#F5BB54'))
    yellow.SetFillStyle(1001)
    yellow.Draw('Fsame')

    green.SetFillColor(hex_to_root_color('#607641'))
    green.SetLineColor(hex_to_root_color('#607641'))
    green.SetFillStyle(1001)
    green.Draw('Fsame')

    median.SetLineColor(1)
    median.SetLineWidth(3)
    median.SetLineStyle(2)
    median.SetMarkerStyle(20)
    median.SetMarkerColor(1)
    median.Draw('Lsame')

    blue.SetLineColor(ROOT.kBlue)
    blue.SetLineWidth(2)
    if not SIGNAL_STRENGTH_ONLY:
        blue.Draw('Lsame')

    atlas_graph.SetLineColor(ROOT.kRed)
    atlas_graph.SetLineWidth(3)
    atlas_graph.SetLineStyle(2)
    atlas_graph.SetMarkerStyle(20)
    atlas_graph.SetMarkerColor(ROOT.kRed)
    # if width == '4':
    #     atlas_graph.Draw('Lsame')

    singlelep.SetLineColor(ROOT.kBlue)
    singlelep.SetLineWidth(3)
    singlelep.SetLineStyle(2)
    singlelep.SetMarkerStyle(20)
    singlelep.SetMarkerColor(ROOT.kBlue)
    # if width == '4':
    #     singlelep.Draw('Lsame')

    obs.SetLineColor(ROOT.kBlack)
    obs.SetLineWidth(3)
    obs.SetMarkerStyle(20)
    obs.SetMarkerColor(ROOT.kBlack)
    obs.Draw('LPsame')

    text = ROOT.TLatex()
    text.SetNDC()
    text.SetTextFont(61)
    text.SetTextSize(0.045)
    text.DrawLatex(0.14, 0.93, "CMS")
    text.SetTextFont(52)
    text.SetTextSize(0.038)
    if FOR_PAS:
        text.DrawLatex(0.14 + 0.1, 0.93, "Preliminary")

    text.SetTextSize(0.036)
    text.SetTextFont(42)
    if YEAR == 'Run2_Run3':
        text.DrawLatex(0.6, 0.93, "173 fb^{-1} (13 + 13.6 TeV)")
    if YEAR == 'all_years_Run2':
        text.DrawLatex(0.7, 0.93, "137.6 fb^{-1} (13 TeV)")
    if YEAR == 'all_years_Run3':
        text.DrawLatex(0.6, 0.93, "34.8.6 fb^{-1} (13.6 TeV)")

    text.SetTextSize(0.038)

    x1 = 0.15
    x2 = x1 + 0.24
    y2 = 0.42
    y1 = 0.15
    legend = ROOT.TLegend(x1,y1,x2,y2)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(0.041)
    legend.SetTextFont(42)

    
    # legend.AddEntry(0, "#bf{SR1b2T - #mu#mu}", "h")
    if not SIGNAL_STRENGTH_ONLY:
        if is_tta:
            legend.AddEntry(blue, "Theory #Gamma/m_{a} = "+width+"%",'L')
        elif is_tth:
            legend.AddEntry(blue, "Theory #Gamma/m_{#phi} = "+width+"%",'L')
        else:
            legend.AddEntry(blue, "Theory #Gamma/m_{Z'} = "+width+"%",'L')
    legend.AddEntry(0, "95% CL upper limits", "h")
    # legend.AddEntry(singlelep, "CMS expected ttZ' (1L)",'L')
    # legend.AddEntry(atlas_graph, "ATLAS expected",'L')
    legend.AddEntry(median, "Median expected",'L')
    legend.AddEntry(green, "68% expected",'f')
    legend.AddEntry(yellow, "95% expected",'f')
    legend.AddEntry(obs, "Observed",'L')

    legend.Draw()

    ROOT.gPad.RedrawAxis()
    output_name = f"{args.output_dir}/{YEAR}/expected_limit_AsymptoticLimits_width{width}_{YEAR}"
    # if FOR_PAS:
    #     output_name += "_forPAS"
    
    if SIGNAL_STRENGTH_ONLY:
        output_name += "_signal_strength"
    if COUPLING:
        output_name += "_coupling"
    else:
        output_name += "_cross_section"
    
    c.SaveAs(f"{output_name}.pdf")
    c.SaveAs(f"{output_name}.png")

    c.Close()



