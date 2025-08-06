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
inputrun2="/afs/cern.ch/work/g/guttley/private/top_reco/AnalysisConfigs/plots/250725_run2_datacards/datacard_CombinedSubJets_mass.root"
inputrun3="/afs/cern.ch/work/g/guttley/private/top_reco/AnalysisConfigs/plots/250725_run3_datacards/datacard_CombinedSubJets_mass.root"
outputdir="output/060825"
```

```bash
python3 scripts/make_datacards.py --input-run2="${inputrun2}" --input-run3="${inputrun3}" --output="${outputdir}"
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