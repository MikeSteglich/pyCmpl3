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


from .CmplException import *
from .CmplSet import *
from .CmplParameter import *

import sys
import io
import os

import re
import time
import subprocess
import math
import copy

if sys.platform in ('darwin', 'win32'):
    import xlwings as xw



#*************** InputSet ***********************************
class InputSet:
    def __init__(self, name, rank, cellRange, lineNr=0):
        self.name=name
        self.rank=rank
        self.sheet=""
        if "!" in cellRange:
            val = re.findall('(.*)\!(.*)',cellRange)
            self.sheet=val[0][0].strip()
            self.cellRange=val[0][1].strip()
        else:
            self.cellRange=cellRange
        self.lineNr=lineNr
#*************** end InputSet ***********************************

#*************** InputParameter ***********************************
class InputParameter:
    def __init__(self, name , defSets, cellRange, lineNr=0):
        if "[" in name:
            self.name=name[: name.find("[")].strip() 
        else:
            self.name=name
        self.sets=defSets
        self.sheet=""
        if "!" in cellRange:
            val = re.findall('(.*)\!(.*)',cellRange)
            self.sheet=val[0][0].strip()
            self.cellRange=val[0][1].strip()
        else:
            self.cellRange=cellRange
        self.lineNr=lineNr
#*************** end InputParameter ***********************************

#*************** OutputElement ***********************************
class OutputElement:
    def __init__(self, name , defSets, cellRange, outType, sheet, lineNr=0):
        if "[" in name:
            self.name=name[: name.find("[")].strip() 
        else:
            self.name=name
        self.sets=defSets
        self.sheet=sheet
        if "!" in cellRange:
            val = re.findall('(.*)\!(.*)',cellRange)
            self.sheet=val[0][0].strip()
            self.cellRange=val[0][1].strip()
        else:
            self.cellRange=cellRange
        self.lineNr=lineNr
        self.outType = outType
        self.indices = []
#*************** end OutputElement ***********************************      

#*************** CmplXlsData ***********************************
class CmplXlsData:
    
    #*************** constructor ***********************************
    def __init__(self, cmplXlsDataFile, cmplArgs=None):

        if sys.platform not in ('darwin', 'win32'):
            raise CmplException("ERROR: CmplXlsData is only availabe for Windows and macOS"  )

        self.__cmplXlsDataFile=cmplXlsDataFile

        self.__xlsFile = ""
        self.__activeSheet = ""
        self.__xlsFileLineNr = 0
        self.__activeSheetLineNr = 0

        self.__wb = None
        self.model = None

        self.__setList = {}
        self.__parameterList = []
        self.__inputParList = []
        self.__inputSetList = {}

        self.__outputList = []

        self.__msgList = []

        self.__lineNr=0

        self.__sheetNames=[]

        self.__xlsDatAttributes = ("objName", "objSense" , "objValue" , "objStatus",  "nrOfVars" , "nrOfCons" ,"solver",  "solverMsg")
        self.__cmplAttributes=("objectiveName", "objectiveSense" , "solution.value" , "solution.status",  "nrOfVariables" , "nrOfConstraints" ,"solver",  "solverMessage")

        self.__readCmplXlsFile()

        if not os.path.isfile(self.__xlsFile):
                self.__lineNr=self.__xlsFileLineNr
                raise CmplException("Excel file <"+self.__xlsFile+"> cannot be found" )

        if sys.platform=='darwin':
                subprocess.check_call(['open', '-a', 'Microsoft Excel', self.__xlsFile])
                time.sleep(0.4)
            
        self.__wb = xw.Book(self.__xlsFile)
        self.__getSheetNames(self.__wb)

        self.__cmplArgs=cmplArgs
    #*************** end constructor ***********************************

    #*************** getters ***********************************
    @property
    def xlsFile(self):
        return self.__xlsFile

    @property
    def solutionElements(self):
        return self.__outputList
    #*************** end getters ***********************************


    #*************** __splitNameVal ***********************************
    def __splitNameVal(self, valString, valType="val"):
        if valType not in ("val","set"):
            raise CmplException("Internal error: wrong type in __contenVal <"+valType+">"  )
    
        if valType=="val":
            val = re.findall('(.*)\<(.*)\>',valString)
        else:
            val = re.findall('(.*)\[(.*)\]',valString)
       
        #if len(val[0])<2:
        if not val:
            self.__error( "inclomplete entry imbedded in < and >  or [ and ]" )
           
        return (val[0][0].strip(),val[0][1].strip())
    #*************** end __splitNameVal ***********************************
    
    #*************** __rankOfSet ***********************************
    def __rankOfSet(self,valString):
        rank = 1
        if "[" in valString:
            (tmp, rankString) = self.__splitNameVal(valString,  "set")

            if rankString.isdigit():
                rank = int (rankString)
            else:
                self.__error( "wrong rank of the set" )
        return rank
    #*************** end __rankOfSet ***********************************

    #*************** __defSets ***********************************
    def __defSets(self,valString):
        setList = []
        if "[" in valString:
            (tmp, setString) = self.__splitNameVal(valString, "set")
            setList = setString.split(",")
            for n,s in enumerate(setList):
                setList[n]=s.strip()
        return setList
    #*************** end __defSets ***********************************

    #*************** __outputNameType ***********************************
    def __outputNameType(self,valString):
        outList=re.findall("(.*)\.(.*)",valString)
        if not outList or len(outList[0])<2 or not outList[0][1] in ("name","activity", "type", "lowerBound", "upperBound", "marginal" ):
            self.__error(  "wrong output type " )
        return outList[0]
    #*************** end __outputNameType ***********************************

    #*************** __error ***********************************
    def __error(self, msg):
        self.__msgList.append((self.__cmplXlsDataFile,  self.__lineNr, msg ))
        raise CmplException("Error in CmplXlsData file <"+self.__cmplXlsDataFile+"> in line <" + str(self.__lineNr) + "> "+ msg)
    #*************** end __error ***********************************
    
    #*************** __getSheetNames ***********************************   
    def __getSheetNames(self, wb):
        for s in wb.sheets:
            self.__sheetNames.append(s.name)
    #*************** end __getSheetNames ***********************************  

    #*************** __readCmplXlsFile ***********************************
    def __readCmplXlsFile(self):      
        dataString=""
        
        if self.__cmplXlsDataFile != None:
            if not os.path.isfile(self.__cmplXlsDataFile):
                raise CmplException("CmplXlsData file <"+self.__cmplXlsDataFile+"> cannot be found" )
            try:
                f = open(self.__cmplXlsDataFile, "r")
                dataString = f.read()
                f.close()
            except IOError as e:
                raise CmplException("IO error for CmplXlsData file <"+self.__cmplXlsDataFile+">")
        else: 
            raise CmplException("No CmplXlsData file has been specified")
        
        lines = io.StringIO(dataString) 

        sourceSection=False
        inputSection=False
        outputSection=False
        
        for line in lines:
            self.__lineNr += 1
            line=line.lstrip()
            
            if line.startswith("@source"):
                sourceSection=True
                inputSection=False
                outputSection=False
                continue
            if line.startswith("@input"):
                sourceSection=False
                inputSection=True
                outputSection=False
                continue
            if line.startswith("@output"):
                sourceSection=False
                inputSection=False
                outputSection=True
                continue

            if  line.startswith("%"):
                (name,val) = self.__splitNameVal(line)
                name=name[1:]
                #print(name,val)
                
                if sourceSection:
                    if name.startswith("file"):
                        self.__xlsFile=val
                        self.__xlsFileLineNr=self.__lineNr
                        if not os.path.exists(self.__xlsFile):
                            self.__error("Can't find Excel file <" + self.__xlsFile+">")
                        
                    elif name.startswith("sheet"):
                        self.__activeSheet=val
                        self.__activeSheetLineNr=self.__lineNr
                        
                    else:
                        self.__error("Unknown entry in meta section <" + name+">")
                
                if inputSection:
                    if " set" in name:
                        setName=name[: name.find("set")].strip() 
                        setRank=self.__rankOfSet(name)
                        setCellRange=val
                        self.__inputSetList[setName] = InputSet(setName,setRank,setCellRange, self.__lineNr) 
                    else:
                        parName=name
                        parDefSets=self.__defSets(name)
                        for s in parDefSets:
                            if not s in self.__inputSetList:
                                self.__error(  " set <"+s+"> not defined  " )
                        parCellRange=val
                        self.__inputParList.append( InputParameter(parName,parDefSets,parCellRange,self.__lineNr) )

                if outputSection:
                    if name in self.__xlsDatAttributes:
                        outName=name
                        outDefSets=[]
                        outType="info"
                    else:
                        (outName,outType)=self.__outputNameType(name)
                        outDefSets=self.__defSets(outName)
                        for s in outDefSets:
                            if not s in self.__inputSetList:
                                self.__error(  " set <"+s+"> not defined  " )
                    outCellRange=val
                    self.__outputList.append( OutputElement(outName,outDefSets,outCellRange,outType, self.__activeSheet, self.__lineNr) )
    #*************** end __readCmplXlsFile ***********************************

    #*************** readXlsData ***********************************
    def readXlsData(self):
        try:
            if not self.__cmplArgs.isSilent:
                print("CMPL: Reading data from Excel file <"+self.__xlsFile+">")
            if self.__activeSheet:
                if not self.__activeSheet in self.__sheetNames:
                    self.__lineNr=self.__activeSheetLineNr
                    raise self.__error("Unknown sheet <"+ self.__activeSheet+ "> in Excel file <"+self.__xlsFile+">")
            else:
                self.__activeSheet=self.__wb.sheets[0].name

            sht = self.__wb.sheets[self.__activeSheet]

            for s in self.__inputSetList.values(): 
                cmplSet = CmplSet( s.name, s.rank ) 
                if s.sheet:
                    if not s.sheet in self.__sheetNames:
                        self.__lineNr=s.lineNr
                        raise self.__error("Unknown sheet <"+ s.sheet + "> in Excel file <"+self.__xlsFile+">")
                    sht = self.__wb.sheets[s.sheet]

                cmplSet.setValues( sht.range( s.cellRange ).value)
                for i in cmplSet.values:
                    if not i:
                        self.__lineNr=s.lineNr
                        raise self.__error("set <"+ s.name+">: one of the indices are empty.")
                    if type(i)== tuple:
                        for e in i:
                            if re.search('\s',str(e)):
                                self.__lineNr=s.lineNr
                                raise self.__error("set <"+ s.name+">: index <"+ str(i)+ "> contains whitespaces.") 

                    elif re.search('\s',str(i)):
                        self.__lineNr=s.lineNr
                        raise self.__error("set <"+ s.name+">: index <"+ str(i) + "> contains whitespaces.") 
                     
    
                if s.sheet:
                    sht = self.__wb.sheets[self.__activeSheet]

                self.__setList[cmplSet.name ]= cmplSet
                print("     Set <"+s.name +"> has been read")
            for p in self.__inputParList:
                sList=[]
                sCount=1

                for s in p.sets:
                    sList.append(self.__setList[s])
                    sCount*=self.__setList[s].len
                
                cmplPar = CmplParameter(p.name, sList)

                if p.sheet:
                    if not p.sheet in self.__sheetNames:
                        self.__lineNr=p.lineNr
                        raise self.__error("Unknown sheet <"+ p.sheet + "> in Excel file <"+self.__xlsFile+">")
                    sht = self.__wb.sheets[p.sheet]

                cmplPar.setValues( sht.range( p.cellRange ).value )

                if cmplPar.len!=sCount:
                    raise self.__error("Dimension of the parameter <"+ p.name + "> does not fit the dimension of its set(s) ")
                
                self.__parameterList.append(cmplPar)

                if p.sheet:
                    sht = self.__wb.sheets[self.__activeSheet]
                
                print("     Parameter <"+p.name +"> has been read")

            for o in self.__outputList:
                if o.outType!="info": 
                    indices=[]
                    firstIdx=True
                    for s in o.sets:
                        if indices:
                            firstIdx=False
                                       
                        if not firstIdx:      
                            tmpIndices=[]   
                            for idx in indices:
                                for e in self.__setList[s].values:  
                                    tmpIdx=idx.copy() 
                                    if type(e) in (list, tuple):
                                        for ei in e:
                                            tmpIdx.append(ei)
                                    else:
                                        tmpIdx.append(e)
                                    tmpIndices.append(tmpIdx)
                            indices=tmpIndices
                        else:
                            for e in self.__setList[s].values:
                                if type(e)==list:
                                    indices.append(e)
                                elif type(e)==tuple:
                                    indices.append( list(e) )
                                else:
                                    indices.append([e])
                    o.indices=indices
           
            return (list(self.__setList.values()), self.__parameterList)

        except CmplException as e:
            raise CmplException(e.msg)

        except:
            raise CmplException("Something went wrong while reading <"+self.__xlsFile+"> : "+str(sys.exc_info()[1]))
    #*************** end readXlsData ***********************************
    

    #*************** writeSolElemToXls ***********************************
    def writeSolElemToXls(self, solElem, idx, sol):
        try:
            o = self.__outputList[idx]
            if o.sheet:
                if not o.sheet in self.__sheetNames:
                    self.__wb.sheets.add(o.sheet)
                
                sht = self.__wb.sheets[o.sheet]
                    
                if o.outType=="info": 
                    attIdx=-1
                    try:
                        attIdx=self.__xlsDatAttributes.index(o.name)
                    except:
                        self.__error("Internal error while accessing attribute <"+o.name+">")
                    val = eval("sol."+self.__cmplAttributes[attIdx])
                    sht.range(o.cellRange).value= val
                else:
                    try:
                        rows = len(sht.range(o.cellRange).rows)
                        cols = len(sht.range(o.cellRange).columns) 
                        solElemLen=0
                        if 'collections.OrderedDict' in str(type(solElem)):
                            solElemLen=len(solElem)
                        else:
                            solElemLen=1
                        if solElemLen!=rows*cols:
                            self.__lineNr=o.lineNr
                            self.__error("Wrong dimension of variable or constraint <"+o.name+"> in comparison to cellRange <"+o.cellRange+">")
                        values=None
                        
                        if rows == 1 and cols == 1:
                            val = eval("solElem."+o.outType)
                            if o.outType in ("activity", "lowerBound", "upperBound", "marginal" ):
                                if math.isnan(val):
                                    val = "NaN"
                                if val==math.inf:
                                        val="inf"
                                if val==-math.inf:
                                    val="-inf"
                            values= val
                        #setting array in the dimensions of the excel cell range
                        elif  rows==1 and cols>1:
                            values=[0 for j in range (cols)]
                        else:
                            values = [ [0 for j in range(cols)] for i in range(rows)]

                        i=0
                        if not (rows == 1 and cols == 1):

                            for idx in o.indices:
                                if len(idx)>1:
                                    key = str(tuple(idx))
                                else:
                                    if type(idx[0])==str:
                                        key="'"+idx[0]+"'"
                                    else:
                                        key = str(idx[0])
                                
                                val = eval('solElem['+key+'].'+o.outType)
                                if o.outType in ("activity", "lowerBound", "upperBound", "marginal" ):
                                    if math.isnan(val):
                                        val = "NaN"
                                    if val==math.inf:
                                        val="inf"
                                    if val==-math.inf:
                                        val="-inf"

                                if rows==1 and cols>1:
                                    values[i]=val
                                elif rows>1 and cols==1:
                                    values[i][0]=val
                                else:
                                    ii=math.ceil( (i+1)/cols )-1
                                    jj=i-ii*cols
                                    values[ii][jj]= val 
                                i+=1
                       
                        sht.range(o.cellRange).value= values

                    except CmplException as e:
                        raise CmplException(e.msg)
                    except:
                        raise CmplException("Internal error while accessing variable or constraint <"+o.name+"> : "+str(sys.exc_info()[1]))
                        
                if o.sheet:
                    sht = self.__wb.sheets[self.__activeSheet]

            print("     <"+o.name+"."+o.outType+"> has been written")
        except CmplException as e:
            raise CmplException(e.msg)
        except:
            raise CmplException("Something went wrong while writing <"+self.__xlsFile+"> : "+str(sys.exc_info()[1]))
    #*************** end writeSolElemToXls ***********************************
#*************** end  CmplXlsData ***********************************