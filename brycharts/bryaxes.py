#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 1997-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# These programs are free software; you can redistribute it and/or modify it  #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #

#Routines connected with actually drawing the axes.

from .roundfns import *
from math import isnan, log10
from . import dragcanvas as SVG

class AxesTextObject(SVG.TextObject):
    def __init__(self, canvas, string="", anchorpoint=(0,0), anchorposition=1, fontsize=12):
        super().__init__(string, anchorpoint, anchorposition, fontsize)
        self.anchorPoint = (x, y) = anchorpoint
        #self.style.transform = f"translate({x}px,{y}px) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x}px,{-y}px)"
        self.attrs["transform"] = f"translate({x},{y}) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x},{-y})"

class AxesWrappingTextObject(SVG.WrappingTextObject):
    def __init__(self, canvas, string="", anchorpoint=(0,0), width, anchorposition=2, fontsize=12):
        super().__init__(canvas, string, anchorpoint, width/canvas.xScaleFactor, anchorposition, fontsize)
        self.anchorPoint = (x, y) = anchorpoint
        #self.style.transform = f"translate({x}px,{y}px) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x}px,{-y}px)"
        self.attrs["transform"] = f"translate({x},{y}) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x},{-y})"

class AxesPoint(SVG.PointObject):
    def __init__(self, canvas, XY=(0,0), colour="black", pointsize=2):
        super().__init__(XY, colour, pointsize)
        self.anchorPoint = (x, y) = XY
        self.attrs["transform"] = f"translate({x},{y}) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x},{-y})"

class Axis(object):
    def __init__(self, Min, Max, label, fontsize=12,
                    majorTickInterval=None, minorTickInterval=None, scaleInterval=None,
                    showScale=True, showMajorTicks=True, showMinorTicks=True, showMajorGrid=True, showMinorGrid=True,
                    showArrow=False, showAxis=True):
        self.min = float(Min)
        self.max = float(Max)
        self.label = label if label else ""
        self.fontsize = fontsize
        for argname in self.__init__.__code__.co_varnames[4:]:
            setattr(self, argname, locals()[argname])
        self.calculateDefaultTicks(5)
        self.min = rounddown(Min, self.scaleInterval)
        self.max = roundup(Max, self.scaleInterval)

    def calculateDefaultTicks(self, MinDivs):
        interval = self.max - self.min
        self.scaleInterval, ScaleBase = roundscale(interval, MinDivs)

        if ScaleBase == 1 or ScaleBase == 10:
            self.majorTickInterval = self.scaleInterval/2.0
            self.minorTickInterval = self.scaleInterval/10.0
        elif ScaleBase == 5:
            self.majorTickInterval = self.scaleInterval
            self.minorTickInterval = self.scaleInterval/5.0
        elif ScaleBase == 2:
            self.majorTickInterval = self.scaleInterval/2.0
            self.minorTickInterval = self.scaleInterval/10.0

class Ticks(SVG.GroupObject):
    def __init__(self, direction, ticktype, axis, omit=[]):
        gap = axis.majorTickInterval if ticktype == "major" else axis.minorTickInterval
        ticklength = axis.tickLength if ticktype == "major" else axis.tickLength/2
        ticks = []
        v = axis.min
        while v <= axis.max:
            if v not in omit:
                if direction == "x":
                    ticks.append(SVG.LineObject([(v, axis.position), (v,axis.position-ticklength)]))
                else:
                    ticks.append(SVG.LineObject([(axis.position, v), (axis.position-ticklength, v)]))
            v += gap
        super().__init__(ticks)

class GridLines(SVG.GroupObject):
    def __init__(self, direction, gridtype, axis, linemin, linemax, omit=[]):
        gap = axis.majorTickInterval if gridtype == "major" else axis.minorTickInterval
        linestyle = "faintdash1" if gridtype == "major" else "faintdash2"
        gridlines = []
        v = axis.min
        while v <= axis.max:
            if v not in omit:
                if direction == "x":
                    gridlines.append(SVG.LineObject([(v, linemin), (v, linemax)], linestyle))
                else:
                    gridlines.append(SVG.LineObject([(linemin, v), (linemax, v)], linestyle))
            v += gap
        super().__init__(gridlines)

class ScaleValues(SVG.GroupObject):
    def __init__(self, canvas, direction, axis, axispos, ticklength, omit=[]):
        scalevalues = []
        v = axis.min
        while v <= axis.max:
            r = round(v, 6)
            if r not in omit:
                n = int(1-log10(axis.scaleInterval))
                scalestring=str(int(v)) if int(r) == r else f"{v:.{n}f}"
                if direction == "x":
                    scalevalues.append(AxesTextObject(canvas, scalestring, (v, axispos-ticklength), 2, fontsize=12))
                else:
                    scalevalues.append(AxesTextObject(canvas, scalestring, (axispos-ticklength, v), 6, fontsize=12))
            v += axis.scaleInterval
        super().__init__(scalevalues)

class AxesCanvas(SVG.CanvasObject):
    def __init__(self, parent, width, height, xAxis=None, yAxis=None, objid=None):
        super().__init__(width, height, objid=objid)
        parent <= self
        self.attrs["preserveAspectRatio"] = "none"
        self.container = SVG.GroupObject(objid="panel")
        #self.container.style.transform = "scaleY(-1)"
        self.container.attrs["transform"] = "scale(1,-1)"
        self.addObject(self.container)
        self.mouseMode = SVG.MouseMode.PAN
        self.lineWidthScaling = False

        self.drawAxes(xAxis, yAxis)

    def attachObject(self, svgobject):
        self.container.addObject(svgobject)

    def attachObjects(self, objectlist):
        for obj in objectlist:
            if isinstance(obj, (list, tuple)):
                self.attachObjects(obj)
            else:
                self.container.addObject(obj)

    def fitContents(self):
        super().fitContents()
        for objid in self.objectDict:
            obj = self.objectDict[objid]
            if isinstance(obj, (AxesTextObject, AxesWrappingTextObject, AxesPoint)):
                (x, y) = obj.anchorPoint
                obj.attrs["transform"] = f"translate({x},{y}) scale({self.xScaleFactor},{-self.yScaleFactor}) translate({-x},{-y})"
        super().fitContents()

    def makeXScaleValue(self, x, y):
        """
        if param(xAxis,PiScaling)=1:
            ApproxDecimaltoFraction(x/3.14159,99,FracPi())
            if FracPi(0)=1:
                Numerator=""
            elif FracPi(0)=-1:
                Numerator="-"
            else:
                Numerator=CStr(FracPi(0))

            if FracPi(1)=1:
                Denominator=""
            else:
                Denominator="/" & CStr(FracPi(1))
                ScaleString=Numerator & "π" & Denominator
        else:
        """
        pass

    def drawAxes(self, xAxis, yAxis):
        if xAxis.max <= xAxis.min or yAxis.max <= yAxis.min: return
        self.setViewBox([(xAxis.min, yAxis.min), (xAxis.max, yAxis.max)])
        xAxis.tickLength = 10*self.yScaleFactor
        yAxis.tickLength = 10*self.xScaleFactor
        xAxis.position = yAxis.min if yAxis.min > 0 else yAxis.max if yAxis.max < 0 else 0
        yAxis.position = xAxis.min if xAxis.min > 0 else xAxis.max if xAxis.max < 0 else 0
        self.xAxis = xAxis
        self.yAxis = yAxis
        self.container.clear()

        if xAxis.showAxis:
            self.xAxisObjects = SVG.GroupObject([
                SVG.LineObject([(xAxis.min, xAxis.position), (xAxis.max, xAxis.position)]),
                AxesTextObject(self, xAxis.label, (xAxis.max, xAxis.position-xAxis.tickLength-1.5*xAxis.fontsize*self.yScaleFactor), 3, fontsize=xAxis.fontsize)
                ])
            if xAxis.showArrow:
                self.xAxisObjects.addObjects([
                    SVG.LineObject([(xAxis.max, xAxis.position), (xAxis.max-yAxis.tickLength, xAxis.position-xAxis.tickLength)]),
                    SVG.LineObject([(xAxis.max, xAxis.position), (xAxis.max-yAxis.tickLength, xAxis.position+xAxis.tickLength)])
                    ])

            if xAxis.showMinorTicks and xAxis.minorTickInterval/self.xScaleFactor>5:
                self.xAxisObjects.addObjects(Ticks("x", "minor", xAxis))
            if xAxis.showMajorTicks:
                self.xAxisObjects.addObjects(Ticks("x", "major", xAxis))
            if xAxis.showScale:
                omit = [yAxis.position] if yAxis.showAxis and yAxis.min < xAxis.position else []
                self.xAxisObjects.addObjects(ScaleValues(self, "x", xAxis, xAxis.position, xAxis.tickLength, omit))

            if xAxis.showMinorGrid and xAxis.minorTickInterval/self.xScaleFactor>5:
                omit = [yAxis.position] if yAxis.showAxis else []
                self.xAxisObjects.addObjects(GridLines("x", "minor", xAxis, yAxis.min, yAxis.max, omit))
            if xAxis.showMajorGrid:
                omit = [yAxis.position] if yAxis.showAxis else []
                self.xAxisObjects.addObjects(GridLines("x", "major", xAxis, yAxis.min, yAxis.max, omit))

            self.attachObject(self.xAxisObjects)

        if yAxis.showAxis:
            self.yAxisObjects = SVG.GroupObject([
                SVG.LineObject([(yAxis.position, yAxis.min), (yAxis.position, yAxis.max)]),
                AxesTextObject(self, yAxis.label, (yAxis.position, yAxis.max), 7, fontsize=yAxis.fontsize)
                ])
            if yAxis.showArrow:
                self.yAxisObjects.addObjects([
                    SVG.LineObject([(yAxis.position, yAxis.max), (yAxis.position-yAxis.tickLength, yAxis.max-xAxis.tickLength)]),
                    SVG.LineObject([(yAxis.position, yAxis.max), (yAxis.position+yAxis.tickLength, yAxis.max-xAxis.tickLength)])
                    ])

            if yAxis.showMinorTicks and yAxis.minorTickInterval/self.yScaleFactor>5:
                self.yAxisObjects.addObjects(Ticks("y", "minor", yAxis))
            if yAxis.showMajorTicks:
                self.yAxisObjects.addObjects(Ticks("y", "major", yAxis))
            if yAxis.showScale:
                omit = [xAxis.position] if xAxis.showAxis and xAxis.min < yAxis.position else []
                self.yAxisObjects.addObjects(ScaleValues(self, "y", yAxis, yAxis.position, yAxis.tickLength, omit))

            if yAxis.showMinorGrid and yAxis.minorTickInterval/self.yScaleFactor>5:
                omit = [xAxis.position] if xAxis.showAxis else []
                self.yAxisObjects.addObjects(GridLines("y", "minor", yAxis, xAxis.min, xAxis.max, omit))
            if yAxis.showMajorGrid:
                omit = [xAxis.position] if xAxis.showAxis else []
                self.yAxisObjects.addObjects(GridLines("y", "major", yAxis, xAxis.min, xAxis.max, omit))

            self.attachObject(self.yAxisObjects)
            self.fitContents()
