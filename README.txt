Welcome to the PGAA Data Analysis Program Dev Branch
This program will probably not work.

==========Changelog==========
v0.2.1
	"xylib-py" wheels are now available under a separate pip package, so they've been moved to requirements.txt
v0.1.1
	Added new requirement "xylib-py" for CNF file support, install using "python3 -m pip install xylib_py-1.6.0-cp37-cp37m-win_amd64.whl"
	Added "Show" page to see individual file results within the program.
	It is now possible to manually enter values into the range adjusters when reviewing peak fit.
	All ROIs are now entered/searched by post-activation isotope (i.e. "B-11", "H-2", etc.) rather than element name.
	ROIs in the "Zoom to ROI" list now show which isotope is being searched for in their particular region
	Added support for CNF files.
	Many small bugfixes and UI improvements.
v0.1.0 
	Initial Beta Release
=============================

Requirements may be installed with the command "python3 -m pip install -r requirements.txt".

You can run the program (from either a command prompt for normal python or an Anaconda prompt for Anaconda) using the command "python main.py" (again from within this folder).
