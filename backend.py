import numpy as np
from scipy.optimize import curve_fit
import itertools
from util import multiple_peak_and_background, get_curve, binary_search_find_nearest, set_all_params, som, KnownPeak
import constants
from parsers import SpectrumParser, StandardsFileParser
from models import GaussianPeak, LinearBackground

class PGAAnalysis:
    def __init__(self, user_prefs = constants.default_prefs, title = ""):
        #TODO: make user_prefs userPrefs (camelCase variables)
        self.user_prefs = user_prefs
        self.fileData = []
        self.fileList = []
        self.knownPeaks = {}
        self.ROIs = []
        self.title = title

    def load_from_dict(self, stored_data):
        self.user_prefs = stored_data["userPrefs"]
        self.title = stored_data["title"]
        self.add_files(stored_data["files"])
        energies = self.fileData[0]["energies"]
        cps = self.fileData[0]["cps"]
        for ROIData in stored_data["ROIs"]:
            lowerIndex = ROIData["indicies"][0]
            upperIndex = ROIData["indicies"][1]
            r = ROI(energies[lowerIndex:upperIndex], cps[lowerIndex:upperIndex], [lowerIndex, upperIndex])
            r.load_from_dict(ROIData)
            self.ROIs.append(r)

    def export_to_dict(self):
        exportROIs = [r.export_to_dict() for r in self.ROIs]
        return {
            "userPrefs" : self.user_prefs,
            "title" : self.title,
            "files" : self.fileList,
            "ROIs" : exportROIs
        }
        
    def add_files(self, files):
        self.fileList = files
        self.fileData = [SpectrumParser(f).getValues() for f in files]
    def load_known_peaks(self, standards_filename):
        l = StandardsFileParser(standards_filename).extract_peaks()
        for p in l:
            self.knownPeaks[str(p.get_ctr())] = p
    def create_ROIs(self, isotope_list):
        regions = []
        peaks = []
        for k in sorted(self.knownPeaks.keys(), key=float):
            p = self.knownPeaks[k]
            if p.get_ele() in isotope_list:
                regions.append(max(p.get_ctr() - self.user_prefs["roi_width"], 0))
                regions.append(min(p.get_ctr() + self.user_prefs["roi_width"], self.fileData[0]["energies"][-1]))
                peaks.append([p])
        if self.user_prefs["overlap_rois"]:
            i=0
            while i < len(regions) - 1:
                if regions[i] > regions[i+1]: #if there is an overlap, delete both points that overlap, leaving a single, larger region
                    del regions[i]
                    del regions[i]
                    peaks[i//2] += peaks[i//2+1]
                    del peaks[i//2+1]
                else:
                    i += 1
        energies = self.fileData[0]["energies"]
        cps = self.fileData[0]["cps"]
        for i in range(0,len(regions),2):
            lower_index = binary_search_find_nearest(energies, regions[i])
            upper_index = binary_search_find_nearest(energies, regions[i+1])
            self.ROIs.append(ROI(energies[lower_index:upper_index],cps[lower_index:upper_index], [lowerIndex, upperIndex], peaks[i//2], self.user_prefs))
    def get_fitted_ROIs(self):
        for ROI in self.ROIs:
            ROI.add_peaks()
            ROI.add_bg()
            ROI.fit()
        return self.ROIs
    def refit_ROI(self, index, newPeaks):
        self.ROIs[index].set_peaks(newPeaks)
        self.ROIs[index].fit()
        return self.ROIs[index].get_fitted_curve()
    def run_evaluators(self, evaluators, e_args):
        out = []
        for i in range(len(self.fileData)):
            if i != 0:
                energies = self.fileData[i]["energies"]
                cps = self.fileData[i]["cps"]
                for r in self.ROIs:
                    bounds = r.get_range()
                    lower_index = binary_search_find_nearest(energies, bounds[0])
                    upper_index = binary_search_find_nearest(energies, bounds[1])
                    r.reanalyze(energies[lower_index:upper_index], cps[lower_index:upper_index])
                out.append([som["evaluators"][e](self.ROIs).get_results(*args) for e, args in zip(evaluators, e_args)])
        return out
           

class ROI:
    def __init__(self, energies, cps, indicies, knownPeaks = [], userPrefs = constants.default_prefs):
        self.energies = energies
        self.range = (energies[0], energies[-1])
        self.cps = cps
        self.knownPeaks = knownPeaks
        self.userPrefs = userPrefs
        self.indicies = indicies
        self.peaks = []
        self.peakPairs = None
        self.fitted = False

    def load_from_dict(self, stored_data):
        self.peaks = [som["peaks"][p["type"]](p["params"]) for p in stored_data["peaks"]]
        self.bg = som["backgrounds"][stored_data["background"]["type"]](stored_data["background"]["params"])
        for kp in stored_data["knownPeaks"]:
            knownPeakObj = KnownPeak(kp["ele"], kp["ctr"])
            if "divisor" in kp.keys():
                knownPeakObj.set_divisor_output(kp["divisor"], kp["output"])
            self.knownPeaks.append(knownPeakObj)
    def export_to_dict(self):
        exportPeaks = [{"type" : p.get_type(), "params" : p.get_params()}for p in self.peaks]
        exportBackground = {"type" : self.bg.get_type(), "params" : self.bg.get_params()}
        exportKnownPeaks = [kp.export_to_dict() for kp in self.knownPeaks]
        return {
            "indicies" : self.indicies,
            "peaks" : exportPeaks,
            "background" : exportBackground,
            "knownPeaks" : exportKnownPeaks
        }

    def set_background(self, bg):
        self.bg = bg

    def add_peaks(self):
        if (self.range[0] > 460 and self.range[0] < 520) or (self.range[1] > 460 and self.range[1] < 520) or (self.range[0] < 460 and self.range[1] > 520):
            #TODO: Boron Peak things
            pass
        self.peaks = som["peaks"][self.userPrefs["peak_type"]].guess_params(self.energies, self.cps)
   
    def add_bg(self):
        self.bg = som["backgrounds"][self.userPrefs["background_type"]].guess_params(self.energies, self.cps)
    
    def set_peaks(self, peaks):
        self.peaks = peaks
    
    def get_peaks(self):
        return self.peaks
    def get_known_peaks(self):
        return self.knownPeaks
                
    def get_range(self):
        return self.range
    def set_range(self, newRange):
        self.range = newRange
        self.energies = np.arange(newRange[0], newRange[1], .01)
    def get_energies(self):
        return self.energies
    def fit(self):
        f = lambda x,*params: multiple_peak_and_background(self.peaks, self.bg, x, params)
        p0 = np.array(self.bg.get_params() + list(itertools.chain.from_iterable([p.get_params() for p in self.peaks])))
        try:
            params, cov = curve_fit(f, self.energies, self.cps, p0=p0)
            variances = np.diag(cov)
            set_all_params(self.peaks, self.bg, params, variances)
            self.fitted = True
        except RuntimeError:
            self.fitted = False
            pass
    
    def get_fitted_curve(self, xdata = None):
        if xdata == None:
            xdata = self.energies
        return get_curve(self.peaks, self.bg, xdata)

    def get_peak_pairs(self):
        return self.peakPairs

    def set_original_peak_pairs(self, pairs):
        self.peakPairs = pairs
        self.originalPeakPairs = pairs

    def reanalyze(self, newEnergies, newCPS):
        if self.peakPairs == None:
            raise RuntimeError("Reanalyze called before peak pairs created!")
        self.energies = newEnergies
        self.cps = newCPS
        self.fit()
        outputs = []
        for p in self.originalPeakPairs:
            closestMatch = self.peaks[min(range(len(self.peaks)), key = lambda i: abs(self.peaks[i].get_ctr()-p[0].get_ctr()))]
            outputs.append([closestMatch, p[1]])  
        self.peakPairs = outputs      
        return outputs





