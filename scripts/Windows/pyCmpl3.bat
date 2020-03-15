@echo off

if exist "%CmplProgPath%bin\cmpl.exe" goto RUN

echo Please install Cmpl into folder : %CmplProgPath%\bin
pause
goto END
 
:RUN

set oldPath=%PATH%
set PATH=%CmplProgPath%;%CmplProgPath%pyCmpl\scripts\Windows\;%PATH%

rem set PythonBin="%CmplProgPath%"pypy\pypy.exe
set PythonBin="%CmplProgPath%Python27\python.exe"
set PythonBin="python3.exe"
	

set PYTHONPATH=%PYTHONPATH%;%CmplProgPath%pyCmpl\lib3;%CmplProgPath%cmplServer
set PYTHONSTARTUP=%CmplProgPath%pyCmpl\lib3\pyCmplShell.py
set CMPLBINARY=%CmplProgPath%bin\cmpl.exe

%PythonBin% "%1" "%2" "%3" "%4" "%5" "%6" "%7" "%8" "%9" "%10"


set PATH=%oldPath%

@echo on