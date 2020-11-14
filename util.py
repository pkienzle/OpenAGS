# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 11:43:52 2020

@author: chris
"""

from numpy import NaN, Inf, arange, asarray, array
import numpy as np
import xylib
from abc import ABC, abstractmethod
import math
from scipy.signal import find_peaks_cwt
from scipy.optimize import curve_fit
import itertools

def multiple_peak_and_background(peaks, background, x, params):
        y = np.zeros_like(x)
        leftCounter = 0
        rightCounter = background.get_num_params()
        
        background.update_params(params[leftCounter:rightCounter])
        y += background.get_ydata(x)
        
        for peak in peaks:
            leftCounter = rightCounter
            rightCounter = leftCounter + peak.get_num_params()
            peak.update_params(params[leftCounter:rightCounter])
            y += peak.get_ydata(x)
            
        return y
    
def mpb_no_update(peaks, background, x):
    y = np.zeros_like(x)
    y += background.get_ydata(x)
    for peak in peaks:
        y += peak.get_ydata(x)
    return y

class Peak(ABC):
    def __init__(self):
        super().__init__()
    @abstractmethod
    def get_num_params(self):
        pass
    @abstractmethod
    def update_params(self, newParams):
        pass
    @abstractmethod
    def get_params(self):
        pass
    @abstractmethod
    def get_ctr(self):
        pass
    @abstractmethod
    def add_variances(self, variances):
        pass
    @abstractmethod
    def get_area(self):
        pass
    @abstractmethod
    def get_area_variance(self):
        pass
    @abstractmethod
    def get_ydata(self, xdata):
        pass
    @abstractmethod
    def get_entry_fields(self):
        pass 
    @abstractmethod
    def handle_entry(self, entry):
        pass
    @abstractmethod
    def get_headers(self):
        pass
    @abstractmethod
    def get_all_data(self):
        pass
    @abstractmethod
    def to_string(self):
        pass
    

class Background(ABC):
    def __init__(self):
        super().__init__()
        
    @abstractmethod
    def get_num_params(self):
        pass
    
    @abstractmethod
    def update_params(self, newParams):
        pass
    
    @abstractmethod
    def get_ydata(self, xdata):
        pass
    
    @abstractmethod
    def get_entry_fields(self):
        pass
    
    @abstractmethod
    def handle_entry(self, entry):
        pass

class LinearBackground(Background):
    def __init__(self, slope=None, intercept = None, pointA = None, pointB = None):
        super().__init__()
        if slope != None and intercept != None:
            self.slope = slope
            self.intergept = intercept
        elif pointA != None and pointB != None:
            x1 = pointA[0]
            y1 = pointA[1]
            x2 = pointB[0]
            y2 = pointB[1]
            self.slope = (y2-y1) / (x2 - x1)
            self.intercept = y1 - self.slope * x1
        else:
            raise TypeError("Provide either 2 points or a slope and intercept")
    def get_num_params(self):
        return 2
    def update_params(self, newParams):
        self.slope, self.intercept = newParams
    def get_ydata(self, xdata):
        return self.slope * xdata + self.intercept

class GaussianPeak(Peak):
    def __init__(self, ctr=0, amp=0, wid = 1):
        super().__init__()
        self.ctr = ctr
        self.amp = amp
        self.wid = wid
    def get_num_params(self):
        return 3
    def update_params(self, newParams):
        self.ctr, self.amp, self.wid = newParams
    def add_variances(self, variances):
        _, self.widVar, self.ampVar = variances
    def get_ctr(self):
        return self.ctr
    def get_area(self):
        return self.amp * self.wid * math.sqrt(2*math.pi)
    def get_area_variance(self):
        return math.sqrt(self.ampVar**2+self.widVar**2)
    def get_entry_fields(self):
        return ["Center (keV): ", "Amplitude (cps): "]
    def handle_entry(self, entry):
        self.ctr = float(entry[0])
        self.amp = float(entry[1])
        self.wid = 1
    def get_ydata(self, xdata):
        return self.amp * np.exp( -((xdata - self.ctr)/self.wid)**2)
    def get_headers(self):
        return ["Center (kEV)", "Amplitude (cps)", "Width", "Area", "Area Stdev"]
    def get_all_data(self):
        return [self.ctr, self.amp, self.wid, self.area, pow(self.areaVar, 1/2)]
    
class ROI():
    def __init__(self, indicies, energies, cps, bg):
        self.indicies = indicies
        self.energies = energies
        self.range = (energies[0], energies[-1])
        self.cps = cps
        self.bg = bg
        self.peaks = []
        self.peakPairs = None
    
    def set_background(self, bg):
        self.bg = bg
    
    def add_gaussian_peaks(self):
        locations = find_peaks_cwt(self.cps, np.linspace(4,14,40))
        self.peaks = [GaussianPeak(self.energies[loc], self.cps[loc], 1) for loc in locations]
    
    def set_peaks(self, peaks):
        self.peaks = peaks
    
    def get_peaks(self):
        return self.peaks
    
    def add_peak(self, peak):
        self.peaks.append(peak)
        
    def remove_peak(self, ctr):
        for p in self.peaks:
            if p.get_ctr() == ctr:
                self.peaks.remove(p)
                
    def get_range(self):
        return self.range
    def set_range(self, newRange):
        self.range = newRange
        self.energies = np.arange(newRange[0], newRange[1], .01)
    def get_energies(self):
        return self.energies
    def fit(self):
        f = lambda x,*params: multiple_peak_and_background(self.peaks, self.background, x, params) 
        curve_fit(f, self.energies, self.cps, p0=list(itertools.chain.from_iterable([p.get_params() for p in self.peaks])))
    
    def get_fitted_curve(self, xdata = None):
        if xdata == None:
            xdata = self.energies
        return mpb_no_update(self.peaks, self.bg, xdata)
    def add_peak_pairs(self, pairs):
        self.peakPairs = pairs
        
    def reanalyze(self, newCPS):
        if self.peakPairs == None:
            raise RuntimeError("Reanalyze called before peak pairs created!")
        self.cps = newCPS
        self.fit()
        outputs = []
        for p in self.peakPairs:
            closestMatch = self.peaks[min(range(len(self.peaks)), key = lambda i: abs(self.peaks[i].get_ctr()-p[0]))]
            outputs.append([p[1],closestMatch])        
        return outputs

class KnownPeak():
    def __init__(self, elementName, center, unit = "mg", sensitivity=None, mass=None):
        self.elementName = elementName
        self.center = center
        if sensitivity == None and mass == None or sensitivity != None and mass != None:
            raise TypeError("Please provide 1 and only 1 of the following: mass, sensitivity")
        if mass != None:
            self.divisor = mass
            self.output = "Sensitivity ("+unit+")"
        else:
            self.divisor = sensitivity
            self.output = "Mass("+unit+")"
    def get_ctr(self):
        return self.center
    def get_ele(self):
        return self.elementName
    def get_outputs(self, area, areaStdev):
        return {self.output: area/self.divisor, self.output+" stdev": areaStdev/self.divisor}

class SpectrumParser:
    """Parser for SPE files"""
    def __init__(self, fname):
        self.fname = fname
        if self.fname.split(".")[-1].lower() == "spe":
            self.spectrumfile = open(fname)
            self.speFile = True
        else:
            self.speFile = False
    def getValues(self):
        if self.speFile:
            text = self.spectrumfile.read()
            l = text.split('$')[1:]
            sections = dict()
            for section in l:
                sp = section.split('\n',1)
                sections[sp[0]] = sp[1]
            livetime, realtime = sections["MEAS_TIM:"].strip().split(" ")
            livetime = float(livetime)
            realtime = float(realtime)
            startind, endind = sections["DATA:"].split("\n")[0].split(" ")
            data = sections["DATA:"].split("\n")[1:-1]
            data = [int(i) for i in data]
            intercept, slope = sections["ENER_FIT:"].strip().split(" ")[:2]
            intercept = float(intercept)
            slope = float(slope)
            energies = [intercept + i*slope for i in range(int(startind),int(endind)+1)]
            cps = [total/livetime for total in data]
            return (livetime, realtime, np.array(energies), np.array(cps))
        else:
            d = xylib.load_file(self.fname, '')
            block = d.get_block(0)
            meta = block.meta
            metaDict = {}
            for i in range(meta.size()):
                key = meta.get_key(i)
                metaDict[key] = meta.get(key)
            ncol = block.get_column_count()
            nrow = block.get_point_count()
            data = [[block.get_column(i).get_value(j) for j in range(nrow)] for i in range(1, ncol+1)]
            livetime = metaDict["live time (s)"]
            realtime = metaDict["real time (s)"]
            return (livetime, realtime, np.array(data[0]), np.array(data[1])/float(livetime))
    def close(self):
        self.spectrumfile.close()
def get_peak_types():
    return {"Gaussian":GaussianPeak()}
"""Functions to search for values in my data, used as utilities in many places. Modified binary search algorithm."""
def binary_search_find_nearest(l, e):
    upperBound = len(l)
    lowerBound = 0
    guess = (upperBound + lowerBound)//2
    while not (e < l[guess+1] and e > l[guess-1]):
        if e > l[guess]:
            lowerBound = guess + 1
        else:
            upperBound = guess - 1
        guess = (upperBound + lowerBound)//2
        if guess <= 2 or guess >= len(l)-2:
            break
    if e > l[guess]:
        guess += 1
    return guess

def binary_search_buried(l, e, i):
    upperBound = len(l)
    lowerBound = 0
    guess = (upperBound + lowerBound)//2
    while not (e < l[guess+1][i] and e > l[guess-1][i]):
        if e > l[guess][i]:
            lowerBound = guess + 1
        else:
            upperBound = guess - 1
        guess = (upperBound + lowerBound)//2
        if guess <= 2 or guess >= len(l)-2:
            break
    if e > l[guess][i]:
        guess += 1
    return guess
