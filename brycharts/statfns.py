#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 1997-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #

from math import ceil, sqrt

def mean(values):
    return sum(values)/len(values)

def sum2(values):
    return sum(x*x for x in values)

def variance(values):
    return(sum2(values)/len(values) - mean(values)**2)

def stdev(values):
    return variance(values)**0.5

def percentileindex(p, n):
    x = n*p/100
    return (int(x), True) if x == int(x) else (int(x)+1, False)

def quartiles(values):
    values.sort()
    n = len(values)
    i, exact = percentileindex(25, n)
    Q1 = (values[i]+values[i+1])/2 if exact else values[i]
    i, exact = percentileindex(50, n)
    Q2 = (values[i]+values[i+1])/2 if exact else values[i]
    i, exact = percentileindex(75, n)
    Q3 = (values[i]+values[i+1])/2 if exact else values[i]
    return (Q1, Q2, Q3)

def regressioninfo(points):
    n = len(points)
    xvalues = [x[0] for x in points]
    yvalues = [x[1] for x in points]
    sx = sum(xvalues)
    sx2 = sum2(xvalues)
    Sxx = sx2 - sx*sx/n
    sy = sum(yvalues)
    sy2 = sum2(yvalues)
    Syy = sy2 - sy*sy/n
    sxy = sum(x*y for (x, y) in points)
    Sxy = sxy - sx*sy/n
    pmcc = Sxy/(Sxx*Syy)**0.5
    gradient = Sxy/Sxx
    yintercept = (sy - gradient*sx)/n
    return pmcc, gradient, yintercept

def convertifnumber(string):
    try:
        x = float(string)
    except ValueError:
        return string
    else:
        n = int(x)
        return n if n == x else x

if __name__=="__main__":
    points = [(164,6.5), (153,3), (163,4), (157,8), (161,5), (155,4), (168,4), (174,7), (167,6), (164,7), (159,3), (167,6)]
    pmcc, gradient, yintercept = regressioninfo(points)
    print(pmcc, gradient, yintercept)
