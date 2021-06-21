#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 1997-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# For details, see the LICENSE file in this repository                        #

#Routines connected with actually drawing the axes.

import time
from math import log10
from . import dragcanvas as SVG
import browser.svg as svg
from .roundfns import *
from .timeclasses import *

class ScaledObjectMixin():
    def rescale(self, canvas):
        (x, y) = self.anchorPoint
        #self.style.transform = f"translate({x}px,{y}px) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x}px,{-y}px)"
        self.attrs["transform"] = f"translate({x},{y}) scale({canvas.xScaleFactor},{-canvas.yScaleFactor}) translate({-x},{-y})"

class AxesTextObject(SVG.TextObject, ScaledObjectMixin):
    def __init__(self, canvas, string="", anchorpoint=(0,0), anchorposition=1, fontsize=12):
        super().__init__(string, anchorpoint, anchorposition, fontsize)
        self.anchorPoint = anchorpoint
        self.rescale(canvas)

class AxesWrappingTextObject(SVG.WrappingTextObject, ScaledObjectMixin):
    def __init__(self, canvas, string="", anchorpoint=(0,0), width=80, anchorposition=2, fontsize=12):
        super().__init__(canvas, string, anchorpoint, width/canvas.xScaleFactor, anchorposition, fontsize)
        self.anchorPoint = anchorpoint
        self.rescale(canvas)

class AxesPoint(svg.circle, ScaledObjectMixin):
    def __init__(self, canvas, XY=(0,0), colour="black", objid=None):
        (x, y) = XY
        sf = canvas.scaleFactor
        svg.circle.__init__(self, cx=float(x), cy=y, r=3, style={"stroke":"#00000000", "stroke-width":5, "fill":colour, "vector-effect":"non-scaling-stroke"})
        self.anchorPoint = self.XY = SVG.Point(XY)
        self.rescale(canvas)
        if objid: self.id = objid

    def _update(self):
        pass

class AxesPolyline(SVG.PolylineObject):
    def __init__(self, canvas, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None):
        super().__init__(pointlist, linecolour, linewidth, fillcolour, objid)
        newobj = SVG.PolylineObject(pointlist, linecolour, linewidth, fillcolour, objid)
        newobj.style.strokeWidth = 6 if canvas.mouseDetected else 10
        newobj.style.opacity = 0.5
        for event in SVG.MOUSEEVENTS: newobj.bind(event, canvas._onHitTargetMouseEvent)
        for event in SVG.TOUCHEVENTS: newobj.bind(event, canvas._onHitTargetTouchEvent)
        newobj.reference = self
        self.hitTarget = newobj
        canvas.hittargets.append(newobj)
        canvas.attachObject(newobj)

class Axis(object):
    def __init__(self, Min, Max, label, fontsize=12,
                    majorTickInterval=None, minorTickInterval=None, scaleInterval=None,
                    showScale=True, showMajorTicks=True, showMinorTicks=True, showMajorGrid=True, showMinorGrid=True,
                    showArrow=False, showAxis=True, axisType="float"):
        self.min = Min
        self.max = Max
        self.label = label if label else ""
        self.fontsize = fontsize
        for argname in self.__init__.__code__.co_varnames[4:]:
            setattr(self, argname, locals()[argname])
        self.calculateDefaultTicks(5)
        self.min = roundtimedown(Min, self.scaleInterval) if self.axisType == "time" else rounddown(Min, self.scaleInterval)
        self.max = roundtimeup(Max, self.scaleInterval) if self.axisType == "time" else roundup(Max, self.scaleInterval)

    def calculateDefaultTicks(self, mindivs):
        if self.axisType == "time":
            self.scaleInterval, self.majorTickInterval, self.minorTickInterval = gettimescaleintervals(self.min, self.max, mindivs)
        else:
            self.scaleInterval, self.majorTickInterval, self.minorTickInterval = getscaleintervals(self.min, self.max, mindivs)
        #print(self.scaleInterval, self.majorTickInterval, self.minorTickInterval)

class Ticks(SVG.GroupObject):
    def __init__(self, direction, ticktype, axis, omit=[]):
        gap = axis.majorTickInterval if ticktype == "major" else axis.minorTickInterval
        ticklength = axis.tickLength if ticktype == "major" else axis.tickLength/2
        ticks = []
        v = axis.min
        while v <= axis.max:
            v1 = float(v)
            if v1 not in omit:
                if direction == "x":
                    ticks.append(SVG.LineObject([(v1, axis.position), (v1,axis.position-ticklength)]))
                else:
                    ticks.append(SVG.LineObject([(axis.position, v1), (axis.position-ticklength, v1)]))
            v += gap
        super().__init__(ticks)

class GridLines(SVG.GroupObject):
    def __init__(self, direction, gridtype, axis, linemin, linemax, omit=[]):
        gap = axis.majorTickInterval if gridtype == "major" else axis.minorTickInterval
        linestyle = "faintdash1" if gridtype == "major" else "faintdash2"
        gridlines = []
        v = axis.min
        while v <= axis.max:
            v1 = float(v)
            if v1 not in omit:
                if direction == "x":
                    gridlines.append(SVG.LineObject([(v1, linemin), (v1, linemax)], linestyle))
                else:
                    gridlines.append(SVG.LineObject([(linemin, v1), (linemax, v1)], linestyle))
            v += gap
        super().__init__(gridlines)

class ScaleValues(SVG.GroupObject):
    def __init__(self, canvas, direction, axis, axispos, ticklength, omit=[]):
        scalevalues = []
        v = axis.min
        while v <= axis.max:
            #r = round(v, 6)
            v1 = float(v)
            if v1 not in omit:
                n = int(1-log10(axis.scaleInterval))
                scalestring=str(v) if axis.axisType=="time" else str(int(v)) if int(v) == v else f"{v:.{n}f}"
                if direction == "x":
                    scalevalues.append(AxesTextObject(canvas, scalestring, (v1, axispos-ticklength), 2, fontsize=12))
                else:
                    scalevalues.append(AxesTextObject(canvas, scalestring, (axispos-ticklength, v1), 6, fontsize=12))
            v += axis.scaleInterval
        super().__init__(scalevalues)

class AxesCanvas(SVG.CanvasObject):
    def __init__(self, parent, width, height, xAxis=None, yAxis=None, title=None, objid=None):
        tt = time.time()
        super().__init__(width, height, objid=objid)
        parent <= self
        self.attrs["preserveAspectRatio"] = "none"
        self.container = SVG.GroupObject(objid="panel")
        #self.container.style.transform = "scaleY(-1)"
        self.container.attrs["transform"] = "scale(1,-1)"
        self.addObject(self.container)
        self.mouseMode = SVG.MouseMode.PAN
        self.lineWidthScaling = False
        self.title = title
        self.tooltips = []
        self.bestFit = None
        self.bind("touchstart", self.clearTooltips)
        self.bind("mousemove", self.onMouseMove)
        #print("set up axes", time.time()-tt)
        tt = time.time()

        self.drawAxes(xAxis, yAxis)
        #print("draw axes", time.time()-tt)
        tt = time.time()

    def attachObject(self, svgobject, fixed=False):
        self.container.addObject(svgobject, fixed)

    def attachObjects(self, objectlist):
        for obj in objectlist:
            if isinstance(obj, (list, tuple)):
                self.attachObjects(obj)
            else:
                self.container.addObject(obj)

    def rescaleObjects(self):
        #print("Using bryaxes rescaleObjects")
        for obj in self.objectDict.values():
            if isinstance(obj, ScaledObjectMixin):
                obj.rescale(self)

    def fitContents(self):
        if self.bestFit:
            self.setViewBox(self.bestFit)
            return self.bestFit
        else:
            super().fitContents()
            self.rescaleObjects()
            viewwindow = super().fitContents()
            return viewwindow

    def onMouseMove(self, event):
        if not self.mouseDetected:
            self.mouseDetected = True
            for obj in self.objectDict.values():
                if hasattr(obj, "reference"):
                    obj.style.strokeWidth = 6

    def clearTooltips(self, event):
        if event.target != self: return
        for tooltip in self.tooltips: tooltip.hide()

    """
    def makeXScaleValue(self, x, y):
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

    def drawAxes(self, xAxis, yAxis):
        #print("xAxis.min", xAxis.min, float(xAxis.min))
        tt = time.time()
        xmin, xmax, ymin, ymax = float(xAxis.min), float(xAxis.max), float(yAxis.min), float(yAxis.max)
        if xmax <= xmin or ymax <= ymin: return
        self.setViewBox([(xmin, -ymax), (xmax, -ymin)])
        xAxis.tickLength = 10*self.yScaleFactor
        yAxis.tickLength = 10*self.xScaleFactor
        xAxis.position = ymin if ymin > 0 else ymax if ymax < 0 else 0
        yAxis.position = xmin if xmin > 0 else xmax if xmax < 0 else 0
        self.xAxis = xAxis
        self.yAxis = yAxis
        self.container.clear()

        if xAxis.showAxis:
            self.xAxisObjects = SVG.GroupObject([
                SVG.LineObject([(xmin, xAxis.position), (xmax, xAxis.position)]),
                AxesTextObject(self, xAxis.label, (xmax, xAxis.position-xAxis.tickLength-1.5*xAxis.fontsize*self.yScaleFactor), 3, fontsize=xAxis.fontsize)
                ])
            if xAxis.showArrow:
                self.xAxisObjects.addObjects([
                    SVG.LineObject([(xmax, xAxis.position), (xmax-yAxis.tickLength, xAxis.position-xAxis.tickLength)]),
                    SVG.LineObject([(xmax, xAxis.position), (xmax-yAxis.tickLength, xAxis.position+xAxis.tickLength)])
                    ])

            if xAxis.showMinorTicks and float(xAxis.minorTickInterval)/self.xScaleFactor>5:
                self.xAxisObjects.addObjects(Ticks("x", "minor", xAxis))
            if xAxis.showMajorTicks:
                self.xAxisObjects.addObjects(Ticks("x", "major", xAxis))
            #print("x-axis lines", time.time()-tt)
            tt = time.time()
            if xAxis.showScale:
                omit = [yAxis.position] if yAxis.showAxis and ymin < xAxis.position else []
                self.xAxisObjects.addObjects(ScaleValues(self, "x", xAxis, xAxis.position, xAxis.tickLength, omit))
            #print("x-axis scale", time.time()-tt)
            tt = time.time()

            if xAxis.showMinorGrid and float(xAxis.minorTickInterval)/self.xScaleFactor>5:
                omit = [yAxis.position] if yAxis.showAxis else []
                self.xAxisObjects.addObjects(GridLines("x", "minor", xAxis, ymin, ymax, omit))
            if xAxis.showMajorGrid:
                omit = [yAxis.position] if yAxis.showAxis else []
                self.xAxisObjects.addObjects(GridLines("x", "major", xAxis, ymin, ymax, omit))

            self.attachObject(self.xAxisObjects, fixed=True)
        #print("x-axis grid", time.time()-tt)
        tt = time.time()

        if yAxis.showAxis:
            self.yAxisObjects = SVG.GroupObject([
                SVG.LineObject([(yAxis.position, ymin), (yAxis.position, ymax)]),
                AxesTextObject(self, yAxis.label, (yAxis.position, ymax), 7, fontsize=yAxis.fontsize)
                ])
            if yAxis.showArrow:
                self.yAxisObjects.addObjects([
                    SVG.LineObject([(yAxis.position, ymax), (yAxis.position-yAxis.tickLength, ymax-xAxis.tickLength)]),
                    SVG.LineObject([(yAxis.position, ymax), (yAxis.position+yAxis.tickLength, ymax-xAxis.tickLength)])
                    ])

            if yAxis.showMinorTicks and yAxis.minorTickInterval/self.yScaleFactor>5:
                self.yAxisObjects.addObjects(Ticks("y", "minor", yAxis))
            if yAxis.showMajorTicks:
                self.yAxisObjects.addObjects(Ticks("y", "major", yAxis))
            if yAxis.showScale:
                omit = [xAxis.position] if xAxis.showAxis and xmin < yAxis.position else []
                self.yAxisObjects.addObjects(ScaleValues(self, "y", yAxis, yAxis.position, yAxis.tickLength, omit))

            if yAxis.showMinorGrid and yAxis.minorTickInterval/self.yScaleFactor>5:
                omit = [xAxis.position] if xAxis.showAxis else []
                self.yAxisObjects.addObjects(GridLines("y", "minor", yAxis, xmin, xmax, omit))
            if yAxis.showMajorGrid:
                omit = [xAxis.position] if xAxis.showAxis else []
                self.yAxisObjects.addObjects(GridLines("y", "major", yAxis, xmin, xmax, omit))

            self.attachObject(self.yAxisObjects, fixed=True)
        if self.title:
            self.attachObject(AxesTextObject(self, self.title, ((xmin+xmax)/2, ymax+1.5*yAxis.fontsize*self.yScaleFactor), 8, yAxis.fontsize*1.25))
        self.fitContents()
        #print("y-axis", time.time()-tt)
        tt = time.time()
