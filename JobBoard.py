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
        self.status = JobBoard.JOB_STATUS["open"]
        self.completedate = kwargs["SDATE"]
        self.paraln = kwargs["PARALN"]
        #Object pointers                  
        self.unit = kwargs["UNIT"]
        #self.unitpolicy = self.unit.gethiringpol()
        self.unitpolicy = {"funcexp":0.6, "geoexp":0.4}
        self.billet = kwargs["BILLET"]
        self.location = kwargs["LOC"]
        self.applicants = []
        self.candidate = None
    
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
            self.status = JobBoard.JOB_STATUS["closed"]
            
    ##########################################################################
    ##    
    def PrettyPrint(self):
        print("Vacancy #:",self.vacid)
        print("\t Open Date:",self.opendate)
        print("\t    Closes:",self.expires)
        print("\t      Unit:",self.unit.uic)
        print("\t    Slot #:",self.paraln)    
        print("\t  Location:",self.location)
        print("\t    status:",self.status)
        print("\t Completed:",self.completedate)
        print("\t#Applicant:",len(self.applicants))
        print("\t  Selectee:",self.candidate)
        
##############################################################################
##############################################################################

##############################################################################
# CLASS:: JobBoard
#
#
class JobBoard(Agent):
    JOB_STATUS = {"open":0,"closed":1,"offered":2,"accepted":3,"declined":4,"canceled":5,"applied":6,"completed":7,"rejected":8}
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
    ## Withdraw
    def Withdraw(self,vacid,empagt):
        if vacid in self.openpos: 
            if empagt in self.openpos[vacid].applicants:
                self.openpos[vacid].applicants.remove(empagt)
        elif vacid in self.closedpos:
            if empagt in self.closedpos[vacid].applicants:
                self.closedpos[vacid].applicants.remove(empagt)
             
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
        
        #Check for PCS... must cut orders
        vaclist = list(self.closedpos.keys())
        for vacid in vaclist:
            #print("\t",vacid," has status ",self.closedpos[vacid].status)
            if self.closedpos[vacid].candidate is not None:
                if self.closedpos[vacid].candidate.acceptedoffer is not None:
                    if self.closedpos[vacid].candidate.acceptedoffer["status"] == JobBoard.JOB_STATUS["completed"]:
                        self.AgentAcceptsOffer(vacid,self.closedpos[vacid].candidate)
                
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
                
        #Step through each closed vacancy and check for completions...
        for vacid in self.closedpos.keys():
            if self.closedpos[vacid].status == JobBoard.JOB_STATUS["completed"]:
                self.completedpos[vacid] = self.closedpos[vacid]
                self.closedpos.pop(vacid)
                
    ##########################################################################
    ##  Rank each vacancy and then select           
    def RankSelect(self):
        for vacid in self.closedpos:
            #Adjust for lagtime
            status = self.closedpos[vacid].status
            if ((self.closedpos[vacid].expires + dt.timedelta(self.closedpos[vacid].lagtime)) < self.model.date):
                if (status == JobBoard.JOB_STATUS["closed"]) or (status == JobBoard.JOB_STATUS["declined"]):
                    finalidx, final = self.AppReviewPolicy(vacid)
                    if final is None:
                        #There were no applicants 
                        print("There were no applicants; announcement cancelled")
                        self.closedpos[vacid].status = JobBoard.JOB_STATUS["cancelled"]
                        self.closedpos[vacid].completedate = self.model.date
                        self.completedpos[vacid] = self.closedpos[vacid]
                        self.closedpos.pop(vacid)
                    else:
                        print("Extending offer to ",finalidx, " agt " ,final.UPI)
                        self.ExtendOffer(vacid,finalidx,final)
                        self.closedpos[vacid].candidate = self.closedpos[vacid].applicants[finalidx]
                        
    ##########################################################################
    ##    
    def AppReviewPolicy(self,vacid): 
        #Initialize the data frames
        final = None
        finalidx = -1
        highest = -1
        i = 0
        #print("\t\tReviewing ", len(self.closedpos[vacid].applicants)," applicants for VACID: ",vacid," with status ",self.closedpos[vacid].status)
        for appagt in self.closedpos[vacid].applicants:
            rank = pow(sum(appagt.funcexp.getSkillArray()),self.closedpos[vacid].unitpolicy["funcexp"])
            rank +=pow(sum(appagt.funcexp.getSkillArray()),self.closedpos[vacid].unitpolicy["geoexp"])
            
            if np.isreal(rank) and rank > highest:
                highest = rank
                final = appagt
                finalidx = i
            #Set as reviewed... then revert the selected one later; saves some processes
            appagt.applications[vacid]["status"] = JobBoard.JOB_STATUS["rejected"]
            i += 1
        
        #print("\t\t#-------------------------------------------------------#")
        #print("\t\t# FINAL SELECTION MATRIX")
        #print("\t\t#",vacid,"  ",finalidx,"  ",self.closedpos[vacid].applicants[finalidx].UPI)
        #print("\t\t#-------------------------------------------------------#")
        return finalidx, final
    
            
    ##########################################################################
    ##
    def ExtendOffer(self,vacid,finalidx,final):
        #Change state to offered
        self.closedpos[vacid].status = JobBoard.JOB_STATUS["offered"]
        
        #Populate the job offer
        offer = {
            "unit": self.closedpos[vacid].unit,
            "grade": self.closedpos[vacid].billet.authgrade,
            "paraln": self.closedpos[vacid].paraln,
            "loc":self.closedpos[vacid].location,
            "startdate": (self.model.date + dt.timedelta(days=np.random.randint(14,60))),
            "status": JobBoard.JOB_STATUS["offered"]
        }
        
        #Notify applicants
        self.closedpos[vacid].applicants[finalidx].ReceiveOffer(vacid,offer)
    
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
        
        ##########################################################################
        # Generate Random Applicants here...
        for i in range(np.random.randint(1,3)):
            ragt = self.GenerateRandAgt()
            ragt.applications[advert.vacid] = {"status" : JobBoard.JOB_STATUS["applied"]}
            self.Apply(advert.vacid, ragt)
            self.model.schedule.add(ragt)
        return suid
    
    ##########################################################################
    ##    
    def Apply(self,vacid,agt): self.openpos[vacid].AddApplicant(agt)
    
        
    ##########################################################################
    ##    
    def AgentAcceptsOffer(self,vacid,agt):
        self.completedpos[vacid] = self.closedpos[vacid]
        self.completedpos[vacid].candidate = agt
        self.completedpos[vacid].status = JobBoard.JOB_STATUS["completed"]
        self.closedpos.pop(vacid)
    
    
    ##########################################################################
    ##    
    def GenerateRandAgt(self):
        #generate new id
        uid = ("%s"%np.random.randint(4000,10000))
        agt = BaseAgent(uid,self.model)
        agt.lastname = ("newemp_%s"%uid)
        age = np.random.randint(20,40)
        agt.SCD = agt.SCD - dt.timedelta(days=int(365*age/10))
        agt.DoB = agt.DoB - dt.timedelta(days=365*age)
        agt.chunks.append( np.random.randint(100,50000) )
        agt.funcexp.initskills_arr(np.random.normal(0.7,0.5,6))
        agt.curloc = self.model.paytable.getrandloc()
        agt.grade = np.random.choice([9,11,12,13])
        agt.salary = self.model.paytable.GetSalVal(agt.curloc,agt.grade,1)
        regidx = np.random.randint(1,6)
        agt.geoexp.initskill(regidx,np.random.normal(0.7,0.5))
        #Generate Task for the Employee
        t = self.model.taskgenerator.NewTask(regidx,agt.funcexp.getMaxSkill()) 
        #Assign task to employee - right now randomly
        agt.assigntask(t)
        
        return agt