# ***********************************************************************
#  This code is part of pyCMPL
#
#  Copyright (C) 
#  Mike Steglich - Technical University of Applied Sciences
#  Wildau, Germany
#
#  pyCMPL is a project of the Technical University of
#  Applied Sciences Wildau and the Institute for Operations Research
#  and Business Management at the Martin Luther University
#  Halle-Wittenberg.
#  Please visit the project homepage <www.coliop.org>
#
#  pyCMPL is free software; you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  pyCMPL is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
#  License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# **********************************************************************

__version__ = "2.0.0"
# April 2021

from math import *
import os
import threading
import random
import subprocess
import sys
import xmlrpc.client
import time
import socket
import time
import tempfile
import io
import pickle
import traceback
import shutil
import collections
import re 


from .CmplDefs import *
from .CmplException import *
from .CmplMsg import *
from .CmplTools import *
from .CmplSolution import *
from .CmplSet import *
from .CmplParameter import *
from .CmplInstance import *
from .CmplXlsData import *
from .CmplArgs import *
from .CmplSolutionReport import *


#################################################################################
#
# Cmpl										
#										
#################################################################################

class Cmpl(threading.Thread):
#class Cmpl:

    # ********************************************************************************
    # Constructor and destructor
    # ********************************************************************************

    # *********** constructor **********
    def __init__(self, model, cmplArgs=None):

        threading.Thread.__init__(self)

        self.__compatibility = COMPATIBILITY

        if type(model) != str:
            raise CmplException(str(model) + " is not a valid file name for a Cmpl file")
        
        self.__cmplFile = model
        self.__cmplFileAlias = None
        
        if not os.path.exists(model):
            raise CmplException("CMPL file " + model + " does not exist."  )

        self.__baseName = os.path.splitext(self.__cmplFile)[0]

        self.__cmplDataStr = io.StringIO()

        self.__setList = []
        self.__parameterList = []
        self.__optionsList = {}

        self.__xlsData = None
        self.__isXlsData = False
        self.__xlsDataFile = ""

        self.__status = None
        self.__solutions = None
        self.__solutionString = ""

        self.__remoteMode = False
        self.__remoteStatus = CMPL_UNKNOWN
        self.__remoteStatusMessage = ""

        self.__jobId = ""
        self.__instStr = ""
        self.__cmplInstance = None

        self.__solver = "cbc"

        self.__cmplServer = None
        self.__cmplUrl = ""
        self.__cmplGridScheduler = None
        self.__cmplGridSchedulerUrl = ""
        self.__serverMode = SERVER_UNKNOWN

        self.__runMode = PYCMPL

        self.__cmplServerRunning = False

        self.__maxCmplServerTries = 10
        self.__maxCmplServerQueuingTime = 5 * 60  # in seconds

        self.__cmplDataFile = None
        self.__cmplMsgFile = None
        self.__cmplSolFile = None     

        self.__refreshTime = 0.1
        self.__printOutput = False

        self.__isCleaned = False
        self.__debug = False

        self.__cmplBinHandler = None
        self.__cmplBinName=""

        try:
            self.__cmplBinName = os.environ['CMPLHOME'] + 'bin'+ os.sep +"cmpl"
            if sys.platform.startswith('win'):
                self.__cmplBinName+=".exe"
        except:
            raise CmplException("Environment variable CMPLHOME not defined")

        if not os.path.exists(self.__cmplBinName):
            raise CmplException("Can't find Cmpl binary: " + cmplBin)

        if cmplArgs:
            self.__cmplArgs = cmplArgs
            self.__runMode = self.__cmplArgs.runMode
        else:
            self.__preCompAlias = "cmpl__"+next(tempfile._get_candidate_names())+"__"
            self.__cmplArgs = CmplArgs(self.__preCompAlias+".optcmpl")
            self.__cmplArgs.setRunMode(PYCMPL)

        self.__solReport = None
        
        self.__outputLeadString = os.path.basename(os.path.splitext(self.__cmplFile)[0]) + "> "

    # *********** end constructor ********

    # *********** destructor *************
    def __del__(self):
        if self.__runMode in (PYCMPL, CMPL_LOCAL, CMPL_REMOTE_SOLVE, CMPL_REMOTE_RETRIEVE):
            try:
                self.__cleanUp()
                #self.__outputString.close()
                self.__cmplDataStr.close()
            except:
                pass
    # *********** end destructor *********

    # *********** reduce *****************
    def __reduce__(self):
        return (self.__class__, (self.__cmplFile,))
    # *********** end reduce *************

    # ********************************************************************************
    # public methods
    # ********************************************************************************

    #******************** dump **********************
    def dump(self, name=None):
        try:
            if name is not None:
                _dumpFileName = name
            else:
                _dumpFileName = tempfile.gettempdir() + os.sep + os.path.basename(self.__cmplFile) + ".dump"
           
            _dumpFile = open(_dumpFileName, 'wb')

            pickle.dump(self.__compatibility, _dumpFile)
            pickle.dump(self.__baseName, _dumpFile)
            pickle.dump(self.__setList, _dumpFile)
            pickle.dump(self.__parameterList, _dumpFile)
            pickle.dump(self.__optionsList, _dumpFile)
            pickle.dump(self.__status, _dumpFile)
            pickle.dump(self.__isXlsData, _dumpFile)
            pickle.dump(self.__xlsDataFile, _dumpFile)
            pickle.dump(self.__solutions, _dumpFile)
            pickle.dump(self.__solutionString, _dumpFile)
            pickle.dump(self.__remoteMode, _dumpFile)
            pickle.dump(self.__remoteStatus, _dumpFile)
            pickle.dump(self.__remoteStatusMessage, _dumpFile)
            pickle.dump(self.__jobId, _dumpFile)
            pickle.dump(self.__instStr, _dumpFile)
            pickle.dump(self.__solver, _dumpFile)
            pickle.dump(self.__cmplUrl, _dumpFile)
            pickle.dump(self.__cmplGridSchedulerUrl, _dumpFile)
            pickle.dump(self.__serverMode, _dumpFile)
            pickle.dump(self.__runMode, _dumpFile)
            pickle.dump(self.__cmplServerRunning, _dumpFile)
            pickle.dump(self.__maxCmplServerTries, _dumpFile)
            pickle.dump(self.__maxCmplServerQueuingTime, _dumpFile)
            pickle.dump(self.__cmplDataFile, _dumpFile)
            pickle.dump(self.__cmplMsgFile, _dumpFile)
            pickle.dump(self.__cmplSolFile, _dumpFile)
            pickle.dump(self.__cmplBinHandler, _dumpFile)
            pickle.dump(self.__refreshTime, _dumpFile)
            pickle.dump(self.__printOutput, _dumpFile)
            pickle.dump(self.__isCleaned, _dumpFile)
            pickle.dump(self.__debug, _dumpFile)
            pickle.dump(self.__cmplFile, _dumpFile)
            pickle.dump(self.__outputLeadString, _dumpFile)

            _dumpFile.close()
        except:
            traceback.print_exc(file=sys.stdout)
            raise CmplException("Internal error, cannot write dump: " + str(sys.exc_info()[1]))
    #******************** end dump **********************
    
    #******************** load **********************
    def load(self, name=None):
        try:
            if name is not None:
                _dumpFileName = name
            else:
                _dumpFileName = tempfile.gettempdir() + os.sep + os.path.basename(self.__cmplFile) + ".dump"

            _dumpFile = open(_dumpFileName, 'rb')

            self.__compatibility = pickle.load(_dumpFile)
            self.__baseName = pickle.load(_dumpFile)
            self.__setList = pickle.load(_dumpFile)
            self.__parameterList = pickle.load(_dumpFile)
            self.__optionsList = pickle.load(_dumpFile)
            self.__status = pickle.load(_dumpFile)
            self.__isXlsData = pickle.load(_dumpFile)
            self.__xlsDataFile = pickle.load(_dumpFile)
            self.__solutions = pickle.load(_dumpFile)
            self.__solutionString = pickle.load(_dumpFile)
            self.__remoteMode = pickle.load(_dumpFile)
            self.__remoteStatus = pickle.load(_dumpFile)
            self.__remoteStatusMessage = pickle.load(_dumpFile)
            self.__jobId = pickle.load(_dumpFile)
            self.__instStr = pickle.load(_dumpFile)
            self.__solver = pickle.load(_dumpFile)
            self.__cmplUrl = pickle.load(_dumpFile)
            self.__cmplGridSchedulerUrl = pickle.load(_dumpFile)
            self.__serverMode = pickle.load(_dumpFile)

            if self.__serverMode == STANDALONE_SERVER:
                if self.__cmplUrl:
                    self.__cmplServer = xmlrpc.client.ServerProxy(self.__cmplUrl)
            if self.__serverMode == CMPL_GRID:
                if self.__cmplUrl:
                    self.__cmplServer = xmlrpc.client.ServerProxy(self.__cmplUrl, allow_none=False)
                if self.__cmplGridSchedulerUrl:
                    self.__cmplGridScheduler = xmlrpc.client.ServerProxy(self.__cmplGridSchedulerUrl)

            self.__runMode = pickle.load(_dumpFile)
            self.__cmplServerRunning = pickle.load(_dumpFile)
            self.__maxCmplServerTries = pickle.load(_dumpFile)
            self.__maxCmplServerQueuingTime = pickle.load(_dumpFile)
            self.__cmplDataFile = pickle.load(_dumpFile)
            self.__cmplMsgFile = pickle.load(_dumpFile)
            self.__cmplSolFile = pickle.load(_dumpFile)
            self.__cmplBinHandler = pickle.load(_dumpFile)
            self.__refreshTime = pickle.load(_dumpFile)
            self.__printOutput = pickle.load(_dumpFile)
            self.__isCleaned = pickle.load(_dumpFile)
            self.__debug = pickle.load(_dumpFile)
            self.__cmplFile = pickle.load(_dumpFile)
            self.__outputLeadString = pickle.load(_dumpFile)

            _dumpFile.close()

            os.remove(_dumpFileName)
        except:
            raise CmplException("No CmplServer object exists. Please send your problem to a CmplServer before other actions.")

    # *********** model (getter) *********
    @property
    def modelName(self):
        return self.__cmplFile

    # *********** end model **************

    # *********** problem (getter) *********
    @property
    def problem(self):
        return self.__baseName

    # *********** end model **************

    # *********** refreshTime ************
    @property
    def refreshTime(self):
        return self.__refreshTime

    # *********** end refreshTime ********

    # *********** cmplMessages ************
    @property
    def cmplMessages(self):
        return self.__status.cmplMessageList

    # *********** end cmplMessages ********
  
    # *********** solutions ***************
    @property
    def solutionPool(self):
        if self.__solutions is None:
            raise CmplException("No Solution found so far")
        elif self.__solutions.nrOfSolutions > 0:
            return self.__solutions.solutions
        else:
            raise CmplException("No Solution found so far")

    # *********** end solutions ***********

    # *********** solutions ***************
    @property
    def solution(self):
        if self.__solutions is None:
            raise CmplException("No Solution found so far")
        elif self.__solutions.nrOfSolutions > 0:
            return self.__solutions.solution
        else:
            raise CmplException("No Solution found so far")

    # *********** end solutions ***********

    # *********** nrOfVariables ***************
    @property
    def nrOfVariables(self):
        if self.__solutions is None:
            raise CmplException("The model isn't generated yet.")
        else:
            return self.__solutions.nrOfVariables

    # *********** end nrOfVariables ***********

    # *********** nrOfConstraints ***************
    @property
    def nrOfConstraints(self):
        if self.__solutions is None:
            raise CmplException("The model isn't generated yet.")
        else:
            return self.__solutions.nrOfConstraints

    # *********** end nrOfConstraints ***********
  
    # *********** objectiveName ***************
    @property
    def objectiveName(self):
        if self.__solutions is None:
            raise CmplException("No Solution found so far")
        else:
            return self.__solutions.objectiveName

    # *********** end objectiveName ***********

    # *********** objectiveSense ***************
    @property
    def objectiveSense(self):
        if self.__solutions is None:
            raise CmplException("No Solution found so far")
        else:
            return self.__solutions.objectiveSense

    # *********** end objectiveSense ***********

    # *********** nrOfSolutions ****************
    @property
    def nrOfSolutions(self):
        if self.__solutions is None:
            raise CmplException("No Solution found so far")
        else:
            return self.__solutions.nrOfSolutions

    # *********** end nrOfSolutions *************

    # *********** solver ************************
    @property
    def solver(self):
        if self.__solutions is None:
            raise CmplException("Since the model isn't solved the solver is not known.")
        else:
            return self.__solutions.solver

    # *********** end solver ********************

    # *********** solverMessage *****************
    @property
    def solverMessage(self):
        if self.__solutions is None:
            raise CmplException("Since the model isn't solved the solver message is not known.")
        else:
            return self.__solutions.solverMessage

    # *********** end nrOfSolutions *************

    # *********** varDisplayOptions *************
    @property
    def varDisplayOptions(self):
        if self.__solutions is None:
            raise CmplException("Since the model isn't solved this option isn't known.")
        else:
            return self.__solutions.varDisplayOptions

    # *********** end varDisplayOptions *********

    # *********** conDisplayOptions *************
    @property
    def conDisplayOptions(self):
        if self.__solutions is None:
            raise CmplException("Since the model isn't solved this option isn't known.")
        else:
            return self.__solutions.conDisplayOptions

    # *********** end conDisplayOptions *********
   
    # *********** cmplStatus **************
    @property
    def cmplStatus(self):
        '''if self.__remoteMode and self.__remoteStatus != CMPL_UNKNOWN:
            return self.__remoteStatus
        else:
        '''
        return self.__status.cmplStatus

    # *********** end cmplStatus ***********

    # *********** cmplStatusText ***********
    @property
    def cmplStatusText(self):
        status = 0
        if self.__remoteMode and self.__remoteStatus != CMPL_UNKNOWN:
            status = self.__remoteStatus
        else:
            status = self.__status.cmplStatus
        return CMPL_STATUS_TXT[status]

    # *********** end cmplStatusText ******

    # *********** solverStatus ************
    @property
    def solverStatus(self):
        if self.__solutions.nrOfSolutions == 0:
            return SOLVER_FAILED
        else:
            return SOLVER_OK

    # *********** end solverStatus ********

    # *********** solverStatusText ********
    @property
    def solverStatusText(self):
        if self.__solutions.nrOfSolutions == 0:
            return "SOLVER_FAILED"
        else:
            return "SOLVER_OK"

    # *********** end solverStatusText ****

    # *********** jobId *******************
    @property
    def jobId(self):
        return self.__jobId

    @property
    def isDebug(self):
        return self.__debug

    # *********** end jobId **************
    
    # *********** setDataFile *******************
    def setDataFile(self, dataFile):
        self.__cmplDataFile=dataFile
     # *********** endDataFile *******************

    # *********** setXlsDataFile *******************
    def setXlsDataFile(self, xlsDataFile):
        self.__xlsData = CmplXlsData(xlsDataFile, self.__cmplArgs)
        self.__xlsDataFile=xlsDataFile
        self.__isXlsData=True
    
        if self.__xlsData:
            tmpSets,tmpPars = self.__xlsData.readXlsData()
            if tmpSets:
                self.setSets(tmpSets)
            if tmpPars:
                self.setParameters(tmpPars)
    # *********** end setXlsDataFile *******************

    # *********** setAsyncMode *******************
    def setRunMode(self, mode):
        self.__runMode = mode
    # *********** end setAsyncMode *******************

    # *********** setOutputPipe **********
    def setOutput(self, ok=False, lStr=None):
        self.__printOutput = ok
        if lStr is not None:
            self.__outputLeadString = lStr

    # *********** end setOutputPipe ******
  
    # *********** setRefreshTime *********
    def setRefreshTime(self, rTime):
        self.__refreshTime = rTime

    # *********** end setRefreshTime *****

    # *********** setSet *****************
    def setSet(self, set):
        if type(set) != CmplSet:
            raise CmplException(str(set) + " is not a CMPL set ")
        else:
            if len(set.valueList) != 0:
                self.__setList.append(set)
                exec('self.'+set.name+'=set')
            else:
                raise CmplException("set " + set.name() + " contains no elements ")

    # *********** end setSet **************

    # *********** setSets *****************
    def setSets(self, *set):
        for s in set:
            if type(s)==list:
                for e in s:
                    self.setSet(e)
            else:
                self.setSet(s)

    # *********** end setSets *************

    # *********** setParameter ************
    def setParameter(self, param):
        if type(param) != CmplParameter:
            raise CmplException("Cmpl.setParameter: " + str(param) + " is not a CMPL parameter ")
        else:
            if len(param.values) != 0:
                self.__parameterList.append(param)
                exec('self.'+param.name+'=param')
            else:
                raise CmplException("parameter " + param.name + " contains no elements ")

    # *********** end setParameter ********

    # *********** setSets *****************
    def setParameters(self, *params):
        for p in params:
            if type(p)==list:
                for e in p:
                    self.setParameter(e)
            else:
                self.setParameter(p)

    # *********** end setSets *************

    # *********** setOption ***************
    def setOption(self, option):
        if type(option) != str:
            raise CmplException(str(option) + " is not a valid CMPL option ")
        else:
            if self.__cmplServerRunning:
                print("Option <"+option+"> is ignored, because problem has been connected with a CMPLServer before.")
            pos = len(self.__optionsList)
            self.__optionsList.update({pos: option})
        return pos

    # *********** end setOption ***********

    # *********** setOption ***************
    def setOptionsList(self, optionList):
        if type(optionList) != dict:
            raise CmplException("Wrong option list ")
        else:
            if self.__cmplServerRunning:
                print("Options are ignored, because problem has been connected with a CMPLServer before.")
            self.__optionsList = optionList

    # *********** end setOption ***********

    # *********** delOption ***************
    def delOption(self, pos):
        if pos not in self.__optionsList:
            raise CmplException(str(pos) + " is not a valid CMPL option ")
        else:
            del self.__optionsList[pos]

    # *********** end delOption ***********

    # *********** delOptions ***************
    def delOptions(self):
        self.__optionsList = {}
    # *********** end delOptions ***********

    # **** setMaxServerQueuingTime *********
    def setMaxServerQueuingTime(self, qTime):
        self.__maxCmplServerQueuingTime = qTime
    # ** end setMaxServerQueuingTime *******

    # **** maxServerQueuingTime ************
    @property
    def maxServerQueuingTime(self):
        return self.__maxCmplServerQueuingTime
    # ** end maxServerQueuingTime **********

    # **** setMaxServerTries ***************
    def setMaxServerTries(self, tries):
        self.__maxCmplServerTries = tries
    # ** end setMaxServerTries *************

    # **** maxServerTries ******************
    @property
    def maxServerTries(self):
        return self.__maxCmplServerTries
    # ** end maxServerTries ****************

    # *********** debug *******************
    def debug(self, mode=True):
        self.__debug = mode
    # *********** end debug ***************

    ####### überprüfen ob das onsolet ist
    # *********** getVarByName ************
    def getVarByName(self, name, solNr=0):
        if solNr < 0 or solNr > self.__solutions.nrOfSolutions - 1:
            raise CmplException("Solution with index " + str(solNr) + " doesn't exist.")
        s = self.__solByNr(solNr)
        return self.__getElementByName(name, s.variables)
    # *********** end getVarByName ********

    # *********** getConByName ************
    def getConByName(self, name, solNr=0):
        if solNr < 0 or solNr > self.__solutions.nrOfSolutions - 1:
            raise CmplException("Solution with index " + str(solNr) + " doesn't exist.")
        s = self.__solByNr(solNr)
        return self.__getElementByName(name, s.constraints)
    # *********** end getConByName ********

    ##### Lassen als public wenn andere Lösungen als die erste gefragt sind
    # *********** varByName ***************
    def varByName(self, solNr=0):
        if solNr < 0 or solNr > self.__solutions.nrOfSolutions - 1:
            raise CmplException("Solution with index " + str(solNr) + " doesn't exist.")
        s = self.__solByNr(solNr)
        self.__elementByName(s.variables)
    # *********** end varByName ***********

    # *********** conByName ***************
    def conByName(self, solNr=0):
        if solNr < 0 or solNr > self.__solutions.nrOfSolutions - 1:
            raise CmplException("Solution with index " + str(solNr) + " doesn't exist.")
        s = self.__solByNr(solNr)
        self.__elementByName(s.constraints)
    # *********** end conByName ***********

    # *********** solve *******************
    def solve(self):
        self.__isCleaned=False
        
        if self.__remoteMode:
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplServer")

            self.__status = CmplMessages()
            self.__solutions = CmplSolutions()

            tries = 0
            while True: # loop is intended for CMPLGrid
                self.__isCleaned = False
                try:
                    if self.__remoteStatus == CMPLSERVER_CLEANED:
                        self.connect(self.__cmplUrl)

                    if self.__serverMode == CMPL_GRID and self.__remoteStatus == CMPLSERVER_ERROR:
                        self.connect(self.__cmplUrl)

                    if self.__remoteStatus == CMPLGRID_SCHEDULER_BUSY:
                        startTime = time.time()
                        while self.__remoteStatus != CMPLGRID_SCHEDULER_OK:
                            time.sleep(self.__refreshTime)
                            self.__knockScheduler()

                            if (time.time() - startTime) >= self.__maxCmplServerQueuingTime:
                                self.__cleanUp()
                                raise CmplException("maximum CmplServer queuing time is exceeded.")
                    
                    self.send()
        
                    if self.__debug:
                        instFile = self.__baseName + ".cinst"
                        try:
                            f = open(instFile, 'w')
                            f.write(self.__instStr)
                            f.close()
                        except IOError as e:
                            raise CmplException("IO error for file " + instFile + ": " + e.strerror)

                    if self.__remoteStatus == CMPLSERVER_BUSY:
                        startTime = time.time()

                    while self.__remoteStatus != PROBLEM_FINISHED:
                        self.knock()

                        time.sleep(self.__refreshTime)
                        if self.__remoteStatus == CMPLSERVER_BUSY and (
                                time.time() - startTime) >= self.__maxCmplServerQueuingTime:
                            raise CmplException("maximum CmplServer queuing time is exceeded.")

                    self.retrieve()
                    break

                except CmplException as e:
                    if self.__serverMode == CMPL_GRID and self.__remoteStatus == CMPLSERVER_ERROR and self.__cmplGridSchedulerUrl != "":
                        try:
                            self.__cmplServerExecute("cmplServerFailed")
                            self.__handleOutput(
                                "CmplServer failed <" + self.__cmplUrl + ">: Problem will be newly connected to CmplGridScheduler and commited to another CmplServer.")

                            self.__cmplUrl = self.__cmplGridSchedulerUrl
                            self.__cmplGridSchedulerUrl = ""
                            self.__cmplGridScheduler = None
                            self.__cmplServer = None
                        except  CmplException as e:
                            raise CmplException("CmplGridScheduler failed: " + e.msg)

                        tries += 1
                        if tries == self.__maxCmplServerTries:
                            raise CmplException(e.msg)

                        continue
                    else:
                        raise CmplException(e.msg)
                    
        else:
            tmpPrefix = self.__baseName
            if self.__cmplArgs.runMode==PYCMPL:
                tmpPrefix += "_cmpl__"+next(tempfile._get_candidate_names())
                self.__cmplFileAlias = tmpPrefix + ".cmpl"
                shutil.copyfile(self.__cmplFile, self.__cmplFileAlias)
            else:
                self.__cmplFileAlias=self.__cmplFile

            if self.__runMode == PYCMPL or not self.__cmplDataFile:
                self.__cmplDataFile = tmpPrefix  + ".cdat"
        
            self.__cmplMsgFile = tmpPrefix + ".cmsg"
            self.__cmplSolFile = tmpPrefix + ".csol"
            
            self.__cmplDataElements()

            self.__status = CmplMessages(self.__cmplMsgFile)
            self.__solutions = CmplSolutions(self.__cmplSolFile)                      
                      
            if self.__cmplArgs.runMode==PYCMPL:
                cmdList = [self.__cmplBinName, self.__cmplFileAlias, "-solution"]
            else:
                cmdList = [self.__cmplBinName,  "-solution"]

            for opt in self.__optionsList:
                tmpOpt = self.__optionsList[opt].split()
                for o in tmpOpt:
                    cmdList.append(o)
            
            cmdList.append("-cmsg")
            cmdList.append(self.__cmplMsgFile)

            self.__runCmpl(cmdList)

            self.__solutions.readSolution()
            self.__solReport=CmplSolutionReport(self.__solutions)

            self.conByName()
            self.varByName()
            self.__writeSolToXls()
      
        self.__cleanUp()


    # *********** end solve ***************

    # *********** run  ********************
    def run(self):
        try:
            self.solve()
        except CmplException as e:
            sys.stderr.write(e.msg + "\n")

    # *********** end run *****************

    # *********** connect  ****************
    def connect(self, cmplUrl):
        if self.__remoteStatus != CMPL_UNKNOWN and self.__remoteStatus != CMPLSERVER_CLEANED and self.__serverMode != CMPL_GRID:
            raise CmplException("Problem is still connected with CMPLServer: at " + cmplUrl + " with jobId " + self.__jobId)

        self.__runCmplPreComp()
        self.setOption("-mark-used solutionAscii solutionCsv")
         
        tries = 0
        while True:
            self.__remoteMode = True
            self.__remoteStatus = CMPL_UNKNOWN
            self.__serverMode = STANDALONE_SERVER
            self.__cmplServer = None
            self.__cmplUrl = cmplUrl
            self.__cmplGridSchedulerUrl = ""
            self.__cmplGridScheduler = None

            try:
                self.__cmplServer = xmlrpc.client.ServerProxy(cmplUrl)
                ret = self.__cmplServer.getJobId(os.path.basename(escape(self.__cmplFile)), self.__solver,self.__compatibility)
                self.__remoteStatus = ret[0]

                if self.__remoteStatus == CMPLSERVER_OK or self.__remoteStatus == CMPLGRID_SCHEDULER_OK or self.__remoteStatus == CMPLGRID_SCHEDULER_BUSY:
                    self.__jobId = ret[2]

                if self.__remoteStatus == CMPLSERVER_OK or self.__remoteStatus == CMPLSERVER_ERROR:
                    self.__serverMode = STANDALONE_SERVER

                elif self.__remoteStatus == CMPLGRID_SCHEDULER_OK or self.__remoteStatus == CMPLGRID_SCHEDULER_ERROR or self.__remoteStatus == CMPLGRID_SCHEDULER_BUSY:
                    self.__serverMode = CMPL_GRID
                    self.__handleOutput("Connected with CmplGridScheduler at " + self.__cmplUrl + " with jobId " + self.__jobId)

                    if self.__remoteStatus == CMPLGRID_SCHEDULER_OK:
                        self.__connectServerViaScheduler(ret[1])
                        self.__serverMode = CMPL_GRID
            except:
                tries += 1

                ret = str(sys.exc_info()[1])
                self.__cmplServer = None

                if self.__remoteStatus != CMPL_UNKNOWN:
                    if tries == self.__maxCmplServerTries:
                        raise CmplException("CmplServer error: " + ret)
                    else:
                        continue
                else:
                    raise CmplException("CmplServer error: " + ret)

            break

        if self.__remoteStatus == CMPLSERVER_ERROR or self.__remoteStatus == CMPLGRID_SCHEDULER_ERROR:
            self.__cleanUp()
            raise CmplException(ret[1])

        self.__cmplServerRunning = True

        if self.__serverMode != CMPL_GRID:
            self.__handleOutput("Connected with CmplServer at " + self.__cmplUrl + " with jobId " + self.__jobId + \
                                " >> maxServerTries <" + str(self.__maxCmplServerTries) + "> maxQueuingTime <" + \
                                str(self.__maxCmplServerQueuingTime) + ">")

        if self.__remoteStatus == CMPLGRID_SCHEDULER_BUSY:
            self.__handleOutput(ret[1])

    # *********** end connect *************

    # *********** connect  ****************
    def disconnect(self):
        self.__cleanUp()

        self.__remoteStatus = CMPL_UNKNOWN
        self.__cmplServer = None
        self.__cmplUrl = ""
        self.__remoteMode = False
        self.__serverMode = STANDALONE_SERVER

    # *********** end connect *************

    # *********** send ********************
    def send(self):
        if self.__remoteMode:       
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplServer")

            if self.__remoteStatus == CMPLSERVER_CLEANED:
                self.connect(self.__cmplUrl)
        
            self.knock()
            if self.__remoteStatus == PROBLEM_RUNNING:
                raise CmplException("Don't send the problem again before the CmplServer finished the previous one")

            self.__cmplDataElements()

            self.__status = CmplMessages()
            self.__solutions = CmplSolutions()
            self.__cmplInstance = CmplInstance()
            self.__instStr = self.__cmplInstance.cmplInstanceStr(self.__cmplFile, self.__cmplArgs, list(self.__optionsList.values()),
                                                                 self.__cmplDataStr.getvalue(), self.__jobId)
     
            ret = self.__cmplServerExecute("send")

            self.__remoteStatus = ret[0]
            if self.__remoteStatus == CMPLSERVER_ERROR:
                self.__cleanUp()
                raise CmplException(ret[1])
        else:
            raise CmplException("Cmpl::send can only be used in remote mode")
    # *********** end send ****************

    # *********** knock *******************
    def knock(self):
        if self.__remoteMode:
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplServer")

            if self.__remoteStatus == CMPLSERVER_CLEANED:
                raise CmplException("Model was received and cleaned on the CmplServer")

            if self.__remoteStatus != PROBLEM_CANCELED:

                ret = self.__cmplServerExecute("knock")
                self.__remoteStatus = ret[0]
              
                self.__handleOutput(ret[2])
                
                if self.__remoteStatus == CMPLSERVER_ERROR or self.__remoteStatus == CMPL_FAILED:
                    self.__cleanUp()
                    raise CmplException(ret[1])
                
        else:
            raise CmplException("Cmpl::knock can only be used in remote mode")
    # *********** end knock ***************

    # *********** retrieve ****************
    def retrieve(self):
        if self.__remoteMode:
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplServer")

            if self.__remoteStatus == CMPLSERVER_CLEANED:
                raise CmplException("Model was received and cleaned from the CmplServer")

            self.knock()

            if self.__remoteStatus == PROBLEM_FINISHED:
                ret = self.__cmplServerExecute("getCmplMessages")

                self.__remoteStatus = ret[0]
                if self.__remoteStatus == CMPLSERVER_ERROR:
                    self.__cleanUp()
                    raise CmplException(ret[1])
                else:
                    self.__status.readCmplMessages(ret[2])
                    
                if self.__status.cmplStatus == CMPL_FAILED:
                    self.__cleanUp()
                    raise CmplException("Cmpl finished with errors", self.__status.cmplMessageList)

                ret = self.__cmplServerExecute("getSolutions")

                if self.__remoteStatus == CMPLSERVER_ERROR:
                    self.__cleanUp()
                    raise CmplException(ret[1])
                else:
                    self.__solutionString = ret[2]
                    self.__solutions.readSolution(self.__solutionString)

                self.__solReport=CmplSolutionReport(self.__solutions)
             
                self.conByName()
                self.varByName()
                self.__writeSolToXls()

                self.__cleanUp()

            else:
                if self.__remoteStatus == PROBLEM_CANCELED:
                    raise CmplException("Model has been canceled by user, cannot retrieve the solution")
                else:
                    raise CmplException("Model is still running, cannot retrieve the solution")
        else:
            raise CmplException("Cmpl::retrieve can only be used in remote mode")

    # if self.__serverMode == CMPL_GRID:
    #	self.disconnect()
  
    # *********** end retrieve ************

    # *********** cancel ******************
    def cancel(self):
        if self.__remoteMode:
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplServer")

            if self.__remoteStatus == CMPLSERVER_CLEANED:
                raise CmplException("Model has been received and cleaned from the CmplServer")

            if self.__remoteStatus != PROBLEM_CANCELED:

                ret = self.__cmplServerExecute("cancel")
                self.__remoteStatus = ret[0]
                if self.__remoteStatus == CMPLSERVER_ERROR:
                    self.__cleanUp()
                    raise CmplException(ret[1])

                ret = self.__cmplServerExecute("removeProblem")
                if self.__remoteStatus == CMPLSERVER_ERROR:
                    self.__cleanUp()
                    raise CmplException(ret[1])
                self.__remoteStatus = CMPLSERVER_CLEANED
        else:
            self.__cleanUp()
    # *********** end cancel **************

    # *********** saveSolution ************
    def saveSolution(self, solFileName=None):
        if self.__solutions.nrOfSolutions > 0:

            if solFileName == None:
                solFile = self.__baseName + ".csol"
            else:
                solFile = solFileName

            self.__solReport.saveSolution(self.__baseName + ".cmpl", solFile)
            self.__handleOutput("CMPL: Solution has been written to cmplSolution file: " + solFile)
    # *********** end saveSolution ********

    # *********** saveSolutionAscii *******
    def saveSolutionAscii(self, solFileName=None):
        if self.__solutions.nrOfSolutions > 0:
            if solFileName == None:
                solFile = self.__baseName + ".sol"
            else:
                solFile = solFileName
            self.solutionReport(solFile)
            self.__handleOutput("CMPL: Solution has been written to ASCII file: " + solFile)
        else:
            raise CmplException("No Solution found so far")

    # *********** saveSolutionAscii *******

    # *********** saveSolutionCsv *******
    def saveSolutionCsv(self, solFileName=None):
        if self.__solutions.nrOfSolutions > 0:
            if solFileName == None:
                solFile = self.__baseName + ".sol"
            else:
                solFile = solFileName
            self.__solReport.saveSolutionCsv( os.path.basename(self.__cmplFile), solFile )
            self.__handleOutput("CMPL: Solution has been written to CSV file: " + solFile)
        else:
            raise CmplException("No Solution found so far")

    # *********** saveSolutionCsv *******

    # *********** solutionReport **********
    def solutionReport(self, fileName=None):
        self.__solReport.solutionReport(os.path.basename(self.__cmplFile), fileName)
    # *********** end solutionReport ******
   
    # *********** saveCmplMessageFile ************
    def saveCmplMessageFile(self, msgFileName=None):
        if msgFileName == None or msgFileName == "":
            fName = self.__baseName + ".cmsg"
        else:
            fName = msgFileName
        #self.__writeAsciiFile(fName, self.__cmplMessageString)
        self.__handleOutput("CMPL: Writing CmplMessages to file: " + fName)
        self.__status.writeCmplMessages(fName)
        

    # *********** saveCmplMessageFile ************

    # ********************************************************************************
    # private methods								*
    # ********************************************************************************

    # *********** running PreCompiler ************
    def __runCmplPreComp(self):
        if self.__cmplArgs.runMode==PYCMPL:
            #print("running preComp")
            
            cmdList = [self.__cmplBinName, self.__cmplFile, "-o-opt", self.__preCompAlias+".optcmpl", "-o-pre", self.__preCompAlias+".precmpl" , "-o-extern", self.__preCompAlias+".extdata", "-modules" , "precomp", "-no-warn-unused"]
            self.__cmplMsgFile

            for opt in self.__optionsList:
                tmpOpt = self.__optionsList[opt].split()
                for o in tmpOpt:
                    cmdList.append(o)

            cmdList.append("-cmsg")
            if not self.__cmplMsgFile:
                self.__cmplMsgFile = os.path.splitext(self.__cmplFile)[0]+".cmsg"
            cmdList.append(self.__cmplMsgFile)
            self.__status = CmplMessages(self.__cmplMsgFile)
            
            self.__runCmpl(cmdList)
            self.__cmplArgs.parseOptFile()
            self.__solver=self.__cmplArgs.solver
    # *********** end running PreCompiler ************
    
            
    # *********** running Cmpl ************  
    def __runCmpl(self, cmdList):
        self.__cmplBinHandler = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        while True:
            line = self.__cmplBinHandler.stdout.readline()
            if len(line) > 0:
                self.__handleOutput(line)
            else:
                break

        if self.__cmplBinHandler.wait() != 0:
            raise CmplException(self.__cmplBinHandler.stderr.read())

        self.__status.readCmplMessages()

        if self.__status.cmplStatus == CMPL_FAILED:
            raise CmplException("Cmpl finished with errors", self.__status.cmplMessageList)
    # *********** end running Cmpl ************  


    # *********** cleanUp ****************
    def __cleanUp(self):
        if not self.__isCleaned:
            if self.__debug:
                #eval(input("Hit Enter to exit"))
                input("Hit Enter to exit")

            if self.__remoteMode:
                if not (self.__serverMode == CMPL_GRID and self.__cmplGridSchedulerUrl == ""):
                    # if not (self.__remoteStatus==PROBLEM_FINISHED or self.__remoteStatus==CMPLSERVER_ERROR or self.__remoteStatus==PROBLEM_CANCELED):
                    if (self.__remoteStatus != PROBLEM_FINISHED and self.__remoteStatus != CMPLSERVER_ERROR and self.__remoteStatus != PROBLEM_CANCELED):
                        if self.__cmplServerRunning:
                            self.__cmplServerExecute("cancel")

                    if (self.__remoteStatus != CMPLSERVER_CLEANED and self.__remoteStatus != CMPLSERVER_ERROR):
                        self.__cmplServerExecute("removeProblem")
                        self.__remoteStatus = CMPLSERVER_CLEANED

                if self.__serverMode == CMPL_GRID:
                    if self.__remoteStatus == CMPLGRID_SCHEDULER_BUSY or self.__remoteStatus == CMPLGRID_SCHEDULER_UNKNOWN:
                        self.__cmplServerExecute("disconnectFromScheduler")

            elif self.__cmplBinHandler != None:
                if self.__cmplBinHandler.poll() == None:
                    self.__cmplBinHandler.kill()

            if self.__cmplDataFile != None and not self.__remoteMode and (self.__cmplArgs.runMode==PYCMPL or self.__isXlsData):
                if os.path.isfile(self.__cmplDataFile):
                    os.remove(self.__cmplDataFile)
                    
            if self.__cmplMsgFile and not self.__cmplArgs.msgFile:
                if os.path.isfile(self.__cmplMsgFile):
                    os.remove(self.__cmplMsgFile)
            
            if self.__cmplSolFile and not self.__cmplArgs.solFile:
                if os.path.isfile(self.__cmplSolFile):
                    os.remove(self.__cmplSolFile)

            #if self.__cmplFileAlias and self.__isAlias:
            if self.__cmplFileAlias and self.__cmplArgs.runMode==PYCMPL:
                if os.path.isfile(self.__cmplFileAlias):
                    os.remove(self.__cmplFileAlias)

            self.__isCleaned = True
    # *********** end cleanUp ************

    # *********** writeCmplDataFile *******
    def __cmplDataElements(self):
        try:
            for s in self.__setList:          
                self.__cmplDataStr.write("%" + s.name)

                if s.rank > 1:
                    self.__cmplDataStr.write(' set[' + str(s.rank) + '] < ')
                else:
                    self.__cmplDataStr.write(' set < ')

                if s.type == 0:
                    self.__cmplDataStr.write('\n')
                    count = 1
                    for i in s.valueList:
                        if type(i) == str:
                            self.__cmplDataStr.write("\"" + i + '\" ')
                        elif type(i) == float:
                            self.__cmplDataStr.write(str(int(i)) + ' ')
                        elif (type(i) == int or type(i) == int):
                            self.__cmplDataStr.write(str(i) + ' ')
                        else:
                            self.__cmplDataStr.write("\"" + str(i) + "\" ")
                        if count == s.rank:
                            self.__cmplDataStr.write('\n')
                            count = 1
                        else:
                            count += 1

                if s.type == 1:
                    self.__cmplDataStr.write('\n')
                    for i in s.valueList:
                        for j in i:
                            if type(j) == list:
                                raise CmplException("set " + s.name + " contains unexpected data " + str(j))
                            if type(j) == str:
                                self.__cmplDataStr.write("\"" + j + "\" ")
                            elif type(j) == float:
                                self.__cmplDataStr.write(str(int(j)) + ' ')
                            elif (type(j) == int or type(j) == int):
                                self.__cmplDataStr.write(str(j) + ' ')
                            else:
                                self.__cmplDataStr.write("\"" + str(j) + "\" ")
                        self.__cmplDataStr.write('\n')

                if s.type == 2:
                    self.__cmplDataStr.write(str(s.valueList[0]) + '..' + str(s.valueList[1]) + ' ')

                if s.type == 3:
                    self.__cmplDataStr.write(
                        str(s.valueList[0]) + '(' + str(s.valueList[1]) + ')' + str(s.valueList[2]) + ' ')

                self.__cmplDataStr.write('>\n')

            for p in self.__parameterList:
                self.__cmplDataStr.write('%' + p.name)

                if p.rank > 0:
                    self.__cmplDataStr.write("[")

                    pos = 0
                    for s in p.setList:
                        setFound = False
                        for j in self.__setList:
                            if j.name == s.name:
                                setFound = True
                                break
                        if not setFound:
                            raise CmplException(
                                "The set " + s.name + " used for the parameter " + p.name + " doesn't exist.")
                        else:
                            self.__cmplDataStr.write(s.name)
                            if pos < len(p.setList) - 1:
                                self.__cmplDataStr.write(",")
                            pos += 1

                    self.__cmplDataStr.write('] ')

                    if 'LIST' in str(type(p.values)).upper():
                        # if type(p.values)==list:
                        self.__cmplDataStr.write(' <\n')
                        for e in p.values:
                            if type(e) == list:
                                self.__cmplDataStr.write(self.__writeListElements(e))
                            else:
                                if type(e) == str:
                                    self.__cmplDataStr.write('\"' + e + "\" \n")
                                else:
                                    self.__cmplDataStr.write(str(e) + '\n')

                    elif 'DICT' in str(type(p.values)).upper():
                        if p.defaultValue != None:

                            if type(p.defaultValue) == str:
                                self.__cmplDataStr.write(' = \"' + p.defaultValue + '\" ')
                            else:
                                self.__cmplDataStr.write(' = ' + str(p.defaultValue) + ' ')

                        self.__cmplDataStr.write(' indices <\n')

                        for e in p.values:

                            if type(e) == tuple:
                                for i in e:
                                    if type(i) == str:
                                        self.__cmplDataStr.write("\"" + i + '\" ')
                                    elif type(i) == float:
                                        self.__cmplDataStr.write(str(int(i)) + ' ')
                                    else:
                                        self.__cmplDataStr.write(str(i) + ' ')
                            elif type(e) == str:
                                self.__cmplDataStr.write('\"' + e + "\" ")
                            elif type(e) == float:
                                self.__cmplDataStr.write(str(int(e)) + ' ')
                            else:
                                self.__cmplDataStr.write(str(e) + ' ')

                            if type(p.values[e]) == str:
                                self.__cmplDataStr.write('\"' + p.values[e] + "\" \n")
                            else:
                                self.__cmplDataStr.write(str(p.values[e]) + '\n')

                    self.__cmplDataStr.write(">\n")

                else:
                    self.__cmplDataStr.write(" < ")
                    if type(p.values[0]) == str:
                        self.__cmplDataStr.write('\"' + p.values[0] + "\" >\n")
                    else:
                        self.__cmplDataStr.write(str(p.values[0]) + " >\n")

            if self.__cmplDataStr.getvalue() != "":
                if self.__remoteMode:
                    pass
                else:
                    f = open(self.__cmplDataFile, 'w')
                    f.write(self.__cmplDataStr.getvalue())
                    f.close()

        except IOError as e:
            raise CmplException("IO error for cmplDateFile " + self.__cmplDataFile + ": " + e.strerror)
    # *********** end writeCmplDataFile ***

    # *********** writeListElements *******
    def __writeListElements(self, valList):
        tmpStr = io.StringIO()
        for v in valList:
            if type(v) == list:
                tmpStr.write(self.__writeListElements(v))
            else:
                if type(v) == str:
                    tmpStr.write('\"' + v + '\" ')
                else:
                    tmpStr.write(str(v) + ' ')
        tmpStr.write('\n')
        tStr = tmpStr.getvalue()
        tmpStr.close()
        return tStr

    # *********** end __writeListElements ****

    # *********** __solByNr ***************
    def __solByNr(self, solNr):
        if self.__solutions.nrOfSolutions > 0:
            if solNr <= self.__solutions.nrOfSolutions:
                return self.__solutions.solutions[solNr]
            else:
                raise CmplException("Solution with number: " + str(solNr) + " doesn't exist.")
        else:
            raise CmplException("No Solution found so far")

    # *********** end __solByNr ***********

    # *********** getElementByName ***********
    def __getElementByName(self, name, solObj):
        if self.__solutions.nrOfSolutions > 0:
            solElements = []
            solElement = None
            isArray = False
            isFound = False

            for e in solObj:
                if e.name.startswith(name):
                    if e.name.find("[") != -1:
                        if e.name.split('[')[0] == name:
                            isArray = True
                            solElements.append(e)
                            isFound = True
                    else:
                        if e.name == name:
                            isArray = False
                            solElement = e
                            isFound = True

            if not isFound:
                raise CmplException(name + " does not exist.")
            if isArray:
                return solElements
            else:
                return solElement
        else:
            raise CmplException("No Solution found so far")
    # *********** end getElementByName *****

    # *********** elementByName ***********
    def __elementByName(self, solObj):
        elemFound = []

        for e in solObj:
            tmpName = ""
            tmpSet = ""
            pos = e.name.find("[")

            if pos != -1:
                tmpName = e.name[:pos]
                if not tmpName in elemFound:
                    exec ("self." + tmpName + "=collections.OrderedDict()")
                    elemFound.append(tmpName)

                tmpSet = e.name[pos + 1:-1].split(',')
                tmpSetStr = io.StringIO()
                tmpSetStr.write("(")
                sNr = 1
                for s in tmpSet:
                    if sNr > 1:
                        tmpSetStr.write(",")
                    if CmplTools.strIsNumber(s):
                        tmpSetStr.write(s)
                    else:
                        tmpSetStr.write("\"" + s + "\"")
                    sNr += 1
                tmpSetStr.write(")")

                exec ("self." + tmpName + "[" + tmpSetStr.getvalue() + "] = e")
                tmpSetStr.close()

            else:
                tmpName = e.name
                exec ("self." + tmpName + "=e")
    # *********** end elementByName *******

    # *********** __handleOutput ************
    def __handleOutput(self, oStr):
        if type(oStr)==bytes:
            oStr=oStr.decode("utf-8")
        if oStr != '':
            if self.__printOutput:
                if self.__outputLeadString != '':
                    print((self.__outputLeadString + oStr.strip().replace("\n", "\n" + self.__outputLeadString)))
                else:
                    print((oStr.strip().replace("\n", "\n" + self.__outputLeadString)))
    # *********** end __handleOutput ********

    # *********** __connectServerViaScheduler  ****************
    def __connectServerViaScheduler(self, cmplUrl):
        self.__cmplGridSchedulerUrl = self.__cmplUrl
        self.__cmplUrl = cmplUrl
        self.__cmplGridScheduler = self.__cmplServer
        self.__serverMode = CMPL_GRID

        try:
            self.__cmplServer = xmlrpc.client.ServerProxy(self.__cmplUrl, allow_none=False)
            self.__handleOutput("Connected with CmplServer at " + self.__cmplUrl + " with jobId " + self.__jobId + \
                                " >> maxServerTries <" + str(self.__maxCmplServerTries) + "> maxQueuingTime <" + str(
                self.__maxCmplServerQueuingTime) + ">")

        except:
            self.__remoteStatus = CMPLSERVER_ERROR
            raise CmplException(str(sys.exc_info()[1]))
    # *********** end __connectServerViaScheduler  ****************

    # *********** __knockScheduler *******************
    def __knockScheduler(self):
        if self.__remoteMode:
            if not self.__cmplServerRunning:
                raise CmplException("Model is not connected to a CmplScheduler")

            if self.__remoteStatus != PROBLEM_CANCELED:

                ret = self.__cmplServerExecute("knock")

                self.__remoteStatus = ret[0]

                if self.__remoteStatus == CMPLGRID_SCHEDULER_ERROR:
                    self.__cleanUp()
                    raise CmplException(ret[1])
                elif self.__remoteStatus == CMPLGRID_SCHEDULER_OK:
                    self.__connectServerViaScheduler(ret[1])
        else:
            raise CmplException("Cmpl::knock can only be used in remote mode")
    # *********** end __knockScheduler ***************

    # *********** cmplServerExecute *******
    def __cmplServerExecute(self, method=""):
        ret = []
        tries = 0
        while True:
            try:
                if method == "cancel":
                    ret = self.__cmplServer.cancel(self.__jobId)
                elif method == "removeProblem":
                    ret = self.__cmplServer.removeProblem(self.__jobId)
                elif method == "send":
                    ret = self.__cmplServer.send(self.__instStr)
                elif method == "knock":
                    ret = self.__cmplServer.knock(self.__jobId)
                elif method == "getCmplMessages":
                    ret = self.__cmplServer.getCmplMessages(self.__jobId)
                elif method == "getSolutions":
                    ret = self.__cmplServer.getSolutions(self.__jobId)
                elif method == "cmplServerFailed":
                    ret = self.__cmplGridScheduler.cmplServerFailed(self.__cmplUrl)
                elif method == "disconnectFromScheduler":
                    ret = self.__cmplServer.disconnectProblem(self.__jobId)
            except:
                tries += 1
                if tries == self.__maxCmplServerTries:
                    self.__remoteStatus = CMPLSERVER_ERROR
                    self.__cleanUp()
                    raise CmplException("CmplServer error : " + str(sys.exc_info()[1]))
                else:
                    continue
            break
        return ret
    # ******** end cmplServerExecute *******

    # *********** __writeSolToXls *******************
    def __writeSolToXls(self):
        if self.__isXlsData and self.__solutions.nrOfSolutions > 0:
            if not self.__xlsData:
                self.__xlsData=CmplXlsData(self.__xlsDataFile,  self.__cmplArgs)
            if not self.__cmplArgs.isSilent:
                print("CMPL: Writing solution to Excel file <"+self.__xlsData.xlsFile+">")

            for idx,o in enumerate(self.__xlsData.solutionElements):
                if o.outType!="info":
                    s = eval("self."+o.name)
                else:
                    s=None
                self.__xlsData.writeSolElemToXls(s,idx, self.__solutions)
    # *********** end __writeSolToXls *******************


    # *********** __writeAsciiFile  *******
    def __writeAsciiFile(self, fname, str):
        try:
            f = open(fname, 'w')
            f.write(str)
            f.close()
        except IOError as e:
            raise CmplException("IO error for file " + fname + ": " + e.strerror)
    # ******** end __writeAsciiFile  *******


#################################################################################
# End Cmpl																		
#################################################################################
