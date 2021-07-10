import numpy as np
from scipy.optimize import curve_fit
import itertools
from util import multiple_peak_and_background, get_curve, binary_search_find_nearest, set_all_params, som, KnownPeak
import constants
from parsers import SpectrumParser, StandardsFileParser
from models import GaussianPeak, LinearBackground
from sigfig import round

class PGAAnalysis:
    def __init__(self, user_prefs = constants.default_prefs, title = ""):
        #TODO: make user_prefs userPrefs (camelCase variables)
        self.user_prefs = user_prefs
        self.fileData = []
        self.fileList = []
        self.knownPeaks = {}
        self.ROIs = []
        self.isotopes = []
        self.title = title
        self.ROIsFitted = False
        self.resultsGenerated = False
    def load_from_dict(self, stored_data):
        if "userPrefs" in stored_data.keys():
            self.user_prefs = stored_data["userPrefs"]
        self.title = stored_data["title"]
        self.add_files(stored_data["files"])
        self.load_known_peaks(stored_data["standardsFilename"])
        energies = self.fileData[0]["energies"]
        cps = self.fileData[0]["cps"]
        self.ROIsFitted = stored_data["ROIsFitted"]
        for ROIData in stored_data["ROIs"]:
            lowerIndex = ROIData["indicies"][0]
            upperIndex = ROIData["indicies"][1]
            r = ROI(energies[lowerIndex:upperIndex], cps[lowerIndex:upperIndex], [lowerIndex, upperIndex])
            r.load_from_dict(ROIData)
            self.ROIs.append(r)
        self.isotopes = list(set(itertools.chain(*[r.get_isotopes() for r in self.ROIs])))
        self.resultsGenerated = stored_data["resultsGenerated"]
        if self.resultsGenerated:
            for i in range(len(stored_data["results"])):
                self.fileData[i]["results"] = stored_data["results"][i]
                self.fileData[i]["headings"] = stored_data["resultHeadings"]
                self.fileData[i]["evaluatorNames"] = stored_data["evaluatorNames"]


    def export_to_dict(self):
        exportROIs = [r.export_to_dict() for r in self.ROIs]
        if self.resultsGenerated:
            return {
            "userPrefs" : self.user_prefs,
            "title" : self.title,
            "files" : self.fileList,
            "standardsFilename" : self.standardsFilename,
            "ROIsFitted" : self.ROIsFitted,
            "ROIs" : exportROIs,
            "resultsGenerated" : True,
            "results": [fd["results"] for fd in self.fileData],
            "resultHeadings": self.fileData[0]["resultHeadings"],
            "evaluatorNames": self.fileData[0]["evaluatorNames"] 
            }
        return {
            "userPrefs" : self.user_prefs,
            "title" : self.title,
            "files" : self.fileList,
            "standardsFilename" : self.standardsFilename,
            "ROIsFitted" : self.ROIsFitted,
            "ROIs" : exportROIs,
            "resultsGenerated" : False
        }

    def add_files(self, files):
        self.fileList = files
        self.fileData = [SpectrumParser(f).getValues() for f in files]

    def load_known_peaks(self, standardsFilename):
        self.standardsFilename = standardsFilename
        l = StandardsFileParser(standardsFilename).extract_peaks()
        for p in l:
            self.knownPeaks[str(p.get_ctr())] = p
    def get_known_peaks(self):
        return self.knownPeaks
    def get_title(self):
        return self.title
    def set_title(self, newTitle):
        self.title = newTitle
    def get_all_isotopes(self):
        return set([self.knownPeaks[key].get_ele() for key in self.knownPeaks.keys()])

    def update_ROIs(self, addedIsotopes, removedIsotopes = []):
        rmvLst = []
        editList = []
        alreadyAdded = []

        for iso in addedIsotopes:
            if iso in self.isotopes:
                alreadyAdded.append(iso)
            else:
                self.isotopes.append(iso)

        for iso in alreadyAdded:
            addedIsotopes.remove(iso)

        for iso in removedIsotopes:
            try:
                self.isotopes.remove(iso)
            except:
                pass

        for r in self.ROIs:
            isotopes = r.get_isotopes()
            removed = len(list(filter(lambda x: x in removedIsotopes, isotopes)))
            if removed == len(isotopes):
                rmvLst.append(r)
            elif removed > 0:
                editList += [kp.get_ctr() for kp in r.get_known_peaks]
        
        regions = []
        peaks = []
        for k in sorted(self.knownPeaks.keys(), key=float):
            p = self.knownPeaks[k]
            if p.get_ele() in addedIsotopes or p.get_ctr() in editList:
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
            lowerIndex = binary_search_find_nearest(energies, regions[i])
            upperIndex = binary_search_find_nearest(energies, regions[i+1])
            r = ROI(energies[lowerIndex:upperIndex],cps[lowerIndex:upperIndex], [lowerIndex, upperIndex], self.user_prefs)
            r.set_known_peaks(peaks[i//2])
            self.ROIs.append(r)
        self.ROIs = sorted(self.ROIs, key=lambda x:x.get_range()[0])

    def get_fitted_ROIs(self):
        for ROI in self.ROIs:
            ROI.add_peaks()
            ROI.add_bg()
            ROI.fit()
        self.ROIsFitted = True
        return self.ROIs

    def get_isotopes(self):
        return self.isotopes

    def get_all_entry_fields(self):
        return {
            "peaks" : {k : som["peaks"][k].get_entry_fields() for k in som["peaks"].keys()},
            "backgrounds" : {k : som["backgrounds"][k].get_entry_fields() for k in som["backgrounds"].keys()}
        }
    def get_entry_repr(self, model, name, ROIIndex, params):
        if model == "peaks":
            testObj = som[model][name]()
            testObj.handle_entry(params)
            return testObj.to_string(), testObj.get_params()
        elif model == "backgrounds":
            tmpObj = som[model][name].guess_params(self.ROIs[ROIIndex].get_energies(), self.ROIs[ROIIndex].get_cps())
            return tmpObj.to_string(), tmpObj.get_params()

    def set_ROI_range(self, ROIIndex, newRange):
        energies = self.fileData[0]["energies"]
        cps = self.fileData[0]["cps"]
        lowerIndex = binary_search_find_nearest(energies, newRange[0])
        upperIndex = binary_search_find_nearest(energies, newRange[1])
        self.ROIs[ROIIndex].set_data([energies[lowerIndex], energies[upperIndex]], energies[lowerIndex:upperIndex], cps[lowerIndex:upperIndex], [lowerIndex, upperIndex])

    def run_evaluators(self, evaluators, e_args):
        for i in range(len(self.fileData)):
            if i != 0:
                energies = self.fileData[i]["energies"]
                cps = self.fileData[i]["cps"]
                for r in self.ROIs:
                    bounds = r.get_range()
                    lowerIndex = binary_search_find_nearest(energies, bounds[0])
                    upperIndex = binary_search_find_nearest(energies, bounds[1])
                    r.reanalyze(energies[lowerIndex:upperIndex], cps[lowerIndex:upperIndex])
            self.fileData[i]["results"] = [e(self.ROIs).get_results(*args) for e, args in zip(evaluators, e_args)]
            self.fileData[i]["resultHeadings"] = [e.get_headings(self.ROIs[0]) for e in evaluators]
            self.fileData[i]["evaluatorNames"] = [e.get_name() for e in evaluators]
        self.resultsGenerated = True
        return None
           

class ROI:
    def __init__(self, energies, cps, indicies, userPrefs = constants.default_prefs):
        self.energies = energies
        self.range = (energies[0], energies[-1])
        self.cps = cps
        self.knownPeaks = []
        self.userPrefs = userPrefs
        self.indicies = indicies
        self.peaks = []
        self.peakPairs = None
        self.fitted = False

    def load_from_dict(self, stored_data):
        self.peaks = [som["peaks"][p["type"]](*p["params"],variances=p["variances"]) for p in stored_data["peaks"]]
        self.bg = som["backgrounds"][stored_data["background"]["type"]](*stored_data["background"]["params"],variances=stored_data["background"]["variances"])
        self.fitted = (self.peaks[0].get_variances()[0] != None)
        for kp in stored_data["knownPeaks"]:
            if kp["ctr"] >= self.energies[0] and kp["ctr"] <= self.energies[-1]:
                knownPeakObj = KnownPeak(kp["ele"], kp["ctr"])
                if "divisor" in kp.keys():
                    knownPeakObj.set_divisor_output(kp["divisor"], kp["output"])
                self.knownPeaks.append(knownPeakObj)
    def export_to_dict(self):
        exportPeaks = [{"type" : p.get_type(), "params" : p.get_original_params(), "variances": p.get_original_variances()}for p in self.peaks]
        exportBackground = {"type" : self.bg.get_type(), "params" : self.bg.get_original_params(), "variances": self.bg.get_original_variances()}
        exportKnownPeaks = [kp.export_to_dict() for kp in self.knownPeaks]
        return {
            "indicies" : self.indicies,
            "peaks" : exportPeaks,
            "background" : exportBackground,
            "knownPeaks" : exportKnownPeaks
        }
    def set_known_peaks(self, peaks):
        self.knownPeaks = peaks
    def set_background(self, bg):
        self.bg = bg
    def get_background(self):
        return self.bg
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
    def get_isotopes(self):
        return [kp.get_ele() for kp in self.knownPeaks]
    def get_peak_ctrs(self):
        return [p.get_ctr() for p in self.peaks]

    def get_known_peaks(self):
        return self.knownPeaks
                
    def get_range(self):
        return list(self.range)
    def get_formatted_range(self):
        return [str(round(float(self.range[0]), decimals=1)), str(round(float(self.range[1]), decimals=1))]
    def set_range(self, newRange):
        self.range = newRange
        self.energies = np.arange(newRange[0], newRange[1], .01)
    def get_energies(self):
        return list(self.energies)
    def get_cps(self):
        return list(self.cps)
    def set_data(self, newRange, energies, cps, indicies):
        self.range = newRange
        self.energies = energies
        self.cps = cps
        self.indicies = indicies

    def fit(self, reanalyze = False):
        f = lambda x,*params: multiple_peak_and_background(self.peaks, self.bg, x, params)
        p0 = np.array(self.bg.get_params() + list(itertools.chain.from_iterable([p.get_params() for p in self.peaks])))
        try:
            params, cov = curve_fit(f, self.energies, self.cps, p0=p0)
            variances = np.diag(cov)
            set_all_params(self.peaks, self.bg, params, variances, reanalyze)
            self.fitted = True
        except RuntimeError:
            self.fitted = False
            pass
    
    def get_fitted_curve(self, xdata = None):
        if xdata == None:
            xdata = np.arange(self.range[0], self.range[-1], .01)
        return [list(xdata), get_curve(self.peaks, self.bg, xdata)]

    def get_peak_pairs(self):
        return self.peakPairs

    def get_indicies(self):
        return self.indicies
    def get_closest_peak(self, kp):
        c = kp.get_ctr()
        minSep = 99999
        minPeak = None
        for p in self.peaks:
            if(abs(p.get_ctr() - c) < minSep):
                minSep = abs(p.get_ctr() - c)
                minPeak = p
        return minPeak
    def set_original_peak_pairs(self, energyPairs):
        pairs = []
        for ep in energyPairs:
            pair = []
            for p in self.peaks:
                if p.get_ctr() == ep[0]:
                    pair.append(p)
                    break
            for kp in self.knownPeaks:
                if kp.get_ctr() == ep[1]:
                    pair.append(kp)
                    break
            pairs.append(pair)
        self.peakPairs = pairs
        self.originalPeakPairs = pairs

    def reanalyze(self, newEnergies, newCPS):
        if self.peakPairs == None:
            raise RuntimeError("Reanalyze called before peak pairs created!")
        self.energies = newEnergies
        self.cps = newCPS
        self.fit(True)
        outputs = []
        for p in self.originalPeakPairs:
            closestMatch = self.peaks[min(range(len(self.peaks)), key = lambda i: abs(self.peaks[i].get_ctr()-p[0].get_ctr()))]
            outputs.append([closestMatch, p[1]])  
        self.peakPairs = outputs      
        return outputs





