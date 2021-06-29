introtext = """
## brycharts - Introduction

This is a Brython package for generating statistical charts.
The Brython website is at https://brython.info
Full documentation for brycharts can be found at https://github.com/andy31lewis/brycharts

Clicking on the tabs at the top of this page gives examples of the various types of graph which brycharts can produce.
On the left of each page is:

• a brief description of the graph(s).
• a box showing how the data for the the graph(s) needs to organised using Python `list`s and/or `dict`s.
• a box showing the code used to draw the graphs (essentially just two lines of code per graph).

The data illustrated by these graphs is from the Numbeo website https://www.numbeo.com/cost-of-living/
This gives information about average salaries and the cost of living in about 540 cities around the world.
The first 25 rows of the table from which the graphs have been generated is shown on the next tab.
This is stored internally as a `list` of `dicts`: each row is a `dict` with the column headings as keys.
"""

piecharttext = """
## Pie Charts

Data about the continents where all 540 cities are located has been extracted as a Python `list` as shown in the first box below.

The code in the second box then feeds this list into a `brycharts.FrequencyData` object. Then two `brycharts.PieChart` objects are created in the `div` on the right (which is called `self.chartbox`).

The first chart uses a 'key' to show the names of the continents. The second has the names around the chart; note that for this the sectors have been automatically rearranged so that small sectors are not next to each other, to avoid the labels being superimposed.
"""

barcharttext = """
## Bar Charts

Numbeo's full Cost of Living Index is broken down into two parts: a Rent Index for housing cost, and Cost of Living Index for everything else.  Here is a selection of six cities (one from each continent), showing the two indices for each city.

The extracted data is organised as a `dict` of `dicts`, as shown in the first box.  This is fed into a `brycharts.LabelledDataDict`, and displayed in two ways: first as a `brycharts.StackedBarChart` (which shows more clearly the total cost of living), and then as a `brycharts.GroupedBarChart` (which perhaps makes it easier to compare the two indices).
"""

linegraphtext = """
## Line Graphs

This shows the change in the cost of renting over a period of 10 years in four European cities.  It is interesting to see that rents in Dublin have nearly doubled, while renting in Rome has become cheaper.

The historical data for this chart comes from a different file.  It is organised as as a `dict` of `lists`, as shown in the first box.  This is fed into a `brycharts.PairedDataDict`, and then displayed as a `brycharts.LineGraph`.
"""

scattergraphtext = """
## Scattergraphs

This compares the "Average Salary Index" with the "Cost of Living plus Rent Index" for all listed cities and towns in the United Kingdom. Those below the regression line will have a higher "Local Purchasing Power Index", since living costs are low compared to salaries.

The extracted data is organised as a `dict` whose values are data pairs, as shown in the first box.  This is fed into a `brycharts.LabelledPairedData` object, and then displayed as a `brycharts.ScatterGraph`.
"""

boxplottext = """
## Box Plots

This compares the "Local Purchasing Power Index" for all cities in three countries: United States, United Kingdom and Germany. It is noticeable that the US has the cities with both the highest and the lowest index.

The extracted data is organised as a `dict` of `lists`, as shown in the first box.  This is fed into a `brycharts.BoxPlotDataDict`, and then displayed as a `brycharts.BoxPlotCanvas`.
"""

histogramtext = """
## Histograms

These look at the "Local Purchasing Power Index" for cities in the United States in more detail.

The data used is just a `list`, as shown in the first box.  This is fed into a `brycharts.GroupedFrequencyData` object, and then displayed as a `brycharts.Histogram`.

These steps are then repeated, but instead of allowing the object to choose its own class boundaries, we have specified a more detailed set of boundaries to show more clearly that the greatest density of values is between 125 and 135.
"""

cumulativefrequencytext = """
## Cumulative Percentage Graph

This uses exactly the same data as the Box Plot example - see comments there.

This time it is fed into a `brycharts.CumulativeFrequencyData` object, and then displayed as a `brycharts.CumulativePercentageGraph`.
"""
