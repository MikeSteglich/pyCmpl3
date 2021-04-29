#***********************************************************************
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
 #**********************************************************************


import os
import sys

from .CmplDefs import *
from .CmplException import *

#*************** CmplArgs ***********************************
class CmplArgs:
	
	def __init__(self, optFile=None):

		self.__optFile = optFile
		
		self.__cmplFile=""
		self.__modelName=""	

		self.__url=""
		self.__maxTries = 10
		self.__maxTime = 300
		
		self.__externalFiles = []

		self.__xlsDataFile = ""
		self.__messageFile=""
		self.__matrixFile=""
		self.__solFile=""
		self.__solAsciiFile=""
		self.__solCsvFile=""

		self.__isFileOut=False

		self.__runMode = CMPL_LOCAL

		self.__isSilent = False

		self.__solver = "cbc"

	#******** getter **********************************************		
	@property
	def optFile(self):
		return self.__optFile

	@property
	def optAlias(self):
		return os.path.splitext(self.__optFile)[0]

	@property
	def cmplFile(self):
		return self.__cmplFile
	
	@property
	def baseName(self):
		return self.__modelName

	@property
	def url(self):
		return self.__url

	@property
	def maxTries(self):
		return self.__maxTries

	@property
	def maxTime(self):
		return self.__maxTime

	@property
	def runMode(self):
		return self.__runMode

	def setRunMode(self, mode):
		if mode in (CMPL_LOCAL, CMPL_REMOTE_SOLVE , CMPL_REMOTE_SEND , CMPL_REMOTE_KNOCK , CMPL_REMOTE_RETRIEVE , CMPL_REMOTE_CANCEL ,PYCMPL):
			self.__runMode = mode
		else:
			raise CmplException("Wrong running mode ")
	
	@property
	def msgFile(self):
		return self.__messageFile

	@property
	def xlsDataFile(self):
		return self.__xlsDataFile

	@property
	def externalFiles(self):
		return self.__externalFiles

	@property
	def msgFile(self):
		return self.__messageFile

	@property
	def solFile(self):
		return self.__solFile

	@property
	def solAsciiFile(self):
		return self.__solAsciiFile

	@property
	def solCsvFile(self):
		return self.__solCsvFile
	
	@property
	def isFileOut(self):
		return self.__isFileOut

	@property
	def isSilent(self):
		return self.__isSilent

	@property
	def solver(self):
		return self.__solver

	#******** getter **********************************************


	#******** parseOptFile **********************************************
	def parseOptFile(self):
		if not self.__optFile:
			raise CmplException("Cannot parse option file, because it is not defined")

		nrOfXlsDataFiles=0
		
		try:
			f = open(self.__optFile, "r")
			opts = f.read()
			f.close()

			if not opts:
				raise CmplException("Cannot read options form opt file")

			lines = opts.split(os.linesep)

			for line in lines:
				line=line.strip()
				
				if line.startswith("#"):
					continue

				if not line:
					continue

				optList=line.split(";")

				key = optList[0].upper()
				if optList[9]=="0":
					val=""
				else:
					val = optList[10]

				if key=="I":
					self.__cmplFile=val[1:-1]
					self.__modelName = os.path.splitext(self.__cmplFile)[0]

				elif key=="XLSDATA":
					if not val or val[1:-1]==":":
						self.__xlsDataFile = self.__modelName+".xdat"
					else:	
						self.__xlsDataFile=val[1:-1]
					nrOfXlsDataFiles+=1

				elif key=="DATA":
					tmpName=""
					if not val or val[1:-1]==":":
						tmpName = self.__modelName+".cdat"
					else:	
						tmpName=val[1:-1]
					self.__externalFiles.append(tmpName)

				elif key=="INCLUDE":
					self.__externalFiles.append(val[1:-1])
					
				elif key=="URL":
					self.__url = val[1:-1]
					self.__runMode = CMPL_REMOTE_SOLVE

				elif key=="SEND":
					self.__runMode = CMPL_REMOTE_SEND

				elif key=="KNOCK":
					self.__runMode = CMPL_REMOTE_KNOCK

				elif key=="RETRIEVE":
					self.__runMode = CMPL_REMOTE_RETRIEVE

				elif key=="CANCEL":
					self.__runMode = CMPL_REMOTE_CANCEL

				elif key=="MAXTRIES":
					self.__maxTries = int(val[1:-1])

				elif key=="MAXTIME":
					self.__maxTime  = int(val[1:-1])

				elif key=="CMSG":
					if not val:
						self.__messageFile=self.__modelName+".cmsg"
					else:	
						self.__messageFile=val[1:-1]

				elif key=="SOLUTION":
					if not val:
						self.__solFile=self.__modelName+".csol"
					else:	
						self.__solFile=val[1:-1]
			
				elif key=="SOLUTIONASCII":
					if not val:
						self.__solAsciiFile=self.__modelName+".sol"
					else:	
						self.__solAsciiFile=val[1:-1]
				
				elif key=="SOLUTIONCSV":
					if not val:
						self.__solCsvFile=self.__modelName+".csv"
					else:	
						self.__solCsvFile=val[1:-1]

				elif key in ("M","FM","P","MATRIX"):
					self.__isFileOut=True
				
				elif key=="SILENT":
					self.__isSilent=True
				
				elif key=="SOLVER":
					self.__solver=val[1:-1]

			if nrOfXlsDataFiles>1:
				raise CmplException("Only one CmplXlsData file per Cmpl model is allowed")
		
		except:
			raise CmplException("Something went wrong while parsing Cmpl arguments: "+str(sys.exc_info()[1]))
	#******** parseOptFile **********************************************



#*************** end CmplArgs *******************************


		
        
        
        

        
