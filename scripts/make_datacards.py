import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, SystMap, CardWriter, AutoRebin
from CombineHarvester.CombinePdfs.morphing import BuildCMSHistFuncFactory
from ROOT import RooWorkspace, RooRealVar
import numpy as np
from argparse import ArgumentParser

description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="make_datacards",description=description,epilog="Success!")
parser.add_argument("--input-run2", type=str, help="Input folder with root files for Run2", default=None)
parser.add_argument("--input-run3", type=str, help="Input folder with root files for Run3", default=None)
parser.add_argument("--output", type=str, help="Output folder for datacards", default="output")
args = parser.parse_args()

input_folder_run2 = args.input_run2
input_folder_run3 = args.input_run3
if input_folder_run2 is None and input_folder_run3 is None:
  raise ValueError("Please provide one of --input-run2 or --input-run3 arguments with valid paths.")
if input_folder_run2 is not None and not os.path.exists(input_folder_run2):
  raise FileNotFoundError(f"Input folder for Run2 not found: {input_folder_run2}")
if input_folder_run3 is not None and not os.path.exists(input_folder_run3):
  raise FileNotFoundError(f"Input folder for Run3 not found: {input_folder_run3}")

output_folder = args.output
if not os.path.exists(output_folder):
  os.makedirs(output_folder)
else:
  os.system(f"rm -rf {output_folder}/datacard.txt")
  os.system(f"rm -rf {output_folder}/shapes.root")
  if os.path.exists(f"{output_folder}/ws.root"):
    os.remove(f"{output_folder}/ws.root")


ch = CombineHarvester()

analysis = ['TopMass']
era_tags = []
if input_folder_run2 is not None:
  era_tags.append("Run2")
if input_folder_run3 is not None:
  era_tags.append("Run3")
chn = ["inc"]
cats = [(0, "inc")]

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
  "1715",
  "1725",
  "1735",
  "1755",
  "1785",
]

# Set up the inputs
ch.AddObservations(['*'], analysis, era_tags, chn, cats)
ch.cp().process(["data_obs"]).ForEachObs(lambda obs: obs.set_process("Data"))
ch.AddProcesses(['*'], analysis, era_tags, chn, bkg_procs, cats, False)
ch.AddProcesses(mass_shifts, analysis, era_tags, chn, sig_procs, cats, True)

# Add the inputs
if input_folder_run2 is not None:
  ch.cp().channel(chn).era(["Run2"]).process(bkg_procs).ExtractShapes(input_folder_run2, "$PROCESS", "$PROCESS_$SYSTEMATIC")
  ch.cp().channel(chn).era(["Run2"]).process(sig_procs).ExtractShapes(input_folder_run2, "$PROCESS_$MASS_GeV", "$PROCESS_$MASS_GeV_$SYSTEMATIC")
if input_folder_run3 is not None:
  ch.cp().channel(chn).era(["Run3"]).process(bkg_procs).ExtractShapes(input_folder_run3, "$PROCESS", "$PROCESS_$SYSTEMATIC")
  ch.cp().channel(chn).era(["Run3"]).process(sig_procs).ExtractShapes(input_folder_run3, "$PROCESS_$MASS_GeV", "$PROCESS_$MASS_GeV_$SYSTEMATIC")

# Auto-rebinning
rebin = AutoRebin()
rebin.SetBinThreshold(0)
rebin.SetBinUncertFraction(0.2)
rebin.SetRebinMode(1)
rebin.SetPerformRebin(True)
rebin.SetVerbosity(1) 
rebin.Rebin(ch,ch)

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
MH = ROOT.RooRealVar("mt", "Top mass", float(mass_shifts[0]), float(mass_shifts[-1]))

# Add the morphing variable to the workspace
for proc in sig_procs:
  BuildCMSHistFuncFactory(ws, ch, MH, proc)

# Add the workspace to CB
ch.AddWorkspace(ws, True)
ch.cp().signals().ExtractPdfs(ch, workspace_name, "$BIN_$PROCESS_morph")
ch.cp().backgrounds().ExtractPdfs(ch, workspace_name, "$BIN_$PROCESS_morph")
ch.cp().ExtractData(workspace_name, "$BIN_data_obs")

# Add MC stats
ch.cp().SetAutoMCStats(ch, 10.0, 0, 1)

# Write the datacards
datacardtxt  = f"{output_folder}/datacard.txt"
datacardroot = f"{output_folder}/shapes.root"
if os.path.exists(datacardtxt):
  os.remove(datacardtxt)
if os.path.exists(datacardroot):
  os.remove(datacardroot)
writer = CardWriter(datacardtxt,datacardroot)
writer.SetVerbosity(1)
writer.SetWildcardMasses([])
writer.WriteCards("cmb", ch)