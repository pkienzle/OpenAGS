from baseClasses import Peak, Background
import math
import numpy as np
from scipy.signal import find_peaks_cwt
from sigfig import round

class LinearBackground(Background):
    def __init__(self, slope, intercept, variances = [None, None]):
        super().__init__()
        self.slope = slope
        self.intercept = intercept
        self.variances = variances
        self.originalParams = [slope, intercept]
        self.originalVariances = variances
    @staticmethod
    def guess_params(xdata, ydata):
        lowerIndex = int(np.where(ydata == min(ydata[:len(xdata)//2]))[0][0])
        upperIndex = int(np.where(ydata == min(ydata[len(xdata)//2:]))[-1][-1])
        x1 = xdata[lowerIndex]
        y1 = ydata[lowerIndex]
        x2 = xdata[upperIndex]
        y2 = ydata[upperIndex]
        slope = float((y2-y1) / (x2 - x1))
        intercept = float(y1 - slope * x1)
        return LinearBackground(slope, intercept)
    @staticmethod
    def get_entry_fields():
        return ["Point 1 Energy", "Point 2 Energy"]
    def get_type(self):
        return "linear"
    def get_num_params(self):
        return 2
    def get_params(self):
        return [self.slope, self.intercept]
    def set_params(self, newParams):
        self.slope, self.intercept = newParams
    def get_variances(self):
        return self.variances
    def set_variances(self, variances):
        self.slopeVar, self.intVar = variances
    def get_original_params(self):
        return self.originalParams
    def set_original_params(self, params):
        self.originalParams = list(params)
    def get_original_variances(self):
        return self.originalVariances
    def set_original_variances(self, variances):
        self.originalVariances = list(variances)
    def get_ydata(self, xdata):
        xdata = np.array(xdata)
        return self.slope * xdata + self.intercept
    def get_ydata_with_params(self,xdata,params):
        xdata = np.array(xdata)
        return params[0] * xdata + params[1]
    def to_string(self):
        return "Linear: Slope = "+round(float(self.slope), sigfigs=4, notation='scientific')+", Intercept = "+round(float(self.intercept), sigfigs=4, notation='scientific')
    def handle_entry(self, entry):
        x1 = float(entry[0])
        y1 = float(entry[1])
        x2 = float(entry[2])
        y2 = float(entry[3])
        self.slope = float((y2-y1) / (x2 - x1))
        self.intercept = float(y1 - self.slope * x1)
    

class GaussianPeak(Peak):
    def __init__(self, ctr=0, amp=0, wid = 1, variances = []):
        super().__init__()
        self.ctr = ctr
        self.amp = amp
        self.wid = wid
        self.ctrVar = None
        self.ampVar = None
        self.widVar = None
        self.originalParams = [ctr, amp, wid]
        self.originalVariances = variances
        if variances != []:
            self.set_variances(variances)
    
    @staticmethod
    def guess_params(xdata, ydata):
        peaks = find_peaks_cwt(ydata, np.linspace(4,14,40))
        return [GaussianPeak(xdata[p],ydata[p],1) for p in peaks]
    @staticmethod
    def get_entry_fields():
        return ["Center (keV): ", "Amplitude (cps): "]

    def get_type(self):
        return "gaussian"
    def get_num_params(self):
        return 3
    def set_params(self, newParams):
        self.ctr, self.amp, self.wid = newParams
    def get_params(self):
        return [self.ctr, self.amp, self.wid]
    def set_variances(self, variances):
        self.ctrVar, self.ampVar, self.widVar = variances
    def get_variances(self):
        return [self.ctrVar, self.ampVar, self.widVar]
    def get_original_params(self):
        return self.originalParams
    def set_original_params(self, params):
        self.originalParams = list(params)
    def get_original_variances(self):
        return self.originalVariances
    def set_original_variances(self, variances):
        self.originalVariances = list(variances)
    def get_ctr(self):
        return self.ctr
    def get_area(self):
        return self.amp * self.wid * math.sqrt(2*math.pi)
    def get_area_stdev(self):
        return self.get_area() * math.sqrt((self.ampVar/self.amp)**2+(self.widVar/self.wid)**2)
    
    def handle_entry(self, entry):
        self.ctr = float(entry[0])
        self.amp = float(entry[1])
        self.wid = 1
    def get_ydata(self, xdata):
        xdata = np.array(xdata)
        return self.amp * np.exp( -((xdata - self.ctr)/self.wid)**2)
    def get_ydata_with_params(self,xdata,params):
        xdata = np.array(xdata)
        return params[1] * np.exp( -((xdata - params[0])/params[2])**2)
    def get_headers(self):
        return ["Center (kEV)", "Amplitude (cps)", "Width", "Area", "Area Stdev"]
    def get_all_data(self):
        return [self.ctr, self.amp, self.wid, self.get_area(), self.get_area_stdev()]
    def to_string(self):
        return "Gaussian: Center " + str(round(float(self.ctr), decimals=1)) + " keV"