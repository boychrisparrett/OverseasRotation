##############################################################################
# Author: Christopher M. Parrett 
# Department of Computational and Data Sciences,
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################
import datetime as dt
import numpy.random as npr
import pandas as pd
from Location import *
#from PayTable import *
from modelenum import * 
from mesa import Agent
##############################################################################            
##############################################################################
# CLASS:: agent_base
#
# Purpose: Implements a generic agent in an organization.
#
class BaseAgent(Agent):
    AGT_ATTR_STR = ["Skills","MssnExperience","Location"]
    AGT_STATUS = {"unassigned":0,"assigned":1, "extended":2, "nonextended":3,"released":4,"retired":5}
    ############################################################################  
    #
    def __init__(self,uid,model):
        super().__init__(uid, model)
        self.UPI = uid             # Agent unique identifier
        self.lastname=""
        
        #Time-related Attributes
        self.SCD = model.date              #Service Computation Date
        self.DoB = model.date              #Date of birth (calc retirement age)
        self.DEROS = None                  #Date Estimated Return CONUS
        self.dwell = 1                     #Time on current Station
        self.daysinstep = 1                #Time in current step
        
        #Salary and Benefits information
        self.type = "GS"
        self.grade = 7
        self.series = 132
        self.paystep = 1
        self.famsize = 0
        self.salary = 0.0
        self.curloc = ""
        
        # Employment related information
        self.status = BaseAgent.AGT_STATUS["unassigned"]
        self.joboffer = None
        self.initiative = npr.randint(1,101) / 100 # Likelihood to move
        self.retire_eligible = False
        self.PLN = None
        
        # Agent Interaction Attributes
        self.unit = "" 
        self.unit_funcexp = FuncSkillSet()
        self.unit_rgnlexp = RgnlSkillSet()
        self.funcexp = FuncSkillSet()
        self.geoexp = RgnlSkillSet()
        self.network = None
        self.personalnet = None
        self.teammembers = []
        
        #records
        self.salhist = {}
        self.lochist = {}
        
    ############################################################################  
    # Standard Get / Set Routines to control access to attributes.
    def settype(self, v): self.type = v
    def setgrade(self, v): self.grade = v
    def setseries(self, v): self.series = v
    def setpaystep(self, v): self.paystep = v
    def setfamsize(self, v): self.famsize = v
    def setinitiative(self, v): self.initiative = v
    def setdwell(self, v): self.dwell = v
        
    def getUPI(self): return self.UPI
    def gettype(self): return self.type
    def getgrade(self): return self.grade
    def getdwell(self): return self.dwell
    def getseries(self): return self.series
    def getpaystep(self): return self.paystep
    def getsalary(self): return self.salary
    def getfamsize(self): return self.famsize
    def getinitiative(self): return self.initiative
    def getfuncexp(self): return self.funcexp
    def getgeoexp(self): return self.geoexp
    
    ############################################################################  
    # Network Specific routines
    def getteammembers(self): return self.teammembers
    def setteammembers(self,team): self.teammembers = team
           
    ############################################################################  
    # UpdatePersNet: 
    def UpdatePersNet(self,nbunch):
        nb = nbunch
        nb.append(self.UPI) #Add self to the network
        if self.personalnet is None:
            self.personalnet = nx.subgraph(self.network,nb)
        else:
            lbn = self.getteammembers()
            self.personalnet = nx.subgraph(self.network,(*nb,*lbn))
            
    
    ############################################################################  
    # UpdateLocation: Change Agent's location to a different unit
    def UpdateLocation(self, loc, deros):
        # Record location history
        self.lochist[self.model.date] = self.curloc
        
        # Reset Dwell time
        self.dwell = 1
        
        # Update to current location
        self.curloc = loc
        
        if deros is not None:
            self.deros = deros
        
    ############################################################################  
    #
    def InitFunctionalExp(self,exp):
        #Set initial functional experience
        self.funcexp.initfunc(exp)
        
    ############################################################################  
    #
    def InitGeographicExp(self,exp):
        #Set initial geographic experience
        self.geoexp.initrgnl(exp)
        
    ############################################################################  
    #
    def UpdateFunctionalExp(self,exp):
        for e in Functions:
            if e.value in exp:
                self.funcexp.incSkill(e.name)
            else:
                self.funcexp.decSkill(e.name)
        
    ############################################################################  
    #
    def UpdateGeographicExp(self,exp):
        for e in Regions:
            if e.value in exp:
                self.geoexp.incSkill(e.name)
            else:
                self.geoexp.decSkill(e.name)
                
    ############################################################################  
    #
    def UpdateSalary(self,sal):
        self.salhist[self.model.date] = sal
        self.salary = sal
    
    ############################################################################  
    #
    # Requires: OCN, TYP, GRD, SER, STP, LOC, GEX, FEX, SAL, LNM, TEAM
    def NewPosition(self, **kwargs):
        d = None
        #If an OCONUS duty station, calculate the DEROS FACTOR IN DWELL
        if kwargs["OCN"]:
            #calculate current date + 5 * 365")
            d = dt.datetime(self.model.date.year + 3,self.model.date.month,self.model.date.day)
            d = d - dt.timedelta(1)
            self.DEROS = d
            
        d = int(-365 * kwargs["SCD"])
        self.SCD = self.SCD + dt.timedelta(days=(d))
        
        d = int(-365 * kwargs["AGE"])
        self.DoB = self.DoB + dt.timedelta(days=(d))
        self.daysinstep =kwargs["TIG"]
        self.lastname=kwargs["LNM"]
        self.type = kwargs["TYP"]
        self.grade = kwargs["GRD"]
        self.series = kwargs["SER"]
        self.paystep = kwargs["STP"]
        self.famsize = kwargs["FMS"]
        self.UpdateLocation(kwargs["LOC"], d)
        self.InitFunctionalExp(kwargs["FEX"])
        self.InitGeographicExp(kwargs["GEX"])
        self.UpdateSalary(kwargs["SAL"])
        self.dwell = kwargs["DWL"]
        self.status = BaseAgent.AGT_STATUS["assigned"]
        self.unit = kwargs["UNT"]
        
    ############################################################################  
    #
    def step(self):
        # print("BaseAgent::Step")
        # Is it in a new area with more pay?
        # if job has my skills, will I apply?
        if self.status ==  BaseAgent.AGT_STATUS["assigned"] or self.status == BaseAgent.AGT_STATUS["extended"] or self.status ==  BaseAgent.AGT_STATUS["nonextended"]:
            
            self.dwell += 1
            self.daysinstep += 1
            timeinservice = (self.model.date - self.SCD).days / 365
            age = (self.model.date - self.DoB).days / 365
            if (timeinservice > 20.0) and (age > 55):
                self.retire_eligible = True
                print("\t **** Retirement Eligible ****")
                self.status = BaseAgent.AGT_STATUS["retired"]

            #Calculate time for within grade increase... simplistic
            if self.paystep != self.model.paytable.GetStep(self.paystep, self.daysinstep):
                print("Employee WGI: ", self.UPI)
                self.paystep += 1
                self.daysinstep = 1
                self.salary = self.model.paytable.GetSalVal(self.curloc,self.grade,self.paystep)

    ############################################################################  
    #
    def PrettyPrint(self):
        print("Employee ID: ",self.UPI)
        print("\t      Name: ",self.lastname)
        print("\t       Age: ",self.DoB)
        print("\t%s-%04d-%02d step %02d"%(self.type,self.series,self.grade,self.paystep))
        print("\t  Location: ",self.curloc)
        print("\t    Salary: $%6.2f"%(self.salary))
        print("\t       SCD: ",self.SCD)
        print("\tInitiative: ",self.initiative)
        print("\t  Fam Size: ",self.famsize)
        print("\t     Dwell: ",self.dwell)
        print("\t  func exp: ")
        self.funcexp.printSkill()
        print("\t   geo exp: ")
        self.geoexp.printSkill()
        print("\t     DEROS: ",self.DEROS)
        print("##-------------------------------##")
        