import datetime, math
from functools import total_ordering

timeunits = ["year", "month", "day", "hour", "minute", "second"]
timeformats = ["%d/%m/%y", "%d/%m/%y", "%H:%M\n%d/%m", "%H:%M", "%H:%M", "%H:%M:%S"]
timefactors = [1,12,30,24,60,60]

@total_ordering
class TimeCoord():
    startfloat = 0
    scalefloat = 1
    defaultformat = "%d/%m/%y %H:%M"
    def __init__(self, date_time, timeformat=None):
        self.asDatetime = date_time
        self.unitlist = [getattr(date_time, unit) for unit in timeunits]
        if not timeformat: timeformat = self.defaultformat
        self.asString = f"{self.asDatetime:{timeformat} }"
        self.asFloat = (self.asDatetime.timestamp()-self.startfloat)/self.scalefloat

    def __repr__(self):
        return self.asString

    def __str__(self):
        return self.asString

    def __float__(self):
        return self.asFloat


    def __add__(self, other):
        if isinstance(other, TimeInterval):
            return TimeCoord(self.asDatetime + other.timedelta, other.timeformat)
        else:
            return NotImplemented

    def __sub__(self, other):
        return self.asDatetime - other.asDatetime

    def __lt__(self, other):
        return float(self) < float(other)

    def __eq__(self, other):
        return self.asDatetime == other.asDatetime

class TimeInterval():
    def __init__(self, interval, unitindex=5, timeformat=None):
        #unit = "day" if unitindex in {0, 1} else timeunits[unitindex]
        unit = timeunits[unitindex]
        args = {unit+"s": interval}
        self.timedelta = datetime.timedelta(**args)
        self.unitIndex = unitindex
        self.interval = interval
        if timeformat:
            self.timeformat = timeformat
        else:
            self.timeformat = timeformats[unitindex]
            if unitindex == 3 and interval >= 6: self.timeformat = timeformats[2]
            if unitindex == 2 and interval >= 28: self.timeformat = timeformats[1]

    def __mul__(self, other):
        return TimeInterval(other*self.interval, self.unitIndex, self.timeformat)

    def __rmul__(self, other):
        return TimeInterval(other*self.interval, self.unitIndex, self.timeformat)

    def __str__(self):
        return str(self.timedelta)

    def __repr__(self):
        return str(self.timedelta)

    def __float__(self):
        return self.timedelta.total_seconds()/TimeCoord.scalefloat

def gettimescaleintervals(tc1, tc2, mindivs=5):
    def roundladder(x, ladder):
        for i in range(len(ladder) - 1):
            if x < ladder[i+1]: return ladder[i]
        return ladder[-1]

    interval = (tc2.asDatetime.timestamp() - tc1.asDatetime.timestamp()) / (mindivs-1)
    unitindex = 5
    while unitindex > 2:
        newinterval = interval/timefactors[unitindex]
        if newinterval < 1: break
        interval = newinterval
        unitindex -= 1

    ladderlist = [None, None, [1,2,7,14,28,91,364], [1,2,3,4,6,12], [1,2,5,10,15,30], [1,2,5,10,15,30]]
    subdivisors = [None, None, {1:(2,6), 2:(2,6), 7:(7,14), 14:(2,14), 28:(2,4), 91:(1,13), 364:(1,13)},
            {1:(2,6), 2:(2,6), 3:(3,6), 4:(4,8), 6:(6,12), 12:(3,12)},
            {1:(2,6), 2:(2,6), 5:(1,5), 10:(2,10), 15:(3,15), 30:(3,6)},
            {1:(2,6), 2:(2,6), 5:(1,5), 10:(2,10), 15:(3,15), 30:(3,6)}]
    scaleinterval = roundladder(interval, ladderlist[unitindex])
    (major, minor) = subdivisors[unitindex][scaleinterval]

    return TimeInterval(scaleinterval, unitindex), TimeInterval(scaleinterval/major, unitindex), TimeInterval(scaleinterval/minor, unitindex)

def roundtimedown(tc, scaleinterval):
    i = scaleinterval.unitIndex
    x = tc.unitlist[i]
    roundx = math.floor(x/scaleinterval.interval) * scaleinterval.interval
    if i ==2 and roundx == 0: roundx = 1
    roundedlist = tc.unitlist[:i] + [roundx] + [0]*(6-i)
    return TimeCoord(datetime.datetime(*roundedlist), scaleinterval.timeformat)

def roundtimeup(tc, scaleinterval):
    tc0 = roundtimedown(tc, scaleinterval)
    return tc0 if tc0.unitlist == tc.unitlist else tc0 + scaleinterval

