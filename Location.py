
##############################################################################
# CLASS::Location
# Purpose: Implements a Location in an organization.
# Requires: NAM, GLC, LMS, GCC, ACT, OPP, OCN
##############################################################################

class Location:
    def __init__(self,uid,model,**kwargs):
        self.model = model
        self.LOCID = uid             # Agent unique identifier
        self.latlon = kwargs["GLC"]
        self.lms = kwargs["LMS"]
        self.conus = kwargs["OCN"]
        self.addcosts = kwargs["ACT"]
        self.oppfactor = kwargs["OPP"] #Opportunity to exit for similar jobs
    
    def getLOCID(self): return self.LOCID
    def getlatlon(self): return self.latlon
    def getlms(self): return self.lms
    def getconus(self): return self.conus
    def getaddcosts(self): return self.addcosts
    def getoppfactor(self): return self.oppfactor
    
    def setLOCID(self,v): self.LOCID = v
    def setlatlon(self,v): self.latlon = v
    def setlms(self,v): self.lms = v
    def setconus(self,v): self.conus = v
    def setaddcosts(self,v): self.addcosts = v
    def setoppfactor(self,v): self.oppfactor = v
        
    def PrettyPrint(self):
        print("LOCID: ",self.LOCID) 
        print("\t latlon:",self.latlon)
        print("\t lms:",self.lms)
        print("\t conus:",self.conus)
        print("\t addcosts:",self.addcosts)
        print("\t oppfactor:",self.oppfactor)