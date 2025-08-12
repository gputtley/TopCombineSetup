import os
from argparse import ArgumentParser

description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="make_datacards", description=description,epilog="Success!")
parser.add_argument("--input", type=str, help="Dictionary formatted categories and root files", default=None)
parser.add_argument("--output", type=str, help="Output folder for datacards", default="output")
parser.add_argument("--step", type=str, help="Processing step to run", default="prepare,t2w,scan,scan_stat_only")
args = parser.parse_args()


steps = args.step.split(",")

for step in steps:


  if step == "prepare":
    os.system(f"python3 scripts/make_datacards.py --input=\"{args.input}\" --output=\"{args.output}\"")

  elif step == "t2w":
    os.system(f"text2workspace.py -o \"{args.output}/ws.root\" \"{args.output}/datacard.txt\" -m 1725")

  elif step == "scan":
    os.system(f"pushd \"{args.output}\"; combine -M MultiDimFit -d \"ws.root\" -t -1 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"mt\" --algo grid --points 100 --setParameterRanges \"mt=1670,1780\" -n \"_TopMassScan\"; popd")
    os.system(f"scripts/plot1DScan.py \"{args.output}/higgsCombine_TopMassScan.MultiDimFit.mH120.root\" -o \"{args.output}/scan\" --POI mt --translate=\"config/translate.json\" --main-label=\"Expected\" --scale-POI=0.1")

  elif step == "scan_stat_only":
    os.system(f"pushd \"{args.output}\"; combine -M MultiDimFit -d \"ws.root\" -t -1 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"mt\" --algo grid --points 100 --setParameterRanges \"mt=1670,1780\" -n \"_TopMassScanStatOnly\" --freezeParameters allConstrainedNuisances; popd")
    os.system(f"scripts/plot1DScan.py \"{args.output}/higgsCombine_TopMassScanStatOnly.MultiDimFit.mH120.root\" -o \"{args.output}/scan_stat_only\" --POI mt --translate=\"config/translate.json\" --main-label=\"Expected\" --scale-POI=0.1")
    if os.path.exists(f"{args.output}/higgsCombine_TopMassScan.MultiDimFit.mH120.root"):
      os.system(f"scripts/plot1DScan.py \"{args.output}/higgsCombine_TopMassScan.MultiDimFit.mH120.root\" -o \"{args.output}/scan_syst_stat\" --POI mt --translate=\"config/translate.json\" --main-label=\"Stat + syst\" --scale-POI=0.1 --others=\"{args.output}/higgsCombine_TopMassScanStatOnly.MultiDimFit.mH120.root:Stat only:2\" --breakdown=\"syst,stat\"")

  elif step == "impacts":
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"mt\" --setParameterRanges \"mt=1670,1780\" --doInitialFit -n \"TopMassImpacts\"; popd")
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"mt\" --setParameterRanges \"mt=1670,1780\" --doFits -n \"TopMassImpacts\"; popd")
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"mt\" --setParameterRanges \"mt=1670,1780\" -o impacts.json -n \"TopMassImpacts\"; popd")
    os.system(f"plotImpacts.py -i \"{args.output}/impacts.json\" -o \"{args.output}/impacts\" --POI mt")

  elif step == "impacts_to_rate":
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"r\" --setParameterRanges \"mt=1670,1780\" --doInitialFit -n \"TtbarRateImpacts\"; popd")
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"r\" --setParameterRanges \"mt=1670,1780\" --doFits -n \"TtbarRateImpacts\"; popd")
    os.system(f"pushd \"{args.output}\"; combineTool.py -M Impacts -d \"ws.root\" -t -1 -m 172.5 --setParameters \"mt=1725,r=1\" --redefineSignalPOIs \"r\" --setParameterRanges \"mt=1670,1780\" -o impacts_rate.json -n \"TtbarRateImpacts\"; popd")
    os.system(f"plotImpacts.py -i \"{args.output}/impacts_rate.json\" -o \"{args.output}/impacts_rate\" --POI r")
