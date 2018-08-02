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
import numpy as np
import pandas as pd
import datetime as dt
from random import choice
from BaseAgent import *

##############################################################################
# CLASS:: JobBoard
#
#  Purpose: Implements a generic agent in an organization.
# Requires: FEX, FEXWGHTS, GEX, GEXWGHTS, UNIT, BILLET, LOC, EXP, LAG
class VacancyAnnouncement:
    def __init__(self,uid,model,**kwargs):
        self.model = model
        self.uid = uid
        self.opendate = kwargs["SDATE"]
        self.vacid = kwargs["SUID"]
        self.expires = self.opendate + dt.timedelta(kwargs["EXP"])
        self.lagtime = np.random.randint(kwargs["EXP"],kwargs["LAG"])
        self.funcexp = kwargs["FEX"]
        self.vacfuncwght = kwargs["FEXWGHTS"]
        self.geoexp = kwargs["GEX"]
        self.vacgeowght = kwargs["GEXWGHTS"]
        self.open = True
        self.status = "open"
        self.completedate = kwargs["SDATE"]
        self.paraln = kwargs["PARALN"]
        #Object pointers                  
        self.unit = kwargs["UNIT"]
        #self.unitpolicy = self.unit.gethiringpol()
        self.unitpolicy = {"funcexp":0.6, "geoexp":0.4}
        self.billet = kwargs["BILLET"]
        self.location = kwargs["LOC"]
        self.applicants = []
        self.candidates = []
    
    ##########################################################################
    ##        
    def AddApplicant(self,appagt):
        if self.open:
            #!!! Can add additional policies here.
            self.applicants.append(appagt)
            
    ##########################################################################
    ##        
    def isClosed(self): return not self.open
    
    ##########################################################################
    ##
    def step(self):
        if self.expires < self.model.date:
            self.open = False
            self.status = "closed"
            
    ##########################################################################
    ##    
    def PrettyPrint(self):
        print("Vacancy #:",self.vacid)
        print("\t Open Date:",self.opendate)
        print("\t    Closes:",self.expires)
        print("\t    Slot #:",self.billet)    
        print("\t  Location:",self.location)
        print("\t    status:",self.status)

        
##############################################################################
##############################################################################

##############################################################################
# CLASS:: JobBoard
#
#
class JobBoard(Agent):
    ##########################################################################
    ##    
    def __init__(self,uid, model):
        super().__init__(uid, model)
        self.openpos = {}
        self.closedpos = {}
        self.completedpos = {}
        self.numttlpos= 0
        self.avghirelag = 90 #days
        self.minopentime = 14 #days
    
    ##########################################################################
    ##
    def getopenings(self): return self.openpos
    def getclosed(self): return self.closedpos
    
    ##########################################################################
    ## Generate a Unique ID number for the vacancy announcement
    def getUniqueID(self,d,i=1):
        #Create unique ID
        s=("%04d%02d%02d%02d%02d%02d_W%04d"%(d.year,d.month,d.day,d.hour,d.minute,d.second,i))
        if (s in self.openpos.keys()):
            s = self.getUniqueID(d,i+1)
        return s
    
    ##########################################################################
    ## Step through vacancy announcements
    def step(self):
        #keys = list(self.openpos.keys())
        #np.random.shuffle(keys)        
        #for advert in keys:
        #    self.openpos[advert].step()
        #    if self.openpos[advert].status == "closed":
        #        self.closedpos[advert] = self.openpos[advert]
        #        self.openpos.pop(advert)
                
        #Check expiration date on new applications
        self.UpdateListings()
        
        #Select Candidates on Closed positions
        self.RankSelect()
        
    ##########################################################################
    ## Update Listings 
    def UpdateListings(self):
        #Step through each vacancy and check for expirations...
        
        #Randomize order
        listings = list(self.getopenings().keys())
        np.random.shuffle(listings)
        for vacid in listings:
            #Have each vacancy ID update it
            self.openpos[vacid].step()
            
            #If the announcement has expired, close it and move it to close
            if self.openpos[vacid].isClosed():
            
                #Time to close vacancy announcement... put in closed queue
                self.closedpos[vacid] = self.openpos[vacid]
                
                #Remove from open queue
                self.openpos.pop(vacid)
        
        #Step through each closed vacancy...
        #Randomize order
        listings = list(self.getclosed().keys())
        np.random.shuffle(listings)
        for vacid in listings:
            #Check to see if closed position status == offered
            if self.closedpos[vacid].status == "offered":
                print(vacid," moving to completed")
                self.completedpos[vacid] = self.closedpos[vacid]
                self.closedpos.pop(vacid)
    
    ##########################################################################
    ##  Rank each vacancy and then select           
    def RankSelect(self):
        for vacid in self.closedpos:
            #Adjust for lagtime
            status = self.closedpos[vacid].status
            if status == "selected":
                pass
            elif status == "accepted":
                pass
            elif ((self.closedpos[vacid].expires + dt.timedelta(self.closedpos[vacid].lagtime)) < 
                  self.model.date) or (status == "declined"):
                finalidx, final = self.AppReviewPolicy(vacid)
                if final is None:
                    #There were no applicants 
                    self.closedpos[vacid].status = "cancelled"
                    self.closedpos[vacid].completedate = self.model.date  
                else:
                    self.ExtendOffer(vacid,finalidx,final)
    
    ##########################################################################
    ##
    def Advertise(self,**kwargs):
        #Create open date and unique identifier
        sudate = self.model.date
        suid = self.getUniqueID(sudate)
        
        #Generate the vacancy announcement
        advert = VacancyAnnouncement(self.numttlpos,self.model,**kwargs, EXP=self.minopentime, 
                                     LAG=self.avghirelag, SDATE=sudate, SUID=suid)
        
        #Update the object statistics
        self.openpos[advert.vacid] = advert
        self.numttlpos += 1
        
        #Return the locator ID to the unit
        for i in range(np.random.randint(1,5)):
            ragt = self.GenerateRandAgt()
            ragt.applications[advert.vacid] = {"status" : "applied"}
            self.Apply(advert.vacid, ragt)
            self.model.schedule.add(ragt)
        return suid
    
    ##########################################################################
    ##    
    def Apply(self,vacid,agt):
        self.openpos[vacid].AddApplicant(agt)
    
    ##########################################################################
    ##
    def ExtendOffer(self,vacid,finalidx,final):
        print(self.closedpos[vacid].applicants[finalidx].PrettyPrint())
        print("VACID:",vacid,"  ",self.closedpos[vacid].applicants[finalidx].applications)
        
        #Notify applicant
        self.closedpos[vacid].status = "offered"
        self.closedpos[vacid].applicants[finalidx].applications[vacid]["status"] = self.closedpos[vacid].status
        
        self.closedpos[vacid].applicants[finalidx].joboffers[vacid] = {
            "unit": self.closedpos[vacid].unit,
            "grade": self.closedpos[vacid].billet.authgrade,
            "loc":self.closedpos[vacid].location,
            "startdate": (self.model.date + dt.timedelta(days=np.random.randint(14,60))),
            "status": self.closedpos[vacid].status
        }

    ##########################################################################
    ##    
    def AgentAcceptsOffer(self,vacid,agt):
        self.closedpos[vacid].status = "accepted"
        self.closedpos[vacid].unit.AssignEmployee(self.closedpos[vacid].paraln, agt)
    
    ##########################################################################
    ##    
    def AppReviewPolicy(self,vacid): 
        #Initialize the data frames
        inal = None
        finalidx = -1
        highest = -1
        i = 0
        for appagt in self.closedpos[vacid].applicants:
            rank = pow(sum(appagt.funcexp.getSkillArray()),self.closedpos[vacid].unitpolicy["funcexp"])
            rank +=pow(sum(appagt.funcexp.getSkillArray()),self.closedpos[vacid].unitpolicy["geoexp"])
            if rank > highest: 
                highest = rank
                final = appagt
                finalidx = i
            i += 1
        
        print("FINAL SELECTION MATRIX\n ------------------------------------------------------------")
        print(finalidx,"  ",self.closedpos[vacid].applicants[finalidx].UPI,"\n ------------------------------------------------------------")
        return finalidx, final
    
            
    ##########################################################################
    ##    
    def GenerateRandAgt(self):
        #generate new id
        uid = np.random.randint(4000,10000)
        agt = BaseAgent(uid,self.model)
        agt.lastname = ("newemp_%s"%uid)
        
        age = np.random.randint(20,40)
        agt.SCD = agt.SCD - dt.timedelta(days=int(365*age/10))
        agt.DoB = agt.DoB - dt.timedelta(days=365*age)
        
        agt.funcexp.initskills_arr(np.random.normal(0.7,0.5,6))
        
        regidx = np.random.randint(1,6)
        agt.geoexp.initskill(regidx,np.random.normal(0.7,0.5))
        
        return agt