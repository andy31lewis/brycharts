#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 1997-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# For details, see the LICENSE file in this repository                        #

import time
import json
from math import sin, cos, pi, log10, exp
from . import dragcanvas as SVG
from . import bryaxes
from .roundfns import *
from .statfns import *
import browser.svg as svg

DEFAULT_COLOURS = [f"hsl({a%360+22.5*(a//1080)},{(3-a//810)*100//3}%, 50%)" for a in range(0,2160,135)]
BARUNIT = 10


# Classes which provide the data structures needed as inputs for the graphs

class LabelledData(dict):
    def __init__(self, data, valueslabel):
       super().__init__(data)
       self.valuesLabel = valueslabel
       self.labels = list(self.keys())
       self.Values = list(self.values())
       self.maxValue = max(self.Values)
       self.total = sum(self.Values)
       self.percentages = [100*value/self.total for value in self.Values]

class LabelledDataDict(dict):
    def __init__(self, datadict, valueslabel):
        if not isinstance(next(iter(datadict.values())), LabelledData):
            datadict = {key:LabelledData(ld, valueslabel) for (key, ld) in datadict.items()}
        super().__init__(datadict)
        self.maxValue = max(ld.maxValue for ld in self.values())
        self.valuesLabel = valueslabel
        labels = set()
        for ld in self.values(): labels.update(ld.keys())
        self.labels = list(labels)
        self.Values = {label:[] for label in self.labels}
        self.sums = {label:[0] for label in self.labels}
        for label in self.labels:
            for ld in self.values():
                value = ld.get(label, 0)
                self.Values[label].append(value)
                self.sums[label].append(self.sums[label][-1] + value)
        self.maxSum = max(sums[-1] for sums in self.sums.values())

class FrequencyData(LabelledData):
    def __init__(self, data=None, rawdata=None, valueslabel="Frequency"):
        if rawdata:
            data = self.fromRawData(rawdata)
        super().__init__(data, valueslabel)

    def fromRawData(self, rawdata):
        #return sorted(Counter(rawdata).items())
        counter = {}
        for x in rawdata:
            if x in counter:
                counter[x] += 1
            else:
                counter[x] = 1
        return sorted(counter.items())

class FrequencyDataDict(LabelledDataDict):
    def __init__(self, datadict=None, rawdatadict=None, valueslabel="Frequency"):
        if rawdatadict:
            fdd = {key:FrequencyData(rawdata=rawdata, valueslabel=valueslabel) for (key, rawdata) in rawdatadict.items()}
        else:
            fdd = {key:FrequencyData(data=data, valueslabel=valueslabel) for (key, data) in datadict.items()}
        super().__init__(fdd, valueslabel)

class PairedData(list):
    def __init__(self, xlabel, ylabel, data):
        super().__init__(data)
        self.xLabel = xlabel
        self.yLabel = ylabel
        self.xValues = [item[0] for item in data]
        self.yValues = [item[1] for item in data]
        self.xMin, self.xMax = min(self.xValues), max(self.xValues)
        self.yMin, self.yMax = min(self.yValues), max(self.yValues)

class TimeSeriesData(PairedData):
    def __init__(self, xlabel, ylabel, data):
        if bryaxes.TimeCoord.startfloat == 0:
            x0 = min(x for (x, y) in data)
            x1 = max(x for (x, y) in data)
            bryaxes.TimeCoord.startfloat = 2*x0.timestamp() - x1.timestamp()
            hours = round((x1.timestamp()-x0.timestamp())/3600)
            bryaxes.TimeCoord.scalefloat = hours if hours > 0 else 1
            bryaxes.TimeCoord.defaultformat = "%H:%M:%S" if hours < 5 else "%H:%M" if hours < 24 else "%d/%m %H:%M" if hours < 840 else "%d/%m/%y"
        data = [(bryaxes.TimeCoord(x), y) for (x, y) in data]
        super().__init__(xlabel, ylabel, data)

class PairedDataDict(dict):
    def __init__(self, xlabel, ylabel, datadict):
        pdd = {key:PairedData(xlabel, ylabel, pd) for (key, pd) in datadict.items()}
        super().__init__(pdd)
        self.xLabel = xlabel
        self.yLabel = ylabel
        self.xMin = min(pd.xMin for pd in pdd.values())
        self.xMax = max(pd.xMax for pd in pdd.values())
        self.yMin = min(pd.yMin for pd in pdd.values())
        self.yMax = max(pd.yMax for pd in pdd.values())

class TimeSeriesDataDict(dict):
    def __init__(self, xlabel, ylabel, datadict):
        x0 = min(x for data in datadict.values() for (x, y) in data)
        x1 = max(x for data in datadict.values() for (x, y) in data)
        bryaxes.TimeCoord.startfloat = 2*x0.timestamp() - x1.timestamp()
        hours = round((x1.timestamp()-x0.timestamp())/3600)
        bryaxes.TimeCoord.scalefloat = hours if hours > 0 else 1
        bryaxes.TimeCoord.defaultformat = "%H:%M:%S" if hours < 5 else "%H:%M" if hours < 24 else "%d/%m %H:%M" if hours < 840 else "%d/%m/%y"
        pdd = {key:TimeSeriesData(xlabel, ylabel, pd) for (key, pd) in datadict.items()}
        super().__init__(pdd)
        self.xLabel = xlabel
        self.yLabel = ylabel
        self.xMin = min(pd.xMin for pd in pdd.values())
        self.xMax = max(pd.xMax for pd in pdd.values())
        self.yMin = min(pd.yMin for pd in pdd.values())
        self.yMax = max(pd.yMax for pd in pdd.values())

class LabelledPairedData(dict):
    def __init__(self, xlabel, ylabel, data):
        super().__init__(data)
        self.xLabel = xlabel
        self.yLabel = ylabel
        self.xValues = [item[0] for item in data.values()]
        self.yValues = [item[1] for item in data.values()]
        self.xMin, self.xMax = min(self.xValues), max(self.xValues)
        self.yMin, self.yMax = min(self.yValues), max(self.yValues)

class LabelledPairedDataDict(dict):
    def __init__(self, xlabel, ylabel, datadict):
        lpdd = {key:LabelledPairedData(xlabel, ylabel, lpd) for (key, lpd) in datadict.items()}
        super().__init__(lpdd)
        self.xLabel = xlabel
        self.yLabel = ylabel
        self.xMin = min(lpd.xMin for lpd in lpdd.values())
        self.xMax = max(lpd.xMax for lpd in lpdd.values())
        self.yMin = min(lpd.yMin for lpd in lpdd.values())
        self.yMax = max(lpd.yMax for lpd in lpdd.values())

class BoxPlotData(list):
    def __init__(self, valueslabel, boxplotdata=None, rawdata=None):
        if rawdata:
            Q1, Q2, Q3 = quartiles(rawdata)
            boxplotdata = [min(rawdata), Q1, Q2, Q3, max(rawdata)]
        super().__init__(boxplotdata)
        self.valuesLabel = valueslabel
        self.xMin = self[0]
        self.xMax = self[-1]

class BoxPlotDataDict(dict):
    def __init__(self, valueslabel, boxplotdatadict=None, rawdatadict=None):
        if rawdatadict:
            boxplotdatadict = {}
            for key, rawdata in rawdatadict.items():
                boxplotdatadict[key] = BoxPlotData(valueslabel, rawdata=rawdata)
        else:
            boxplotdatadict = {key:BoxPlotData(valueslabel, boxplotdata) for key, boxplotdata in boxplotdatadict.items()}
        super().__init__(boxplotdatadict)
        self.xMin = min(bpd.xMin for bpd in self.values())
        self.xMax = max(bpd.xMax for bpd in self.values())
        self.valuesLabel = valueslabel

class GroupedFrequencyData(list):
    def __init__(self, valueslabel, data=None, rawdata=None, boundaries=None, classwidth=None):
        if data:
            (b, f) = data[-1]
            if f != 0: data.append((2*b - data[-2][0], 0))
        else:
            datamin, datamax = min(rawdata), max(rawdata)
            if not boundaries:
                if not classwidth: classwidth, _, _ = getscaleintervals(datamin, datamax, 5)
                minboundary = rounddown(datamin, classwidth)
                maxboundary = roundup(datamax, classwidth)
                boundaries =  [minboundary]
                while boundaries[-1] < maxboundary: boundaries.append(boundaries[-1] + classwidth)
            else:
                if datamin < boundaries[0]:
                    classwidth = boundaries[1] - boundaries[0]
                    boundaries.insert(0, rounddown(datamin, classwidth))
                if datamax > boundaries[-1]:
                    classwidth = boundaries[-1] - boundaries[-2]
                    boundaries.append(roundup(datamax, classwidth))
            data = self.fromRawData(rawdata, boundaries)
        super().__init__(data)
        self.boundaries = [item[0] for item in data]
        self.frequencies = [item[1] for item in data]
        self.xMin, self.xMax = self.boundaries[0], self.boundaries[-1]
        self.maxFrequency = max(self.frequencies)
        self.frequencyDensities = []
        for i in range(len(self.boundaries)-1):
            self.frequencyDensities.append(self.frequencies[i]/(self.boundaries[i+1]-self.boundaries[i]))
        self.maxFrequencyDensity = max(self.frequencyDensities)
        self.valuesLabel = valueslabel
        #print("Means", mean(rawdata), self.mean())
        #print("Variances", variance(rawdata), self.variance())

    def fromRawData(self, rawdata, boundaries):
        L = len(boundaries)
        frequencies = [0] * L
        for value in rawdata:
            for i in range(L):
                if value < boundaries[i+1]:
                    frequencies[i] += 1
                    break
        return list(zip(boundaries, frequencies))

    def mean(self):
        self.midpoints = [(self[i][0] + self[i+1][0])/2 for i in range(len(self)-1)]
        sumfx = sum(x*f for (x, f) in zip(self.midpoints, self.frequencies[:-1]))
        sumf = sum(self.frequencies)
        return sumfx/sumf

    def variance(self):
        m = self.mean()
        sumfx2 = sum(x*x*f for (x, f) in zip(self.midpoints, self.frequencies[:-1]))
        sumf = sum(self.frequencies)
        return sumfx2/sumf - m*m

class GroupedFrequencyDataDict(dict):
    def __init__(self, valueslabel, datadict=None, rawdatadict=None, boundaries=None, classwidth=None):
        if rawdatadict:
            gfdd = {}
            for key, rawdata in rawdatadict.items():
                gfdd[key] = GroupedFrequencyData(valueslabel, rawdata=rawdata, boundaries=boundaries, classwidth=classwidth)
        else:
            gfdd = {key:GroupedFrequencyData(valueslabel, gfd) for key, gfd in datadict.items()}
        super().__init__(gfdd)
        self.xMin = min(gfd.xMin for gfd in self.values())
        self.xMax = max(gfd.xMax for gfd in self.values())
        self.maxFrequency = max(gfd.maxFrequency for gfd in self.values())
        self.maxFrequencyDensity = max(gfd.maxFrequencyDensity for gfd in self.values())
        self.valuesLabel = valueslabel

class CumulativeFrequencyData(list):
    def __init__(self, valueslabel, cumfreqdata=None, groupedfreqdata=None, rawdata=None, boundaries=None, classwidth=None):
        if rawdata:
            groupedfreqdata = GroupedFrequencyData(valueslabel=valueslabel, rawdata=rawdata, boundaries=boundaries, classwidth=classwidth)
        if groupedfreqdata:
            cumfreqdata = self.fromGFD(groupedfreqdata)
        else:
            (b, f) = cumfreqdata[0]
            if f != 0: cumfreqdata.insert(0, (2*b - cft[1][0], 0))
        super().__init__(cumfreqdata)
        self.boundaries = [item[0] for item in cumfreqdata]
        self.cumfrequencies = [item[1] for item in cumfreqdata]
        self.xMin, self.xMax = self.boundaries[0], self.boundaries[-1]
        self.totalFrequency = self.cumfrequencies[-1]
        self.valuesLabel = valueslabel

    def fromGFD(self, groupedfreqdata):
        (b, f) = groupedfreqdata[-1]
        if f != 0: groupedfreqdata.append((2*b - groupedfreqdata[-2][0], 0))
        L = len(groupedfreqdata)
        boundaries, frequencies = zip(*groupedfreqdata)
        cumfrequencies = [0] * L
        for i in range(1, L):
            cumfrequencies[i] = cumfrequencies[i-1] + frequencies[i-1]
        return list(zip(boundaries, cumfrequencies))

class CumulativeFrequencyDataDict(dict):
    def __init__(self, valueslabel, cfdatadict=None, gfdatadict=None, rawdatadict=None, boundaries=None, classwidth=None):
        if rawdatadict:
            cfdd = {}
            for key, rawdata in rawdatadict.items():
                cfdd[key] = CumulativeFrequencyData(valueslabel, rawdata=rawdata, boundaries=boundaries, classwidth=classwidth)
        elif gfdatadict:
            cfdd = {key:CumulativeFrequencyData(valueslabel, groupedfreqdata=gfd) for key, gfd in gfdatadict.items()}
        else:
            cfdd = {key:CumulativeFrequencyData(valueslabel, cfd) for key, cfd in cfdatadict.items()}
        super().__init__(cfdd)
        self.xMin = min(cfd.xMin for cfd in self.values())
        self.xMax = max(cfd.xMax for cfd in self.values())
        self.maxTotalFrequency = max(cfd.totalFrequency for cfd in self.values())
        self.valuesLabel = valueslabel

# Classes which provide the charts

class PieChart(SVG.CanvasObject):
    def __init__(self, parent, data, title="", colours=None, usekey=True, fontsize=14, width="95%", height="95%", objid=None):
        super().__init__(width, height, objid=objid)
        parent <= self
        self.tooltip = None
        if not colours: colours = DEFAULT_COLOURS
        if not usekey:
            D = data.items()
            n = len(D)
            L = sorted(D, key = lambda x:x[1])
            M = []
            for pair in zip(L[n//2:], L[:n//2]): M.extend(pair)
            if n%2 == 1: M.append(L[-1])
            data = LabelledData(M, data.valuesLabel)
        angles = [0]
        for percentage in data.percentages:
            angles.append(angles[-1] + percentage*3.6)
        self.sectors = [PieChartSector(self, (0,0), 100, angles[i], angles[i+1], data.labels[i], data.Values[i], data.percentages[i], colours[i]) for i in range(len(angles)-1)]
        self.addObjects(self.sectors)
        self.fitContents()
        self.mouseMode = SVG.MouseMode.PAN
        self.bind("touchstart", self.clearTooltip)

        if usekey:
            keysize = fontsize*1.25
            keypos = SVG.Point((140, -len(data.labels)*keysize/2))
            for i, label in enumerate(data.labels):
                self.addObject(SVG.GroupObject([
                    SVG.RectangleObject([keypos, keypos+(fontsize,fontsize)], fillcolour=colours[i]),
                    SVG.TextObject(label, keypos+(keysize,fontsize/2), anchorposition=4, fontsize=fontsize)
                    ]))
                keypos += (0,keysize)
            titlepos = (120, -110)
        else:
            anchorpositions = [7, 4, 1, 3, 6, 9]
            for i, label in enumerate(data.labels):
                anglepos = (angles[i] + angles[i+1]) / 2
                anchorposition = anchorpositions[int(anglepos//60)]
                anchorpoint = (105*sin(anglepos*pi/180), -105*cos(anglepos*pi/180))
                self.addObject(SVG.TextObject(label, anchorpoint, anchorposition, fontsize=fontsize))
            titlepos = (0, -130)
        if title: self.addObject(SVG.TextObject(title, titlepos, anchorposition=8, fontsize=fontsize*1.25))
        self.fitContents()

    def clearTooltip(self, event):
        if event.target != self: return
        if self.tooltip: self.tooltip.hide()

class BarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", direction="vertical", colour="yellow", fontsize=14, width="95%", height="95%", objid=None):
        xaxis = bryaxes.Axis(0, BARUNIT*len(data), label=None, showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, data.maxValue, data.valuesLabel)
        if direction == "horizontal": xaxis, yaxis = yaxis, xaxis
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        self.attachObject(Bars(self, data, direction=direction, colour=colour))
        for i in range(len(data)):
            if direction == "horizontal":
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], (-10*self.xScaleFactor, (i+0.6)*BARUNIT), 80, anchorposition=6, fontsize=fontsize)
            else:
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], ((i+0.6)*BARUNIT, 0), 0.8*BARUNIT, fontsize=fontsize)
            self.attachObject(label)
        self.fitContents()

class StackedBarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", direction="vertical", colours=None, fontsize=14, width="95%", height="95%", objid=None):
        if not colours: colours = DEFAULT_COLOURS
        xaxis = bryaxes.Axis(0, BARUNIT*len(data.labels), label="", showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, data.maxSum, data.valuesLabel)
        if direction == "horizontal": xaxis, yaxis = yaxis, xaxis
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        for i, key in enumerate(data.keys()):
            self.attachObject(Bars(self, data, "stacked", i, key, direction, colours[i]))
        for i in range(len(data.labels)):
            if direction == "horizontal":
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], (-10*self.xScaleFactor, (i+0.6)*BARUNIT), 80, anchorposition=6, fontsize=fontsize)
            else:
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], ((i+0.6)*BARUNIT, 0), 0.8*BARUNIT, fontsize=fontsize)
            self.attachObject(label)
        keywidth = 20*self.xScaleFactor
        keyheight = fontsize*2*self.yScaleFactor
        keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.min+keyheight))
        for i, key in enumerate(data.keys()):
            self.attachObject(SVG.GroupObject([
                SVG.RectangleObject([keypos, keypos+(keywidth,keyheight/2)], fillcolour=colours[i]),
                bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=7, fontsize=fontsize)
                ]))
            keypos += (0, keyheight)
        self.bestFit = self.fitContents()

class GroupedBarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", direction="vertical", colours=None, fontsize=14, width="95%", height="95%", objid=None):
        if not colours: colours = DEFAULT_COLOURS
        xaxis = bryaxes.Axis(0, BARUNIT*len(data.labels), label="", showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, data.maxValue, data.valuesLabel)
        if direction == "horizontal": xaxis, yaxis = yaxis, xaxis
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        for i, key in enumerate(data.keys()):
            self.attachObject(Bars(self, data, "grouped", i, key, direction, colours[i]))
        for i in range(len(data.labels)):
            if direction == "horizontal":
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], (-10*self.xScaleFactor, (i+0.6)*BARUNIT), 80, anchorposition=6, fontsize=fontsize)
            else:
                label = bryaxes.AxesWrappingTextObject(self, data.labels[i], ((i+0.6)*BARUNIT, 0), 0.8*BARUNIT, fontsize=fontsize)
            self.attachObject(label)
        keywidth = 20*self.xScaleFactor
        keyheight = fontsize*2*self.yScaleFactor
        keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.min+keyheight))
        for i, key in enumerate(data.keys()):
            self.attachObject(SVG.GroupObject([
                SVG.RectangleObject([keypos, keypos+(keywidth,keyheight/2)], fillcolour=colours[i]),
                bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=7, fontsize=fontsize)
                ]))
            keypos += (0, keyheight)
        self.bestFit = self.fitContents()

class ScatterGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colour="red", showregressionline=False, fontsize=14, width="95%", height="95%", objid=None):
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.xLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(data.yMin, data.yMax, data.yLabel, showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        if showregressionline:
            self.regressionLine = RegressionLine(self, data)
            self.attachObject(self.regressionLine)
        if isinstance(data, LabelledPairedData):
            self.dataPoints = [DataPoint(self, label, coords, colour) for (label, coords) in data.items()]
        else:
            self.dataPoints = [DataPoint(self, None, coords, colour) for coords in data]
        self.container.attach(self.dataPoints)

class BasicScatterGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colour="red", showregressionline=False, fontsize=14, width="95%", height="95%", objid=None):
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.xLabel, showMajorGrid=True, showMinorGrid=False)
        yaxis = bryaxes.Axis(data.yMin, data.yMax, data.yLabel, showMajorGrid=True, showMinorGrid=False)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        if showregressionline:
            self.regressionLine = RegressionLine(self, data)
            self.attachObject(self.regressionLine)
        if isinstance(data, LabelledPairedData):
            data = data.values()
        basepoint = svg.circle(cx=0, cy=0, r=3, fill=colour, stroke="none")
        self.dataPoints = []
        for (x, y) in data:
            point = basepoint.cloneNode(True)
            (point.attrs["cx"], point.attrs["cy"]) = (x, y)
            point.attrs["transform"] = f"translate({x},{y}) scale({self.xScaleFactor},{-self.yScaleFactor}) translate({-x},{-y})"
            self.dataPoints.append(point)
        self.container.attach(self.dataPoints)

class MultiScatterGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colours=None, showregressionlines=False, fontsize=14, width="95%", height="95%", objid=None):
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.xLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(data.yMin, data.yMax, data.yLabel, showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        if not colours: colours = DEFAULT_COLOURS
        if showregressionlines==True: showregressionlines = [True]*len(data)
        if showregressionlines==False: showregressionlines = [False]*len(data)
        for i, (key, dataset) in enumerate(data.items()):
            if showregressionlines[i]:
                self.regressionLine = RegressionLine(self, dataset, colours[i])
                self.attachObject(self.regressionLine)
            if isinstance(dataset, LabelledPairedData):
                self.dataPoints = [DataPoint(self, label, coords, colours[i]) for (label, coords) in dataset.items()]
            else:
                self.dataPoints = [DataPoint(self, None, coords, colours[i]) for coords in dataset]
            self.container.attach(self.dataPoints)
        keywidth = 20*self.xScaleFactor
        keyheight = fontsize*2*self.yScaleFactor
        keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.min+keyheight))
        for i, key in enumerate(data.keys()):
            self.attachObject(SVG.GroupObject([
                SVG.EllipseObject(pointlist=[keypos, keypos+(keywidth,keyheight/2)], fillcolour=colours[i]),
                bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=7, fontsize=fontsize)
                ]))
            keypos += (0, keyheight)
        self.bestFit = self.fitContents()

class LineGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colours=None, fontsize=14, width="95%", height="95%", objid=None):
        tt = time.time()
        xaxistype = "time" if isinstance(data, (TimeSeriesData, TimeSeriesDataDict)) else "float"
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.xLabel, showMajorGrid=True, showMinorGrid=False, axisType=xaxistype)
        yaxis = bryaxes.Axis(data.yMin, data.yMax, data.yLabel, showMajorGrid=True, showMinorGrid=False)
        #print("axes", time.time()-tt)
        tt = time.time()
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        #print("canvas", time.time()-tt)
        tt = time.time()
        if not colours: colours = DEFAULT_COLOURS
        if isinstance(data, PairedData):
            coordslist = [(float(x), y) for (x, y) in data]
            self.attachObject(SVG.PolylineObject(coordslist, linecolour=colours[0]))
        else:
            keywidth = 20*self.xScaleFactor
            keyheight = fontsize*2*self.yScaleFactor
            keypos = SVG.Point((float(self.xAxis.max) + keywidth, self.yAxis.max))
            keydata = []
            for i, (key, pd) in enumerate(data.items()):
                coordslist = [(float(x), y) for (x, y) in pd]
                self.attachObject(SVG.PolylineObject(coordslist, linecolour=colours[i], linewidth=2))
                self.attachObjects([DataPoint(self, key, coords, colours[i]) for coords in pd])
                keydata.append((coordslist[-1][1], key, colours[i]))
            keydata.sort(key = lambda x: -x[0])
            for (_, key, colour) in keydata:
                self.attachObject(SVG.GroupObject([
                    SVG.LineObject([keypos, keypos+(keywidth,0)], linecolour=colour, linewidth=2),
                    bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=4, fontsize=fontsize)
                    ]))
                keypos += (0, -keyheight)
            self.bestFit = self.fitContents()
        #print("lines", time.time()-tt)
        tt = time.time()

class BoxPlotCanvas(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colour="yellow", fontsize=14, width="95%", height="95%", objid=None):
        if isinstance(data, BoxPlotData): data = BoxPlotDataDict(data.valuesLabel, {"":data})
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.valuesLabel)
        yaxis = bryaxes.Axis(0, 50*len(data), "", showAxis=False, showMajorTicks=False, showMinorTicks=False)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        self.fitContents()
        yheight = 25
        for label, boxplotdata in data.items():
            self.attachObject(BoxPlot(boxplotdata, label, yheight, colour))
            if label: self.attachObject(bryaxes.AxesWrappingTextObject(self, label, (xaxis.min-10*self.xScaleFactor, yheight), 100, 6, fontsize))
            yheight += 50
        self.bestFit = self.fitContents()

class Histogram(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", shownormalcurve=False, colour="yellow", fontsize=14, width="95%", height="95%", objid=None):
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.valuesLabel)
        yaxis = bryaxes.Axis(0, data.maxFrequencyDensity, "Frequency density")
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        self.attachObject(HistogramBars(data, colour))
        if shownormalcurve:
            self.attachObject(NormalCurve(self, data))

class CumulativeFrequencyGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colours=None, fontsize=14, width="95%", height="95%", objid=None):
        if isinstance(data, CumulativeFrequencyData): data = CumulativeFrequencyDataDict(data.valuesLabel, {"":data})
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.valuesLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(0, data.maxTotalFrequency, "Cumulative frequency", showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        if not colours: colours = DEFAULT_COLOURS
        for i, (key, cfd) in enumerate(data.items()):
            self.attachObject(CumulativeFrequencyLine(self, key, cfd, colours[i]))
        if len(data) > 1:
            keywidth = 20*self.xScaleFactor
            keyheight = fontsize*2*self.yScaleFactor
            keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.max))
            for i, key in enumerate(data.keys()):
                self.attachObject(SVG.GroupObject([
                    SVG.LineObject([keypos, keypos+(keywidth,0)], linecolour=colours[i], linewidth=2),
                    bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=4, fontsize=fontsize)
                    ]))
                keypos += (0, -keyheight)
            self.bestFit = self.fitContents()

class CumulativePercentageGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", colours=None, fontsize=14, width="95%", height="95%", objid=None):
        if isinstance(data, CumulativeFrequencyData): data = CumulativeFrequencyDataDict(data.valuesLabel, {"":data})
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.valuesLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(0, 100, "Cumulative percentage", showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        if not colours: colours = DEFAULT_COLOURS
        for i, (key, cfd) in enumerate(data.items()):
            self.attachObject(CumulativePercentageLine(self, key, cfd, colours[i]))
        if len(data) > 1:
            keywidth = 20*self.xScaleFactor
            keyheight = fontsize*2*self.yScaleFactor
            keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.max))
            for i, key in enumerate(data.keys()):
                self.attachObject(SVG.GroupObject([
                    SVG.LineObject([keypos, keypos+(keywidth,0)], linecolour=colours[i], linewidth=2),
                    bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=4, fontsize=fontsize)
                    ]))
                keypos += (0, -keyheight)
            self.bestFit = self.fitContents()

# Utility classes not needed by end users

class PieChartSector(SVG.SectorObject):
    def __init__(self, canvas, centre, radius, startangle, endangle, label, value, percentage, colour):
        super().__init__(centre, radius, startangle, endangle, fillcolour=colour)
        self.canvas = canvas
        self.centre = (self.pointList[0] + self.pointList[1] + self.pointList[2])/3
        self.tooltiptext = f"{label}\n{value} ({percentage:.2f}%)"
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        self.canvas.tooltip = Tooltip(self.canvas, self.tooltiptext, self.centre)

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class Tooltip(SVG.TextObject):
    def __init__(self, canvas, text, coords):
        super().__init__(text, coords, anchorposition=5)
        self.canvas = canvas
        self.coords = coords
        self._background = None
        self.style.pointerEvents = "none"
        self.canvas.addObject(self)
        self.setBackground()
        self.canvas <= self

    def setBackground(self):
        bbox = self.getBBox()
        width, height = bbox.width, bbox.height
        x, y = self.coords
        self._background  = SVG.RectangleObject([(x-width/2, y-height/2), (x+width/2, y+height/2)], linecolour="#d3d3d3d0", fillcolour="#d3d3d3d0")
        self.canvas.addObject(self._background)
        self._background.style.pointerEvents = "none"

    def hide(self):
        self.canvas.deleteObject(self._background)
        self.canvas.deleteObject(self)
        self.canvas.tooltip = None

class AxesTooltip(bryaxes.AxesTextObject):
    def __init__(self, canvas, text, coords):
        super().__init__(canvas, text, coords, anchorposition=8)
        self.canvas = canvas
        self.coords = coords
        self._background = None
        self.style.pointerEvents = "none"
        self.canvas.attachObject(self)
        self.setBackground()
        self.canvas.container <= self

    def setBackground(self):
        bbox = self.getBBox()
        width, height = bbox.width*self.canvas.xScaleFactor, bbox.height*self.canvas.yScaleFactor
        x, y = self.coords
        self._background  = SVG.RectangleObject([(x-width/2, y+height), (x+width/2, y)], linecolour="#d3d3d3d0", fillcolour="#d3d3d3d0")
        self.canvas.attachObject(self._background)
        self._background.style.pointerEvents = "none"

    def hide(self):
        self.canvas.removeObject(self._background)
        self.canvas.removeObject(self)
        self.canvas.tooltip = None

class Bar(SVG.RectangleObject):
    def __init__(self, canvas, pointlist, key, value, direction="vertical", colour="yellow"):
        if direction == "horizontal": pointlist = [(y, x) for (x, y) in pointlist]
        super().__init__(pointlist, fillcolour=colour)
        self.canvas = canvas
        self.tooltiptext = f"{key}\n{value}" if key else f"{value}"
        self.centre = (self.pointList[0] + self.pointList[1])/2
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, self.centre)

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class Bars(SVG.GroupObject):
    def __init__(self, canvas, data, graphtype=None, index=None, key=None, direction="vertical", colour="yellow"):
        super().__init__()
        if graphtype == "stacked":
            barminvalues = [sums[index] for sums in data.sums.values()]
            barmaxvalues = [sums[index+1] for sums in data.sums.values()]
            barwidth = 0.8*BARUNIT
            offset = 0.2*BARUNIT
        elif graphtype == "grouped":
            barminvalues = [0]*len(data.labels)
            barmaxvalues = [values[index] for values in data.Values.values()]
            barwidth = 0.8*BARUNIT/len(data)
            offset = 0.2*BARUNIT+barwidth*index
        else:
            barminvalues = [0]*len(data)
            barmaxvalues = data.Values
            barwidth = 0.8*BARUNIT
            offset = 0.2*BARUNIT

        for i, label in enumerate(data.labels):
            [barstart, barend] = [i*BARUNIT+offset, i*BARUNIT+offset+barwidth]
            value = data.Values[label][index] if key else data.Values[i]
            if value > 0:
                self.addObject(Bar(canvas, [(barstart, barmaxvalues[i]), (barend,barminvalues[i])], key, value, direction, colour))

class DataPoint(bryaxes.AxesPoint):
    def __init__(self, canvas, label, coords, colour="red", objid=None):
        (x, y) = coords
        super().__init__(canvas, (float(x), y), colour)
        self.canvas = canvas
        self.coords = (float(x), y)
        self.tooltiptext = f"{label}\n{coords}" if label else f"{coords}"
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, self.coords)

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class RegressionLine(bryaxes.AxesPolyline):
    def __init__(self, canvas, data, colour="black"):
        points = data.values() if isinstance(data, LabelledPairedData) else data
        pmcc, gradient, yintercept = regressioninfo(points)
        sign = "" if yintercept < 0 else "+"
        n1 = 2-int(log10(gradient))
        n2 = 2-int(log10(yintercept))
        self.tooltiptext = f"y = {gradient:.{n1}f}x{sign}{yintercept:.{n2}f}\n(PMCC = {pmcc:.2f})"
        x1, x2 = data.xMin, data.xMax
        y1, y2 = gradient*x1 + yintercept, gradient*x2 + yintercept
        super().__init__(canvas, [(x1,y1), (x2,y2)], linecolour=colour, linewidth=2)

        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        (x, y) = self.canvas.getSVGcoords(event)
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, (x, -y))

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class BoxPlot(SVG.GroupObject):
    def __init__(self, boxplotinfo, label, yheight, colour="yellow"):
        xmin, Q1, Q2, Q3, xmax = boxplotinfo
        super().__init__([
            SVG.LineObject([(xmin, yheight-5), (xmin, yheight+5)]),
            SVG.LineObject([(xmin, yheight), (Q1, yheight)]),
            SVG.RectangleObject([(Q1, yheight-15), (Q2, yheight+15)], fillcolour = colour),
            SVG.RectangleObject([(Q2, yheight-15), (Q3, yheight+15)], fillcolour = colour),
            SVG.LineObject([(Q3, yheight), (xmax, yheight)]),
            SVG.LineObject([(xmax, yheight-5), (xmax, yheight+5)])
            ])
        self.tooltiptext = f"{label}\nMin={xmin}, Q1={Q1}, Q2={Q2}, Q3={Q3}, Max={xmax}"
        self.centre = ((Q1+Q2)/2, yheight)
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, self.centre)

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class HistogramBar(SVG.RectangleObject):
    def __init__(self, gfd, i, colour="yellow"):
        [barleft, barright] = gfd.boundaries[i:i+2]
        super().__init__([(barleft, gfd.frequencyDensities[i]), (barright, 0)], fillcolour=colour)
        self.tooltiptext = f"{barleft}≤x<{barright}\nFrequency: {gfd.frequencies[i]}\nFrequency Density: {gfd.frequencyDensities[i]}"
        self.centre = ((barleft+barright)/2, gfd.frequencyDensities[i]/2)
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, self.centre)

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class HistogramBars(SVG.GroupObject):
    def __init__(self, gfd, colour="yellow"):
        super().__init__()
        for i in range(len(gfd)-1):
            self.addObject(HistogramBar(gfd, i, colour))

class NormalCurve(bryaxes.AxesPolyline):
    def __init__(self, canvas, gfd):
        m = gfd.mean()
        v = gfd.variance()
        s = v**0.5
        k = sum(gfd.frequencies)/(s*(2*pi)**0.5)
        x0 = gfd.xMin
        dx = (gfd.xMax - x0)/200
        points = [(x0+i*dx, k*exp(-0.5*(((x0+i*dx)-m)/s)**2)) for i in range(201)]
        super().__init__(canvas, points, linewidth=2)
        self.tooltiptext = f"µ = {m:.1f}\nσ² = {v:.1f}"
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        (x, y) = self.canvas.getSVGcoords(event)
        self.canvas.tooltip = AxesTooltip(self.canvas, self.tooltiptext, (x, -y))

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()


class CumulativeFrequencyLine(bryaxes.AxesPolyline):
    def __init__(self, canvas, key, cfd, colour):
        super().__init__(canvas, cfd, linecolour=colour, linewidth=2)
        self.key = key
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        (x, y) = self.canvas.getSVGcoords(event)
        n = int(3-log10(x))
        tooltiptext = f"{self.key}\nNumber of values < {x:.{n}f}: {-y:.0f}"
        self.canvas.tooltip = AxesTooltip(self.canvas, tooltiptext, (x, -y))

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class CumulativePercentageLine(bryaxes.AxesPolyline):
    def __init__(self, canvas, key, cfd, colour):
        total = cfd.totalFrequency
        points = [(x, 100*y/total) for (x, y) in cfd]
        super().__init__(canvas, points, linecolour=colour, linewidth=2)
        self.key = key
        self.bind("mouseenter", self.showtooltip)
        self.bind("touchstart", self.showtooltip)
        self.bind("mouseleave", self.hidetooltip)

    def showtooltip(self, event):
        if self.canvas.tooltip: self.canvas.tooltip.hide()
        (x, y) = self.canvas.getSVGcoords(event)
        n = int(3-log10(x))
        tooltiptext = f"{self.key}\n%age of values < {x:.{n}f}: {-y:.0f}%"
        self.canvas.tooltip = AxesTooltip(self.canvas, tooltiptext, (x, -y))

    def hidetooltip(self, event):
        self.canvas.tooltip.hide()

class DataTable(list):
    def __init__(self, csvfile=None, jsonfile=None, datasets="columns", headers=True):
        if csvfile:
            with open(csvfile) as datafile:
                lines = datafile.readlines()
            #datafile = open(csvfile)
            #lines = datafile.readlines()
            data = [line.strip().split(",") for line in lines]
            data = [[convertifnumber(item) for item in row] for row in data]
        elif jsonfile:
            with open(jsonfile) as datafile:
                data = json.load(datafile)
            #datafile = open(jsonfile)
            #data = json.load(datafile)
        fieldnames = data[0]
        datalist = [{key:value for key, value in zip(fieldnames, data[i])} for i in range(1, len(data))]
        super().__init__(datalist)
