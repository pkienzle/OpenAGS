from backend import PGAAnalysis, ROI
from parsers import StandardsFileParser, SpectrumParser
from evaluators import HBondAnalysis
from models import GaussianPeak
import os
from util import ivw_combine

outputData = [["Filename"] + HBondAnalysis.get_headings()]

for _, dirs, files in os.walk("./spectra"):
    for fname in files:
        currentRun = PGAAnalysis()
        currentRun.load_known_peaks("HSensitivity.csv")
        currentRun.add_files(["./spectra/"+fname])
        currentRun.create_ROIs(["H-2","Al-28", "F-20"])
        currentRun.ROIs[0].set_peaks([GaussianPeak(1633.33,1,1)])
        currentRun.ROIs[1].set_peaks([GaussianPeak(1778.92,1,1)])
        currentRun.ROIs[2].set_peaks([GaussianPeak(2223.25,1,1)])
        for ROI in currentRun.ROIs:
            ROI.add_bg()
            ROI.fit()
            ROI.set_original_peak_pairs([[ROI.peaks[0], ROI.get_known_peaks()[0]]])

        HPeak = currentRun.ROIs[2].peaks[0]
        AlPeak = currentRun.ROIs[1].peaks[0]
        outputData.append([fname]+currentRun.run_evaluators([HBondAnalysis], [[]])[0][0])
    """
    for d in dirs:
        for _, dirs, files in os.walk("./spectra/"+d):
            currentRun = PGAAnalysis()
            currentRun.load_known_peaks("HSensitivity.csv")
            currentRun.add_files(["./spectra/"+d+"/"+ f for f in files])
            currentRun.create_ROIs(["H-2","Al-28", "F-20"])
            currentRun.ROIs[0].set_peaks([GaussianPeak(333.97,1,1)])
            currentRun.ROIs[1].set_peaks([GaussianPeak(1778.92,1,1)])
            currentRun.ROIs[2].set_peaks([GaussianPeak(2223.25,1,1)])
            for ROI in currentRun.ROIs:
                ROI.add_bg()
                ROI.fit()
                ROI.set_original_peak_pairs([[ROI.peaks[0], ROI.get_known_peaks()[0]]])
            evalResults = currentRun.run_evaluators([HBondAnalysis], [[]])
            HBondResults = [e[0] for e in evalResults]
            combinedResults = ivw_combine([h[0] for h in HBondResults], stdev=[h[1]/2 for h in HBondResults])
            outputData.append([d, combinedResults[0], combinedResults[1] * 2, HBondResults[0][2]])"""


f = open("Houtput.csv", "w")
f.write("\n".join([', '.join([str(x) for x in line]) for line in outputData]))
f.close()