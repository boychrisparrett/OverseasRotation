import datetime as dt
import pandas as pd
import networkx as nx
from BaseAgent import *
from JobBoard import *
from Location import *
from Unit import *
from Billet import *
from PayTable import *
from mesa import Model, Agent
from mesa.time import RandomActivation

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

class Enterprise(Model):
    def __init__(self,basedate):
        super().__init__(1)
        self.date = basedate
        self.num_baseagents = 0
        self.num_locations = 0
        self.locations = {}
        self.schedule = RandomActivation(self)
        self.paytable = PayTable("2018-general-schedule-pay-rates.csv")
        self.units = {}
        self.deadpool = []
        #
        #self.jobboard = JobBoard(0,self)
        #self.schedule.add(self.jobboard)
        
        self.agt_network = nx.Graph()
        self.unit_network = nx.DiGraph()
        self.unit_displaypos = None
        
    def LoadData(self):
        
        #Read in locations data
        #--> LOC, GLC, LMS, OPP, OCN, ACT, OPP
        locs = pd.DataFrame().from_csv("locations.csv").reset_index()
        loc_params = {}
        
        #Establish locations
        for l in locs.index:
            loc_params = {"GLC":locs.loc[l]["GLC"],"OPP":locs.loc[l]["OPP"],"OCN":locs.loc[l]["OCN"],
                          "LMS":locs.loc[l]["LMS"],"ACT":locs.loc[l]["ACT"]}
            loc = Location(locs.loc[l]["LOC"],self,**loc_params)
            self.locations[locs.loc[l]["LOC"]] = loc
            self.num_locations+=1
        
        #Read in unit data
        #--> Node ID, UIC, NAM, LOCID, CMD
        Units = pd.DataFrame().from_csv("orgs.csv")
        
        #Read in network specific chain of command
        self.unit_network, self.unit_displaypos = ReadNetLayout("command.net")  
        
        #Read in TDA data
        #--> UIC,UPN,LOCID,PLN,GRD,SER,STP,CMD,FND,OCN,EID,LNM,DERS,FMSZ,DWL,SKLZ,EXP,SCD
        TDAData = pd.DataFrame().from_csv("tdadata.csv").groupby("UIC")
    
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
            for uid in myo.index:
                newagt = None
                if myo.loc[uid]["EID"] != "VACANT":
                    newagt = BaseAgent(myo.loc[uid]["EID"],self)
                
                    # Place Billet and Employee
                    s = self.paytable.GetSalVal(myo.loc[uid]["LOC"],myo.loc[uid]["GRD"],myo.loc[uid]["STP"])
                    emp_dict = {"SAL":s, "UNT": newunit}
                
                    #build required parameter string
                    for d in ["OCN", "TYP", "GRD", "SER", "STP", "LOC", "LNM", "DWL", "SCD", "FMS", "AGE","TIG"]:
                        emp_dict[d] = myo.loc[uid][d]
                    emp_dict["FEX"] = myo.loc[uid]["FEX"].split("|")
                    emp_dict["GEX"] = myo.loc[uid]["GEX"].split("|")
                    
                    newagt.NewPosition(**emp_dict)
                    
                    #Unit aggregate experience
                    newunit.agg_funcexp.add(newagt.getfuncexp())
                    newunit.agg_geoexp.add(newagt.getgeoexp())
                    
                    #Forceset the dwell on initialization
                    newagt.setdwell(myo.loc[uid]["DWL"])
                    
                    #Record the agent and their respective dwell
                    netw.append([newagt.getUPI(),newagt.getdwell()])
                    
                    #add node to the network, UPI is the Node ID
                    self.agt_network.add_node(newagt.getUPI(),object=newagt)
                    
                    #record number of base agents
                    self.num_baseagents += 1
                    
                    #Add Employee agent to scheduler
                    self.schedule.add(newagt)
                
                # Place billet and occupant into TDA
                #build required parameter string
                tda_dict = {"OCC":newagt,"KEY":False}
                for d in ["UPN", "AMS", "AGD", "SER", "LOC", "PLN"]: 
                    tda_dict[d] = myo.loc[uid][d]               
                newunit.InitTDA(**tda_dict)
                
                #print("Adding node: ",myo.loc[uid]["UPN"])
                self.unit_network.add_node(myo.loc[uid]["UPN"])
                #print("Adding Edge from: ",myo.loc[uid]["UPN"]," to: ", Units.loc[uic]["NID"])
                self.unit_network.add_edge(myo.loc[uid]["UPN"], Units.loc[uic]["NID"])
                    
            for (n_i,i_w) in netw:
                for (n_j,j_w) in netw:
                    if (n_j != j_w):
                        dwellweight = i_w / j_w #Risk of DIV/0
                        self.agt_network.add_edge(n_i,n_j,weight=dwellweight)
                            
            #Add location to Schedule
            #print("Adding unit:", newunit.getname())
            newunit.RecordCivPay()
            newunit.RecordFillRate()
            #self.schedule.add(newunit)
            self.units[newunit.uic] = newunit
            
            #Increase locid number 
            i+=1
            
        self.num_locations = i

        #Load TDAs into Locations

    def PrintLocations(self):
        for a in self.schedule.agents:
            print(a)
            
    def RemoveAgent(self,agt):
        self.deadpool.append(agt)
        self.schedule.remove(agt)
        
    def step(self):
        print("Model step ",self.date)
        self.date = self.date + dt.timedelta(days=1)
        #Step Through Agents
        self.schedule.step()
        
        #Step through units for clean-up
        #ul = np.random.shuffle(list(self.units.keys()))
        for u in self.units.keys():
            self.units[u].step()
