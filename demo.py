from browser import document, html, window
import json
import brywidgets as ws
import brycharts
from content import *

class ListDict(dict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = []
            return self[key]

class DemoPage(ws.NotebookPage):
    def __init__(self, pageindex, title, backgroundcolour):
        super().__init__(title, backgroundcolour)
        self.viewed = False
        self.chartbox =  ws.ColumnPanel(className="chartcontainer")
        self.description = html.DIV(Class="description")
        self.databox = html.TEXTAREA(Class="databox")
        self.codebox = html.TEXTAREA(Class="codebox")
        self.attach(ws.RowPanel([
            html.DIV([
                self.description,
                html.P("How the data is structured:", Class="boxlabel"),
                self.databox,
                html.P("Code to generate the charts:", Class="boxlabel"),
                self.codebox
                ], Class="leftpane"),
            self.chartbox
            ]))

class IntroPage(ws.NotebookPage):
    def __init__(self):
        super().__init__("Introduction", "powderblue", tabwidth="12%", id="intro")
        self.attach([
            html.DIV(formatted(introtext), Class="intro")])

class PieChartPage(DemoPage):
    def __init__(self):
        super().__init__(1, "Pie Charts", "#fafabe")
        self.description.attach(formatted(piecharttext))
        self.databox.attach(f"continentlist = {continentlist}")
        self.codebox.attach("""freqdata = brycharts.FrequencyData(rawdata=continentlist)
brycharts.PieChart(self.chartbox, freqdata, height="45%", usekey=True)
brycharts.PieChart(self.chartbox, freqdata, height="45%", usekey=False)""")

    def update(self):
        if self.viewed: return
        freqdata = brycharts.FrequencyData(rawdata=continentlist)
        title = "Location of the cities which are included in the Numbeo database file"
        brycharts.PieChart(self.chartbox, freqdata, title, height="45%", usekey=True)
        brycharts.PieChart(self.chartbox, freqdata, title, height="45%", usekey=False)
        self.viewed = True

class BarChartPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Bar Charts", "#7fffab")
        self.description.attach(formatted(barcharttext))
        self.databox.attach(f"livingcostdata = {livingcostdata}")
        self.codebox.attach("""labelleddatadict = brycharts.LabelledDataDict(livingcostdata, "Cost Index")
brycharts.StackedBarChart(self.chartbox, labelleddatadict, height="45%")
brycharts.GroupedBarChart(self.chartbox, labelleddatadict, height="45%")""")

    def update(self):
        if self.viewed: return
        labelleddatadict = brycharts.LabelledDataDict(livingcostdata, "Cost Index")
        title = "Breakdown of living costs in six cities"
        brycharts.StackedBarChart(self.chartbox, labelleddatadict, title, height="45%")
        brycharts.GroupedBarChart(self.chartbox, labelleddatadict, title, height="45%")
        self.viewed = True

class LineGraphPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Line Graphs", "#7ff9ff")
        self.description.attach(formatted(linegraphtext))
        self.databox.attach(f"rentdata = {rentdata}")
        self.codebox.attach("""paireddatadict = brycharts.PairedDataDict("Year", "Monthly rent (€)", rentdata)
brycharts.LineGraph(self.chartbox, paireddatadict)""")

    def update(self):
        if self.viewed: return
        paireddatadict = brycharts.PairedDataDict("Year", "Monthly rent (€)", rentdata)
        brycharts.LineGraph(self.chartbox, paireddatadict)
        self.viewed = True

class ScattergraphPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Scattergraphs", "#94adf9")
        self.description.attach(formatted(scattergraphtext))
        self.databox.attach(f"salaryvscostsdata = {salaryvscostsdata}")
        self.codebox.attach("""paireddata = brycharts.PairedData("Average Salary Index", "Total Cost of Living Index", salaryvscostsdata)
brycharts.ScatterGraph(self.chartbox, paireddata, showRegressionLine=True)""")

    def update(self):
        if self.viewed: return
        lpd = brycharts.LabelledPairedData("Average Salary Index", "Total Cost of Living Index", salaryvscostsdata)
        brycharts.ScatterGraph(self.chartbox, lpd, showRegressionLine=True)
        self.viewed = True

class BoxPlotPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Box Plots", "#f9a5eb")
        self.description.attach(formatted(boxplottext))
        self.databox.attach(f"purchasingpowerdict = {purchasingpowerdict}")
        self.codebox.attach("""bpdd = brycharts.BoxPlotDataDict("Local Purchasing Power Index", rawdatadict=purchasingpowerdict)
brycharts.BoxPlotCanvas(self.chartbox, bpdd)""")

    def update(self):
        if self.viewed: return
        bpdd = brycharts.BoxPlotDataDict("Local Purchasing Power Index", rawdatadict=purchasingpowerdict)
        brycharts.BoxPlotCanvas(self.chartbox, bpdd)
        self.viewed = True

class HistogramPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Histograms", "#fff77f")
        self.description.attach(formatted(histogramtext))
        self.databox.attach(f"USpurchasingpower = {USpurchasingpower}")
        self.codebox.attach("""gfd1 = brycharts.GroupedFrequencyData(label="Total marks", rawdata=USpurchasingpower)
brycharts.Histogram(self.chartbox, gfd1, height="45%")
gfd2 = brycharts.GroupedFrequencyData(label="Total marks", rawdata=USpurchasingpower,
boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
brycharts.Histogram(self.chartbox, gfd2, height="45%")""")

    def update(self):
        if self.viewed: return
        gfd1 = brycharts.GroupedFrequencyData(label="Local Purchasing Power Index", rawdata=USpurchasingpower)
        brycharts.Histogram(self.chartbox, gfd1, height="45%")
        gfd2 = brycharts.GroupedFrequencyData(label="Local Purchasing Power Index", rawdata=USpurchasingpower,
                                                boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
        brycharts.Histogram(self.chartbox, gfd2, height="45%")
        self.viewed = True

class CumulativePercentagePage(DemoPage):
    def __init__(self):
        super().__init__(2, "Cum %age Graph", "#adff7f")
        self.description.attach(formatted(cumulativefrequencytext))
        self.databox.attach(f"USpurchasingpower = {USpurchasingpower}")
        self.codebox.attach("""cfd = brycharts.CumulativeFrequencyData(label="Local Purchasing Power Index", rawdata=USpurchasingpower,
boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
brycharts.CumulativePercentageGraph(self.chartbox, cfd)""")

    def update(self):
        if self.viewed: return
        cfd = brycharts.CumulativeFrequencyData(label="Local Purchasing Power Index", rawdata=USpurchasingpower,
                                                boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
        brycharts.CumulativePercentageGraph(self.chartbox, cfd)
        self.viewed = True

def formatted(inputstring):
    output = []
    stringlist = inputstring.split("\n\n")
    for s in stringlist:
        s = s.strip()
        if s[:3] == "## ":
            output.append(html.H2(s[3:]))
        else:
            while " http" in s:
                start = s.index(" http")
                end1 = s.find(" ", start+1)
                if end1 < 0: end1 = 1e12
                end2 = s.find("\n", start+1)
                end = min(end1, end2)
                if end < 0: end = None
                link = s[start+1:end]
                s = s.replace(link, f" <a href='{link}'>{link}</a>")

            markup = [("`", "code"), ("**", "bold"), ("*", "italic")]
            for (code, className) in markup:
                while code in s:
                    L = len(code)
                    start = s.index(code)
                    end = s.find(code, start+L)
                    text = s[start:end+L]
                    s = s.replace(text, f" <span class='{className}'>{text[L:-L]}</span>")

            s = s.replace("\n", "<br />\n")
            output.append(html.P(s))
    return output


def getalldata():
    with open("cost-of-living-data.json") as f:
        data = json.load(f)
    headings = data[0]
    return [{key:value for key, value in zip(headings, data[i])} for i in range(1, len(data))]

def gethistoricaldata():
    with open("rent-costs.json") as f:
        data = json.load(f)
    headings = data[0]
    rentdata = {}
    for row in data[1:]:
        rentdata[row[0]] = [(year, value) for (year, value) in zip(headings[1:], row[1:]) if value != "NaN"]
    return rentdata

# Get data for pie charts
alldata = getalldata()
continentlist = [city["Continent"] for city in alldata]

# Get data for bar charts
cities = ["San Francisco", "Hong Kong", "Athens", "Nairobi", "Adelaide", "Rio De Janeiro"]
livingcostdata = {index:{city["City"]:city[index] for city in alldata if city["City"] in cities}
                    for index in ["Cost of Living Index", "Rent Index"]}

# Get data for line graphs
rentdata = gethistoricaldata()

# Get data for scattergraph
#salaryvscostsdata = [(city["Average Disposable Salary Index"], city["Cost of Living plus Rent Index"])
#                        for city in alldata if city["Country"] == "United Kingdom"]
salaryvscostsdata = {city["City"]:(city["Average Disposable Salary Index"], city["Cost of Living plus Rent Index"])
                        for city in alldata if city["Country"] == "United Kingdom"}

# Get data for box plots, histograms and cumulative frequency graph
countrylist = ["United States", "Germany", "United Kingdom"]
purchasingpowerdict = ListDict()
for city in alldata:
    if city["Country"] not in countrylist: continue
    purchasingpowerdict[city["Country"]].append(city["Local Purchasing Power Index"])
USpurchasingpower = purchasingpowerdict["United States"]

pages = [IntroPage(), PieChartPage(), BarChartPage(), LineGraphPage(), ScattergraphPage(), BoxPlotPage(), HistogramPage(), CumulativePercentagePage()]
document["body"].innerHTML = ""
document <= (notebook := ws.Notebook(pages))
pageheight = f"calc(100vh - {notebook.tabrow.offsetHeight}px)"
for page in pages: page.style.height = pageheight
