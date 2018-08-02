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
# CLASS:: Billet
#
# Purpose: Implements a generic billet for a TDA.
# Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC
class Billet:
    def __init__(self,**kwargs):
        self.UPN = kwargs["UPN"]          #Universal Personnel Number
        self.AMSCO = kwargs["AMS"]        #Funding stream
        self.authgrade = kwargs["AGD"]    #Authorized Grade
        self.authseries = kwargs["SER"]   #Authorized Series/Speciality
        self.key = kwargs["KEY"]          #Key position?
        self.occupant = kwargs["OCC"]     #Pointer to BaseAgent/Employee
        self.location = kwargs["LOC"]     #Locality of position.
        self.supv = kwargs["SUP"]         #Is a supervisor?
        self.status = "Vacant"            #Vacant/Filled/Hiring/Hold
        
    ##########################################################################    
    # Standard Get routines    
    def getupn(self): return self.UPN
    def getamsco(self): return self.AMSCO
    def getprog(self): return self.prog
    def getgrade(self): return self.authgrade
    def getseries(self): return self.authseries
    def getoccupant(self): return self.occupant
    def getloc(self): return self.location
    def isKeyPos(self): return self.key
    def isSupv(self): return self.supv
    
    ##########################################################################    
    ## Modifying routines
    def makeSupv(self): self.supv = True
    def makeNonSupv(self): self.supv = False
    def KeyPos(self,kp): self.key = kp             #Designate key positions
    def Fill(self, occ): 
        self.occupant = occ       #Slot employee against billet
        self.status = "Filled"
    def Vacate(self): 
        self.occupant = None         #Remove employee from billet
        self.status = "Vacant"
    def Restructure(self,ams,grd,ser):             #Restructure billet  
        self.AMSCO = ams
        self.authgrade = grd
        self.authseries = ser
    ##########################################################################    
    ## Management Directed Reassignment
    def MDR(self, to_loc): self.location = to_loc  #Move billet to new location
    
    ##########################################################################
    ## Pretty Print for verification purposes
    def PrettyPrint(self):
        print("\t\tUPN ", self.UPN)
        print("\t\tAMSCO ", self.AMSCO)
        print("\t\tAuthgrade ", self.authgrade)
        print("\t\tAuthseries ", self.authseries)
        print("\t\tKey ", self.key)
        print("\t\tOccupant ", self.occupant)
        print("\t\tLocation ", self.location)