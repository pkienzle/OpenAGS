from backend import PGAAnalysis, StandardsFileParser, SpectrumParser
from evaluators import HBondAnalysis

currentRun = PGAAnalysis()
currentRun.load_known_peaks("HSensitivity.csv")
currentRun.add_files(["./spectra/2019-11-22-TCG-G10-A-air-gp1.SPE"])
currentRun.create_ROIs(["H-2","Al-28"])
currentRun.get_fitted_ROIs()
for r in currentRun.ROIs:
    for p in r.get_peaks():
        print(p.to_string())
        try:
            print(p.get_variances())
        except:
            pass
for r in currentRun.ROIs:
    k = r.get_known_peaks()[0]
    p = sorted(r.get_peaks(), key = lambda x:abs(k.get_ctr() - x.get_ctr()))[0]
    r.set_original_peak_pairs([[p,k]])
print(currentRun.run_evaluators([HBondAnalysis],[[False, True]]))