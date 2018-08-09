##############################################################################
# Author: Christopher M. Parrett 
# George Mason University, Department of Computational and Data Sciences
# Computational Social Science Program
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################
import datetime as dt
import numpy.random as npr
import pandas as pd
from Location import *
from Experience import * 
from TaskGenerator import *
from mesa import Agent

##############################################################################            
##############################################################################
# CLASS:: agent_base
#
# Purpose: Implements a generic agent in an organization.
#
GLBL_AGT_MRA = 57.0
GLBL_AGT_MIN_TIS = 20.0
GLBL_AGT_MAX_TIS = 40.0
GLBL_AGT_STD_SHIFT = 8.0

class BaseAgent(Agent):
    AGT_ATTR_STR = ["Skills","MssnExperience","Location"]
    AGT_STATUS = {"unassigned":0,"assigned":1, "extended":2, "nonextended":3,"released":4,"retired":5, "promoted":6, "PCS":7}
    ############################################################################  
    #
    def __init__(self,uid,model):
        super().__init__(uid, model)
        self.UPI = uid             # Agent unique identifier
        self.lastname=""
        
        #Time-related Attributes
        self.SCD = model.date              #Service Computation Date
        self.LastStatUpdate = model.date
        self.DoB = model.date              #Date of birth (calc retirement age)
        self.DEROS = None                  #Date Estimated Return CONUS
        self.dwell = 1                     #Time on current Station
        self.daysinstep = 1                #Time in current step
        
        #Salary and Benefits information
        self.type = "GG"                   #Pay Scale... will be GG for now
        self.grade = 7                     #Base grade is GG-07... prob not
        self.series = 132                  #Series is typically 0132 for closed system
        self.paystep = 1                   #Default to base step
        self.oplevel = 0                   #Level in the operational org-chart
        self.famsize = 0                   #Family size... important for PCS costs
        self.salary = 0.0                  #Civpay
        self.curloc = ""                   #Location determines locality supplement 
        self.clockhours = 0                #Total hours worked
        self.chunks = []                    #Total tasks completed
        
        # Employment related information
        self.status = BaseAgent.AGT_STATUS["unassigned"]     #Start off unattached
        self.applications = {}
        self.joboffers = {}
        self.acceptedoffer = None                            #Accepted job offer
        self.aptitude = npr.normal(0.9,0.05)                 #aptitude
        self.retire_eligible = False                         #Retirement eligble flag
        self.PLN = None
        self.supv = False
        
        
        # Agent Interaction Attributes
        self.unit = ""                                       #Current Unit
        self.funcexp = FuncSkillSet()                        #Current Functional Experience
        self.geoexp = RgnlSkillSet()                         #Current Regional Experience
        self.task = ""
        self.network = model.agt_network                     #Total network... unbounded
        self.teammembers = []                                #list of employee's teammember
        
        
        
        #records
        self.salhist = {}                                    #Employee's salary history
        self.lochist = {}                                    
        
    ############################################################################  
    # Standard Get / Set Routines to control access to attributes.
    def settype(self, v): self.type = v
    def setgrade(self, v): self.grade = v
    def setseries(self, v): self.series = v
    def setpaystep(self, v): self.paystep = v
    def setfamsize(self, v): self.famsize = v
    def setaptitude(self, v): self.aptitude = v
    def setdwell(self, v): self.dwell = v
    def setoplevel(self, v): self.oplevel = v
    def setsupv(self,v): self.supv = v
        
    # Assign task 
    def assigntask(self,t): self.task = t
    
    def getUPI(self): return self.UPI
    def gettype(self): return self.type
    def getgrade(self): return self.grade
    def getdwell(self): return self.dwell
    def getseries(self): return self.series
    def getpaystep(self): return self.paystep
    def getsalary(self): return self.salary
    def getfamsize(self): return self.famsize
    def getaptitude(self): return self.aptitude
    def getfuncexp(self): return self.funcexp
    def getgeoexp(self): return self.geoexp
    def getoplevel(self): return self.oplevel
    def issupv(self): return self.supv
    
    #for array calculations
    def getfuncexparray(self): return self.funcexp.getSkillArray()
    def getgeoexparray(self): return self.geoexp.getSkillArray()
    
    ############################################################################  
    # Network Specific routines
    def getteammembers(self): return self.teammembers
    def setteammembers(self,team): self.teammembers = team
    
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
            
        #Calculate service computation date
        d = int(-365 * kwargs["SCD"])
        self.SCD = self.SCD + dt.timedelta(days=(d))
        
        #Calculate age for minimum retirement age computation
        d = int(-365 * kwargs["AGE"])
        self.DoB = self.DoB + dt.timedelta(days=(d))
        
        self.daysinstep =kwargs["TIG"]         #Days in current time step
        self.lastname=kwargs["LNM"]            #Last name for human reading
        self.type = kwargs["TYP"]              #Employee type (e.g. - GS, GG, WG)
        self.grade = kwargs["GRD"]             #Grade/category for pay ranges
        self.series = kwargs["SER"]            #Occupational specialty
        self.paystep = kwargs["STP"]           #Current pay step
        self.famsize = kwargs["FMS"]           #Family size... for moving costs.
        self.UpdateLocation(kwargs["LOC"], d)  #Location... local market supplement (LMS)
        
        self.InitFunctionalExp(kwargs["FEX"], kwargs["EXP"])  #Functional experience
        self.InitGeographicExp(kwargs["GEX"], kwargs["EXP"])  #Geographic experience
        
        self.UpdateSalary(kwargs["SAL"])       #Current salary based on grade-step + LMS
        self.dwell = kwargs["DWL"]             #Current time at current duty station
        self.unit = kwargs["UNT"]
        self.supv = kwargs["SUP"]
        self.status = BaseAgent.AGT_STATUS["assigned"]
        self.LastStatUpdate = self.model.date
        self.chunks.append(self.model.learningcurve.GetChunkLevel_X(kwargs["EXP"]))
    
    ############################################################################  
    # InitFunctionalExp
    def InitFunctionalExp(self,fex,exp):
        #Get Current position in learning curve
        self.funcexp.initskills_arr(fex)
        
    ############################################################################  
    # InitGeographicExp
    def InitGeographicExp(self,gex,exp):
        #Get Current position in learning curve
        self.geoexp.initskills_arr(gex)
    
    ############################################################################  
    # UpdateSalary
    def UpdateSalary(self,sal):
        self.salhist[self.model.date] = sal
        self.salary = sal
            
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
    def ClearOffers(self):
        for app in self.applications:
            self.model.jobboard.Withdraw(app,self)
        self.applications = {}
        
        if self.acceptedoffer is not None:
            self.acceptedoffer["status"] = self.model.jobboard.JOB_STATUS["completed"]
        
        joffers = list(self.joboffers.keys())
        for offer in joffers:
            if self.joboffers[offer]["status"] != self.model.jobboard.JOB_STATUS["accepted"]:
                #print(self.lastname," removing offer",offer,"|-->",self.joboffers[offer])
                self.joboffers.pop(offer)
                
        
    
    ############################################################################  
    # 
    def ReceiveOffer(self,vacid,offer):
        #insert offer
        self.joboffers[vacid] = offer
    
    ############################################################################  
    # step
    def step(self):
        #AGE Agents
        if (self.status ==  BaseAgent.AGT_STATUS["assigned"] or self.status == BaseAgent.AGT_STATUS["extended"] or 
            self.status ==  BaseAgent.AGT_STATUS["nonextended"]):
            
            #Agent is still active in the organization... increase timesteps
            self.dwell += 1
            self.daysinstep += 1
            timeinservice = (self.model.date - self.SCD).days / 365
            age = (self.model.date - self.DoB).days / 365
            
            #Check for possibility of retirement
            if (timeinservice > GLBL_AGT_MIN_TIS) and (age > GLBL_AGT_MRA):
                self.retire_eligible = True
                print("\t **** Retirement Eligible ****")
            elif (self.dwell > 365) and (self.status == BaseAgent.AGT_STATUS["unassigned"]):
                print("Unemployable... retiring")
                self.retire_eligible = True
                
            #Calculate time for within grade increase... simplistic
            if self.paystep != self.model.paytable.GetStep(self.paystep, self.daysinstep):
                self.paystep += 1
                self.daysinstep = 1
                self.salary = self.model.paytable.GetSalVal(self.curloc,self.grade,self.paystep)
            
            #Clock in hours... increase experience
            if self.model.date.isoweekday() < 6:
                self.clockhours += GLBL_AGT_STD_SHIFT
                
                curr_func_delta = 0.75 - np.matmul(self.funcexp.getSkillArray(), self.task.getTaskasArr("func")) 
                curr_reg_delta  = 0.75 - np.matmul(self.geoexp.getSkillArray(), self.task.getTaskasArr("reg"))
                
                #First, try to donate...
                for ln in self.unit.teams.out_edges(self.PLN):
                    if self.unit.teams.nodes[ln[1]]["occupant"] is not None:
                        if curr_func_delta > 0:
                            self.unit.teams.edges[ln]["funcdelta"] = curr_func_delta / 2
                        else:
                            self.unit.teams.edges[ln]["funcdelta"] = 0.01
                            
                        if curr_reg_delta > 0:     
                            self.unit.teams.edges[ln]["regdelta"] = curr_reg_delta /2 
                        else:
                            self.unit.teams.edges[ln]["regdelta"] = 0.01    
                        self.network.add_edge(*ln,t=self.model.date)
                        
                #Gather donated effort 
                for ln in self.unit.teams.in_edges(self.PLN):
                    if self.unit.teams.nodes[ln[1]]["occupant"] is not None:
                        if curr_func_delta < 0:
                            if self.unit.teams.edges[ln]["funcdelta"] >= 0:
                                curr_func_delta += self.unit.teams.edges[ln]["funcdelta"]
                            else:
                                print("FAIL CONDITION... look to personal network?")
                            
                        if curr_reg_delta > 0:     
                            if self.unit.teams.edges[ln]["regdelta"] >= 0:
                                curr_reg_delta += self.unit.teams.edges[ln]["regdelta"] 
                            else:
                                print("FAIL CONDITION... look to personal network?")
                        self.network.add_edge(*ln,t=self.model.date)
                       
                #Check assigned task vs. current skills
                surplus_reg, numtasks, surplus_funarr = self.task.MeetTask(curr_reg_delta, curr_func_delta)
                
                # Chunks per step = (self_effort + SUM(in_effort) - SUM(out_effort)) * self_aptitude
                addchunks = (self.aptitude * numtasks)
                self.chunks.append(self.chunks[-1] + addchunks)

                #self.funcexp = agg_func_skills * self.model.learningcurve.GetExpLevel_Y(addchunks)
                #self.geoexp  = agg_reg_skills * self.model.learningcurve.GetExpLevel_Y(addchunks)
                
        elif self.status == BaseAgent.AGT_STATUS["unassigned"] or self.status == BaseAgent.AGT_STATUS["released"]:
            #Degrade skills
            age = (self.model.date - self.DoB).days / 365
            self.dwell += 1
            self.funcexp *= 0.99
            self.geoexp *= 0.99
        elif self.status == BaseAgent.AGT_STATUS["retired"]:
            #This should not ever be entered... 
            print("Warning: Accessing retired or released employee",self.UPI," ",self.lastname)
        
        #Look at job market
        if self.status != BaseAgent.AGT_STATUS["retired"]:
            #Step through job board
            for advert in self.model.jobboard.getopenings():
                #Don't submit for a position to which one has already applied
                if advert not in self.applications.keys():
                    #If more money/higher grade and local, apply.
                    opening = self.model.jobboard.openpos[advert]
                    if opening.location == self.curloc and opening.billet.getgrade() > self.grade and self.dwell > (2*365):
                        #promotion opportunity in-place
                        self.applications[advert] = {"status" : self.model.jobboard.JOB_STATUS["applied"]}
                        self.model.jobboard.Apply(advert,self)
                    elif self.status == BaseAgent.AGT_STATUS["unassigned"] and opening.billet.getgrade() >= self.grade:
                        self.applications[advert] = {"status" : self.model.jobboard.JOB_STATUS["applied"]}
                        self.model.jobboard.Apply(advert,self)
                    elif (self.status == BaseAgent.AGT_STATUS["nonextended"] and opening.billet.getgrade() >= 
                          self.grade and opening.location != self.curloc):
                        self.applications[advert] = {"status" : self.model.jobboard.JOB_STATUS["applied"]}
                        self.model.jobboard.Apply(advert,self)
                    
        #Check Job Offers
        joboffers = list(self.joboffers.keys())
        np.random.shuffle(joboffers)
        for offer in joboffers:
            if (self.joboffers[offer]["status"] == self.model.jobboard.JOB_STATUS["offered"]) and (self.status != BaseAgent.AGT_STATUS["PCS"]) and (self.status != BaseAgent.AGT_STATUS["promoted"]):
                if self.joboffers[offer]["loc"] == self.curloc and self.joboffers[offer]["grade"] > self.grade:
                    #print("\t\t Agent ",self.UPI," accepts promotion")
                    self.status = BaseAgent.AGT_STATUS["promoted"]
                    self.joboffers[offer]["status"] = self.model.jobboard.JOB_STATUS["accepted"]
                    self.acceptedoffer = self.joboffers[offer]
                    self.acceptedoffer["unit"].AddToGains(offer,self)
                elif self.joboffers[offer]["grade"] > self.grade:
                    #print("\t\t Agent ",self.UPI," accepts PCS")
                    self.status = BaseAgent.AGT_STATUS["PCS"]
                    #self.model.jobboard.AgentAcceptsOffer(offer,self)
                    self.joboffers[offer]["status"] = self.model.jobboard.JOB_STATUS["accepted"]
                    self.acceptedoffer = self.joboffers[offer]
                    self.acceptedoffer["unit"].AddToGains(offer,self)
                elif self.status == BaseAgent.AGT_STATUS["unassigned"]:
                    #print("\t\t Agent ",self.UPI," accepts offer")
                    if self.joboffers[offer]["loc"] != self.curloc:
                        #print("\t\t \tAgent will have to PCS")
                        self.status = BaseAgent.AGT_STATUS["PCS"]
                    else:
                        #print("\t\t \tAgent will have to PCS")
                        self.status = BaseAgent.AGT_STATUS["promoted"]
                    self.joboffers[offer]["status"] = self.model.jobboard.JOB_STATUS["accepted"]
                    self.acceptedoffer = self.joboffers[offer]
                    self.acceptedoffer["unit"].AddToGains(offer,self)
            else:
                #Nothing... get this out of my queue...
                #print("\t Agent ",self.UPI," removing offer ",offer," from queue")
                self.joboffers.pop(offer)
                
    ############################################################################  
    #
    def PrettyPrint(self):
        print(" Employee ID: ",self.UPI)
        print("\t      Name: ",self.lastname)
        print("\t       Age: ",self.DoB)
        print("\t%s-%04d-%02d step %02d"%(self.type,self.series,self.grade,self.paystep))
        print("\t  Location: ",self.curloc)
        print("\t    Salary: $%6.2f"%(self.salary))
        print("\t       SCD: ",self.SCD)
        print("\t  aptitude: ",self.aptitude)
        print("\t  Fam Size: ",self.famsize)
        print("\t     Dwell: ",self.dwell)
        print("\t    ParaLn: ",self.PLN)
        print("\t    Status: ",self.status)
        print("\t      Unit: ",self.unit)
        print("\t       UIC: ",self.unit.uic)
        print("\t  func exp: ")
        self.funcexp.PrettyPrint()
        print("\t   geo exp: ")
        self.geoexp.PrettyPrint()
        print("\t     DEROS: ",self.DEROS)
        print("##-------------------------------##")
        