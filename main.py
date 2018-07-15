import datetime as dt
from Enterprise import *
 
m = Enterprise(dt.datetime.today())
m.Setup()
start = m.date
ddays = 1*365

for i in range(ddays):
    m.step()
    
stop = m.date + dt.timedelta(days=ddays)
