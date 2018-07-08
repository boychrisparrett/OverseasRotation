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

##############################################################################
# CLASS:: JobBoard
#
#  Purpose: Implements a generic agent in an organization.
# Requires: FEX, FEXWGHTS, GEX, GEXWGHTS, UNIT, BILLET, LOC, EXP, LAG
class VacancyAnnouncement(Agent):
    def __init__(self,uid,model,**kwargs):
        super().__init__(uid, model)
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
        
        #Object pointers                  
        self.unit = kwargs["UNIT"]
        self.unitpolicy = self.unit.gethiringpol()
        self.billet = kwargs["BILLET"]
        self.location = kwargs["LOC"]
        self.applicants = []
        self.candidates = []
        
    def AddApplicant(self,appagt):
        if self.open:
            #!!! Can add additional policies here.
            self.applicants.append(appagt)
                              
    def isClosed(self): return not self.open

    def SetCandidates(self,appagt):
        pass

    def step(self):
        if self.expires < self.model.date:
            self.open = False
            self.status = "closed"
    
    def select(self,final):
        #Step through the sorted array with index = appindex
        clearbreak = np.percentile(final, 85)
        #Step through each candidate in order of score value
        for cand in final.index:
            if (final[cand] > clearbreak):
                print("Emp# ",cand, " scored ",final[cand])
                self.candidates.append(cand)
                
        if len(self.candidates) >= 1:
            #one or more selectee with high score... random choose 1
            selectee = choice(self.candidates)
            ### CANT DELETE
            #del self.candidates[selectee]
            return selectee
        else:
            return None
        
##############################################################################
# CLASS:: JobBoard
#
# Purpose: Implements a generic agent in an organization.
#
class JobBoard(Agent):
    def __init__(self,uid, model):
        super().__init__(uid, model)
        self.openpos = {}
        self.closedpos = {}
        self.completedpos = {}
        self.numttlpos= 0
        self.avghirelag = 90 #days
        self.minopentime = 14 #days

    def getopenings(self): return self.openpos
        
    def getUniqueID(self,d,i=1):
        #Create unique ID
        s=("%04d%02d%02d%02d%02d%02d_W%04d"%(d.year,d.month,d.day,d.hour,d.minute,d.second,i))
        if (s in self.openpos.keys()):
            s = self.getUniqueID(d,i+1)
        return s

    def step(self):
        #Check expiration date on new applications
        self.updatelistings()
        
        #Select Candidates
        self.rankselect()
        
    def updatelistings(self):
        cps = []
        for vacid in self.getopenings():
            if self.openpos[vacid].isClosed():
                self.closedpos[vacid] = self.openpos[vacid]
                cps.append(vacid)
        for cp in cps: 
            #del self.openpos[cp]
            print("CLOSED... NEED TO DO SOMETHING HERE")
        
    def rankselect(self):
        #unit_policy = {"geoexp":0.5,"funcexp":0.5}
        #vacfuncweights = [0.3,0.6,0.1]
        #vacgeoweights = [0.33,0.34,0.33]
        for vacid in self.closedpos:
            #Adjust for lagtime
            status = self.closedpos[vacid].status
            if status == "selected":
                pass
            elif status == "accepted":
                pass
            elif ((self.closedpos[vacid].expires + dt.timedelta(self.closedpos[vacid].lagtime)) < 
                  self.model.date) or (status == "declined"):
                self.extendoffer(vacid, self.apprevpolicy(vacid))

    def Advertise(self,**kwargs):
        #Create open date and unique identifier
        sudate = dt.datetime.now() #!! Need to update to current Model time
        suid = self.getUniqueID(sudate)
        
        #Generate the vacancy announcement
        advert = VacancyAnnouncement(self.numttlpos,self.model,**kwargs, EXP=self.minopentime, 
                                     LAG=self.avghirelag, SDATE=sudate, SUID=suid)
        
        #Update the object statistics
        self.openpos[advert.vacid] = advert
        self.numttlpos += 1
        
        self.model.schedule.add(advert)
        
        #Return the locator ID to the unit
        return suid
    
    def Apply(self,vacid,agt):
        self.openpos[vacid].AddApplicant(agt)
                    
    def extendoffer(self,vacid,final):
        if final is None:
            #There were no applicants 
            self.closedpos[vacid].status = "cancelled"
            self.closedpos[vacid].completedate = self.model.time  
        else:
            selectee = self.closedpos[vacid].select(final)
            self.closedpos[vacid].status = "reviewed"
            
            #Notify applicant
            self.closedpos[vacid].applicants[selectee].status = "offered"
            self.closedpos[vacid].applicants[selectee].joboffer = {}
            '''
                Job Offer should have:
                Grade-Series-Step
                Location
                StartDate
                #Set Start date 
                    #@14 days within locality
                    #@28 days within CONUS
                    #@60-90 days within locality
            '''
    
    def apprevpolicy(self,vacid): 
        #Initialize the data frames
        numapps = len(self.closedpos[vacid].applicants)
        func_df = pd.DataFrame(index=range(numapps),columns=(self.closedpos[vacid].funcexp),data=0)
        geo_df  = pd.DataFrame(index=range(numapps),columns=(self.closedpos[vacid].geoexp) ,data=0)
        i = 0
        appidx = []
        final = None
        for appagt in self.closedpos[vacid].applicants:
            #Load dataframes
            #appidx.append(appagt.getUPI())
            #func_df.iloc[i] = [appagt.getfuncexp.count(x) for x in self.closedpos[vacid].funcexp]
            #geo_df.iloc[i]  = [appagt.getgeoexp.count(x) for x in self.closedpos[vacid].geoexp]

            ## V&V Purposes only ##
            appidx.append(appagt) #V&V Purposes only
            getfuncexp = [0.3,0.4,0.1,0.1]
            getgeoexp = [0.3,0.3,0.2,0.1]
            
            #Count the required skills in the workforce
            func_df.iloc[i] = [getfuncexp.count(x) for x in self.closedpos[vacid].funcexp]
            geo_df.iloc[i]  = [getgeoexp.count(x) for x in self.closedpos[vacid].geoexp]

            i+=1

            #Apply weights and unit priorities
            func_df = (func_df * self.closedpos[vacid].vacfuncwght).sum(axis=1) * self.closedpos[vacid].unitpolicy["funcexp"]
            geo_df = (geo_df * self.closedpos[vacid].vacgeowght).sum(axis=1) * self.closedpos[vacid].unitpolicy["geoexp"]

            #Grab final ranking matrix and sort
            final = pd.Series(index=appidx,data=((func_df + geo_df).values)).sort_values(ascending=False)
            print("FINAL SELECTION MATRIX\n ------------------------------------------------------------")
            print(final)
            
        return final