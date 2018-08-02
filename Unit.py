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
import networkx as nx
from Billet import *
from Experience import *
from BaseAgent import *
##############################################################################

##############################################################################
# CLASS:: Unit
#
#  Purpose: Implements a generic agent in an organization.
#  Requires: CMD, UIC, NAM       
class Unit(Agent):
    def __init__(self,uid,model,**kwargs):
        super().__init__(uid, model)
        
        #Load Unit attributes
        self.cmdno = kwargs["CMD"]
        self.uic = kwargs["UIC"]
        self.name = kwargs["NAM"]
        
        #Choose the Unit Hiring / Assessment Policy (default values to be set later)
        d = np.random.normal(0.5,0.05)
        self.unitpolicy = {"funcexp":d, "geoexp":(1-d)}
        
        #Functional Organizational Focus and Experience
        self.agg_funcexp = None            #Aggregated Functional Experience Pandas Dataframe
        self.aggfuncarr = []               #Aggregated functions array over time
        
        #Geographic Organizational Focus and Experience
        self.geofocus = 0                  #kwargs["GEO"]
        self.agg_geoexp = None             #Aggregated Regional Experience Pandas Dataframe    
        self.aggregnarr = []               #Aggregated regions array overtime
        
        #Pointer to model's unit network... for readability
        self.unit_network = model.unit_network
        
        #The Unit's personnel records
        self.TDA = {}          #Force Structure
        self.roster = {}       #Employee roster 
        self.vacann = []       #Vacancy Announcements
        self.teams = nx.DiGraph()
        
        #Stats
        self.pcscost = 0
        self.civpay = []       #Civpay overtime
        self.fillrate = []     #Fillrate overtime
       
        
    ############################################################################  
    # Standard Get Functions
    def getUIC(self): return self.uic
    def getcmdno(self): return self.cmdno
    def getname(self): return self.name
    def getTDA(self): return self.TDA
    def getroster(self): return self.roster
    def getvacann(self): return self.vacann
    def getcivpay(self): return self.civpay
    def getfillrate(self): return self.fillrate
    def gethiringpol(self): return self.unitpolicy 
    ############################################################################  
    # Set the hiring policy where fexp + gexp = 1 
    def sethiringpol(self,fexp,gexp=None): 
        if gexp is None or (fexp + gexp != 1.0):
            self.unitpolicy = {"funcexp": fexp, "geoexp":(1.0-fexp)}
        else:
            self.unitpolicy = {"funcexp": fexp, "geoexp": gexp}
    
    ############################################################################  
    # Initialize the force structure by loading billets
    # Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC, PLN
    def InitTDA(self,**kwargs):
        # Create New Billet
        b = Billet(**kwargs) # Requires: UPN, AMS, AGD, ASR, KEY, OCC, LOC
        #Place on the TDA at Para-Line = PLN
        self.TDA[kwargs["PLN"]] = b
        #If Billet is Occupied by an employee (OCC), assign to that line
        if kwargs["OCC"] is not None:
            kwargs["OCC"].PLN = kwargs["PLN"]
            self.AssignEmployee(kwargs["PLN"],kwargs["OCC"])
            self.teams.add_node(kwargs["PLN"],occupant=kwargs["OCC"])
        else:
            self.teams.add_node(kwargs["PLN"],occupant=None)
            
    ############################################################################  
    # Setup the unit for operations
    def Setup(self):
        # Collect and record initial civpay
        self.RecordCivPay()
        
        # Calculate and record initial fillrate
        self.RecordFillRate()
        
        # Formulate list of all billets on the TDA
        billets = self.TDA.keys()
        
        # Setup the aggregations for stats DataFrame[Billet][functions /Regions]
        self.agg_funcexp = pd.DataFrame(index=list(billets),columns=[f for f in Functions().functions.keys()],data=0.0)
        self.agg_geoexp = pd.DataFrame(index=list(billets),columns=[r for r in GeoRegions().regions.keys()],data=0.0)
        
        len_f = len(Functions().functions)
        len_r = len(GeoRegions().regions)
        
        #Build team network first
        nnodes = list(billets)
        i=0
        supv_ID=0
        for paraln in billets:
            #Get the occupying employee Agent
            if self.TDA[paraln].isSupv():
                supv_ID = i 
                for otherparaln in billets:
                    if paraln != otherparaln:
                        self.teams.add_edge(paraln,otherparaln,weight=1,reg=RgnlSkillSet(),func=FuncSkillSet(),t=1)
            else:
                left = i-1
                if left < 0: left = len(nnodes)-1
                if  left == supv_ID:
                    if left == 0: left = len(nnodes)-1
                    else:left -= 1
                rght=  i+1
                if rght >= len(nnodes): rght = 0
                if rght ==supv_ID: 
                    if rght+1 == len(nnodes): rght=0
                    else:rght +=1
                self.teams.add_edge(nnodes[i],nnodes[left],weight=1,reg=RgnlSkillSet(),func=FuncSkillSet(),t=None)
                self.teams.add_edge(nnodes[i],nnodes[rght],weight=1,reg=RgnlSkillSet(),func=FuncSkillSet(),t=None)
            i+=1
                
        #For each billet, with ID == paraln
        for paraln in billets:   
            eid = self.TDA[paraln].occupant
            if eid is not None:
                #Record existing employee Agent 
                self.agg_funcexp.loc[paraln] = self.roster[eid].getfuncexparray()
                self.agg_geoexp.loc[paraln] = self.roster[eid].getgeoexparray()
                f_focus = np.random.randint(2,6)
                if int(self.roster[eid].grade) == 14:
                    #DEFAULT to Leadership
                    f_focus = 1
                    
                #Generate Task for the Employee
                t = self.model.taskgenerator.NewTask(self.geofocus,f_focus) 
                
                #Assign task to employee - right now randomly
                self.roster[eid].assigntask(t)

            else:
                #VACANT Billet... insert zeros
                self.agg_funcexp.loc[paraln] = np.zeros(len_f)
                self.agg_geoexp.loc[paraln] = np.zeros(len_r)
         
            
        
    ############################################################################  
    #
    def UpdateStats(self):
        #Record Civpay and Fillrates
        self.RecordCivPay()
        self.RecordFillRate()
        
        #Record skill levels
        for paraln in self.TDA.keys():
            eid = self.TDA[paraln].occupant
            if eid is not None:
                #Record existing employee Agent 
                self.agg_funcexp.loc[paraln] = self.roster[eid].getfuncexparray()
                self.agg_geoexp.loc[paraln] = self.roster[eid].getgeoexparray()
                i= len(self.roster[eid].chunks) - 1
                self.model.UnitMatrix.loc[self.uic, paraln][self.model.date] = self.model.learningcurve.GetExpLevel_Y(
                    self.roster[eid].chunks[i])
                
        #Record mean skill levels over time
        self.aggfuncarr.append(self.agg_funcexp.mean())
        self.aggregnarr.append(self.agg_geoexp.mean())
        
    ############################################################################  
    # Assign an employee agent to the unit: slot in TDA and add to roster
    def AssignEmployee(self,paraln,empagt):
        print("assigning employee")
        eid = empagt.getUPI()
        if empagt.status == "PCS":
            self.pcscost = 12500 * empagt.famsize #need a distance factor?
            empagt.salary = self.model.paytable.GetSalVal(empagt.curloc,empagt.grade,empagt.step)
        self.TDA[paraln].occupant = eid #Only store the employee ID
        self.TDA[paraln].status = "assigned"
        self.TDA[paraln].dwell = 1 
        self.roster[eid] = empagt       #Point to the actual agent
        self.roster[eid].PLN = paraln

    ############################################################################  
    # Release employee... add to released
    def ReleaseEmployee(self,eid):
        #Remove agent from the schedule
        self.model.RemoveAgent(self.roster[eid])
        
        #Get agent's location in the organization
        paraln = self.roster[eid].PLN
        
        #Remove experience from the organization
        self.agg_funcexp.loc[paraln] = np.zeros(len(Functions().functions))
        self.agg_geoexp.loc[paraln] = np.zeros(len(GeoRegions().regions))
        
        #Remove agent from the unit's authorization table
        self.TDA[paraln].Vacate()
        
        #Remove agent from the official roster
        self.roster.pop(eid)
        self.teams.node[paraln]["occupant"] = None 
        
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
        #get average daily by dividing by 52 weeks * 5 days/week ==> 260 days
        self.civpay.append(self.pcscost + daypay / 260)
        self.pcscost = 0
    
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
        self.UpdateStats()
        
        # Get list of cur_employees from the Roster
        cur_emps = list(self.roster.keys())
        for eid in cur_emps:
            
            #If Agent is retirement eligible, make the decision
            if self.roster[eid].retire_eligible :
                if np.random.rand() > 0.80:
                    #right now, it is based on a random draw at 20% chance... this should increase
                    self.roster[eid].status = BaseAgent.AGT_STATUS["retired"]
                    self.roster[eid].LastStatUpdate = self.model.date
                    
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
                        self.roster[eid].LastStatUpdate = self.model.date
                        print("Extending Employee ",eid," Again")
                    else:
                        self.roster[eid].status = BaseAgent.AGT_STATUS["nonextended"]
                        self.roster[eid].LastStatUpdate = self.model.date
                        #Employee should go on a placement list somewhere...
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["nonextended"]:
                if self.roster[eid].dwell >= (2*365):
                    print("Releasing Employee ",eid)
                    self.roster[eid].status = BaseAgent.AGT_STATUS["released"]
                    self.roster[eid].LastStatUpdate = self.model.date
                    self.ReleaseEmployee(eid)
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["Promoted"]:
                #Update status, change to SUPV (currently one level of promotion)
                self.roster[eid].LastStatUpdate = self.model.date
                self.roster[eid].supv = True
                #Find supervisory position
                for paraln in self.TDA.keys():
                    if self.TDA[paraln].isSupv():
                        if self.TDA[paraln].occupant == "Vacant":
                            print("POSSIBLE ERROR")
                        self.TDA[paraln].occupant = self.roster[eid]
            elif self.roster[eid].status == BaseAgent.AGT_STATUS["PCS"]:
                print("Need to implement PCS")
                self.roster[eid].LastStatUpdate = self.model.date
            #else:
                    #if (date + 240) >= deros and (dwell > 360):
            #       #   if not keypos
            #           #    employee.NonExtend
            #if status == PCS:
            #    #Employee has offer to move... 
            #    #if date = employee.pcs_date:
            #        #remove from roster
            #        self.ReleaseEmployee()
        
        for slot in self.TDA: 
            if self.TDA[slot].occupant is None:
                if self.TDA[slot].status == "Vacant":
                    # Move to fill vacancy]
                    print("Unit ",self.uic," is generating an RPA for ", slot)
                    self.TDA[slot].status = "Hiring"
                    print("*** NEED TO FIGURE OUT HOW TO SPECIFY REQUIRED SKILLS ****")
                    rpa_dict = {"GEX":list(self.agg_geoexp.sum()), "GEXWGHTS":[0],
                                "FEX":list(self.agg_funcexp.sum()), "FEXWGHTS":[0],
                                "UNIT":self, "BILLET":self.TDA[slot], 
                                "LOC":self.TDA[slot].getloc(), "PARALN": slot}
                    self.vacann.append( self.model.jobboard.Advertise(**rpa_dict) )
                elif self.TDA[slot].status is "PCS":
                    print("PCS:: self.vacann")
                elif self.TDA[slot].status is "Promote":
                    print("PCS:: self.vacann")