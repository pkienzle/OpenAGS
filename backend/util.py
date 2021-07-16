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
import itertools
from sigfig import round

class KnownPeak:
    def __init__(self, elementName, center, unit = "mg", sensitivity=None, mass=None, halfLife = None, decayConstant = None, decayUnit="min"):
        self.elementName = elementName
        self.center = center
        self.delayed = True


        if sensitivity != None and mass != None:
            raise TypeError("Please provide no more than 1 of the following: mass, sensitivity")
        if mass != None:
            self.divisor = mass
            self.output = "Sensitivity ("+unit+")"
        elif sensitivity != None:
            self.divisor = sensitivity
            self.output = "Mass ("+unit+")"
        else:
            self.divisor = None
            self.output = "Area (cps)"
        
        if halfLife != None and decayConstant != None:
            raise TypeError("Please provide no more than 1 of the following: half-life, decay constant")
        elif halfLife != None:
            self.decayConstant = math.log(2) / halfLife
        elif decayConstant != None:
            self.decayConstant = decayConstant
        else:
            self.delayed = False

        if self.delayed:
            if decayUnit in ("s", "sec"):
                self.decayConstant *= 60
            if decayUnit in ("h", "hr"):
                self.decayConstant /=60


    def export_to_dict(self):
        if self.divisor != None:
            return {
                "ele" : self.elementName,
                "ctr" : self.center,
                "divisor" : self.divisor,
                "output" : self.output
            }
        else:
            return {
                "ele" : self.elementName,
                "ctr" : self.center
            }
    
    def set_delay_times(self, irr, wait, count):
        self.irrTime = irr
        self.waitTime = wait
        self.countTime = count

    def set_divisor_output(self,divisor,output):
        self.divisor = divisor
        self.output = output

    def get_ctr(self):
        return self.center
    def get_ele(self):
        return self.elementName
    def to_string(self):
        return self.elementName + " : " + str(round(float(self.center), decimals=1))
    def get_output(self):
        return self.output
    def get_tcf(self):
        if self.delayed:
            return (1 - math.e ** (-1 * self.decayConstant * self.irrTime)) * math.e ** (-1 * self.decayConstant * self.waitTime) * (1 - math.e ** (-1 * self.decayConstant * self.countTime))
        else:
            return 1
    def get_results(self, area, areaStdev):
        if self.divisor == None:
            return [area/self.get_tcf(), areaStdev/self.get_tcf()]
        return [area/self.divisor/self.get_tcf(), areaStdev/self.divisor/self.get_tcf()]

def multiple_peak_and_background(peaks, background, x, params):
        y = np.zeros_like(x)
        leftCounter = 0
        rightCounter = background.get_num_params()
        y += background.get_ydata_with_params(x,params[leftCounter:rightCounter])
        
        for peak in peaks:
            leftCounter = rightCounter
            rightCounter = leftCounter + peak.get_num_params()
            y += peak.get_ydata_with_params(x,params[leftCounter:rightCounter])
            
        return y

def set_all_params(peaks, background, params, variances, reanalyze):
    leftCounter = 0
    rightCounter = background.get_num_params()

    noVars = (variances[0] == np.inf) or (variances[0] == -1 * np.inf)

    background.set_params(params[leftCounter:rightCounter])
    if not noVars:
        background.set_variances(variances[leftCounter:rightCounter])
    if not reanalyze:
        background.set_original_params(params[leftCounter:rightCounter])
        if not noVars:
            background.set_original_variances(variances[leftCounter:rightCounter])
    for peak in peaks:
        leftCounter = rightCounter
        rightCounter = leftCounter + peak.get_num_params()
        peak.set_params(params[leftCounter:rightCounter])
        if not noVars:
            peak.set_variances(variances[leftCounter:rightCounter])
        if not reanalyze:
            peak.set_original_params(params[leftCounter:rightCounter])
            if not noVars:
                peak.set_original_variances(variances[leftCounter:rightCounter])

def get_curve(peaks, background, x):
    y = np.zeros_like(x)
    y += background.get_ydata(x)
    for peak in peaks:
        y += peak.get_ydata(x)
    return list(y)


"""Functions to search for values in my data, used as utilities in many places. Modified binary search algorithm."""
def binary_search_find_nearest(l, e):
    upperBound = len(l)
    lowerBound = 0
    guess = (upperBound + lowerBound)//2
    if guess == 0:
        return guess
    if guess == 1:
        if abs(e - l[0]) < abs(e - l[1]):
            return 0
        return 1
        
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
def ivw_combine(meas, stdev = None, variance = None):
    var = None
    res = None
    if variance != None:
        var = 1/sum([1/v for v in variance])
        res = var * sum([m/v for m,v in zip(meas, variance)])
    else:
        var = 1/sum([1/s**2 for s in stdev])
        res = var * sum([m/s**2 for m,s in zip(meas, stdev)])
    return [res, var**.5]
