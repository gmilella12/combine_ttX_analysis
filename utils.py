import ROOT, sys, re
import ctypes
import numpy
from array import array
import numpy as np
import math

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptFit(0)
ROOT.gStyle.SetOptDate(0)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFile(0)
ROOT.gStyle.SetOptTitle(0)

ROOT.gStyle.SetPadTopMargin(0.1)
ROOT.gStyle.SetPadBottomMargin(0.12)
ROOT.gStyle.SetPadLeftMargin(0.13)
ROOT.gStyle.SetPadRightMargin(0.05)
ROOT.gStyle.SetHistMinimumZero(True)

ROOT.gStyle.SetCanvasBorderMode(0)
ROOT.gStyle.SetCanvasColor(ROOT.kWhite)

ROOT.gStyle.SetPadBorderMode(0)
ROOT.gStyle.SetPadColor(ROOT.kWhite)
ROOT.gStyle.SetGridColor(ROOT.kBlack)
ROOT.gStyle.SetGridStyle(2)
ROOT.gStyle.SetGridWidth(1)

ROOT.gStyle.SetEndErrorSize(2)
#ROOT.gStyle.SetErrorX(0.)
ROOT.gStyle.SetMarkerStyle(20)

ROOT.gStyle.SetHatchesSpacing(0.9)
ROOT.gStyle.SetHatchesLineWidth(2)

ROOT.gStyle.SetTitleColor(1, "XYZ")
ROOT.gStyle.SetTitleFont(43, "XYZ")
ROOT.gStyle.SetTitleSize(32, "XYZ")
ROOT.gStyle.SetTitleXOffset(1.135)
ROOT.gStyle.SetTitleOffset(1.32, "YZ")

ROOT.gStyle.SetLabelColor(1, "XYZ")
ROOT.gStyle.SetLabelFont(43, "XYZ")
ROOT.gStyle.SetLabelSize(29, "XYZ")

ROOT.gStyle.SetAxisColor(1, "XYZ")
ROOT.gStyle.SetAxisColor(1, "XYZ")
ROOT.gStyle.SetStripDecimals(True)
# ROOT.gStyle.SetNdivisions(1005, "X")
ROOT.gStyle.SetNdivisions(506, "Y")

ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)

ROOT.gStyle.SetPaperSize(8.0*1.35,6.7*1.35)
ROOT.TGaxis.SetMaxDigits(3)
ROOT.gStyle.SetLineScalePS(2)

# ROOT.gStyle.SetPalette(57)
# ROOT.gStyle.SetPalette(ROOT.kRainBow)
ROOT.gStyle.SetPaintTextFormat(".2f")

COLORS = []

def newColorRGB(red, green, blue):
    newColorRGB.colorindex += 1
    color = ROOT.TColor(newColorRGB.colorindex, red, green, blue)
    COLORS.append(color)
    return color

def HLS2RGB(hue, light, sat):
    r, g, b = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    ROOT.TColor.HLS2RGB(
        int(round(hue*255.)),
        int(round(light*255.)),
        int(round(sat*255.)),
        r,g,b
    )
    return r.value/255., g.value/255., b.value/255.
    
def newColorHLS(hue,light,sat):
    r,g,b = HLS2RGB(hue,light,sat)
    return newColorRGB(r,g,b)

def createYearVariations(h, l, s):
    # Variation factors for different years
    return {
        '2016': newColorHLS(max(h - 0.15, 0), max(l - 0.2, 0), min(s + 0.2, 1)),  # Darker and less saturated for 2016
        '2017': newColorHLS(min(h + 0.15, 1), min(l + 0.2, 1), max(s - 0.2, 0))   # Lighter and more saturated for 2017
    }

def RGB2HLS(r, g, b):
    h = ctypes.c_float()
    l = ctypes.c_float()
    s = ctypes.c_float()

    ROOT.TColor.RGB2HLS(r, g, b, ctypes.byref(h), ctypes.byref(l), ctypes.byref(s))

    return h.value, l.value, s.value

newColorRGB.colorindex = 301


def makeColorTable(reverse=False):
    colorList = [
        [0.,newColorHLS(0.6, 0.47,0.6)],
        [0.,newColorHLS(0.56, 0.65, 0.7)],
        [0.,newColorHLS(0.52, 1., 1.)],
    ]

    colorList = [
    [0.,newColorHLS(0.9, 0.5, 0.9)],
    [0.,newColorHLS(0.9, 0.88, 1.0)],
    [0.,newColorHLS(0.9, 0.95, 1.0)],
    ]
    
    if reverse:
        colorList = reversed(colorList)

    lumiMin = min(map(lambda x:x[1].GetLight(),colorList))
    lumiMax = max(map(lambda x:x[1].GetLight(),colorList))

    for color in colorList:
        if reverse:
            color[0] = ((lumiMax-color[1].GetLight())/(lumiMax-lumiMin))
        else:
            color[0] = ((color[1].GetLight()-lumiMin)/(lumiMax-lumiMin))

    stops = numpy.array(list(map(lambda x:x[0],colorList)))
    red   = numpy.array(list(map(lambda x:x[1].GetRed(),colorList)))
    green = numpy.array(list(map(lambda x:x[1].GetGreen(),colorList)))
    blue  = numpy.array(list(map(lambda x:x[1].GetBlue(),colorList)))

    start = ROOT.TColor.CreateGradientColorTable(stops.size, stops, red, green, blue, 200)
    ROOT.gStyle.SetNumberContours(200)
    return

rootObj = []

def makeCanvas(name="cv", width=800, height=670):
    ROOT.gStyle.SetPaperSize(width*0.0135, height*0.0135)
    cv = ROOT.TCanvas(name, "", width, height)
    rootObj.append(cv)
    return cv

def makePad(x1, y1, x2, y2, name="pad"):
    pad = ROOT.TPad(name, name, x1, y1, x2, y2)
    return pad

def makePaveText(x1, y1, x2, y2, name="cv"):
    pave = ROOT.TPaveText(x1, y1, x2, y2, "NDC") # NDC sets coordinates relative to the canvas
    # pave.SetBorderSize(1)
    pave.SetFillColor(0) # Transparent fill
    pave.SetTextFont(43)
    pave.SetTextSize(29)
    pave.SetBorderSize(0)
    # pave.SetLabel(name)
    # pave.AddText("Histogram 1")
    # pave.AddText("Histogram 2")
    return pave

def makeLegend(x1, y1, x2, y2):
    legend = ROOT.TLegend(x1, y1, x2, y2)
    legend.SetBorderSize(0)
    legend.SetTextFont(43)
    legend.SetTextSize(29)
    legend.SetFillStyle(0)
    rootObj.append(legend)
    return legend

def makeCMSText(x1, y1, additionalText=None, dx=0.088, size=30):
    pTextCMS = ROOT.TPaveText(x1, y1, x1, y1, "NDC")
    pTextCMS.AddText("CMS")
    pTextCMS.SetTextFont(63)
    pTextCMS.SetTextSize(size)
    pTextCMS.SetTextAlign(13)
    pTextCMS.SetBorderSize(0)
    rootObj.append(pTextCMS)
    pTextCMS.Draw("Same")

    if additionalText:
        pTextAdd = ROOT.TPaveText(x1+dx, y1, x1+dx, y1, "NDC")
        pTextAdd.AddText(additionalText)
        pTextAdd.SetTextFont(53)
        pTextAdd.SetTextSize(size)
        pTextAdd.SetTextAlign(13)
        pTextAdd.SetBorderSize(0)
        rootObj.append(pTextAdd)
        pTextAdd.Draw("Same")
    return

def adjustFrame(frame, x_label='none', y_label='none'):
    frame.GetYaxis().SetTitle(y_label)
    # frame.GetXaxis().SetTitle('subleading jet AK8 pNet_{TvsQCD}')
    # frame.GetXaxis().SetTitle('minimum AK8 BDT score')
    frame.GetXaxis().SetTitle(x_label)
    # frame.GetYaxis().SetRangeUser(0., 1.1)
    return frame

def makeLumiText(x1, y1, lumi, year, size=30):
    pText = ROOT.TPaveText(x1, y1, x1, y1, "NDC")
    if year == 'all_years_Run2':
        pText.AddText(str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13 TeV)")
    elif year == 'all_years_Run3':
        pText.AddText(str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13.6 TeV)")
    else:
        pText.AddText(str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13 + 13.6 TeV)")
    # if str(year) == '2022' or str(year) == '2022EE':
    #     pText.AddText(str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13.6 TeV)")
    # else:
    #     pText.AddText( str(lumi) + " fb#lower[-0.8]{#scale[0.7]{-1}} (13 TeV)") #str(lumi) +
    #     # pText.AddText( " (13 TeV)") #str(lumi) +
    pText.SetTextFont(63)
    pText.SetTextSize(size)
    pText.SetTextAlign(13)
    pText.SetBorderSize(0)
    rootObj.append(pText)
    pText.Draw("Same")
    return
 
def makeText(x1,y1,x2, y2, text,size=30, font=43):
    pText = ROOT.TPaveText(x1, y1, x2, y2, "NBNDC")
    pText.AddText(text)
    pText.SetTextFont(font)
    pText.SetTextSize(size)
    pText.SetTextAlign(13)
    pText.SetFillColorAlpha(ROOT.kWhite, 0.01)
    rootObj.append(pText)
    pText.Draw()
    return

def makeLine(x1, y1, x2, y2, size=30):
    line = ROOT.TLine(x1, y1, x2, y2)
    line.SetLineColor(ROOT.kRed)
    line.SetLineWidth(2)
    line.Draw('same')
    return

ptSymbol = "p#kern[-0.8]{ }#lower[0.3]{#scale[0.7]{T}}"
metSymbol = ptSymbol+"#kern[-2.3]{ }#lower[-0.8]{#scale[0.7]{miss}}"
metSymbol_lc = ptSymbol+"#kern[-2.3]{ }#lower[-0.8]{#scale[0.7]{miss,#kern[-0.5]{ }#mu-corr.}}}"
minDPhiSymbol = "#Delta#phi#lower[-0.05]{*}#kern[-1.9]{ }#lower[0.3]{#scale[0.7]{min}}"
htSymbol = "H#kern[-0.7]{ }#lower[0.3]{#scale[0.7]{T}}"
mhtSymbol = "H#kern[-0.7]{ }#lower[0.3]{#scale[0.7]{T}}#kern[-2.2]{ }#lower[-0.8]{#scale[0.7]{miss}}"
rSymbol = mhtSymbol+"#lower[0.05]{#scale[1.2]{/}}"+metSymbol
rSymbol_lc = mhtSymbol+"#lower[0.05]{#scale[1.2]{/}}"+metSymbol_lc
mzSymbol = "m#lower[0.3]{#scale[0.7]{#mu#mu}}"
gSymbol = "#tilde{g}"
qbarSymbol = "q#lower[-0.8]{#kern[-0.89]{#minus}}"
mgSymbol = "m#lower[0.2]{#scale[0.8]{#kern[-0.75]{ }"+gSymbol+"}}"
chiSymbol = "#tilde{#chi}#lower[-0.5]{#scale[0.65]{0}}#kern[-1.2]{#lower[0.6]{#scale[0.65]{1}}}"
mchiSymbol = "m#lower[0.2]{#scale[0.8]{"+chiSymbol+"}}"

def clamp(val, minimum=0, maximum=255):
    if val < minimum: return minimum
    if val > maximum:
        return maximum
    return int(val)

def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)
    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return "#%02x%02x%02x" % (r, g, b)


def auto_rebin(hist):
    """
    Automatically rebin a TH1 histogram to avoid empty bins while preserving the range.
    Start the rebinning process only if there is at least one empty bin.

    Args:
        hist (TH1): Input histogram to be rebinned.

    Returns:
        TH1: Rebinned histogram with the same range as the input.
    """
    # Check if there is at least one empty bin
    nbins = hist.GetNbinsX()
    has_empty_bins = any(hist.GetBinContent(bin_idx) == 0 for bin_idx in range(1, nbins + 1))
    if not has_empty_bins:
        print("No empty bins found in the BACKGROUND histogram!")
        return hist, array('d')  # Return the original histogram if no empty bins are found
    print("Rebinning procedure to avoid empty histograms!")

    bin_edges = [hist.GetBinLowEdge(1)]  # Start with the first bin edge (preserve the lower edge)
    previous_non_empty_bin = None  # Keep track of the previous non-empty bin

    for bin_idx in range(1, nbins + 1):  # Loop over bins from start to end
        bin_content = hist.GetBinContent(bin_idx)

        if bin_content > 0:  # Non-empty bin
            bin_edges.append(hist.GetBinLowEdge(bin_idx + 1))  # Add the upper edge of this bin
            previous_non_empty_bin = bin_idx
        else:
            if previous_non_empty_bin is None:
                continue  # If no previous non-empty bin, merge with the next one

    # Merge first two bins by removing the second bin edge
    # if len(bin_edges) > 2:
    #     print(f"Merging first two bins: [{bin_edges[0]}, {bin_edges[1]}] + [{bin_edges[1]}, {bin_edges[2]}]")
    #     del bin_edges[1]

    if bin_edges[-1] != hist.GetXaxis().GetXmax():
        bin_edges[-1] = hist.GetXaxis().GetXmax()  # Add the uppermost edge if missing

    bin_edges_array = array('d', bin_edges)
    rebinned_hist = hist.Rebin(
        len(bin_edges_array) - 1, 
        # f"{hist.GetName()}_rebinned", 
        hist.GetName(),
        bin_edges_array
    )

    # --- check if uncertainties are greater than 100% of the nominal
    for ibin in range(1, rebinned_hist.GetNbinsX()+1):
        content = rebinned_hist.GetBinContent(ibin)
        error = rebinned_hist.GetBinError(ibin)

        if error > content:
            print('WARNING: bin uncertainties larger than nominal value -> the uncertainty will be set to the nominal value!')
            rebinned_hist.SetBinError(ibin, content)
    # ---

    return rebinned_hist, bin_edges_array


def bin_exclusion(hist):
    """
    Excluding first bin from the templates for GoF study in Run 3 (ee channel)

    Args:
        hist (TH1): Input histogram to be rebinned.

    Returns:
        TH1: New histogram with the exclusion and bin edges.
    """

    # Create new histogram with Nbins - 1
    nbins_orig = hist.GetNbinsX()
    full_edges = [hist.GetBinLowEdge(bin) for bin in range(1, nbins_orig + 2)]
    new_edges = array('d', full_edges[1:]) 

    h_new = ROOT.TH1F(hist.GetName(), hist.GetTitle(), len(new_edges) - 1, new_edges)

    # Fill the new histogram from bin 2 onward
    for bin in range(2, nbins_orig + 1):  # 1-based indexing in ROOT
        content = hist.GetBinContent(bin)
        error = hist.GetBinError(bin)
        h_new.SetBinContent(bin - 1, content)
        h_new.SetBinError(bin - 1, error)

    return h_new #, bin_edges_array

LUMINOSITY = {
    '2018': '59', '2017': '41.4',
    '2016preVFP': '19.5', '2016': '16.5',
    '2022': '7.8', '2022EE': '26.7',
    'all_years_Run2': '138',
    'all_years_Run3': '34.7', 
    'Run2_Run3': '173'
}
def additional_text(channel, year, miscellanea='', x1=0.16, x2=0.35, y1=0.85, y2=0.87):
    makeCMSText(0.13, 0.965, additionalText="Preliminary")
    if year == 'all_years_Run2':
        makeLumiText(0.68, 0.965, lumi=LUMINOSITY[str(year)], year=year)
    else:
        makeLumiText(0.64, 0.965, lumi=LUMINOSITY[str(year)], year=year)

    lepton_text = {}
    lepton_text['mumu'] = "#mu^{#pm}#mu^{#mp}"
    lepton_text['ee'] = "e^{#pm}e^{#mp}"
    lepton_text['ll'] = "l^{#pm}l^{#mp}"
    lepton_text['emu'] ="e^{#pm}#mu^{#mp}"

    # makeText(x1, 0.85, x2, 0.87, "CR2J2T", size=25)
    
    # if '2b' in channel:
    #     makeText(x1, 0.77, x2, 0.81, f"#geq2b, #geq2J, #geq2T", size=25)
    # elif '1b' in channel: 
    #     makeText(x1, 0.77, x2, 0.81, f"1b, #geq2J, #geq2T", size=25)
    # else:
    #     makeText(x1, 0.77, x2, 0.81, f"#geq2J, #geq2T", size=25)

    if '1b' in channel:
        makeText(x1, 0.85, x2, 0.87, "SR1b2T", size=25)
    if '2b' in channel:   
        makeText(x1, 0.85, x2, 0.87, "SR2b2T", size=25)
    if 'emu' in channel:
        makeText(x1, 0.77, x2, 0.81, lepton_text["emu"], size=25)
    if 'ee' in channel:
        makeText(x1, 0.77, x2, 0.81, lepton_text["ee"], size=25)
    if 'mumu' in channel:
        makeText(x1, 0.77, x2, 0.81, lepton_text["mumu"], size=25)

    if 'all_leptons' in channel:
        makeText(x1, 0.77, x2, 0.81, "All lepton channels", size=25)

    return

def rebin_with_edges(hist_raw, miscellanea=None):
    """
    Rebins a histogram with numeric bin indices into one with custom bin edges.
    """
    fine_bins = np.arange(0., 5020., 20)
    fine_bins_array = array('d', fine_bins)
    h_fine = ROOT.TH1F(f"h_fine_{miscellanea}", "", len(fine_bins)-1, fine_bins_array)

    for i in range(1, hist_raw.GetNbinsX() + 1):
        bin_center = hist_raw.GetBinCenter(i)
        content = hist_raw.GetBinContent(i)
        error = hist_raw.GetBinError(i)

        fine_bin = h_fine.FindBin(bin_center)
        h_fine.AddBinContent(fine_bin, content)
        h_fine.SetBinError(fine_bin, (h_fine.GetBinError(fine_bin)**2 + error**2)**0.5)

    new_bin_edges = [0., 300, 600, 800, 1000, 1240, 1500, 2000, 5100]
    new_bin_edges_array = array('d', new_bin_edges)
    h_variable = ROOT.TH1F(f"{hist_raw.GetName()}_rebinned_{miscellanea}", "", len(new_bin_edges) - 1, new_bin_edges_array)

    # Fill h_variable from h_fine
    for i in range(1, h_fine.GetNbinsX() + 1):
        bin_center = h_fine.GetBinCenter(i)
        content = h_fine.GetBinContent(i)
        error = h_fine.GetBinError(i)

        if content == 0 and error == 0:
            continue

        var_bin = h_variable.FindBin(bin_center)
        if var_bin <= 0 or var_bin > h_variable.GetNbinsX():
            continue  # skip underflow/overflow

        h_variable.AddBinContent(var_bin, content)
        h_variable.SetBinError(var_bin, (h_variable.GetBinError(var_bin)**2 + error**2)**0.5)

    return h_variable

def graph_to_hist(graph, name="hist_from_graph"):
    """
    Converts a TGraphAsymmErrors to a TH1F.
    Assumes the graph points represent bin centers and bin widths.
    """
    nbins = graph.GetN()
    bin_edges = []

    for i in range(nbins):
        x = graph.GetX()[i]
        ex_low = graph.GetErrorXlow(i)
        ex_high = graph.GetErrorXhigh(i)
        bin_edges.append(x - ex_low)
    x_last = graph.GetX()[nbins - 1]
    bin_edges.append(x_last + graph.GetErrorXhigh(nbins - 1))

    import array
    bin_edges_array = array.array('d', bin_edges)
    hist = ROOT.TH1F(name, graph.GetTitle(), nbins, bin_edges_array)

    for i in range(nbins):
        y = graph.GetY()[i]
        hist.SetBinContent(i + 1, y)
        err = 0.5 * (graph.GetErrorYhigh(i) + graph.GetErrorYlow(i))
        hist.SetBinError(i + 1, err)

    return hist


def convert_index_hist_to_mjj(hist_indexed, mjj_bin_edges, name=''):
    """
    Converts a histogram with integer bin indices (1, 2, ...) on the x-axis
    to one with real MJJ bin edges.

    Args:
        hist_indexed (TH1): Original histogram with bin index x-axis.
        mjj_bin_edges (array): Real MJJ bin edges.

    Returns:
        TH1F: New histogram with MJJ binning and content from indexed histogram.
    """
    nbins_indexed = hist_indexed.GetNbinsX()
    # print(nbins_indexed, hist_indexed.GetName())

    # Make sure the index histogram has at most len(mjj_bin_edges) - 1 bins
    assert nbins_indexed <= len(mjj_bin_edges) - 1, "More bins than MJJ bin edges!"

    h_mjj = ROOT.TH1F(
        name,
        hist_indexed.GetTitle(),
        len(mjj_bin_edges) - 1,
        mjj_bin_edges
    )
    # print(h_mjj, h_mjj.GetNbinsX())

    for i in range(1, nbins_indexed + 1):
        content = hist_indexed.GetBinContent(i)
        error = hist_indexed.GetBinError(i)
        h_mjj.SetBinContent(i, content)
        h_mjj.SetBinError(i, error)

    return h_mjj
