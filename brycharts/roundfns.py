#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 1997-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# For details, see the LICENSE file in this repository                        #

import math

def sign(X):
    return math.copysign(1, X)

def roundUp (X, n):
    nn = math.copysign(10, X) if abs(n) > 10 else n
    p = 10**nn
    return int(X * p + 1) / p

def roundDown (X, n):
    nn = math.copysign(10, X) if abs(n) > 10 else n
    p = 10**nn
    return int(X * p) / p

def rounddown (x, n):
    return math.floor(x/n) * n

def roundup (x, n):
    return math.ceil(x/n) * n

def getscaleintervals (xmin, xmax, mindivs):
    interval = xmax - xmin
    if interval == 0: return 1, 1, 1
    if mindivs < 2: return interval, interval, interval
    X = interval/(mindivs - 1)
    L = 10**math.floor(math.log10(X))
    xx = X / L
    Y = 1 if xx<=2 else 2 if xx<=5 else 5 if xx<=10 else 10
    scaleinterval = Y * L
    if Y  in {1, 2, 10}:
        majordivisor, minordivisor = 2, 5
    elif Y == 5:
        majordivisor, minordivisor = 1, 5
    return scaleinterval, majordivisor, minordivisor

def roundsf2 (X, n):
    if X == 0:
        return 0
    else:
        L = float(10) ** math.floor(math.log10(abs(X)))
        xx = X / L
        return round(xx, n - 1) * L

def roundsf(x, sf=3):
    if x == 0: return 0
    xx = -x if x < 0 else x
    return round(x, sf-int(math.floor(math.log10(xx)))-1)

def linintx(ycoord, point1, point2):
    (x1, y1) = point1
    (x2, y2) = point2
    return (x1+(ycoord-y1)*(x2-x1)/(y2-y1), ycoord)

def lininty(xcoord, point1, point2):
    (x1, y1) = point1
    (x2, y2) = point2
    return (xcoord, y1+(xcoord-x1)*(y2-y1)/(x2-x1))

if __name__ == "__main__":
    for xmin, xmax, mindivs in [(0,100,5), (0,100,6), (0,273,7), (0,97, 6)]:
        print(xmax, mindivs, getscaleintervals(xmin, xmax, mindivs))
