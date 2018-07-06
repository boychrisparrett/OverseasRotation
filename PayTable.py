import pandas as pd
##############################################################################
##############################################################################
# CLASS:: PayTable
#
# Purpose: Simple class that reads in paytable
#
class PayTable:
    '''Read in the designated paytable into memory and group by locality. 
       Return the salary value when supplied the locality, grade, and step
    '''
    def __init__(self, fptr):
        self.paytabs = pd.DataFrame().from_csv(fptr).groupby("LOCNAME")
    
    def GetSalVal(self,loc,grade,step):
        st = "ANNUAL%d"%step
        return self.paytabs.get_group(loc)[st].iloc[int(grade)-1]
    
    def GetStep(self,curstep,timeinstep):
        if curstep < 4 and timeinstep >= 365:
            return curstep + 1
        elif curstep < 7 and timeinstep >= 2*365:
            return curstep + 1
        elif curstep >= 7 and curstep < 10 and timeinstep >= 3*365:
            return curstep + 1
        else:
            return curstep