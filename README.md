# TopCombineSetup

## Setup

```bash
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
git -c advice.detachedHead=false clone --depth 1 --branch v10.2.1 https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
scramv1 b clean; scramv1 b # always make a clean build
cd ../..
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
git checkout v3.0.0-pre1
cd CombineHarvester
scram b
cd ..
git clone https://github.com/gputtley/TopCombineSetup.git
cd TopCombineSetup
```

## Making datacards
```bash
inputdir="/afs/cern.ch/work/g/guttley/private/top_reco/AnalysisConfigs/plots/"
years=("2016_PreVFP" "2016_PostVFP" "2017" "2018" "2022_preEE" "2022_postEE" "2023_preBPix" "2023_postBPix")
dcinput=""; for year in "${years[@]}"; do dcinput+="Year_${year}:${inputdir}110825_${year}_datacards_syst_inc/datacard_CombinedSubJets_mass.root,"; done; dcinput="${dcinput%,}"
outputdir="output/060825"
```

```bash
python3 scripts/make_datacards.py --input="${dcinput}" --output="${outputdir}"
```

## Making workspace
```bash
text2workspace.py -o "${outputdir}/ws.root" "${outputdir}/datacard.txt" -m 1725
```

## Run fit
```bash
pushd "${outputdir}"; combine -M MultiDimFit -d "ws.root" -t -1 --setParameters "mt=1725,r=1" --redefineSignalPOIs "mt" --algo grid --points 100 --setParameterRanges "mt=1670,1780" -n "_TopMassScan"; popd
```

## Plot fit
```bash
scripts/plot1DScan.py "${outputdir}/higgsCombine_TopMassScan.MultiDimFit.mH120.root" -o ${outputdir}/scan --POI mt --translate="config/translate.json" --main-label="Expected" --scale-POI=0.1
```

## Run impacts
```bash
pushd "${outputdir}"; combineTool.py -M Impacts -d "ws.root" -t -1 -m 172.5 --setParameters "mt=1725,r=1" --redefineSignalPOIs "mt" --setParameterRanges "mt=1670,1780" --doInitialFit -n "TopMassImpacts"; popd
pushd "${outputdir}"; combineTool.py -M Impacts -d "ws.root" -t -1 -m 172.5 --setParameters "mt=1725,r=1" --redefineSignalPOIs "mt" --setParameterRanges "mt=1670,1780" --doFits -n "TopMassImpacts"; popd
pushd "${outputdir}"; combineTool.py -M Impacts -d "ws.root" -t -1 -m 172.5 --setParameters "mt=1725,r=1" --redefineSignalPOIs "mt" --setParameterRanges "mt=1670,1780" -o impacts.json -n "TopMassImpacts"; popd
```

## Plot impacts
```bash
plotImpacts.py -i "${outputdir}/impacts.json" -o "${outputdir}/impacts" --POI mt
```

