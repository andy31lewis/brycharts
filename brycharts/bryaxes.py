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
        canvas.scaledObjects.append(self)

class AxesWrappingTextObject(SVG.WrappingTextObject, ScaledObjectMixin):
    def __init__(self, canvas, string="", anchorpoint=(0,0), width=80, anchorposition=2, fontsize=12):
        super().__init__(canvas, string, anchorpoint, width/canvas.xScaleFactor, anchorposition, fontsize)
        self.anchorPoint = anchorpoint
        self.rescale(canvas)
        canvas.scaledObjects.append(self)

class AxesPoint(svg.circle, ScaledObjectMixin):
    def __init__(self, canvas, XY=(0,0), colour="black", objid=None):
        (x, y) = XY
        sf = canvas.scaleFactor
        svg.circle.__init__(self, cx=float(x), cy=y, r=3, style={"stroke":"#00000000", "stroke-width":5, "fill":colour, "vector-effect":"non-scaling-stroke"})
        self.anchorPoint = self.XY = SVG.Point(XY)
        self.rescale(canvas)
        if objid: self.id = objid
        canvas.scaledObjects.append(self)

    def _update(self):
        pass

class AxesPolyline(SVG.PolylineObject):
    def __init__(self, canvas, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None):
        super().__init__(pointlist, linecolour, linewidth, fillcolour, objid)
        #self.style.vectorEffect = "non-scaling-stroke"
        newobj = SVG.PolylineObject(pointlist, linecolour, linewidth, fillcolour, objid)
        newobj.style.strokeWidth = 6 if canvas.mouseDetected else 10
        newobj.style.opacity = 0
        for event in SVG.MOUSEEVENTS: newobj.bind(event, canvas._onHitTargetMouseEvent)
        for event in SVG.TOUCHEVENTS: newobj.bind(event, canvas._onHitTargetTouchEvent)
        newobj.reference = self
        self.hitTarget = newobj
        canvas.hittargets.append(newobj)
        canvas.attachObject(newobj)

class AxesLine(SVG.LineObject):
    def __init__(self, pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour="none", objid=None):
        super().__init__(pointlist, style, linecolour, linewidth, fillcolour, objid)
        self.style.vectorEffect = "non-scaling-stroke"

class AxesGroup(svg.g):
    def __init__(self, objlist=[], objid=None):
        svg.g.__init__(self)
        for obj in objlist: self.attach(obj)
        if objid: self.id = objid

class Axis(object):
    def __init__(self, Min, Max, label, fontsize=12,
                    scaleInterval=None, majorDivisor=None, minorDivisor=None,
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
            self.scaleInterval, self.majorDivisor, self.minorDivisor = gettimescaleintervals(self.min, self.max, mindivs)
        else:
            self.scaleInterval, self.majorDivisor, self.minorDivisor = getscaleintervals(self.min, self.max, mindivs)
        #print(self.scaleInterval, self.majorTickInterval, self.minorTickInterval)

class BasicAxis(AxesGroup):
    def __init__(self, canvas, axis):
        super().__init__()
        axismin, axismax = float(axis.min), float(axis.max)
        if axis.direction == "x":
            self.attach([AxesLine([(axismin, axis.position), (axismax, axis.position)]),
                         AxesTextObject(canvas, axis.label, (axismax, axis.position-3*axis.tickLength), 3, fontsize=axis.fontsize)])
            if axis.showArrow:
                self.attach([AxesLine([(axismax, axis.position), (axismax-axis.arrowLength, axis.position-axis.tickLength)]),
                             AxesLine([(axismax, axis.position), (axismax-axis.arrowLength, axis.position+axis.tickLength)])])
        else:
            self.attach([AxesLine([(axis.position, axismin), (axis.position, axismax)]),
                         AxesTextObject(canvas, axis.label, (axis.position, axismax), 7, fontsize=axis.fontsize)])
            if axis.showArrow:
                self.attach([AxesLine([(axis.position, axismax), (axis.position-axis.tickLength, axismax-axis.arrowLength)]),
                             AxesLine([(axis.position, axismax), (axis.position+axis.tickLength, axismax-axis.arrowLength)])])

class Ticks(AxesGroup):
    def __init__(self, axis, ticktype):
        values = axis.majorTickValues if ticktype == "major" else axis.minorTickValues
        ticklength = axis.tickLength if ticktype == "major" else axis.tickLength/2
        tickend = axis.position-ticklength
        super().__init__()
        for v in values:
            if axis.direction == "x":
                self.attach(AxesLine([(v, axis.position), (v, tickend)]))
            else:
                self.attach(AxesLine([(axis.position, v), (tickend, v)]))
        axis.axisObjects.attach(self)

class GridLines(AxesGroup):
    def __init__(self, axis, gridtype):
        values = axis.majorTickValues if gridtype == "major" else axis.minorTickValues
        linemin, linemax = axis.gridMin, axis.gridMax
        linestyle = "faintdash1" if gridtype == "major" else "faintdash2"
        super().__init__()
        for v in values:
            if axis.direction == "x":
                self.attach(AxesLine([(v, linemin), (v, linemax)], linestyle))
            else:
                self.attach(AxesLine([(linemin, v), (linemax, v)], linestyle))
        axis.axisObjects.attach(self)

class ScaleValues(AxesGroup):
    def __init__(self, canvas, axis):
        super().__init__()
        v = axis.min
        while v <= axis.max:
            v1 = float(v)
            if v1 != axis.omitScale:
                n = int(1-log10(axis.scaleInterval))
                scalestring=str(v) if axis.axisType=="time" else str(int(v)) if int(v) == v else f"{v:.{n}f}"
                if axis.direction == "x":
                    self.attach(AxesTextObject(canvas, scalestring, (v1, axis.position-axis.tickLength), 2, fontsize=12))
                else:
                    self.attach(AxesTextObject(canvas, scalestring, (axis.position-axis.tickLength, v1), 6, fontsize=12))
            v += axis.scaleInterval
        axis.axisObjects.attach(self)

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
        self.tooltip = None
        self.bestFit = None
        self.scaledObjects = []
        self.bind("touchstart", self.clearTooltip)
        self.bind("mousemove", self.onMouseMove)
        #print("set up axes", time.time()-tt)
        tt = time.time()

        self.drawAxes(xAxis, yAxis)
        #print("draw axes", time.time()-tt)
        tt = time.time()

    def attachObject(self, svgobject, fixed=False):
        if isinstance(svgobject, (AxesGroup, AxesLine, ScaledObjectMixin)):
            self.container.attach(svgobject)
        else:
            self.container.addObject(svgobject, fixed)

    def attachObjects(self, objectlist):
        for obj in objectlist:
            if isinstance(obj, (list, tuple)):
                self.attachObjects(obj)
            else:
                self.attachObject(obj)

    def removeObject(self, svgobject):
        self.container.removeChild(svgobject)
        if isinstance(svgobject, ScaledObjectMixin):
            self.scaledObjects.remove(svgobject)

    def rescaleObjects(self):
        #print(self.scaledObjects)
        for obj in self.scaledObjects:
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

    def clearTooltip(self, event):
        if event.target != self: return
        if self.tooltip: self.tooltip.hide()

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
        #tt = time.time()
        xmin, xmax, ymin, ymax = float(xAxis.min), float(xAxis.max), float(yAxis.min), float(yAxis.max)
        if xmax <= xmin or ymax <= ymin: return
        self.setViewBox([(xmin, -ymax), (xmax, -ymin)])
        (xAxis.direction, yAxis.direction) = ("x", "y")
        xAxis.tickLength = yAxis.arrowLength = 0.75*xAxis.fontsize*self.yScaleFactor
        yAxis.tickLength = xAxis.arrowLength = 0.75*yAxis.fontsize*self.xScaleFactor
        xAxis.position = ymin if ymin > 0 else ymax if ymax < 0 else 0
        yAxis.position = xmin if xmin > 0 else xmax if xmax < 0 else 0
        xAxis.omitScale = yAxis.position if yAxis.showAxis and ymin < xAxis.position else None
        yAxis.omitScale = xAxis.position if xAxis.showAxis and xmin < yAxis.position else None
        xAxis.gridMin, xAxis.gridMax = ymin, ymax
        yAxis.gridMin, yAxis.gridMax = xmin, xmax
        self.container.clear()

        for axis in [xAxis, yAxis]:
            if not axis.showAxis: continue
            axis.basicAxis = BasicAxis(self, axis)
            axis.axisObjects = AxesGroup(axis.basicAxis)

            axismin, axismax = float(axis.min), float(axis.max)
            majortickinterval = float(axis.scaleInterval)/axis.majorDivisor
            count = int(round((axismax - axismin)/majortickinterval))
            axis.majorTickValues = [axismin + i*majortickinterval for i in range(count+1)]
            if axis.showMinorTicks or axis.showMinorGrid:
                minortickinterval = majortickinterval/axis.minorDivisor
                count = count*axis.minorDivisor
                axis.minorTickValues = [axismin + i*minortickinterval for i in range(count+1) if i%axis.minorDivisor != 0]

            if axis.showMinorTicks and minortickinterval > 0.5*axis.arrowLength:
                axis.minorTicks = Ticks(axis, "minor")
            if axis.showMajorTicks:
                axis.majorTicks = Ticks(axis, "major")
            #print("x-axis lines", time.time()-tt)
            #tt = time.time()
            if axis.showScale:
                axis.scaleValues = ScaleValues(self, axis)
            #print("x-axis scale", time.time()-tt)
            #tt = time.time()

            if axis.showMinorGrid and minortickinterval > 0.5*axis.arrowLength:
                axis.minorGrid = GridLines(axis, "minor")
            if axis.showMajorGrid:
                axis.majorGrid = GridLines(axis, "major")

            self.attachObject(axis.axisObjects)
            #print("x-axis grid", time.time()-tt)

        self.xAxis = xAxis
        self.yAxis = yAxis
        if self.title:
            self.attachObject(AxesTextObject(self, self.title, ((xmin+xmax)/2, ymax+1.5*yAxis.fontsize*self.yScaleFactor), 8, yAxis.fontsize*1.25))
        self.fitContents()
