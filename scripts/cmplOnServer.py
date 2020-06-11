# ***********************************************************************
#  This code is part of pyCMPL
#
#  Copyright (C) 2013 - 2019
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


#!/usr/bin/python3

#Cmpl 1.12.0
#March 2018
#Stegger


import sys
import os
#import pickle
import tempfile
#import traceback

from pyCmpl import *


def usage():
	usage = """
cmplRemote <problem.cmpl> [option]*
Options:
	Synchronious mode:
	-url=<http://url:port>          Sets the url of a CmplServer and runs the problem on it and waits for the results

	Asynchronious mode: 
	-url=<http://url:port> -send    Sets the url of a CmplServer and sends the problem to it
	-knock                          Retrieves the status and the output of the problem running on a CmplServer
	-retrieve                       Retrieves the results of the problem
	-cancel                         Cancels a problem running on a CmplServer

	General options:
	-maxTries=<tries>               Defines the maximum number of failed accesses to a CmplServer
  	-maxTime=<time>                 Defines the maximum queuing time of failed accesses to a CmplServer
	
	Cmpl options:
	All options excluding <-m, -fm, -p> can be used as for the Cmpl binary
"""
	print(usage)


modName=""
cmplFile=""
cmplUrl=""
maxTries=0
maxQueuingTime=0
asyncMode=0

optionsList = {}
tmpOption=""

messageFile=""
matrixFile=""
solFile=""
solAsciiFile=""
solCsvFile=""

isError=False
isMessage=False

isOption=False

tmpPath = tempfile.gettempdir()+os.sep

idx=0

for argument in sys.argv[1:]:

	arg=argument.strip()

	if arg=="":
		continue

	if arg.startswith("-") :

		if isOption:
			#close optionString for the previous option
			pos = len(optionsList)
			if tmpOption!="":
				optionsList.update({pos:tmpOption})

		isOption=False
		isSolFile=False
		isSolAscii=False
		isSolCsv=False
		isMessage=False

		args=arg.split("=")
		key=args[0].upper()[1:]

		if len(args)==2:
			val=val=args[1]
		else:
			val=""

		if key=="H":  
			usage();

		elif key=="URL":
			cmplUrl = val

		elif key=="SEND":
			asyncMode = 1

		elif key=="KNOCK":
			asyncMode = 2

		elif key=="RETRIEVE":
			asyncMode = 3

		elif key=="CANCEL":
			asyncMode = 4

		elif key=="MAXTRIES":
			maxTries = int(val)

		elif key=="MAXTIME":
			maxQueuingTime = int(val)

		elif key=="CMSG":
			isMessage=True

		elif key=="SOLUTION":
			isSolFile=True
			solFile=modName+".csol"
			
		elif key=="SOLUTIONASCII":
			isSolAscii=True
			solAsciiFile=modName+".sol"
	
		elif key=="SOLUTIONCSV":
			isSolCsv=True
			solCsvFile=modName+".csv"

		elif key in ("M","FM","P"):
			print("Error: argument not allowed on CmplServer <"+key+">")
			usage()

		else:
			#new option
			tmpOption = args[0]
			isOption=True

	else:
		if idx==0:
			cmplFile = arg
			modName = os.path.splitext(cmplFile)[0]

		else:
			if isMessage:
				messageFile=arg
			elif isSolAscii:
				solAsciiFile=arg
			elif isSolCsv:
				solCsvFile=arg
			elif isSolFile:
				solFile=arg
			else:
				tmpOption += " " + arg
	
	idx+=1

if isOption and tmpOption!="" :
	pos = len(optionsList)
	optionsList.update({pos:tmpOption})	


try:

	if not os.path.isfile(cmplFile):
		raise CmplException("ERROR: Cmpl file does not exist <"+cmplFile+">" )

	if (asyncMode==0 or asyncMode==1) and cmplUrl=="":
		print ("ERROR: Url of the CmplServer not defined")
		usage()
		raise Exception()
		

	if asyncMode>1 and cmplUrl!="":
		print ("WARNING: The newly defined URL of the CmplServer was ignored and the original was used.\n")
	
	if asyncMode == 0:
		model = Cmpl(cmplFile)
		model.setOptionsList(optionsList)
		model.setOutput(True, "")
	
		if maxQueuingTime!=0:
			model.setMaxServerQueuingTime(maxQueuingTime)
		
		if maxTries!=0:
			model.setMaxServerTries(maxTries)
		
		model.connect(cmplUrl)
		#model.debug()
		model.solve()
		
		if model.cmplStatus==CMPL_WARNINGS:
			for m in model.cmplMessages:
				print(m.type, m.file, m.line, m.description)
	
		if model.solverStatus == SOLVER_OK:
			if not (solFile != "" or solCsvFile != "" or solAsciiFile != ""):
				model.solutionReport()
			if solFile != "":
				model.saveSolution(solFile)
			if solAsciiFile != "":
				model.saveSolutionAscii(solAsciiFile)
			if solCsvFile != "":
				model.saveSolutionCsv(solCsvFile)
				
	elif asyncMode == 1:
		model = Cmpl(cmplFile)
		model.setOptionsList(optionsList)
		model.setOutput(True, "")
		model.setAsyncMode(asyncMode)
	
		if maxQueuingTime!=0:
			model.setMaxServerQueuingTime(maxQueuingTime)
		
		if maxTries!=0:
			model.setMaxServerTries(maxTries)
		
		model.connect(cmplUrl)
		#model.debug()
		model.send()
		
		model.dump()
		
	elif asyncMode == 2:

		model = Cmpl(cmplFile)
		
		model.load()
		model.setAsyncMode(asyncMode)
		model.knock()
		model.dump()

			
	elif asyncMode == 3:
		model = Cmpl(cmplFile)
		
		model.load()
		model.setAsyncMode(asyncMode)
		model.retrieve()
			
		if model.cmplStatus==CMPL_WARNINGS:
			for m in model.cmplMessages:
				print(m.type, m.file, m.line, m.description)

		if model.solverStatus == SOLVER_OK:
			if not (solFile != "" or solCsvFile != "" or solAsciiFile != ""):
				model.solutionReport()
			if solFile != "":
				model.saveSolution(solFile)
			if solAsciiFile != "":
				model.saveSolutionAscii(solAsciiFile)
			if solCsvFile != "":
				model.saveSolutionCsv(solCsvFile)
			
	elif asyncMode == 4:
		model = Cmpl(cmplFile)
		
		model.load()
		model.setAsyncMode(asyncMode)
		model.cancel()

		print("Problem is canceled ...")
		
			
			
except CmplException as e:
	if e.msg.startswith("pyCmpl error: Model is still running, cannot retrieve the solution"):
		print(e.msg)
		if model.cmplStatus!=PROBLEM_FINISHED and model.cmplStatus!=PROBLEM_CANCELED:
			model.dump()

	elif not isMessage :
		print(e.msg)
		isError=True

	elif not e.msg.startswith("pyCmpl error: Cmpl finished with errors"):
		print(e.msg)
		isError=True
		
	
except IOError as e:
	print(str(sys.exc_info()[1]))
	isError=True
	
except: 
	isError=True
	print(str(sys.exc_info()[1]))
	#traceback.print_exc(file=sys.stdout)
	
try:
	if isMessage and (asyncMode==0 or asyncMode==3) and not isError:
		model.saveCmplMessageFile(messageFile)
	
except CmplException as e:
	print(e.msg)
except:
	print(str(sys.exc_info()[1]))
	#traceback.print_exc(file=sys.stdout)
