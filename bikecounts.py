from browser import document, ajax, timer
import json, datetime
import brycharts

def drawgraph():
    def oncomplete(request):
        global count
        count += 1
        document.clear()
        data = json.loads(request.responseText)
        ld = {}
        for bikepoint in data:
            idstring = bikepoint["id"]
            idno = int(idstring.split("_")[-1])
            if idno not in bikepoints: continue
            bikes = [d for d in bikepoint["additionalProperties"] if d["key"] == "NbBikes"][0]
            bikecount = int(bikes["value"])
            ld[bikepoints[idno]] = bikecount

            now = datetime.datetime.now()
            timenow = now.hour+now.minute/100
            timeseries[bikepoints[idno]].append((timenow, bikecount))

        if count > 1:
            pdd = brycharts.PairedDataDict("Time", "Bikes available", timeseries)
            brycharts.LineGraph(document, pdd, title)
        else:
            ld = brycharts.LabelledData(ld, "Bikes available")
            brycharts.BarChart(document, ld, title)
        if count == 30: timer.clear_interval(timerid)

    req = ajax.ajax()
    req.open("GET", url, True)
    req.bind("complete", oncomplete)
    document.text = "Waiting..."
    req.send()

url = "https://api.tfl.gov.uk/BikePoint/"
bikepoints = {85:"Tanner Street", 201:"Dorset Square", 307:"Black Lion Gate", 392:"Imperial College", 428:"Exhibition Road", 785:"Olympic Aquatic Centre"}
timeseries = {place:[] for place in bikepoints.values()}
count = 0
title = "Bikes available at six bikepoints"
drawgraph()
timerid = timer.set_interval(drawgraph, 60000)
