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
import pandas as pd
import networkx as nx
from BaseAgent import *
from JobBoard import *
from Location import *
from Unit import *
from Billet import *
from PayTable import *
from TaskGenerator import *
from mesa import Model, Agent
from mesa.time import RandomActivation


##############################################################################
# ReadNetLayout
#
def ReadNetLayout(file):
    G = nx.DiGraph()
    retlay = nx.random_layout(G)
    fd = open(file,'r') 
    for f in fd:
        flds = f.rstrip().replace('"','').split(" ")
        if len(flds) == 5:
            G.add_node(int(flds[0]),name=flds[1],layout=[float(flds[2]),float(flds[3])])
            retlay[int(flds[0])] = [float(flds[2]),float(flds[3])]
        elif len(flds) == 3:
            G.add_edge(int(flds[0]),int(flds[1]),weight=float(flds[2]))
        else:
            pass
    return G, retlay

##############################################################################
# CLASS:: Enterprise
#
#  Purpose: Implements a generic agent in an organization.
# Requires: FEX, FEXWGHTS, GEX, GEXWGHTS, UNIT, BILLET, LOC, EXP, LAG
class Enterprise(Model):
    ##########################################################################        
    #
    def __init__(self,basedate,fn=None):
        super().__init__(1)
        self.basedate = basedate                       #Model Start Date
        self.date = basedate                           #Model Date Counter
        self.num_baseagents = 0                        #Number of Agents
        self.num_locations = 0                         #Number of Locations
        self.num_units = 0                             #Number of Units
        self.locations = {}                            #Dictionary of Locations
        self.units = {}                                #Dictionary of Units
        self.deadpool = {"retired":[]}                 #Employee history
        self.paytable = None                           #Enterprise Pay Scale
        self.jobboard = None                           #Job Board
        self.agt_network = nx.DiGraph()                #Network of agents
        self.unit_network = nx.DiGraph()               #Organizational Structure
        self.unit_displaypos = None                    #Display units
        self.schedule = RandomActivation(self)         #MESA Activation Schedule
        self.taskgenerator = TaskGenerator(self)
        self.learningcurve = LearningCurve(2.5)
        self.filename = fn
        self.UnitMatrix = None
        
    ##########################################################################        
    #
    def Setup(self,ts=None):
        
        # Load Enterprise Pay Scale from file
        try: self.paytable = PayTable("2018-general-schedule-pay-rates.csv")
        except: print("Error loading Pay Table!")
        
        #Read in locations data
        #--> LOC, GLC, LMS, OPP, OCN, ACT, OPP
        locs = pd.DataFrame().from_csv("locations.csv").reset_index()
        loc_params = {}
        
        #Establish locations
        for l in locs.index:
            loc_params = {"GLC":locs.loc[l]["GLC"],"OPP":locs.loc[l]["OPP"],"OCN":locs.loc[l]["OCN"],
                          "LMS":locs.loc[l]["LMS"],"ACT":locs.loc[l]["ACT"]}
            loc = Location(locs.loc[l]["LOC"],**loc_params)
            self.locations[locs.loc[l]["LOC"]] = loc
            self.num_locations+=1
        
        #Read in unit data
        #--> Node ID, UIC, NAM, LOCID, CMD
        Units = pd.DataFrame().from_csv("orgs.csv")
        
        #Read in network specific chain of command
        self.unit_network, self.unit_displaypos = ReadNetLayout("command.net")  
        
        #Read in TDA data
        #--> UIC,UPN,LOCID,PLN,GRD,SER,STP,CMD,FND,OCN,EID,LNM,DERS,FMSZ,DWL,SKLZ,EXP,SCD
        if self.filename == None:
            TDAData = pd.DataFrame().from_csv("tdadata.csv").groupby("UIC")
            #TDAData = pd.DataFrame().from_csv("IDEAL_tdadata.csv").groupby("UIC")
        else:
            TDAData = pd.DataFrame().from_csv(self.filename).groupby("UIC")
        #Establish units
        unit_params = {}
        i=1
        for uic in Units.index:
            #Load Unit Location Data
            unit = Units.loc[uic]
            
            #Set up unit parameters UIC, name, and command
            unit_params = {"UIC":uic, "NAM":unit["NAM"], "CMD":unit["CMD"], "NID":unit["NID"]}
            
            #Instantiate Unit Agent
            newunit = Unit(i,self,**unit_params)
            
            #Load Unit Personnel Data//Build out TDA
            myo = TDAData.get_group(uic).reset_index()
            
            #keep track of Agents IDs for network instantiation
            netw = []
            supv_ID=0 
            for uid in myo.index:
                newagt = None
                if myo.loc[uid]["EID"] != "VACANT":
                    newagt = BaseAgent(myo.loc[uid]["EID"],self)
                
                    # Place Billet and Employee
                    s = self.paytable.GetSalVal(myo.loc[uid]["LOC"],myo.loc[uid]["GRD"],myo.loc[uid]["STP"])
                    emp_dict = {"SAL":s, "UNT": newunit}
                
                    #build required parameter string
                    for d in ["OCN", "TYP", "GRD", "SER", "STP", "LOC", "LNM", "DWL", "SCD", "FMS", "AGE","TIG","SUP","EXP"]:
                        emp_dict[d] = myo.loc[uid][d]
                    emp_dict["FEX"] = myo.loc[uid]["FEX"].split("|")
                    emp_dict["GEX"] = myo.loc[uid]["GEX"].split("|")
                    
                    newagt.NewPosition(**emp_dict)
                    
                    #Forceset the dwell on initialization
                    newagt.setdwell(myo.loc[uid]["DWL"])
                    
                    #Keep track of supervisor node
                    if emp_dict["SUP"]>0: supv_ID = newagt.getUPI()
                        
                    #Record the agent and their respective dwell
                    netw.append(newagt.getUPI())
                    
                    #add node to the AGENT network, UPI is the Node ID
                    self.agt_network.add_node(newagt.getUPI(),object=newagt)
                    
                    #record number of base agents
                    self.num_baseagents += 1
                    
                    #Add Employee agent to scheduler
                    self.schedule.add(newagt)
                
                #Place billet and occupant into TDA
                #build required parameter string
                tda_dict = {"OCC":newagt,"KEY":False}
                for d in ["UPN", "AMS", "AGD", "SER", "LOC", "PLN","SUP"]: 
                    tda_dict[d] = myo.loc[uid][d]               
                newunit.InitTDA(**tda_dict)
                
                #Adding node to the unit network
                self.unit_network.add_node(myo.loc[uid]["UPN"])
                #Adding Command Relationship
                self.unit_network.add_edge(myo.loc[uid]["UPN"], Units.loc[uic]["NID"])
            
            #Add location to Schedule
            #print("Adding unit:", newunit.getname())
            newunit.Setup()
            
            #self.schedule.add(newunit)
            self.units[newunit.uic] = newunit
            
            #Increase locid number 
            i+=1
            
        self.num_locations = i
        self.jobboard = JobBoard(0,self)
        #self.schedule.add(self.jobboard)
        
        #Setup Master Matrix
        tups = []
        if ts is not None:
            for uic in self.units.keys():
                for b in self.units[uic].TDA.keys():
                    tups.append((uic,b)) 
            idx = pd.MultiIndex.from_tuples(tups, names=["UIC","PLN"])
            self.UnitMatrix = pd.DataFrame(index=idx,columns=ts,data=0.0)
    
    ##########################################################################        
    #
    def PrintLocations(self):
        for a in self.schedule.agents:
            print(a)
            
    ##########################################################################        
    #
    def RemoveAgent(self,agt):
        if agt.status == BaseAgent.AGT_STATUS["retired"]:
            self.deadpool["retired"].append(agt)
        self.schedule.remove(agt)
        
    ##########################################################################        
    #
    def step(self):
        print("Model step ",self.date)
        self.date = self.date + dt.timedelta(days=1)
        #Step Through Agents
        self.schedule.step()
        
        #Step through units for clean-up
        #ul = np.random.shuffle(list(self.units.keys()))
        for u in self.units.keys():
            self.units[u].step()
        
        self.jobboard.step()