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

from .CmplSolution import *
from .CmplException import *


#*************** CmplSolution  ***********************************
class CmplSolutionReport(object):

    #*********** constructor **********
    def __init__(self, solutions):
        self.__solutions = solutions
    #*********** end constructor ******
    

# *********** solutionReport **********
    def solutionReport(self, problemName, fileName=None):

        repStr = io.StringIO()
        
        if self.__solutions.nrOfSolutions > 0:
            repStr.write(
                "---------------------------------------------------------------------------------------------------------\n")
            repStr.write('%-20s %-s\n' % ("Problem", problemName))

            repStr.write('%-20s %-s\n' % ("Nr. of variables", str(self.__solutions.nrOfVariables)))
            repStr.write('%-20s %-s\n' % ("Nr. of constraints", str(self.__solutions.nrOfConstraints)))
            repStr.write('%-20s %-s\n' % ("Objective name", self.__solutions.objectiveName))
            if self.__solutions.nrOfSolutions > 1:
                repStr.write('%-20s %-s\n' % ("Nr. of solutions", str(self.__solutions.nrOfSolutions)))
            repStr.write('%-20s %-s\n' % ("Solver name", self.__solutions.solver))
            repStr.write('%-20s %-s\n' % ("Display variables", self.__solutions.varDisplayOptions))
            repStr.write('%-20s %-s\n' % ("Display constraints", self.__solutions.conDisplayOptions))
            repStr.write(
                '---------------------------------------------------------------------------------------------------------\n')
            for s in self.__solutions.solutions:
                repStr.write('\n')
                if self.__solutions.nrOfSolutions > 1:
                    repStr.write('%-20s %-s\n' % ("Solution nr.", str(s.idx + 1)))
                repStr.write('%-20s %-s\n' % ("Objective status", s.status))
                repStr.write(
                    '%-20s %-20s(%s!)\n' % ("Objective value", "%-20.2f" % s.value, self.__solutions.objectiveSense))
                repStr.write('\n')
                if len(s.variables) > 0:
                    repStr.write('%-20s\n' % "Variables")
                    repStr.write('%-20s%5s%20s%20s%20s%20s\n' % (
                    "Name", "Type", "Activity", "LowerBound", "UpperBound", "Marginal"))
                    repStr.write(
                        '---------------------------------------------------------------------------------------------------------\n')
                    for v in s.variables:
                        if v.type == "C":
                            repStr.write(
                                '%-20s%5s%20.2f%20.2f%20.2f' % (v.name, v.type, v.activity, v.lowerBound, v.upperBound))
                        else:
                            repStr.write(
                                '%-20s%5s%20g%20.2f%20.2f' % (v.name, v.type, v.activity, v.lowerBound, v.upperBound))
                        if self.__solutions.isIntegerProgram:
                            repStr.write('%20s\n' % "-")
                        else:
                            repStr.write('%20.2f\n' % v.marginal)
                    repStr.write(
                        '---------------------------------------------------------------------------------------------------------\n')
                if len(s.constraints) > 0:
                    repStr.write('\n')
                    repStr.write('%-20s\n' % "Constraints")
                    repStr.write('%-20s%5s%20s%20s%20s%20s\n' % (
                    "Name", "Type", "Activity", "LowerBound", "UpperBound", "Marginal"))
                    repStr.write(
                        '---------------------------------------------------------------------------------------------------------\n')
                    for c in s.constraints:
                        repStr.write(
                            '%-20s%5s%20.2f%20.2f%20.2f' % (c.name, c.type, c.activity, c.lowerBound, c.upperBound))
                        if self.__solutions.isIntegerProgram:
                            repStr.write('%20s\n' % "-")
                        else:
                            repStr.write('%20.2f\n' % c.marginal)
                    repStr.write(
                        '---------------------------------------------------------------------------------------------------------\n')

            if fileName != None:
                try:
                    f = open(fileName, 'w')
                    f.write(repStr.getvalue())
                    f.close()
                except IOError as e:
                    raise CmplException("IO error for file " + fileName + ": " + e.strerror)
            else:
                print((repStr.getvalue()))

            repStr.close()

        else:
            raise CmplException("No Solution found so far")

    # *********** end solutionReport ******


    # *********** saveSolutionCsv **********
    def saveSolutionCsv(self, problemName, solFileName ):

        if self.__solutions.nrOfSolutions > 0:

            try:
                f = open(solFileName, 'w')
                f.write("CMPL csv export\n")
                f.write("\n")
                f.write("%s;%s\n" % ("Problem", problemName))
                f.write("%s;%g\n" % ("Nr. of variables", self.__solutions.nrOfVariables))
                f.write("%s;%g\n" % ("Nr. of constraints", self.__solutions.nrOfConstraints))
                f.write("%s;%s\n" % ("Objective name", self.__solutions.objectiveName))
                if self.__solutions.nrOfSolutions > 1:
                    f.write("%s;%g\n" % ("Nr. of solutions", self.__solutions.nrOfSolutions))
                f.write("%s;%s\n" % ("Solver name", self.__solutions.solver))
                f.write("%s;%s\n" % ("Display variables", self.__solutions.varDisplayOptions))
                f.write("%s;%s\n" % ("Display constraints", self.__solutions.conDisplayOptions))

                for s in self.__solutions.solutions:

                    f.write("\n")
                    if self.__solutions.nrOfSolutions > 1:
                        f.write("%s;%g\n" % ("Solution nr", s.idx + 1))
                    f.write("%s;%s\n" % ("Objective status", s.status))
                    f.write("%s;%f;(%s!)\n" % ("Objective value", s.value, self.__solutions.objectiveSense))
                    if len(s.variables) > 0:
                        f.write("%s\n" % "Variables")
                        f.write("%s;%s;%s;%s;%s;%s\n" % (
                        "Name", "Type", "Activity", "LowerBound", "UpperBound", "Marginal"))
                        for v in s.variables:
                            if v.type == "C":
                                f.write("%s;%s;%f;%f;%f" % (v.name, v.type, v.activity, v.lowerBound, v.upperBound))
                            else:
                                f.write("%s;%s;%g;%f;%f" % (v.name, v.type, v.activity, v.lowerBound, v.upperBound))
                            if self.__solutions.isIntegerProgram:
                                f.write(";-\n")
                            else:
                                f.write(";%f\n" % v.marginal)
                    if len(s.constraints) > 0:
                        f.write("%s\n" % "Constraints")
                        f.write("%s;%s;%s;%s;%s;%s\n" % (
                        "Name", "Type", "Activity", "LowerBound", "UpperBound", "Marginal"))
                        for c in s.constraints:
                            f.write("%s;%s;%f;%f;%f" % (c.name, c.type, c.activity, c.lowerBound, c.upperBound))
                            if self.__solutions.isIntegerProgram:
                                f.write(";-\n")
                            else:
                                f.write(";%f\n" % c.marginal)

                f.close()
               
            except IOError as e:
                raise CmplException("IO error for file " + solFileName + ": " + e.strerror)

        else:
            raise CmplException("No Solution found so far")

    # *********** end saveSolutionCsv *****

    # *********** saveSolution ************
    def saveSolution(self, problemName, solFileName):
        if self.__solutions.nrOfSolutions > 0:

            pos1=self.__solutions.solFileContent.find('<instanceName>')+len('<instanceName>')
            pos2=self.__solutions.solFileContent.find('</instanceName>')
            solutionString = self.__solutions.solFileContent[:pos1] + problemName + self.__solutions.solFileContent[pos2:]

            try:
                f = open(solFileName, 'w')
                f.write(solutionString)
                f.close()
                self.__solutions.delSolFileContent()

            except IOError as e:
                raise CmplException("IO error for file " + solFileName + ": " + e.strerror)
            
        else:
            raise CmplException("No Solution found so far")

    # *********** end saveSolution ********
    
        
        
        
#*************** end CmplSolutionReport ********************************

