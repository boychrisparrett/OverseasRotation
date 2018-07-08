##############################################################################
# Author: Christopher M. Parrett 
# George Mason University, Department of Computational and Data Sciences
# Computational Social Science Program
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################
from mesa import Agent, Model
import datetime as dt
import numpy as np
import pandas as pd
from Billet import *
from Experience import *
from BaseAgent import *
##############################################################################            
##############################################################################
# CLASS:: Unit
#
#  Purpose: Implements a generic agent in an organization.
# Requires: CMD, UIC, NAM       
class Unit(Agent):
    def __init__(self,uid,model,**kwargs):
        super().__init__(uid, model)
        self.cmdno = kwargs["CMD"]
        self.uic = kwargs["UIC"]
        self.name = kwargs["NAM"]
        #Default values to be set later
        d = np.random.normal(0.5,0.05)
        self.unitpolicy = {"funcexp":d, "geoexp":(1-d)}
        #Functional Organizational Focus and Experience
        self.agg_funcexp = None  #Aggregated Functional Experience Pandas Dataframe
        self.funcskills = FuncSkillSet()
        
        #Geographic Organizational Focus and Experience
        self.agg_geoexp = None   #Aggregated Regional Experience Pandas Dataframe
        self.geoskills = RgnlSkillSet()
        
        self.TDA = {}
        self.roster = {}
        self.vacann = []
        self.civpay = []
        self.fillrate = []

    ############################################################################  
    #
    def getUIC(self): return self.uic
    def getcmdno(self): return self.cmdno
    def getname(self): return self.name
    def getTDA(self): return self.TDA
    def getroster(self): return self.roster
    def getvacann(self): return self.vacann
    def getcivpay(self): return self.civpay
    def getfillrate(self): return self.fillrate
    def getgeoskills(self): return self.geoskills
    def getfuncskills(self): return self.funcskills
    
    def setgeofocus(self,v): self.geoskills = v
    def setreqskills(self,v): self.funcskills = v 
    def sethiringpol(self,fexp,gexp=None): 
        if gexp is None or (fexp + gexp != 1.0):
            self.unitpolicy = {"funcexp": fexp, "geoexp":(1.0-fexp)}
        else:
            self.unitpolicy = {"funcexp": fexp, "geoexp": gexp}
    
    ############################################################################  
    #
    # Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC, PLN
    def InitTDA(self,**kwargs):
        # Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC
        b = Billet(**kwargs)
        self.TDA[kwargs["PLN"]] = b
        if kwargs["OCC"] is not None:
            kwargs["OCC"].PLN = kwargs["PLN"]
            self.AssignEmployee(kwargs["PLN"],kwargs["OCC"])
            
    ############################################################################  
    #    
    def Initialize(self):
        self.RecordCivPay()
        self.RecordFillRate()
        billets = self.TDA.keys()
        self.agg_funcexp = pd.DataFrame(index=list(billets),columns=[f.name for f in Functions],data=0.0)
        self.agg_geoexp = pd.DataFrame(index=list(billets),columns=[r.name for r in Regions],data=0.0)
        for paraln in billets:
            eid = self.TDA[paraln].occupant
            if eid is not None:
                self.agg_funcexp.loc[paraln] = self.roster[eid].getfuncexparray()
                self.agg_geoexp.loc[paraln] = self.roster[eid].getgeoexparray()
            else:
                self.agg_funcexp.loc[paraln] = np.zeros(len(Functions))
                self.agg_geoexp.loc[paraln] = np.zeros(len(Regions))
    ############################################################################  
    #
    def AssignEmployee(self,paraln,empagt):
        eid = empagt.getUPI()
        self.TDA[paraln].occupant = eid
        self.roster[eid] = empagt
                       
    ############################################################################  
    #
    def ReleaseEmployee(self,eid):
        #Remove agent from the schedule
        self.model.RemoveAgent(self.roster[eid])
        
        #Get agent's location in the organization
        paraln = self.roster[eid].PLN
        
        #Remove experience from the organization
        self.agg_funcexp.loc[paraln] = np.zeros(len(Functions))
        self.agg_geoexp.loc[paraln] = np.zeros(len(Regions))
        
        #Remove agent from the unit's authorization table
        self.TDA[paraln].Vacate()
        
        #Remove agent from the official roster
        self.roster.pop(eid)
    
                
    ############################################################################  
    #
    def ExtendEmployee(self,eid):
        self.roster[eid].status = BaseAgent.AGT_STATUS["extended"]
        #reset dwell time to 1 and adjust DEROS by 2 years
        self.roster[eid].dwell = 1
        self.roster[eid].DEROS = self.roster[eid].DEROS - dt.timedelta(days=(2*365))
        
    ############################################################################  
    #
    def RecordCivPay(self):
        daypay = pd.Series([self.roster[eid].getsalary() for eid in self.roster]).sum()
        #get average daily by dividing by 260
        self.civpay.append(daypay / 260)
    
    ############################################################################  
    #
    def RecordFillRate(self):
        self.fillrate.append( len(self.roster) / len(self.TDA) )
    
    ############################################################################  
    #
    def PrettyPrint(self):
        print("Unit:", self.name)
        print("\t cmdno", self.cmdno)
        print("\t uic",self.uic)
        print("\t unitpolicy",self.unitpolicy)
        print("\t agg_funcexp:")
        self.agg_funcexp.printSkill()
        print("\t agg_geoexp:")
        self.agg_geoexp.printSkill()
        print("\t TDA:")
        for t in self.TDA.keys():
            print("\t\t ",t,"::",self.TDA[t])
        print("\t roster:")
        for t in self.roster.keys():
            print("\t\t ",t,"::",self.roster[t])
        print("\t vacann",self.vacann)
        print("\t civpay",self.civpay)
        print("\t fillrate",self.fillrate)
        print("------------------------------")    
    
        
    ############################################################################  
    #
    def step(self):
        #print("Unit::Step")
        #record stats at begining of day...
        self.RecordCivPay()
        self.RecordFillRate()
        
        #Should check for weekend here... only work M-F...
        '''
        for slot in self.TDA: 
            if self.TDA[slot].occupant is None:
                # Move to fill vacancy
                rpa_dict = {"GEX":self.geofocus, "GEXWGHTS":[0],
                            "FEX":self.reqskills, "FEXWGHTS":[0],
                            "UNIT":self, "BILLET":self.TDA[slot], 
                            "LOC":self.TDA[slot].getloc()}
                print("\t\t Vacancy Announcement")
                self.vacann.append( self.model.jobboard.Advertise(**rpa_dict) )
        '''
        cur_emps = list(self.roster.keys())
        for eid in cur_emps:
            #If Agent is retirement eligible, make the decision
            if self.roster[eid].retire_eligible :
                if np.random.rand() > 0.80:
                    #right now, it is based on a random draw at 20% chance... this should increase
                    self.roster[eid].status = BaseAgent.AGT_STATUS["retired"]
                    
            #Run through current roster
            if self.roster[eid].status == BaseAgent.AGT_STATUS["retired"]:
                print("Employee Retiring: ", self.roster[eid].lastname, " EID: ",eid, " PARALN: ",self.roster[eid].PLN)
                #Remove from unit
                self.ReleaseEmployee(eid)
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["assigned"]:
                #Deal with assigned employees... OCONUS first
                if self.roster[eid].DEROS is not None:
                    if self.roster[eid].dwell >= (3*365):
                        print("Extending Employee: ", self.roster[eid].lastname, " EID: ",eid)
                        self.ExtendEmployee(eid)
                else:
                    #CONUS Employee... no need for anything now
                    pass
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["extended"]:
                #Only if an OCONUS Assignment
                if self.roster[eid].dwell >= (1.5*365):
                    if np.random.rand() > 0.05:
                        self.ExtendEmployee(eid)
                        print("Extending Employee ",eid," Again")
                    else:
                        self.roster[eid].status = BaseAgent.AGT_STATUS["nonextended"]       
                        #Employee should go on a placement list somewhere...
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["nonextended"]:
                if self.roster[eid].dwell >= (2*365):
                    print("Releasing Employee ",eid)
                    self.roster[eid].status = BaseAgent.AGT_STATUS["released"]
                    self.ReleaseEmployee(eid)
                
            #else:
                    #if (date + 240) >= deros and (dwell > 360):
            #       #   if not keypos
            #           #    employee.NonExtend
            #if status == PCS:
            #    #Employee has offer to move... 
            #    #if date = employee.pcs_date:
            #        #remove from roster
            #        self.ReleaseEmployee()
