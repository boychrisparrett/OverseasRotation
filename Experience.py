##############################################################################
# Author: Christopher M. Parrett 
# George Mason University, Department of Computational and Data Sciences
# Computational Social Science Program
#
# Developed on a Windows 10 platform, AMD PhenomII X6 3.3GHz w/ 8GB RAM
# using Python 3.5.2 | Anaconda 4.2.0 (64-bit).
##############################################################################
##############################################################################
from enum import Enum,auto
import scipy.special as ss
import numpy as np


###################################################################################
## Class
class LearningCurve:
    LEVELS = {0.9:"SME",0.75:"Journeyman",0.5:"Apprentice",0.1:"Entry",0.0:"Basic"}
    def __init__(self,avg,maxrng=50000):
        self.MAX_CHUNKS_PERDAY = 2.6
        self.scale = 5415
        self.maxrng= maxrng
        self.avgcpd= avg
        x = np.array([i for i in range(-1*self.maxrng,self.maxrng)])
        x = (x + (self.scale * self.avgcpd)) / (self.maxrng / 10)
        self.curve = ss.expit(x)
    
    def GetAvgChnkPerDay(self): return self.avgcpd
    
    def GetExpLevel_Y(self,val): return self.curve[int(val)]

    def GetChunkLevel_X(self,val): return np.where(self.curve >= val)[0][0]

    
###################################################################################
## TEMPLATE Class
class GeoRegions:
    def __init__(self):
        self.regions = {
            1: "Europe",
            2: "Africa",
            3: "SouthAm",
            4: "NorthAm",
            5: "Pacific",
            6: "MidEast"}

class Functions:
    def __init__(self):
        self.functions = {
            1: "Leadership",
            2: "IT",
            3: "ProjMgt",
            4: "GISDataMgt",
            5: "Analysis",
            6: "Rqmnts",
        }


###################################################################################
## TEMPLATE Class
class Experience:
    ###############################################################################
    def __init__(self): 
        self.skills = {}
        self.experience = {}
        
    #Initialize Skills to a constant val or an array of constants
    def initskill(self,skidx,v):
        self.experience[self.skills[skidx]] = v
            
    def initskills_arr(self,exparr):
        i=1
        for v in exparr: 
            self.experience[self.skills[i]] = float(v)
            i+=1
                    
    #Subtract values to skills from array 
    def subtract(self,kws,varr):
        retarr = {}
        i=0
        for k in kws:
            retarr[k] = self.experience[self.skills[k]] - varr[i]
            i+=1
        return retarr
    
    def hasSkill(self,kw): return (k in self.skills.keys())
    
    def getSkillLevel(self,kw): 
        return self.experience[self.skills[kw]]

    def getSkillArray(self): 
        return list(self.experience.values())
    
    def setSkillLevel(self,kw,lvl): 
        self.experience[self.skills[kw]] = lvl
        
    def seSkillArray(self,lvls):
        for v in self.skills.keys():
            self.experience[self.skills[v]] = lvls[v]
    
    def PrettyPrint(self,disphdr=True):
        hdr = ""
        skl = ""
        for k in self.experience.keys():
            hdr = "%s%s\t"%(hdr,k)
            skl = "%s%1.3f\t"%(skl,self.experience[k])
        if disphdr: 
            print("\t\t",hdr)
        print("\t\t",skl)
        
###################################################################################
## 
class FuncSkillSet(Experience):
    def __init__(self):
        super().__init__()
        self.skills = Functions().functions
        for f in self.skills:
            self.experience[self.skills[f]] = 0
        self.numskills = len(self.skills)
        self.ranking = [1/self.numskills for x in self.skills]
        
                        
    #Add values to skills from array 
    def __add__(self,other):
        new = FuncSkillSet()
        if type(self) == type(other):
            for k in new.experience:
                new.experience[k] = self.experience[k] + other.experience[k]
        else:
            for k in self.skills.keys():
                kw = self.skills[k]
                if k in other.taskstr["func"]:
                    i = other.taskstr["func"].index(k)
                    new.experience[kw] = self.experience[kw] + other.tasklevel["func"][i]
                else:
                    new.experience[kw] = self.experience[kw]
        return new
                        
    #Add values to skills from array 
    def __sub__(self,other):
        new = FuncSkillSet()    
        if type(self) == type(other):
            for k in new.experience:
                new.experience[k] = self.experience[k] - other.experience[k]
        else:
            for k in self.skills.keys():
                kw = self.skills[k]
                if k in other.taskstr["func"]:
                    i = other.taskstr["func"].index(k)
                    new.experience[kw] = self.experience[kw] - other.tasklevel["func"][i]
                else:
                    new.experience[kw] = self.experience[kw]
        return new

    def __mul__(self,other):
        new = FuncSkillSet()
        if type(self) == type(other):
            for k in new.experience:
                new.experience[k] = self.experience[k] * other.experience[k]
        else:
            for k in self.skills.keys():
                kw = self.skills[k]
                new.experience[kw] = self.experience[kw] * other
        return new

    #Add values to skills from array 
    def __truediv__(self,other):
        new = FuncSkillSet()
        if other != 0:
            for k in new.experience:
                new.experience[k] = self.experience[k] / other
            return new
        else:
            raise("Div By Zeor Error:")
            return None
    
###################################################################################
## 
class RgnlSkillSet(Experience):
    def __init__(self,):
        super().__init__()
        self.skills = GeoRegions().regions
        for r in self.skills:
            self.experience[self.skills[r]] = 0
            
    #Add values to skills from array 
    def __add__(self,other):
        new = RgnlSkillSet()
        if type(self) == type(other):
            # RgnlSkillSet + RgnlSkillSet
            for k in new.experience:
                new.experience[k] = self.experience[k] + other.experience[k]
        else:
            # RgnlSkillSet + Task
            for k in self.skills.keys():
                kw = self.skills[k]
                if k in other.taskstr["reg"]:
                    i = other.taskstr["reg"].index(k)
                    new.experience[kw] = self.experience[kw] + other.tasklevel["func"][i]
                else:
                    new.experience[kw] = self.experience[kw]
        return new
    
    #Add values to skills from array 
    def __sub__(self,other):
        new = RgnlSkillSet()
        if type(self) == type(other):
            # RgnlSkillSet - RgnlSkillSet
            for k in new.experience:
                new.experience[k] = self.experience[k] - other.experience[k]
        else:
            # RgnlSkillSet - Task
            for k in self.skills.keys():
                kw = self.skills[k]
                if k in other.taskstr["reg"]:
                    i = other.taskstr["reg"].index(k)
                    new.experience[kw] = self.experience[kw] - other.tasklevel["func"][i]
                else:
                    new.experience[kw] = self.experience[kw]
        return new
    
    def __mul__(self,other):
        new = RgnlSkillSet()
        if type(self) == type(other):
            for k in new.experience:
                new.experience[k] = self.experience[k] * other.experience[k]
            return new
        else:
            for k in self.skills.keys():
                kw = self.skills[k]
                new.experience[kw] = self.experience[kw] * other
        return new
    
    #Add values to skills from array 
    def __truediv__(self,other):
        new = RgnlSkillSet()
        if other != 0:
            for k in new.experience:
                new.experience[k] = self.experience[k] / other
            return new
        else:
            raise("Div By Zeor Error:")
            return None
    
        