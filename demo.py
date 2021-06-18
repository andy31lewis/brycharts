from browser import document, html, window
import time
tt = time.time()
import json
import brywidgets as ws
import brycharts
from content import *
#import datetime
#print("imports", time.time()-tt)
tt = time.time()

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

class DataTablePage(ws.NotebookPage):
    def __init__(self):
        super().__init__("Data Table", "#fbb0b0", tabwidth="12%", id="datatable")
        lines = open("cost-of-living-2018.csv").readlines()
        data = [line.strip().split(",") for line in lines]
        self.attach(html.TABLE(
            html.TR(html.TH(header) for header in data[0]) +
            (html.TR(html.TD(field) for field in row) for row in data[1:])
            ))

class PieChartPage(DemoPage):
    def __init__(self):
        super().__init__(1, "Pie Charts", "#fafabe")
        self.description.attach(formatted(piecharttext))
        self.databox.attach(f'''continentlist = [row["Continent"] for row in datatable]

This results in:
continentlist = {continentlist}''')

        self.codebox.attach("""title = "Location of the cities which are included in the Numbeo database file"
freqdata = brycharts.FrequencyData(rawdata=continentlist)
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
        self.databox.attach(
f'''cities = ["San Francisco", "Hong Kong", "Athens", "Nairobi", "Adelaide", "Rio De Janeiro"]
fields = ["Cost of Living Index", "Rent Index"]
livingcostdata = {{
field:{{row["City"]:row[field] for row in datatable if row["City"] in cities}}
                    for field in fields}}

This results in:
livingcostdata = {livingcostdata}''')

        self.codebox.attach(
"""title = "Breakdown of living costs in six cities"
ldd = brycharts.LabelledDataDict(livingcostdata, "Cost Index")
brycharts.StackedBarChart(self.chartbox, ldd, title, height="45%")
brycharts.GroupedBarChart(self.chartbox, ldd, title, direction="horizontal", height="45%")""")

    def update(self):
        if self.viewed: return
        ldd = brycharts.LabelledDataDict(livingcostdata, "Cost Index")
        title = "Breakdown of living costs in six cities"
        brycharts.StackedBarChart(self.chartbox, ldd, title, height="45%")
        brycharts.GroupedBarChart(self.chartbox, ldd, title, direction="horizontal", height="45%")
        self.viewed = True

class LineGraphPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Line Graphs", "#7ff9ff")
        self.description.attach(formatted(linegraphtext))
        self.databox.attach(f"rentdata = {rentdata}")
        self.codebox.attach(
"""title = "Change in rental costs over a 10 year period"
paireddatadict = brycharts.PairedDataDict("Year", "Monthly rent (€)", rentdata)
brycharts.LineGraph(self.chartbox, paireddatadict, title)""")

    def update(self):
        if self.viewed: return
        title = "Change in rental costs over a 10 year period"
        tt = time.time()
        paireddatadict = brycharts.PairedDataDict("Year", "Monthly rent (€)", rentdata)
        #paireddatadict = brycharts.TimeSeriesDataDict("Year", "Monthly rent (€)", rentdata)
        #print("data", time.time()-tt)
        tt = time.time()
        brycharts.LineGraph(self.chartbox, paireddatadict, title)
        #print("graph", time.time()-tt)
        tt = time.time()
        self.viewed = True

class ScattergraphPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Scattergraphs", "#94adf9")
        self.description.attach(formatted(scattergraphtext))
        self.databox.attach(
f'''salaryvscostsdata = {{row["City"]:(row["Average Disposable Salary Index"], row["Cost of Living plus Rent Index"])
for row in datatable if row["Country"] == "United Kingdom"}}

This results in:
salaryvscostsdata = {salaryvscostsdata}''')

        self.codebox.attach(
"""title = "Salaries and Living Costs for towns/cities in the UK"
lpd = brycharts.LabelledPairedData("Average Salary Index", "Total Cost of Living Index", salaryvscostsdata)
brycharts.ScatterGraph(self.chartbox, lpd, showregressionline=True)""")

    def update(self):
        if self.viewed: return
        lpd = brycharts.LabelledPairedData("Average Salary Index", "Total Cost of Living Index", salaryvscostsdata)
        title = "Salaries and Living Costs for towns/cities in the UK"
        brycharts.ScatterGraph(self.chartbox, lpd, title, showregressionline=True)
        self.viewed = True

class BoxPlotPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Box Plots", "#f9a5eb")
        self.description.attach(formatted(boxplottext))
        self.databox.attach(
f'''purchasingpowerdict = {{country: [row["Local Purchasing Power Index"] for row in datatable if row["Country"] == country]
for country in countrylist}}

This results in:
purchasingpowerdict = {purchasingpowerdict}''')

        self.codebox.attach(
"""title = "Comparison of Purchasing Power in three countries"
bpdd = brycharts.BoxPlotDataDict("Local Purchasing Power Index", rawdatadict=purchasingpowerdict)
brycharts.BoxPlotCanvas(self.chartbox, bpdd, title)""")

    def update(self):
        if self.viewed: return
        bpdd = brycharts.BoxPlotDataDict("Local Purchasing Power Index", rawdatadict=purchasingpowerdict)
        title = "Comparison of Purchasing Power in three countries"
        brycharts.BoxPlotCanvas(self.chartbox, bpdd, title)
        self.viewed = True

class CumulativePercentagePage(DemoPage):
    def __init__(self):
        super().__init__(2, "Cum %age Graph", "#adff7f")
        self.description.attach(formatted(cumulativefrequencytext))
        self.databox.attach(
f'''purchasingpowerdict = {{country: [row["Local Purchasing Power Index"] for row in datatable if row["Country"] == country]
for country in countrylist}}

This results in:
purchasingpowerdict = {purchasingpowerdict}''')

        self.codebox.attach(
"""title = "Comparison of Purchasing Power in three countries"
cfd = brycharts.CumulativeFrequencyData(label="Local Purchasing Power Index", rawdata=purchasingpowerdict,
boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
brycharts.CumulativePercentageGraph(self.chartbox, cfd, title)""")

    def update(self):
        if self.viewed: return
        cfd = brycharts.CumulativeFrequencyDataDict(valueslabel="Local Purchasing Power Index", rawdatadict=purchasingpowerdict,
                                                    boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
        title = "Comparison of Purchasing Power in three countries"
        brycharts.CumulativePercentageGraph(self.chartbox, cfd, title)
        self.viewed = True

class HistogramPage(DemoPage):
    def __init__(self):
        super().__init__(2, "Histograms", "#fff77f")
        self.description.attach(formatted(histogramtext))
        self.databox.attach(
f'''USpurchasingpower = purchasingpowerdict["United States"]

This results in:
USpurchasingpower = {USpurchasingpower}''')

        self.codebox.attach(
"""gfd1 = brycharts.GroupedFrequencyData("Local Purchasing Power Index", rawdata=USpurchasingpower)
brycharts.Histogram(self.chartbox, gfd1, title, height="45%")

gfd2 = brycharts.GroupedFrequencyData("Local Purchasing Power Index", rawdata=USpurchasingpower,
boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
brycharts.Histogram(self.chartbox, gfd2, title, shownormalcurve=True, height="45%")""")

    def update(self):
        if self.viewed: return
        title = "Purchasing Power in towns/cities in the USA"
        gfd1 = brycharts.GroupedFrequencyData("Local Purchasing Power Index", rawdata=USpurchasingpower)
        brycharts.Histogram(self.chartbox, gfd1, title, height="45%")
        gfd2 = brycharts.GroupedFrequencyData("Local Purchasing Power Index", rawdata=USpurchasingpower,
                                                boundaries = [60, 80, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180])
        brycharts.Histogram(self.chartbox, gfd2, title, shownormalcurve=True, height="45%")
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
    #headings = [datetime.datetime(2021,6,8,8,15,0) + datetime.timedelta(minutes=6*i) for i in range(12)]
    rentdata = {}
    for row in data[1:]:
        rentdata[row[0]] = [(year, value) for (year, value) in zip(headings[1:], row[1:]) if value != "NaN"]
    return rentdata

# Get data for pie charts
datatable = brycharts.DataTable(csvfile="cost-of-living-2018.csv")

#alldata = getalldata()
continentlist = [row["Continent"] for row in datatable]

# Get data for bar charts
cities = ["San Francisco", "Hong Kong", "Athens", "Nairobi", "Adelaide", "Rio De Janeiro"]
fields = ["Cost of Living Index", "Rent Index"]
livingcostdata = {field:{row["City"]:row[field] for row in datatable if row["City"] in cities}
                    for field in fields}

# Get data for line graphs
rentdata = gethistoricaldata()

# Get data for scattergraph
salaryvscostsdata = {row["City"]:(row["Average Disposable Salary Index"], row["Cost of Living plus Rent Index"])
                        for row in datatable if row["Country"] == "United Kingdom"}

# Get data for box plots, histograms and cumulative frequency graph
countrylist = ["United Kingdom", "Germany", "United States"]
purchasingpowerdict = {country: [row["Local Purchasing Power Index"] for row in datatable if row["Country"] == country]
                        for country in countrylist}
USpurchasingpower = purchasingpowerdict["United States"]

pages = [IntroPage(), DataTablePage(), PieChartPage(), BarChartPage(), LineGraphPage(), ScattergraphPage(), BoxPlotPage(), HistogramPage(), CumulativePercentagePage()]
document["body"].innerHTML = ""
notebook = ws.Notebook(pages)
document <= notebook
pageheight = f"calc(100vh - {notebook.tabrow.offsetHeight}px)"
for page in pages: page.style.height = pageheight

