from BaseAgent import *
from Experience import *
import pandas as pd
import numpy as np
import datetime as dt
from random import sample

class Task:
    TASK_PRI = [0.70,0.20,0.10]
    def __init__(self,uid,start,f_focus,cmplx):
        self.taskid = uid
        f_avail = (Functions().functions)
        f_avail.pop(f_focus)
        t2 = sample(list(f_avail.keys()),cmplx-1)
        tstr = [f_focus,*t2] 
        self.taskstr = {"reg":[0],"func": tstr}
        self.tasklevel = {"reg":[np.random.normal(0.8,0.05)],"func":Task.TASK_PRI}
        self.start = start
        self.stop = None
        self.active = True
    
    def MeetTask(self,reg,fun):
        d_reg = reg.getSkillArray()[0] - self.tasklevel["reg"][0]
        d_fun = []
        d_funagg = 0
        i=0
        for f in self.taskstr["func"]:
            d_fun.append(fun.getSkillLevel(f) - self.tasklevel["func"][i])
            d_funagg += pow(self.tasklevel["func"][i],Task.TASK_PRI[i])
            i+=1
        return d_reg,d_funagg,d_fun
    
    def PrettyPrint(self):
        print("Task ID:",self.taskid)
        print("\t Task Str:",self.taskstr)
        print("\t Task Lvl:",self.tasklevel)
        print("\t Task Start:",self.start)
        print("\t Task Stop:",self.stop)
        print("\t Task Active:",self.active)
        
class TaskGenerator:
    def __init__(self,model):
        self.model = model
        self.tasklog = {}
        self.taskid = 0
        self.tcomplexity = 3
        self.taskstatus = False
             
    def NewTask(self,reg_focus,func_focus):
        self.taskid += 1
        self.tasklog[self.taskid] = Task(self.taskid,self.model.date,func_focus,self.tcomplexity)
        self.tasklog[self.taskid].taskstr["reg"] = [reg_focus]
        return self.tasklog[self.taskid]
             
    def GetTask(self,tid): return self.tasklog[tid]
             
    def CloseTask(self,tid):
        self.tasklog[self.taskid].active = False
        self.tasklog[self.taskid].stop = model
