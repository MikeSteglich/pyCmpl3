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
import xml.dom.minidom as dom
import random
import io
from xml.sax.saxutils import unescape, escape

from .CmplException import *

#*************** CmplInstance ***********************************
class CmplInstance(object):

	#*********** constructor **********
	def __init__(self):
		
		self.__cmplFile = ""
		self.__cmplAlias = ""
		self.__cmplContent=""
		self.__optionsList = []
		self.__dataString = ""
		self.__cmplFileList = {}
		self.__instStr = io.StringIO()
		self.__jobId = ""
		self.__cmplName = ""
		self.__args=None
		self.__withPreComp=False
		
	#*********** end constructor ******
	
	#*********** destructor ***********
	def __del__(self):
		self.__instStr.close()
	#*********** end destructor *******
		
	# getter **************************	
	@property
	def jobId(self):
		return self.__jobId
		
	@property
	def options(self):
		return self.__optionsList

	@property
	def withPreComp(self):
		return self.__withPreComp
	# end getter ***********************	
	

	def __readAsciiFile(self, fName):
		fContent=""
		try:
			f = open(fName, "r")
			fContent = f.read()
			f.close()		
			return fContent
		except IOError as e:
			raise CmplException("IO error for file <"+fName+"> : "+str(e))

	def __isFullPath(self, fName):
		fullPath=False
		if fName.startswith(os.sep) or fName[1:2] == ":":
			fullPath = True 
		return fullPath

	def __getExternalFiles(self):

		isFullPath=self.__isFullPath(self.__cmplFile)
				
		self.__cmplAlias=os.path.splitext(os.path.basename(self.__cmplFile))[0] 

		fAlias=self.__cmplAlias+".optcmpl"
		self.__cmplFileList[fAlias]=self.__readAsciiFile(self.__args.optAlias+".optcmpl")
		self.__optionsList.append("-i-opt "+fAlias)

		fAlias=self.__cmplAlias+".precmpl"
		self.__cmplFileList[fAlias]=self.__readAsciiFile(self.__args.optAlias+".precmpl")
		self.__optionsList.append("-i-pre "+fAlias)

		fAlias=self.__cmplAlias+".extdata"
		self.__cmplFileList[fAlias]=self.__readAsciiFile(self.__args.optAlias+".extdata")
		self.__optionsList.append("-i-extern "+fAlias)

		if self.__args.xlsDataFile:
			fAlias=self.__cmplAlias+".cdat"

			if isFullPath and not self.__isFullPath(self.__args.xlsDataFile):
				self.__optionsList.append("-filealias "+os.path.dirname(self.__cmplFile)+os.sep+self.__args.xlsDataFile+"="+fAlias)
			else:
				self.__optionsList.append("-filealias "+self.__args.xlsDataFile+"="+fAlias)
			self.__cmplFileList[fAlias] = self.__dataString
					
		for fName in self.__args.externalFiles:
			fAlias=os.path.basename(fName)
			if fAlias[-1]==":":
				fAlias=fAlias[:-1]
				fName=fName[:-1]

			if fName!=fAlias: 
				if isFullPath and not self.__isFullPath(fName):
					self.__optionsList.append("-filealias "+os.path.dirname(self.__cmplFile)+os.sep+fName+"="+fAlias)
				else:
					self.__optionsList.append("-filealias "+fName+"="+fAlias)

			if fAlias==self.__cmplAlias+ ".cdat":
				if not self.__dataString:
					self.__cmplFileList[fAlias] = self.__readAsciiFile(fName)	
				else:
					self.__cmplFileList[fAlias] = self.__dataString
			else:
				self.__optionsList.append("-filealias "+fName+"="+fAlias)
				self.__cmplFileList[fAlias] = self.__readAsciiFile(fName)	

		if isFullPath:
			self.__optionsList.append("-basename "+self.__cmplAlias)
			
		
	#*********** cmplInstanceStr **********
	def cmplInstanceStr(self, cmplFileName, cmplArgs, optList, dataString, jobId):

		self.__args=cmplArgs
		self.__cmplFile = cmplFileName

		self.__optionsList = optList
		self.__jobId = jobId
		self.__dataString = dataString

		self.__getExternalFiles()
		
		try:
			self.__instStr.write("<?xml version = \"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n")
			self.__instStr.write("<CmplInstance version=\"2.0\">\n")
			self.__instStr.write("<general>\n")
			self.__instStr.write("<name>"+os.path.basename(self.__cmplFile)+"</name>\n")
			self.__instStr.write("<jobId>"+self.__jobId+"</jobId>\n")
			self.__instStr.write("<preComp>no</preComp>\n")
			self.__instStr.write("</general>\n")
			
			if len(self.__optionsList) > 0:
				self.__instStr.write("<options>\n")
				for opt in self.__optionsList:
					self.__instStr.write("<opt>"+opt+"</opt>\n")
				self.__instStr.write("</options>\n")
			
			self.__instStr.write("<problemFiles>\n")
			
			for d in self.__cmplFileList:
				self.__instStr.write("<file name=\""+ d + "\">\n")
				self.__instStr.write(escape(self.__cmplFileList[d]) )
				self.__instStr.write("\n")	
				self.__instStr.write("</file>\n")
			self.__instStr.write("</problemFiles>\n")	
			self.__instStr.write("</CmplInstance>\n")	

		except IOError as e:
			raise CmplException("IO error : "+str(e))
		
		return self.__instStr.getvalue()
		
	#*********** end cmplInstanceStr ******	

		
	#*********** writeCmplInstance **********
	def writeCmplInstance(self, folder, instStr):	
		if os.path.exists(folder) == False:
			raise CmplException("Path <"+self.__cmplServerPath+"> doesn't exist.")
			
		instDom = dom.parseString(instStr)

		if instDom.firstChild.nodeName!="CmplInstance":
			raise CmplException("Cant't read cmplInstance file - wrong file type!")
			
		for entry in instDom.firstChild.childNodes: 
				if entry.nodeName == "general":
					for entry1 in entry.childNodes:
						if entry1.nodeName == "name":
							self.__cmplName = unescape( entry1.firstChild.data.strip() , entities={ "&apos;":"'"} )
							continue
						if entry1.nodeName == "jobId":
							self.__jobId = entry1.firstChild.data.strip()
							continue
						if entry1.nodeName == "preComp":
							if entry1.firstChild.data.strip()=="no":
								self.__withPreComp=False
							elif entry1.firstChild.data.strip()=="yes":
								self.__withPreComp=True
							continue
							
				if entry.nodeName == "options":
					for entry1 in entry.childNodes: 
						if entry1.nodeName == "opt":
							self.__optionsList.append(entry1.firstChild.data.strip())
							
				if entry.nodeName == "problemFiles":
					for entry1 in entry.childNodes: 
						if entry1.nodeName == "file":
							tmpName = folder+self.__jobId+os.sep+entry1.getAttribute("name")
							tmpContent = unescape(entry1.firstChild.data.strip() , entities={ "&apos;":"'"})
							try:
								f = open(tmpName, 'w')
								f.write(tmpContent)		
								f.close()
							except IOError as e:
								raise CmplException("IO error for file " + tmpName + ": "+e)
	#*********** end writeCmplInstance *******

#*************** end CmplInstance  ******************************

		