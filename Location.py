##############################################################################
# Author: Christopher M. Parrett 
# George Mason University, Department of Computational and Data Sciences
# Computational Social Science Program
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################

##############################################################################
# CLASS::Location
# Purpose: Implements a Location in an organization.
# Requires: NAM, GLC, LMS, GCC, ACT, OPP, OCN
class Location:
    def __init__(self,uid,**kwargs):
        self.LOCID = uid                       # Unique identifier
        self.latlon = kwargs["GLC"]            # Lat/Lon of location
        self.lms = kwargs["LMS"]               # Local Market Supplement (LMS)
        self.conus = kwargs["OCN"]             # Overseas flag
        self.addcosts = kwargs["ACT"]          # Additional costs (%housing,etc.)
        self.oppfactor = kwargs["OPP"]         # Opportunity/market competition
                                               #    for similar jobs
    
    ## Standard Get Routines
    def getLOCID(self): return self.LOCID
    def getlatlon(self): return self.latlon
    def getlms(self): return self.lms
    def getconus(self): return self.conus
    def getaddcosts(self): return self.addcosts
    def getoppfactor(self): return self.oppfactor
    
    ## Standard Set Routines
    def setLOCID(self,v): self.LOCID = v
    def setlatlon(self,v): self.latlon = v
    def setlms(self,v): self.lms = v
    def setconus(self,v): self.conus = v
    def setaddcosts(self,v): self.addcosts = v
    def setoppfactor(self,v): self.oppfactor = v
        
    ##########################################################################
    ## Pretty Print for verification purposes
    def PrettyPrint(self):
        print("LOCID: ",self.LOCID) 
        print("\t latlon:",self.latlon)
        print("\t lms:",self.lms)
        print("\t conus:",self.conus)
        print("\t addcosts:",self.addcosts)
        print("\t oppfactor:",self.oppfactor)