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

from collections import Counter
from math import sin, cos, pi
#import brySVG.dragcanvas as SVG
from . import dragcanvas as SVG
from . import bryaxes
from .roundfns import *
from .statfns import *

DEFAULT_COLOURS = [f"hsl({a%360+22.5*(a//1080)},{(3-a//810)*100//3}%, 50%)" for a in range(0,2160,135)]

class PairedData(list):
    def __init__(self, xLabel, yLabel, data):
        super().__init__(data)
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.xValues = [item[0] for item in data]
        self.yValues = [item[1] for item in data]
        self.xMin, self.xMax = min(self.xValues), max(self.xValues)
        self.yMin, self.yMax = min(self.yValues), max(self.yValues)

class LabelledPairedData(dict):
    def __init__(self, xLabel, yLabel, data):
        super().__init__(data)
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.xValues = [item[0] for item in data.values()]
        self.yValues = [item[1] for item in data.values()]
        self.xMin, self.xMax = min(self.xValues), max(self.xValues)
        self.yMin, self.yMax = min(self.yValues), max(self.yValues)

class PairedDataDict(dict):
    def __init__(self, xLabel, yLabel, datadict):
        pdd = {key:PairedData(xLabel, yLabel, pd) for (key, pd) in datadict.items()}
        super().__init__(pdd)
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.xMin = min(pd.xMin for pd in pdd.values())
        self.xMax = max(pd.xMax for pd in pdd.values())
        self.yMin = min(pd.yMin for pd in pdd.values())
        self.yMax = max(pd.yMax for pd in pdd.values())

class LabelledData(dict):
    def __init__(self, data, axisLabel=None):
       super().__init__(data)
       self.axisLabel = axisLabel
       self.labels = list(self.keys())
       self.Values = list(self.values())
       self.maxValue = max(self.Values)
       self.total = sum(self.Values)
       self.percentages = [100*value/self.total for value in self.Values]

class LabelledDataDict(dict):
    def __init__(self, datadict, axisLabel=None):
        ldd = {key:LabelledData(ld) for (key, ld) in datadict.items()}
        super().__init__(ldd)
        self.maxValue = max(ld.maxValue for ld in ldd.values())
        self.axisLabel = axisLabel
        labels = set()
        for ld in ldd.values(): labels.update(ld.keys())
        self.labels = list(labels)
        self.sums = {label:[0] for label in self.labels}
        for label in self.labels:
            for ld in ldd.values(): self.sums[label].append(self.sums[label][-1] + ld.get(label, 0))
        self.maxSum = max(sums[-1] for sums in self.sums.values())

class FrequencyData(LabelledData):
    def __init__(self, data=None, rawdata=None):
        if rawdata:
            data = self.fromRawData(rawdata)
        super().__init__(data)
        self.axisLabel = "Frequency"
        self.frequencies = self.Values
        self.maxFrequency = self.maxValue

    def fromRawData(self, rawdata):
        return sorted(Counter(rawdata).items())

class GroupedFrequencyData(list):
    def __init__(self, label, data=None, rawdata=None, boundaries=None, classwidth=None):
        if data:
            (b, f) = data[-1]
            if f != 0: data.append((2*b - data[-2][0], 0))
        else:
            datamin, datamax = min(rawdata), max(rawdata)
            datarange = datamax - datamin
            if not boundaries:
                if not classwidth: classwidth, _ = roundscale(datarange, 5)
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
        self.label = label

    def fromRawData(self, rawdata, boundaries):
        L = len(boundaries)
        frequencies = [0] * L
        for value in rawdata:
            for i in range(L):
                if value < boundaries[i+1]:
                    frequencies[i] += 1
                    break
        return list(zip(boundaries, frequencies))

class BoxPlotData(list):
    def __init__(self, axisLabel, boxplotdata=None, rawdata=None):
        if rawdata:
            Q1, Q2, Q3 = quartiles(rawdata)
            boxplotdata = [min(rawdata), Q1, Q2, Q3, max(rawdata)]
        super().__init__(boxplotdata)
        self.axisLabel = axisLabel
        self.xMin = self[0]
        self.xMax = self[-1]

class BoxPlotDataDict(dict):
    def __init__(self, axisLabel, boxplotdatadict=None, rawdatadict=None):
        if rawdatadict:
            boxplotdatadict = {}
            for key, rawdata in rawdatadict.items():
                boxplotdatadict[key] = BoxPlotData(axisLabel, rawdata=rawdata)
        else:
            boxplotdatadict = {key:BoxPlotData(axisLabel, boxplotdata) for key, boxplotdata in boxplotdatadict.items()}
        super().__init__(boxplotdatadict)
        self.xMin = min(bpd.xMin for bpd in self.values())
        self.xMax = max(bpd.xMax for bpd in self.values())
        self.axisLabel = axisLabel

class CumulativeFrequencyData(list):
    def __init__(self, label, cumfreqdata=None, groupedfreqdata=None, rawdata=None, boundaries=None, classwidth=None):
        if rawdata:
            groupedfreqdata = GroupedFrequencyData(label=label, rawdata=rawdata, boundaries=boundaries, classwidth=classwidth)
        if groupedfreqdata:
            cumfreqdata = self.fromGFD(groupedfreqdata)
        else:
            (b, f) = cft[0]
            if f != 0: cumfreqdata.insert(0, (2*b - cft[1][0], 0))
        super().__init__(cumfreqdata)
        self.boundaries = [item[0] for item in cumfreqdata]
        self.cumfrequencies = [item[1] for item in cumfreqdata]
        self.xMin, self.xMax = self.boundaries[0], self.boundaries[-1]
        self.totalFrequency = self.cumfrequencies[-1]
        self.label = label

    def fromGFD(self, groupedfreqdata):
        L = len(groupedfreqdata)
        boundaries, frequencies = zip(*groupedfreqdata)
        cumfrequencies = [0] * L
        for i in range(1, L):
            cumfrequencies[i] = cumfrequencies[i-1] + frequencies[i-1]
        return list(zip(boundaries, cumfrequencies))

class Bars(SVG.GroupObject):
    def __init__(self, data, graphtype=None, index=None, key=None, colour="yellow"):
        super().__init__()
        if graphtype == "stacked":
            barminvalues = [sums[index] for sums in data.sums.values()]
            barmaxvalues = [sums[index+1] for sums in data.sums.values()]
            barwidth = 80
            offset = 20
        elif graphtype == "grouped":
            barminvalues = [0]*len(data.labels)
            barmaxvalues = [data[key].get(label, 0) for label in data.labels]
            barwidth = 80/len(data)
            offset = 20+barwidth*index
        else:
            barminvalues = [0]*len(data)
            barmaxvalues = data.Values
            barwidth = 80
            offset = 20

        for i in range(len(data.labels)):
            [barstart, barend] = [i*100+offset, i*100+offset+barwidth]
            self.addObject(SVG.RectangleObject([(barstart, barmaxvalues[i]), (barend,barminvalues[i])], fillcolour=colour))

class BarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, ld, title="", width="95%", height="95%", colour="yellow", fontsize=16):
        xaxis = bryaxes.Axis(0, 100*len(ld), label="", showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, ld.maxFrequency, ld.axisLabel)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        self.attachObject(Bars(ld, colour=colour))
        for i in range(len(ld)):
            label = bryaxes.AxesWrappingTextObject(self, ld.labels[i], (i*100+60, 0), 80, fontsize=fontsize)
            self.attachObject(label)
        self.fitContents()

class StackedBarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, ldd, title="", width="95%", height="95%", colours=None, fontsize=16, objid=None):
        if not colours: colours = DEFAULT_COLOURS
        xaxis = bryaxes.Axis(0, 100*len(ldd.labels), label="", showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, ldd.maxSum, ldd.axisLabel)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        for i, key in enumerate(ldd.keys()):
            self.attachObject(Bars(ldd, "stacked", i, key, colours[i]))
        for i in range(len(ldd.labels)):
            label = bryaxes.AxesWrappingTextObject(self, ldd.labels[i], (i*100+60, 0), 80, fontsize=fontsize)
            self.attachObject(label)
        keywidth = 20*self.xScaleFactor
        keyheight = fontsize*2*self.yScaleFactor
        keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.min+keyheight))
        for i, key in enumerate(ldd.keys()):
            self.attachObject(SVG.GroupObject([
                SVG.RectangleObject([keypos, keypos+(keywidth,keyheight/2)], fillcolour=colours[i]),
                bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=7, fontsize=fontsize)
                ]))
            keypos += (0, keyheight)
        #if title: self.attachObject(bryaxes.AxesTextObject(self, title, ((xaxis.min+xaxis.max)/2, yaxis.max + keyheight), anchorposition=8, fontsize=fontsize))
        self.fitContents()

class GroupedBarChart(bryaxes.AxesCanvas):
    def __init__(self, parent, ldd, title="", width="95%", height="95%", colours=None, fontsize=16, objid=None):
        if not colours: colours = DEFAULT_COLOURS
        xaxis = bryaxes.Axis(0, 100*len(ldd.labels), label="", showScale=False,
                            showMajorTicks=False, showMinorTicks=False, showMajorGrid=False, showMinorGrid=False)
        yaxis = bryaxes.Axis(0, ldd.maxValue, ldd.axisLabel)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis, title=title, objid=objid)
        for i, key in enumerate(ldd.keys()):
            self.attachObject(Bars(ldd, "grouped", i, key, colours[i]))
        for i in range(len(ldd.labels)):
            label = bryaxes.AxesWrappingTextObject(self, ldd.labels[i], (i*100+60, 0), 80, fontsize=fontsize)
            self.attachObject(label)
        keywidth = 20*self.xScaleFactor
        keyheight = fontsize*2*self.yScaleFactor
        keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.min+keyheight))
        for i, key in enumerate(ldd.keys()):
            self.attachObject(SVG.GroupObject([
                SVG.RectangleObject([keypos, keypos+(keywidth,keyheight/2)], fillcolour=colours[i]),
                bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=7, fontsize=fontsize)
                ]))
            keypos += (0, keyheight)
        self.fitContents()

class HistogramBars(SVG.GroupObject):
    def __init__(self, gfd, colour="yellow"):
        super().__init__()
        for i in range(len(gfd)-1):
            [barleft, barright] = gfd.boundaries[i:i+2]
            self.addObject(SVG.RectangleObject([(barleft, gfd.frequencyDensities[i]), (barright, 0)], fillcolour=colour))

class Histogram(bryaxes.AxesCanvas):
    def __init__(self, parent, gfd, title="", width="95%", height="95%", colour="yellow"):
        xaxis = bryaxes.Axis(gfd.xMin, gfd.xMax, gfd.label)
        yaxis = bryaxes.Axis(0, gfd.maxFrequencyDensity, "Frequency density")
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        self.attachObject(HistogramBars(gfd, colour))

class CumulativeFrequencyLine(SVG.PolylineObject):
    def __init__(self, cfd):
        super().__init__(cfd)

class CumulativePercentageLine(SVG.PolylineObject):
    def __init__(self, cfd):
        total = cfd.totalFrequency
        points = [(x, 100*y/total) for (x, y) in cfd]
        super().__init__(points)

class CumulativeFrequencyGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, cfd, title="", width="95%", height="95%"):
        xaxis = bryaxes.Axis(cfd.xMin, cfd.xMax, cfd.label, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(0, cfd.totalFrequency, "Cumulative frequency", showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        self.attachObject(CumulativeFrequencyLine(cfd))

class CumulativePercentageGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, cfd, title="", width="95%", height="95%"):
        xaxis = bryaxes.Axis(cfd.xMin, cfd.xMax, cfd.label, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(0, 100, "Cumulative percentage", showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        self.attachObject(CumulativePercentageLine(cfd))

class DataPoints(SVG.GroupObject):
    def __init__(self, canvas, paireddata, colour="red"):
        super().__init__()
        for dp in paireddata:
            self.addObject(bryaxes.AxesPoint(canvas, dp, colour))

class LabelledDataPoint(SVG.GroupObject):
    def __init__(self, canvas, label, coords, colour="red", objid=None):
        super().__init__()
        self.point = bryaxes.AxesPoint(canvas, coords, colour)
        self.label = bryaxes.AxesTextObject(canvas, f"{label}\n{coords}", coords, anchorposition=8)
        self.label.style.visibility = "hidden"
        self.addObjects([self.point, self.label])
        self.point.bind("mouseenter", self.showlabel)
        self.point.bind("mouseleave", self.hidelabel)

    def showlabel(self, event):
        self.label.style.visibility = "visible"

    def hidelabel(self, event):
        self.label.style.visibility = "hidden"

class LabelledDataPoints(SVG.GroupObject):
    def __init__(self, canvas, lpd, colour="red"):
        super().__init__()
        for index, (label, coords) in enumerate(lpd.items()):
            self.addObject(LabelledDataPoint(canvas, label, coords, colour, objid=f"{canvas.id}_dp_{index}"))

class RegressionLine(SVG.LineObject):
    def __init__(self, data):
        points = data.values() if isinstance(data, LabelledPairedData) else data
        pmcc, gradient, yintercept = regressioninfo(points)
        x1, x2 = data.xMin, data.xMax
        y1, y2 = gradient*x1 + yintercept, gradient*x2 + yintercept
        super().__init__([(x1,y1), (x2,y2)])

class ScatterGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", width="95%", height="95%", colour="red", showRegressionLine=False):
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.xLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(data.yMin, data.yMax, data.yLabel, showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        if isinstance(data, LabelledPairedData):
            self.attachObject(LabelledDataPoints(self, data, colour))
        else:
            self.attachObject(DataPoints(self, data, colour))
        if showRegressionLine: self.attachObject(RegressionLine(data))

class LineGraph(bryaxes.AxesCanvas):
    def __init__(self, parent, datavalues, titles="", width="95%", height="95%", colours=None, fontsize=16, objid=None):
        xaxis = bryaxes.Axis(datavalues.xMin, datavalues.xMax, datavalues.xLabel, showMajorGrid=True, showMinorGrid=True)
        yaxis = bryaxes.Axis(datavalues.yMin, datavalues.yMax, datavalues.yLabel, showMajorGrid=True, showMinorGrid=True)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        if isinstance(datavalues, PairedData):
            self.attachObject(SVG.PolylineObject(datavalues, linecolour=colours[0]))
        else:
            if not colours: colours = DEFAULT_COLOURS
            keywidth = 20*self.xScaleFactor
            keyheight = fontsize*2*self.yScaleFactor
            keypos = SVG.Point((self.xAxis.max + keywidth, self.yAxis.max))
            keydata = []
            for i, (key, pd) in enumerate(datavalues.items()):
                self.attachObject(SVG.PolylineObject(pd, linecolour=colours[i], linewidth=2))
                keydata.append((pd.yValues[-1], key, colours[i]))
            keydata.sort(key = lambda x: -x[0])
            for (_, key, colour) in keydata:
                self.attachObject(SVG.GroupObject([
                    SVG.LineObject([keypos, keypos+(keywidth,0)], linecolour=colour, linewidth=2),
                    bryaxes.AxesTextObject(self, key, keypos+(keywidth*1.25,0), anchorposition=4, fontsize=fontsize)
                    ]))
                keypos += (0, -keyheight)
            self.fitContents()

class BoxPlot(SVG.GroupObject):
    def __init__(self, boxplotinfo, yheight, colour="yellow"):
        xmin, Q1, Q2, Q3, xmax = boxplotinfo
        super().__init__([
            SVG.LineObject([(xmin, yheight-5), (xmin, yheight+5)]),
            SVG.LineObject([(xmin, yheight), (Q1, yheight)]),
            SVG.RectangleObject([(Q1, yheight-15), (Q2, yheight+15)], fillcolour = colour),
            SVG.RectangleObject([(Q2, yheight-15), (Q3, yheight+15)], fillcolour = colour),
            SVG.LineObject([(Q3, yheight), (xmax, yheight)]),
            SVG.LineObject([(xmax, yheight-5), (xmax, yheight+5)])
            ])

class BoxPlotCanvas(bryaxes.AxesCanvas):
    def __init__(self, parent, data, title="", width="95%", height="95%", colour="yellow"):
        if isinstance(data, BoxPlotData): data = BoxPlotDataDict(data.axisLabel, {"":data})
        xaxis = bryaxes.Axis(data.xMin, data.xMax, data.axisLabel)
        yaxis = bryaxes.Axis(0, 50*len(data), "", showAxis=False, showMajorTicks=False, showMinorTicks=False)
        super().__init__(parent, width, height, xAxis=xaxis, yAxis=yaxis)
        self.fitContents()
        yheight = 25
        for label, boxplotdata in data.items():
            self.attachObject(BoxPlot(boxplotdata, yheight, colour))
            if label: self.attachObject(bryaxes.AxesWrappingTextObject(self, label, (xaxis.min-10*self.xScaleFactor, yheight), 100, 6))
            yheight += 50
        self.fitContents()

class PieChart(SVG.CanvasObject):
    def __init__(self, parent, data, title="", width="95%", height="95%", colours=None, usekey=True, fontsize=12, objid=None):
        super().__init__(width, height, objid=objid)
        parent <= self
        if not colours: colours = DEFAULT_COLOURS
        if not usekey:
            data = data.items()
            n = len(data)
            L = sorted(data, key = lambda x:x[1])
            M = []
            for pair in zip(L[n//2:], L[:n//2]): M.extend(pair)
            if n%2 == 1: M.append(L[-1])
            data = LabelledData(M)
        angles = [0]
        for percentage in data.percentages:
            angles.append(angles[-1] + percentage*3.6)
        self.sectors = SVG.GroupObject([SVG.SectorObject((0,0), 100, angles[i], angles[i+1], fillcolour=colours[i]) for i in range(len(angles)-1)])
        self.addObject(self.sectors)
        self.fitContents()

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
        if title: self.addObject(SVG.TextObject(title, titlepos, anchorposition=8, fontsize=fontsize))
        self.fitContents()




