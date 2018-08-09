from BaseAgent import *
from Experience import *
import pandas as pd
import numpy as np
import datetime as dt
from random import sample

##############################################################################            
##############################################################################
# CLASS:: Task
#
# Purpose: 
#
class Task:
    TASK_PRI = [0.70,0.20,0.10]
    ####################################################################################
    # __init__ initializes a new task
    def __init__(self,uid,model,f_focus,cmplx):
        self.taskid = uid          # Unique Task ID
        self.model = model
        
        # Create dict of both "kene"
        self.taskstr = {"reg":[0],"func": self.gentask(f_focus,cmplx,Functions().functions)}
        
        # Define focus of each level
        self.tasklevel = {"reg": np.random.normal(0.8,0.05,1), "func": np.random.normal(0.8,0.05,cmplx)}
        self.start = self.model.date                        
        self.stop = None
        self.active = True
        
    ####################################################################################
    #         
    def getTaskasArr(self,ttyp):
        miter = FuncSkillSet().numskills
        arr = np.zeros(miter)
        k=0
        for i in self.taskstr[ttyp]:
            arr[i-1] = self.tasklevel[ttyp][k]
            k+=1
        return arr
        
    ####################################################################################
    # 
    def transtoskillarr(self):
        #self.taskstr = {"reg":[0],"func": self.gentask(f_focus,cmplx,Functions().functions)}
        newtstr = {"reg": RgnlSkillSet(),"func": FuncSkillSet()}
        for r in self.taskstr["reg"]:
            newtstr["reg"][r] = 1
        
        for f in self.taskstr["func"]:
            newtstr["func"][f] = 1
         
        return newstr
    
    ####################################################################################
    # gentask - generate a task kene
    def gentask(self,f_focus,cmplx,ttlset):
        # Generate task string
        # Get available functions
        f_avail = (ttlset)
        
        # Select Primary tasks
        f_avail.pop(f_focus)                        
        
        # Generate remaining tasks 
        t2 = sample(list(f_avail.keys()),cmplx-1)   
        tstr = [f_focus,*t2]
        
        #Return task str
        return tstr
    
    ####################################################################################
    # MeetTask - Agent compares current skillset to its given task
    # reg: Calling agent's regional skill string
    # fun: Calling agent's functional skill string
    def MeetTask(self,reg,fun):
        # Calculate the regional experience - currently an constant
        #d_reg = reg.getSkillArray()[0] - self.tasklevel["reg"][0]
        d_reg = reg- self.tasklevel["reg"][0]
        
        d_funagg = 0
        i=0
        d_fun = np.zeros(len(self.taskstr["func"]))
        delta = 0 
        init_fun = fun
        for f in self.taskstr["func"]:
            delta = (self.tasklevel["func"][i] * Task.TASK_PRI[i] * init_fun)
            d_fun[i]=delta
            d_funagg += delta
            init_fun -= delta
            if init_fun < 0:
                break
            i+=1
        return d_reg,d_funagg,np.array(d_fun)
    
    ####################################################################################
    # PrettyPrint for verification / validation support
    def PrettyPrint(self):
        print("Task ID:",self.taskid)
        print("\t Task Str:",self.taskstr)
        print("\t Task Lvl:",self.tasklevel)
        print("\t Task Start:",self.start)
        print("\t Task Stop:",self.stop)
        print("\t Task Active:",self.active)
        
##############################################################################            
##############################################################################
# CLASS::TaskGenerator
#
# Purpose: 
#
class TaskGenerator:
    def __init__(self,model):
        self.model = model
        self.tasklog = {}
        self.taskid = 0
        self.tcomplexity = 3
        self.taskstatus = False
             
    def NewTask(self,reg_focus,func_focus):
        self.taskid += 1
        self.tasklog[self.taskid] = Task(self.taskid,self.model,func_focus,self.tcomplexity)
        self.tasklog[self.taskid].taskstr["reg"] = [reg_focus]
        return self.tasklog[self.taskid]
             
    def GetTask(self,tid): return self.tasklog[tid]
             
    def CloseTask(self,tid):
        self.tasklog[self.taskid].active = False
        self.tasklog[self.taskid].stop = self.model.date
