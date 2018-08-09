import matplotlib.pyplot as plt
from Enterprise import *

#############################################################################
def plotAgentAgeHist(m,fn):
    demographic = []
    for agt in m.schedule.agents:
        if type(agt) == BaseAgent and BaseAgent.AGT_STATUS["assigned"]:
            yrs = ((m.date-agt.DoB).days) / 365
            demographic.append(yrs)

    demographic.sort()
    npdemo = np.array(demographic)

    num_bins = 20
    mu = npdemo.mean()  # mean of distribution
    sigma = npdemo.std()  # standard deviation of distribution

    fig, ax = plt.subplots()

    # the histogram of the data
    n, bins, patches = ax.hist(npdemo, num_bins, density=1)

    # add a 'best fit' line
    y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
         np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
    ax.plot(bins, y, '--')
    ax.set_xlabel('Age Range')
    ax.set_ylabel('Num Agents')
    ax.set_title(r'Histogram of Agent Age')

    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.savefig(fn)
    
def plotAgentSCD(m,fn):
    demographic = []
    for agt in m.schedule.agents:
        if type(agt) == BaseAgent and BaseAgent.AGT_STATUS["assigned"]:
            yrs = ((m.date-agt.SCD).days) / 365
            demographic.append(yrs)

    demographic.sort()
    npdemo = np.array(demographic)

    num_bins = 20
    mu = npdemo.mean()  # mean of distribution
    sigma = npdemo.std()  # standard deviation of distribution

    fig, ax = plt.subplots()

    # the histogram of the data
    n, bins, patches = ax.hist(npdemo, num_bins, density=1)

    # add a 'best fit' line
    y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
         np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
    ax.plot(bins, y, '--')
    ax.set_xlabel('Age Range')
    ax.set_ylabel('Num Agents')
    ax.set_title(r'Histogram of Agent Service Date')

    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.savefig(fn)

#############################################################################

#instantiate the model
MasterMatrix=None
MasterUnitPay=None

ddays = 50*365
NumRuns = 10
start = dt.datetime.today()
for mdlrun in range(NumRuns):
    m = Enterprise(start)
    stop = m.date + dt.timedelta(days=50*365)
    ts = pd.date_range(start, stop)
    m.Setup(ts)

    #plotAgentSCD(m,("%d_%d_SCD_before.png"%(mdlrun,m.date.microsecond)))
    #plotAgentAgeHist(m,("%d_%d_AgeHist_before.png"%(mdlrun,m.date.microsecond)))

    start = m.date
    for i in range(ddays):
        m.step()
    stop = m.date + dt.timedelta(days=ddays)

    #plotAgentSCD(m,("%d_%d_SCD_after.png"%(m.date.microsecond,mdlrun)))
    #plotAgentAgeHist(m,("%d_%d_AgeHist_after.png"%(m.date.microsecond,mdlrun)))
    
    if MasterMatrix is None:
        MasterMatrix = m.UnitMatrix
        MasterUnitPay = pd.DataFrame(index=list(m.units.keys()),columns=ts,data=0.0)
        for u in m.units.keys():
            MasterUnitPay.loc[u] = np.array(m.units[u].civpay)
    else:
        MasterMatrix += m.UnitMatrix
        for u in m.units.keys():
            MasterUnitPay.loc[u] += np.array(m.units[u].civpay)

MasterMatrix /= NumRuns
MasterMatrix.to_csv(("%d_mastermatrix.csv"%m.date.microsecond))
MasterUnitPay /= 10
MasterUnitPay.to_csv(("%d_mastunitpay.csv"%m.date.microsecond))
