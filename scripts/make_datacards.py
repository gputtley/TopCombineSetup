import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, SystMap, CardWriter, AutoRebin
from CombineHarvester.CombinePdfs.morphing import BuildCMSHistFuncFactory
from ROOT import RooWorkspace, RooRealVar
import numpy as np
from argparse import ArgumentParser

description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="make_datacards", description=description,epilog="Success!")
parser.add_argument("--input", type=str, help="Dictionary formatted categories and root files", default=None)
parser.add_argument("--output", type=str, help="Output folder for datacards", default="output")
args = parser.parse_args()

output_folder = args.output
if not os.path.exists(output_folder):
  os.makedirs(output_folder)#

if args.input is None:
  raise ValueError("Please provide the --input argument with a valid path to the input dictionary.")

analysis = ['TopMass']
era_tags = ["inc"]
cats = []
input_folders = []
for cat_ind, cat_info in enumerate(args.input.split(',')):
  cat_name, input_folder = cat_info.split(':')
  if not os.path.exists(input_folder):
    raise FileNotFoundError(f"Input folder not found: {input_folder}")
  input_folders.append(input_folder)
  cats.append((cat_ind, cat_name))
cat_names = [cat[1] for cat in cats]
chn = ["inc"]

bkg_procs = [
  "Other",
  "ST",
  "WJ"
]
sig_procs = [
  "TT"
]
mass_shifts = [
  "1665",
  "1695",
  "1705",
  "1715",
  "1725",
  "1735",
  "1745",
  "1755",
  "1785",
]

# Set up the inputs
ch = CombineHarvester()
ch.AddObservations(['*'], analysis, era_tags, chn, cats)
ch.AddProcesses(['*'], analysis, era_tags, chn, bkg_procs, cats, False)
ch.AddProcesses(mass_shifts, analysis, era_tags, chn, sig_procs, cats, True)

# Add systematics
jec_systs = {
  "AbsoluteMPFBias": {"Correlation" : 1},
  "AbsoluteScale": {"Correlation" : 1},
  "AbsoluteStat": {"Correlation" : 0},
  "FlavorQCD": {"Correlation" : 1},
  "Fragmentation": {"Correlation" : 1},
  "PileUpDataMC": {"Correlation" : 1},
  "PileUpPtBB": {"Correlation" : 1},
  "PileUpPtEC1": {"Correlation" : 1},
  "PileUpPtEC2": {"Correlation" : 1},
  "PileUpPtHF": {"Correlation" : 1},
  "PileUpPtRef": {"Correlation" : 1},
  "RelativeFSR": {"Correlation" : 1},
  "RelativePtBB": {"Correlation" : 1},
  "RelativePtEC1": {"Correlation" : 0},
  "RelativePtEC2": {"Correlation" : 0},
  "RelativePtHF": {"Correlation" : 1},
  "RelativeBal": {"Correlation" : 1},
  "RelativeSample": {"Correlation" : 0},
  "RelativeStatEC": {"Correlation" : 0},
  "RelativeStatFSR": {"Correlation" : 0},
  "RelativeStatHF": {"Correlation" : 0},
  "SinglePionECAL": {"Correlation" : 1},
  "SinglePionHCAL": {"Correlation" : 1},
  "TimePtEta": {"Correlation" : 0},
}

years = ["2016_PreVFP", "2016_PostVFP", "2017", "2018", "2022_preEE", "2022_postEE", "2023_preBPix", "2023_postBPix"]

for syst, props in jec_systs.items():
  if props["Correlation"] == 1 or props["Correlation"] == 0.5:
    ch.cp().bin(cat_names).process(bkg_procs).AddSyst(ch, syst, "shape", SystMap()(1.0))
    ch.cp().bin(cat_names).process(sig_procs).AddSyst(ch, syst, "shape", SystMap()(1.0))
  if props["Correlation"] == 0 or props["Correlation"] == 0.5:
    for yr in years:
      if f"Year_{yr}" in cat_names:
        ch.cp().bin([f"Year_{yr}"]).process(bkg_procs).AddSyst(ch, f"{syst}_{yr}", "shape", SystMap()(1.0))
        ch.cp().bin([f"Year_{yr}"]).process(sig_procs).AddSyst(ch, f"{syst}_{yr}", "shape", SystMap()(1.0))

# Add the inputs
for cat_ind, cat_name in cats:
  input_folder = input_folders[cat_ind]
  ch.cp().bin([cat_name]).process(bkg_procs).ExtractShapes(input_folders[cat_ind], "$PROCESS", "$PROCESS_$SYSTEMATIC")
  ch.cp().bin([cat_name]).process(sig_procs).ExtractShapes(input_folders[cat_ind], "$PROCESS_$MASS_GeV", "$PROCESS_$MASS_GeV_$SYSTEMATIC")

# Auto-rebinning
rebin = AutoRebin()
rebin.SetBinThreshold(0)
rebin.SetBinUncertFraction(0.15)
rebin.SetRebinMode(1)
rebin.SetPerformRebin(True)
rebin.SetVerbosity(1) 
rebin.Rebin(ch,ch)

# Scale all signal to 1725 yield
class GetRate:
  def __init__(self):
    self.rates = {}
  def __call__(self, proc):
    self.rates[proc.mass()] = proc.rate()
for cat_ind, cat_name in cats:
  get_rate = GetRate()
  ch.cp().bin([cat_name]).process(sig_procs).ForEachProc(get_rate)
  def set_rate(proc): 
    proc.set_rate(proc.rate() * get_rate.rates["1725"] / get_rate.rates[proc.mass()])
  ch.cp().bin([cat_name]).process(sig_procs).ForEachProc(set_rate)


# Print histograms
def print_histogram(proc):
  h = proc.shape()
  if h:  
    h.Print("all")
    
ch.ForEachProc(print_histogram)
ch.ForEachObs(print_histogram)

# Create workspace
workspace_name = "workspace"
ws = ROOT.RooWorkspace(workspace_name, workspace_name)

# Define the morphing variable
mt = ROOT.RooRealVar("mt", "Top mass", float(mass_shifts[0]), float(mass_shifts[-1]))

# Add the morphing variable to the workspace
for proc in sig_procs:
  BuildCMSHistFuncFactory(ws, ch, mt, proc)

# Add the workspace to CB
ch.AddWorkspace(ws, True)
ch.cp().signals().ExtractPdfs(ch, workspace_name, "$BIN_$PROCESS_morph")
ch.cp().backgrounds().ExtractPdfs(ch, workspace_name, "$BIN_$PROCESS_morph")
ch.cp().ExtractData(workspace_name, "$BIN_data_obs")

# Add MC stats
ch.SetAutoMCStats(ch, 10., 1, 1)

# Write the datacards
datacardtxt  = f"{output_folder}/datacard.txt"
datacardroot = f"{output_folder}/shapes.root"
writer = CardWriter(datacardtxt,datacardroot)
writer.SetVerbosity(1)
writer.SetWildcardMasses([])
writer.WriteCards("cmb", ch)