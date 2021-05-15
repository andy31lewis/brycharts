# brycharts

A Brython package for the creation of statistical charts (pie charts, histograms) etc).

### Hello World

All software should have a Hello World example. ;-)

Here is a minimalist html file to show the frequency of the letters in HELLOWORLD as a pie chart:

```html
<html>
  <head>
    <script src="https://cdn.jsdelivr.net/npm/brython@3.9.2/brython.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/brython@3.9.2/brython_stdlib.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/andy31lewis/brycharts@latest/brycharts.brython.js"></script>
    <script type="text/python">
from browser import document
import brycharts
freqdata = brycharts.FrequencyData(rawdata=list("HELLOWORLD"))
brycharts.PieChart(document, freqdata)
    </script>
  </head>
  <body id="body" onLoad="brython()">
  </body>
</html>
```

And here is the result:



This example can be seen at http://mathsanswers.org.uk/oddments/brycharts/helloworld.html

For many more examples, with details of how they were created, see  
http://mathsanswers.org.uk/oddments/brycharts/demo.html

Full documentation will follow soon!