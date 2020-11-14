# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 11:43:52 2020

@author: chris
"""

from numpy import NaN, Inf, arange, asarray, array
import numpy as np


def peakdet(v, delta, x = None):
    """
    Peak finder
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    maxtab = []
    mintab = []
       
    if x is None:
        x = arange(len(v))
    
    v = asarray(v)
    
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    
    lookformax = True
    
    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return maxtab
def var_mul(e1, var1, e2, var2): #assume these are independent variables, and multiply their variances together
    return var1*var2 + e1**2*var2 + e2**2 *var1

class SpectrumParser:
    """Parser for SPE files"""
    def __init__(self, fname):
        self.fname = fname
        self.spectrumfile = open(fname)
    def getValues(self):
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
    def close(self):
        self.spectrumfile.close()
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
