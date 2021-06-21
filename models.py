from baseClasses import Peak, Background
import math
import numpy as np
from scipy.signal import find_peaks_cwt

class LinearBackground(Background):
    def __init__(self, slope=None, intercept = None, pointA = None, pointB = None):
        super().__init__()
        if slope != None and intercept != None:
            self.slope = slope
            self.intergept = intercept
        elif pointA != None and pointB != None:
            x1 = float(pointA[0][0])
            y1 = float(pointA[1])
            x2 = float(pointB[0][-1])
            y2 = float(pointB[1])
            self.slope = (y2-y1) / (x2 - x1)
            self.intercept = y1 - self.slope * x1
    @staticmethod
    def guess_params(xdata, ydata):
        lower_index = min(ydata[:len(xdata//2)])
        upper_index = min(ydata[len(xdata)//2:])
        x1 = xdata[lower_index]
        y1 = ydata[lower_index]
        x2 = xdata[upper_index]
        y2 = ydata[upper_index]
        slope = (y2-y1) / (x2 - x1)
        intercept = y1 - slope * x1
        return LinearBackground(slope = slope, intercept=intercept)
    def get_type(self):
        return "linear"
    def get_num_params(self):
        return 2
    def get_params(self):
        return [self.slope, self.intercept]
    def set_params(self, newParams):
        self.slope, self.intercept = newParams
    def set_variances(self, variances):
        self.slopeVar, self.intVar = variances
    def get_ydata(self, xdata):
        return self.slope * xdata + self.intercept
    def get_ydata_with_params(self,xdata,params):
        return params[0] * xdata + params[1]
    def to_string(self):
        return "Linear: Slope = "+self.slope+", Intercept = "+self.intercept
    def get_entry_fields(self):
        return ["Point 1 Energy", "Point 2 Energy"]
    def handle_entry(self, entry):
        pass
    

class GaussianPeak(Peak):
    def __init__(self, ctr=0, amp=0, wid = 1):
        super().__init__()
        self.ctr = ctr
        self.amp = amp
        self.wid = wid
    
    @staticmethod
    def guess_params(xdata, ydata):
        peaks = find_peaks_cwt(ydata, np.linspace(4,14,40))
        return [GaussianPeak(xdata[p],ydata[p],1) for p in peaks]
    
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
    def get_ctr(self):
        return self.ctr
    def get_area(self):
        return self.amp * self.wid * math.sqrt(2*math.pi)
    def get_area_stdev(self):
        return math.sqrt(self.ampVar**2+self.widVar**2)
    def get_entry_fields(self):
        return ["Center (keV): ", "Amplitude (cps): "]
    def handle_entry(self, entry):
        self.ctr = float(entry[0])
        self.amp = float(entry[1])
        self.wid = 1
    def get_ydata(self, xdata):
        return self.amp * np.exp( -((xdata - self.ctr)/self.wid)**2)
    def get_ydata_with_params(self,xdata,params):
        return params[1] * np.exp( -((xdata - params[0])/params[2])**2)
    def get_headers(self):
        return ["Center (kEV)", "Amplitude (cps)", "Width", "Area", "Area Stdev"]
    def get_all_data(self):
        return [self.ctr, self.amp, self.wid, self.get_area(), self.get_area_stdev()]
    def to_string(self):
        return "Gaussian: Center " + str(self.ctr) + " keV, "+str(self.amp)+" "+str(self.wid)