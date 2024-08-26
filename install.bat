@echo off

REM Save the current directory (where the batch file is located)
set SCRIPT_DIR=%~dp0

REM Navigate to the directory containing the batch file
cd /d "%SCRIPT_DIR%"

REM Create the virtual environment
echo "Creating the virtual environment"
python -m venv --copies .venv

REM Activate the virtual environment
echo "Activating the virtual environment"
call .venv\Scripts\activate.bat

REM Install required packages
echo "Installing required packages"
pip install --require-virtualenv -r requirements.txt