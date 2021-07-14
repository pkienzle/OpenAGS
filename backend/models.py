from baseClasses import Peak, Background, StandardPeak, BoronPeak
import math
from util import binary_search_find_nearest
from copy import deepcopy
import numpy as np
from scipy.signal import find_peaks_cwt, convolve
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
    

class GaussianPeak(StandardPeak):
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
    
    def handle_entry(self, entry, bounds=[0,16000]):
        self.ctr = float(entry[0])
        if self.ctr < bounds[0] or self.ctr > bounds[1]:
            raise ValueError("Out of Bounds Peak")
        self.amp = float(entry[1])
        self.wid = 1
    def get_ydata(self, xdata):
        xdata = np.array(xdata)
        return self.amp * np.exp( -((xdata - self.ctr)/self.wid)**2)
    def get_ydata_with_params(self,xdata,params):
        xdata = np.array(xdata)
        return params[1] * np.exp( -((xdata - params[0])/params[2])**2)
    def to_string(self):
        return "Gaussian: Center " + str(round(float(self.ctr), decimals=1)) + " keV"

class KuboSakaiBoronPeak(BoronPeak):
    def __init__(self, E0=477.6, N0=1, D=1, delta=1, variances = []):
        super().__init__()
        self.E0 = E0
        self.N0 = N0
        self.D = D
        self.delta = delta
        self.originalParams = [E0,N0,D,delta]
        self.variances = variances
        self.originalVariances = variances

    @staticmethod
    def guess_params(xdata, ydata):
        startIndex = binary_search_find_nearest(xdata, 477.6)
        curIndex = startIndex
        N0 = 0
        width = xdata[1] - xdata[0]
        while xdata[curIndex] < 487.6:
            N0 += 2 * width * min(ydata[curIndex], ydata[2*startIndex - curIndex])
            curIndex += 1
        return KuboSakaiBoronPeak(477.6, N0, 2, 1.3)
    
    @staticmethod
    def remove_from_data(xdata, ydata):
        newYData = deepcopy(ydata)
        startIndex = binary_search_find_nearest(xdata, 477.6)
        curIndex = startIndex
        minVal = min(ydata)
        while xdata[curIndex] < 487.6:
            toSub = min(xdata[curIndex], xdata[2*startIndex - curIndex]) - minVal
            newYData[curIndex] -= toSub
            newYData[2*startIndex - curIndex] -= toSub
            curIndex += 1
        return newYData

    def get_type(self):
        return "kubo_sakai"
    def get_num_params(self):
        return 4
    def get_params(self):
        return [self.E0, self.N0, self.D, self.delta]
    def set_params(self, params):
        self.E0, self.N0, self.D, self.delta = params
    def get_variances(self):
        return self.variances
    def set_variances(self, variances):
        self.variances = variances
    def get_original_params(self):
        return self.originalParams
    def set_original_params(self, params):
        self.originalParams = list(params)
    def get_original_variances(self):
        return self.originalVariances
    def set_original_variances(self, variances):
        self.originalVariances = list(variances)
    def get_ctr(self):
        return self.E0
    def get_area(self):
        return self.N0
    def get_area_stdev(self):
        return math.sqrt(self.variances[1])

    def get_ydata(self, xdata):
        decayConstant = 9.49516685699
        c = 3*10**8
        v0=4.8*10**6
        if xdata[1] - xdata[0] > .1:
            step = (xdata[1] - xdata[0]) / 10
        else:
            step = (xdata[1] - xdata[0])
        
        DoGx = np.arange(xdata[0], xdata[-1]+.01, step)
        DoG = c*self.N0/(2*self.E0*v0) * decayConstant / (decayConstant - self.D) * (1-(c*abs(DoGx-self.E0)/(self.E0*v0))**((decayConstant - self.D)/self.D))
        for i in range(len(DoGx)):
            if abs(DoGx[i] - self.E0) > 7.64:
                DoG[i] = 0
                
        numSteps = int((xdata[0] + 5)//step)
        start = xdata[0] - (numSteps * step)
        DoG = np.concatenate((np.zeros(numSteps), DoG))

        IRx = np.arange(start, 5, step)
        IR = 1/(self.delta * math.sqrt(2*math.pi)) * math.e ** (-.5*(IRx/self.delta)**2) * step

        convRes = convolve(DoG, IR)
        if xdata[1] - xdata[0] > .1:
            return convRes[len(IRx)//2 + numSteps:len(IRx)//2 + numSteps + len(DoGx):10]
        else:
            return convRes[len(IRx)//2 + numSteps:len(IRx)//2 + numSteps + len(DoGx)]

    def get_ydata_with_params(self, xdata, params):
        E0, N0, D, delta = params
        decayConstant = 9.49516685699
        c = 3*10**8
        v0=4.8*10**6
        step = (xdata[1] - xdata[0]) / 10
        DoGx = np.arange(xdata[0], xdata[-1]+.01, step)
        DoG = c*N0/(2*E0*v0) * decayConstant / (decayConstant - D) * (1-(c*abs(DoGx-E0)/(E0*v0))**((decayConstant - D)/D))
        for i in range(len(DoGx)):
            if abs(DoGx[i] - E0) > 7.64:
                DoG[i] = 0
                
        numSteps = int((xdata[0] + 5)//step)
        start = xdata[0] - (numSteps * step)
        DoG = np.concatenate((np.zeros(numSteps), DoG))

        IRx = np.arange(start, 5, step)
        IR = 1/(delta * math.sqrt(2*math.pi)) * math.e ** (-.5*(IRx/delta)**2) * step

        convRes = convolve(DoG, IR)

        return convRes[len(IRx)//2 + numSteps:len(IRx)//2 + numSteps + len(DoGx):10]
    @staticmethod
    def get_entry_fields():
        return ["Center (keV)", "Max Amplitude"]

    def handle_entry(self, entry, bounds=[0,16000]):
        self.E0 = float(entry[0])
        if self.E0 < bounds[0] or self.E0 > bounds[1]:
            raise ValueError("Out of Bounds Peak")
        self.N0 = 10 * float(entry[1])
        self.D = 2
        self.delta = 1.8
    
    def to_string(self):
        return "Boron Peak, Center "+str(round(float(self.E0), decimals=1))+" keV, Area "+str(round(float(self.N0), decimals=1))
    