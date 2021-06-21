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
from models import GaussianPeak, LinearBackground

class KnownPeak:
    def __init__(self, elementName, center, unit = "mg", sensitivity=None, mass=None):
        self.elementName = elementName
        self.center = center
        if sensitivity != None and mass != None:
            raise TypeError("Please provide no more than 1 of the following: mass, sensitivity")
        if mass != None:
            self.divisor = mass
            self.output = "Sensitivity ("+unit+")"
        elif sensitivity != None:
            self.divisor = sensitivity
            self.output = "Mass("+unit+")"
        else:
            self.divisor = None
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
    def set_divisor_output(self,divisor,output):
        self.divisor = divisor
        self.output = output

    def get_ctr(self):
        return self.center
    def get_ele(self):
        return self.elementName
    def get_output(self):
        return self.output
    def get_results(self, area, areaStdev):
        if self.divisor == None:
            raise TypeError("No Sensitivity or Mass was provided for known peak: "+str(self.center))
        return [area/self.divisor, areaStdev/self.divisor]

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

def set_all_params(peaks, background, params, variances):
    leftCounter = 0
    rightCounter = background.get_num_params()
    background.set_params(params[leftCounter:rightCounter])
    background.set_variances(variances[leftCounter:rightCounter])
    for peak in peaks:
        leftCounter = rightCounter
        rightCounter = leftCounter + peak.get_num_params()
        peak.set_params(params[leftCounter:rightCounter])
        peak.set_variances(variances[leftCounter:rightCounter])

def get_curve(peaks, background, x):
    y = np.zeros_like(x)
    y += background.get_ydata(x)
    for peak in peaks:
        y += peak.get_ydata(x)
    return y


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

som = {
    "backgrounds":
    {
        "linear":LinearBackground
    },
    "peaks":
    {
        "gaussian":GaussianPeak
    }
}
