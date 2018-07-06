##############################################################################            
##############################################################################
# CLASS:: Billet
#
# Purpose: Implements a generic agent in an organization.
# Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC
class Billet:
    def __init__(self,**kwargs):
        self.UPN = kwargs["UPN"]
        self.AMSCO = kwargs["AMS"]
        self.authgrade = kwargs["AGD"]
        self.authseries = kwargs["SER"]
        self.key = kwargs["KEY"]
        self.occupant = kwargs["OCC"]
        self.location = kwargs["LOC"]
        
    def getupn(self): return self.UPN
    def getamsco(self): return self.AMSCO
    def getprog(self): return self.prog
    def getgrade(self): return self.authgrade
    def getseries(self): return self.authseries
    def getoccupant(self): return self.occupant
    def getloc(self): return self.location
    def isKeyPos(self): return self.key
    
    def KeyPos(self,kp): self.key = kp #boolean: True if key pos
    def Fill(self, occ): self.occupant = occ
    def Vacate(self): self.occupant = None
    def Restructure(self,ams,grd,ser):
        self.AMSCO = ams
        self.authgrade = grd
        self.authseries = ser
    def MDR(self, to_loc):
        self.location = to_loc
    def PrettyPrint(self):
        print("\t\tUPN ", self.UPN)
        print("\t\tAMSCO ", self.AMSCO)
        print("\t\tAuthgrade ", self.authgrade)
        print("\t\tAuthseries ", self.authseries)
        print("\t\tKey ", self.key)
        print("\t\tOccupant ", self.occupant)
        print("\t\tLocation ", self.location)