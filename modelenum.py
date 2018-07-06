from enum import Enum,auto

###ENUMERATIONS
class Regions(Enum):
    Europe = auto()
    Africa = auto()
    SouthAm = auto()
    NorthAm = auto()
    Pacific = auto()
    MidEast = auto()
    
class Functions(Enum):
    Leadership = auto()
    IT = auto()
    ProjMgt = auto()
    GISDataMgt = auto()
    Analysis = auto()
    Rqmnts = auto()
    

class Experience:
    def __init__(self):
        self.experience = {}
    def incSkill(self,kw): 
        pass
    def decSkill(self,kw): 
        pass
    def add(self,exp):
        pass
    def subtract(self,exp): 
        pass     
    def hasSkill(self,kw):
        if self.experience[kw] > 0:
            return True
        else:
            return False
       
    def adjustSkill(self,kw,rate):
        if self.experience[kw] == 0:
            self.experience[kw] = abs(rate)
        else:
            self.experience[kw] *= (1 + rate)
            if self.experience[kw] < abs(rate):
                self.experience[kw] = abs(rate)
                
    def printSkill(self,disphdr=True):
        hdr = ""
        skl = ""
        for k in self.experience.keys():
            hdr = "%s%s\t"%(hdr,k)
            skl = "%s%1.3f\t"%(skl,self.experience[k])
        if disphdr: 
            print("\t\t",hdr)
        print("\t\t",skl)
        
class FuncSkillSet(Experience):
    def __init__(self):
        super().__init__()
        self.incrate = 0.002
        self.decrate = -0.002
        self.keys = []
        for f in Functions:
            self.experience[f.name] = 0
            self.keys.append(f.name)
    
    def initfunc(self,kws):
        for f in kws:
            self.experience[Functions(int(f)).name] = self.incrate
     
    def incSkill(self,kw): self.adjustSkill(kw,self.incrate)   
    def decSkill(self,kw): self.adjustSkill(kw,self.decrate)
        
    def add(self,fexp):
        for f in Functions:
            self.experience[f.name] += fexp.experience[f.name]
            
    def subtract(self,fexp):
        for f in Functions: 
            self.experience[f.name] -= fexp.experience[f.name]
        
class RgnlSkillSet(Experience):
    def __init__(self,):
        super().__init__()
        self.incrate = 0.002
        self.decrate = -0.002
        self.keys = []
        for r in Regions:
            self.experience[r.name] = 0
            self.keys.append(r.name)
        
    def initrgnl(self,kws):
        for r in kws:
            self.experience[Regions(int(r)).name] = self.incrate
            
    def incSkill(self,kw): self.adjustSkill(kw,self.incrate)
    def decSkill(self,kw): self.adjustSkill(kw,self.decrate)
    
    def add(self,rexp):
        for r in Regions: 
            self.experience[r.name] += rexp.experience[r.name]
    
    def subtract(self,rexp):
        for r in Regions: 
            self.experience[r.name] -= rexp.experience[r.name]