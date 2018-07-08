##############################################################################
# Author: Christopher M. Parrett 
# George Mason University, Department of Computational and Data Sciences
# Computational Social Science Program
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################
import pandas as pd

##############################################################################
# CLASS:: PayTable
#
# Purpose: Simple class that reads in paytable
#
class PayTable:
    '''Read in the designated paytable into memory and group by locality. 
       Return the salary value when supplied the locality, grade, and step.
       This is designed to read in the output from OPM located at:
       https://www.opm.gov/policy-data-oversight/pay-leave/salaries-wages
    '''
    ########################################################################
    #
    #
    def __init__(self, fptr):
        self.paytabs = pd.DataFrame().from_csv(fptr).groupby("LOCNAME")
    
    ########################################################################
    #
    #
    def GetSalVal(self,loc,grade,step):
        st = "ANNUAL%d"%step
        return self.paytabs.get_group(loc)[st].iloc[int(grade)-1]
    
    ########################################################################
    #
    #
    def GetStep(self,curstep,timeinstep):
        if curstep < 4 and timeinstep >= 365:
            return curstep + 1
        elif curstep < 7 and timeinstep >= 2*365:
            return curstep + 1
        elif curstep >= 7 and curstep < 10 and timeinstep >= 3*365:
            return curstep + 1
        else:
            return curstep