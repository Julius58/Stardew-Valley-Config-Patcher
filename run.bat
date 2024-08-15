@echo off

REM Save the current directory (where the batch file is located)
set SCRIPT_DIR=%~dp0

REM Navigate to the directory containing the batch file
cd /d "%SCRIPT_DIR%"

REM Activate the virtual environment
call .venv\Scripts\activate

REM Run the Python script
python config_patcher.py %*

REM Optional: Deactivate the virtual environment (usually done automatically)
REM deactivate