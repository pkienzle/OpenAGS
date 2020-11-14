# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 09:14:05 2020

@author: chris
"""
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from util import SpectrumParser, binary_search_find_nearest
from ttkwidgets.autocomplete import AutocompleteCombobox
from ElementalAnalysis import ElementalAnalysisFrame

class PGAAAnalysisApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        """Configure the GUI and other important features (load peak locations)"""
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("PGAA Data Analysis App")
        
        sens_file = open("AllSensitivity.csv")
        self.all_peaks_sens = [line.strip(" ").split(",") for line in sens_file.read().split("\n")][:-1]
        sens_file.close()
        
        menuBar = tk.Menu(self, tearoff=0)
        
        fileMenu = tk.Menu(menuBar, tearoff=0)
        fileMenu.add_command(label="Add File(s)", command = lambda:self.add_files(tk.filedialog.askopenfilenames(initialdir = ".",title = "Select files",filetypes = [("Spectrum files","*.spe")])))
        fileMenu.add_command(label="Remove File(s)", command = self.remove_file_GUI)
        menuBar.add_cascade(label="File",menu=fileMenu)
        
        editMenu = tk.Menu(menuBar, tearoff=0)
        editMenu.add_command(label="ROIs", command = self.edit_ROIs_GUI)
        menuBar.add_cascade(label="Edit",menu=editMenu)
        
        viewMenu = tk.Menu(menuBar, tearoff=0)
        viewMenu.add_command(label="Side-by-Side", command = self.side_to_side_GUI)
        viewMenu.add_command(label="Zoom to ROI", command = self.ROIZoomGUI)
        menuBar.add_cascade(label="View",menu=viewMenu)
        
        analyzeMenu = tk.Menu(menuBar, tearoff=0)
        analyzeMenu.add_command(label="Elemental Analysis", command = self.Elemental_Analysis_GUI)
        analyzeMenu.add_command(label="Decomposition Analysis", command = lambda:0)
        menuBar.add_cascade(label="Analyze",menu=analyzeMenu)
        
        self.config(menu=menuBar)
        
        graphInfo = tk.Frame(self)
        
        tk.Label(graphInfo, text="Current File:").grid(row=0,column=0)
        self.selectedFile = tk.StringVar()
        self.fileSelector = ttk.OptionMenu(graphInfo, self.selectedFile, "No Files to Display", command=self.change_file)
        self.fileSelector.grid(row=0,column=1, padx=(0,75))
        
        tk.Label(graphInfo, text="Livetime:").grid(row=0,column=2)
        self.currentLivetime = tk.Label(graphInfo, text="    N/A    ", borderwidth=2, relief="sunken")
        self.currentLivetime.grid(row=0,column=3, padx=(0,20))
        tk.Label(graphInfo, text="Realtime:").grid(row=0,column=4)
        self.currentRealtime = tk.Label(graphInfo, text="    N/A    ", borderwidth=2, relief="sunken")
        self.currentRealtime.grid(row=0,column=5)
        graphInfo.grid(row=0,column=1, pady=(10,0))
        
        f = Figure(figsize=(7,3), dpi=100)
        self.plotAxes = f.add_subplot(111)
        f.subplots_adjust(bottom=0.15)
        self.plotAxes.set_xlabel("Energy (kEv)")
        self.plotAxes.set_ylabel("Counts Per Second")
        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1,column=0,columnspan=6, rowspan=6)
        toolbarFrame = tk.Frame(self)
        toolbarFrame.grid(row=8,column=0,columnspan=6, sticky="w")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        toolbar.children['!button6'].pack_forget()
        toolbar._Spacer()
        self.scaleChangeButton = tk.Button(toolbar, text="LOG", command=self.toggle_y_scale)
        self.scaleChangeButton.pack(side="left")
        
        win = tk.Toplevel()
        win.wm_title("Edit ROIs")
        ttk.Label(win, text="Add/Remove Elements of Interest:").grid(row=0,column=0,columnspan=2)
        elementsList = ['Actinium', 'Aluminum', 'Americium', 'Antimony', 'Argon', 'Arsenic', 'Astatine', 'Barium', 'Berkelium', 'Beryllium', 'Bismuth', 'Bohrium', 'Boron', 'Bromine', 'Cadmium', 'Calcium', 'Californium', 'Carbon', 'Cerium', 'Cesium', 'Chlorine', 'Chromium', 'Cobalt', 'Copper', 'Curium', 'Darmstadtium', 'Dubnium', 'Dysprosium', 'Einsteinium', 'Erbium', 'Europium', 'Fermium', 'Fluorine', 'Francium', 'Gadolinium', 'Gallium', 'Germanium', 'Gold', 'Hafnium', 'Hassium', 'Helium', 'Holmium', 'Hydrogen', 'Indium', 'Iodine', 'Iridium', 'Iron', 'Krypton', 'Lanthanum', 'Lawrencium', 'Lead', 'Lithium', 'Lutetium', 'Magnesium', 'Manganese', 'Meitnerium', 'Mendelevium', 'Mercury', 'Molybdenum', 'Neodymium', 'Neon', 'Neptunium', 'Nickel', 'Niobium', 'Nitrogen', 'Nobelium', 'Oganesson', 'Osmium', 'Oxygen', 'Palladium', 'Phosphorus', 'Platinum', 'Plutonium', 'Polonium', 'Potassium', 'Praseodymium', 'Promethium', 'Protactinium', 'Radium', 'Radon', 'Rhenium', 'Rhodium', 'Roentgenium', 'Rubidium', 'Ruthenium', 'Rutherfordium', 'Samarium', 'Scandium', 'Seaborgium', 'Selenium', 'Silicon', 'Silver', 'Sodium', 'Strontium', 'Sulfur', 'Tantalum', 'Technetium', 'Tellurium', 'Terbium', 'Thallium', 'Thorium', 'Thulium', 'Tin', 'Titanium', 'Tungsten', 'Ununbium', 'Ununhexium', 'Ununpentium', 'Ununquadium', 'Ununseptium', 'Ununtrium', 'Uranium', 'Vanadium', 'Xenon', 'Ytterbium', 'Yttrium', 'Zinc', 'Zirconium']
        self.comboValue = tk.StringVar()
        combo = AutocompleteCombobox(win, elementsList, textvariable=self.comboValue)
        combo.grid(row=1,column=0)
        ttk.Button(win, text="Add", command=lambda: self.add_element(win, self.elementIndex, self.comboValue.get())).grid(row=1, column=1)
        self.eleLabelList = []
        self.removeBtnList = []
        self.elementIndex = 2
        ttk.Button(win, text="Submit", command=self.edit_ROIs).grid(row=1000,column=0, columnspan=2)
        self.ROIEditWindow = win
        self.ROIEditWindow.withdraw()
        self.ROIEditWindow.protocol("WM_DELETE_WINDOW", self.ROIEditWindow.withdraw)
        
        self.files = []
        self.fileInfo = []
        self.elements = []
        self.polyFills = []
        self.fitIndices = []
        self.fitRanges = []
        self.graphEnergies = []
        self.graphCPS = []
        self.selectionList = []
        
    def toggle_y_scale(self):
        """Change scale between linear and log"""
        if self.scaleChangeButton.cget("text") == "LOG":
            self.plotAxes.set_yscale("log")
            self.scaleChangeButton.configure(text="LIN")
        else:
            self.plotAxes.set_yscale("linear")
            self.scaleChangeButton.configure(text="LOG")
        self.canvas.draw()
    def add_files(self, files: list):
        """Add files to the graph pane"""
        #TODO: Check for duplicates
        updateGraph = (len(self.files) == 0)
        for f in files:
            if "\\" in f:
                trimName = "\\".join(f.split("\\")[-2:])
            else:
                trimName = "/".join(f.split("/")[-2:])
            if trimName not in self.files:
                self.files.append(trimName)
                s = SpectrumParser(f)
                self.fileInfo.append(s.getValues())
        self.fileSelector.set_menu(self.files[0], *self.files)
        if updateGraph:
            self.plotAxes.cla()
            self.plotAxes.plot(self.fileInfo[0][2], self.fileInfo[0][3])
            self.canvas.draw()
            self.currentLivetime.configure(text=str(self.fileInfo[0][0]))
            self.currentRealtime.configure(text=str(self.fileInfo[0][1]))
            self.graphEnergies = self.fileInfo[0][2]
            self.graphCPS = self.fileInfo[0][3]
    def change_file(self, newName: str):
        """Update the graph when we change which file we're looking at"""
        newInd = self.files.index(self.selectedFile.get())
        self.plotAxes.cla()
        
        self.plotAxes.set_xlabel("Energy (kEv)")
        self.plotAxes.set_ylabel("Counts Per Second")
        
        if self.scaleChangeButton.cget("text") == "LOG":
            self.plotAxes.set_yscale("linear")
        else:
            self.plotAxes.set_yscale("log")
            
            
        self.graphEnergies = self.fileInfo[newInd][2]
        self.graphCPS = self.fileInfo[newInd][3]
        self.plotAxes.plot(self.graphEnergies, self.graphCPS)
        self.currentLivetime.configure(text=str(self.fileInfo[newInd][0]))
        self.currentRealtime.configure(text=str(self.fileInfo[newInd][1]))
        fitIndices = self.fitIndices
        for i in self.polyFills:
            i.remove()
        self.polyFills = []
        for i in range(0, len(fitIndices), 2):
            self.polyFills.append(self.plotAxes.fill_between(self.graphEnergies[fitIndices[i]:fitIndices[i+1]],self.graphCPS[fitIndices[i]:fitIndices[i+1]]))
        self.canvas.draw()
    def remove_files(self, win, checkboxValues: list):
        """Remove files from the graph pane and program"""
        win.destroy()
        updateGraph = False
        toRemove = []
        for i in range(len(self.files)):
            if checkboxValues[i].get():
                toRemove.append(self.files[i])
        for f in toRemove:
            ind = self.files.index(f)
            del self.files[ind]
            del self.fileInfo[ind]
        if len(self.files)==0:
            self.fileSelector.set_menu("No Files to Display")
            self.plotAxes.cla()
            self.canvas.draw()
            self.currentLivetime.configure(text="    N/A    ")
            self.currentRealtime.configure(text="    N/A    ")
        else:
            self.fileSelector.set_menu(self.files[0], *self.files)
            self.plotAxes.cla()
            self.plotAxes.plot(self.fileInfo[0][2], self.fileInfo[0][3])
            self.canvas.draw()
            self.currentLivetime.configure(text=str(self.fileInfo[0][0]))
            self.currentRealtime.configure(text=str(self.fileInfo[0][1]))
    def remove_file_GUI(self):
        """A small GUI wrapper around the remove_files function"""
        win = tk.Toplevel()
        win.wm_title("Remove Files")
        ttk.Label(win, text="Select Files to Remove:").grid(row=0,column=0, columnspan=2)
        selectorList = []
        i=1
        for f in self.files:
            temp = tk.IntVar()
            ttk.Checkbutton(win, text=f, variable=temp).grid(row=i, column=0, columnspan=2)
            selectorList.append(temp)
            i += 1
        ttk.Button(win,text="Remove", command=lambda:self.remove_files(win, selectorList)).grid(row=i,column=0)
        ttk.Button(win,text="Cancel", command=win.destroy).grid(row=i,column=1)
    def edit_ROIs_GUI(self):
        """Open the ROI selection window"""
        self.ROIEditWindow.deiconify()
    def get_fitting_ranges(self,elementSymbols):
        """Given a list of elements of interest, develops regions of interest around them (these are then modified by the """
        peaksOfInterest = []
        for peak in self.all_peaks_sens:
            for sym in elementSymbols:
                if peak[0].startswith(sym):
                    peaksOfInterest.append(peak)
        peakFittingAreas = []
        for region in peaksOfInterest:
            radius = 15
            peakFittingAreas += [float(region[1]) - radius, float(region[1]) + radius]
        i = 1
        while i < len(peakFittingAreas)-2:
            if peakFittingAreas[i] > peakFittingAreas[i+1]:
                del peakFittingAreas[i]
                del peakFittingAreas[i]
            else:
                i+=2 
        return peakFittingAreas
    def edit_ROIs(self):
        """Edit ROIs for the program when submitted from ROI edit window"""
        self.ROIEditWindow.withdraw()
        elementMap = {'Hydrogen': 'H', 'Helium': 'He', 'Lithium': 'Li', 'Beryllium': 'Be', 'Boron': 'B', 'Carbon': 'C', 'Nitrogen': 'N', 'Oxygen': 'O', 'Fluorine': 'F', 'Neon': 'Ne', 'Sodium': 'Na', 'Magnesium': 'Mg', 'Aluminum': 'Al', 'Silicon': 'Si', 'Phosphorus': 'P', 'Sulfur': 'S', 'Chlorine': 'Cl', 'Argon': 'Ar', 'Potassium': 'K', 'Calcium': 'Ca', 'Scandium': 'Sc', 'Titanium': 'Ti', 'Vanadium': 'V', 'Chromium': 'Cr', 'Manganese': 'Mn', 'Iron': 'Fe', 'Cobalt': 'Co', 'Nickel': 'Ni', 'Copper': 'Cu', 'Zinc': 'Zn', 'Gallium': 'Ga', 'Germanium': 'Ge', 'Arsenic': 'As', 'Selenium': 'Se', 'Bromine': 'Br', 'Krypton': 'Kr', 'Rubidium': 'Rb', 'Strontium': 'Sr', 'Yttrium': 'Y', 'Zirconium': 'Zr', 'Niobium': 'Nb', 'Molybdenum': 'Mo', 'Technetium': 'Tc', 'Ruthenium': 'Ru', 'Rhodium': 'Rh', 'Palladium': 'Pd', 'Silver': 'Ag', 'Cadmium': 'Cd', 'Indium': 'In', 'Tin': 'Sn', 'Antimony': 'Sb', 'Tellurium': 'Te', 'Iodine': 'I', 'Xenon': 'Xe', 'Caesium': 'Cs', 'Barium': 'Ba', 'Lanthanum': 'La', 'Cerium': 'Ce', 'Praseodymium': 'Pr', 'Neodymium': 'Nd', 'Promethium': 'Pm', 'Samarium': 'Sm', 'Europium': 'Eu', 'Gadolinium': 'Gd', 'Terbium': 'Tb', 'Dysprosium': 'Dy', 'Holmium': 'Ho', 'Erbium': 'Er', 'Thulium': 'Tm', 'Ytterbium': 'Yb', 'Lutetium': 'Lu', 'Hafnium': 'Hf', 'Tantalum': 'Ta', 'Tungsten': 'W', 'Rhenium': 'Re', 'Osmium': 'Os', 'Iridium': 'Ir', 'Platinum': 'Pt', 'Gold': 'Au', 'Mercury': 'Hg', 'Thallium': 'Tl', 'Lead': 'Pb', 'Bismuth': 'Bi', 'Polonium': 'Po', 'Astatine': 'At', 'Radon': 'Rn', 'Francium': 'Fr', 'Radium': 'Ra', 'Actinium': 'Ac', 'Thorium': 'Th', 'Protactinium': 'Pa', 'Uranium': 'U', 'Neptunium': 'Np', 'Plutonium': 'Pu', 'Americium': 'Am', 'Curium': 'Cm', 'Berkelium': 'Bk', 'Californium': 'Cf', 'Einsteinium': 'Es', 'Fermium': 'Fm', 'Mendelevium': 'Md', 'Nobelium': 'No', 'Lawrencium': 'Lr', 'Rutherfordium': 'Rf', 'Dubnium': 'Db', 'Seaborgium': 'Sg', 'Bohrium': 'Bh', 'Hassium': 'Hs', 'Meitnerium': 'Mt', 'Darmstadtium': 'Ds', 'Roentgenium': 'Rg', 'Copernicium': 'Cn', 'Ununtrium': 'Uut', 'Flerovium': 'Fl', 'Ununpentium': 'Uup', 'Livermorium': 'Lv', 'Ununseptium': 'Uus', 'Ununoctium': 'Uuo'}
        self.elementSymbols = [elementMap[e] for e in self.elements]
        fitRanges = self.get_fitting_ranges(self.elementSymbols)
        self.fitRanges = fitRanges
        if len(self.graphEnergies) > 0:
            l = lambda x:binary_search_find_nearest(self.graphEnergies, x)
            fitIndices = list(map(l, fitRanges))
            self.fitIndices = fitIndices
            for i in self.polyFills:
                i.remove()
            self.polyFills = []
            for i in range(0, len(fitIndices), 2):
                self.polyFills.append(self.plotAxes.fill_between(self.graphEnergies[fitIndices[i]:fitIndices[i+1]],self.graphCPS[fitIndices[i]:fitIndices[i+1]]))
            self.canvas.draw()
    def add_element(self, win, i, ele):
        """Add an element to the ROI select GUI"""
        elementsList = ['Actinium', 'Aluminum', 'Americium', 'Antimony', 'Argon', 'Arsenic', 'Astatine', 'Barium', 'Berkelium', 'Beryllium', 'Bismuth', 'Bohrium', 'Boron', 'Bromine', 'Cadmium', 'Calcium', 'Californium', 'Carbon', 'Cerium', 'Cesium', 'Chlorine', 'Chromium', 'Cobalt', 'Copper', 'Curium', 'Darmstadtium', 'Dubnium', 'Dysprosium', 'Einsteinium', 'Erbium', 'Europium', 'Fermium', 'Fluorine', 'Francium', 'Gadolinium', 'Gallium', 'Germanium', 'Gold', 'Hafnium', 'Hassium', 'Helium', 'Holmium', 'Hydrogen', 'Indium', 'Iodine', 'Iridium', 'Iron', 'Krypton', 'Lanthanum', 'Lawrencium', 'Lead', 'Lithium', 'Lutetium', 'Magnesium', 'Manganese', 'Meitnerium', 'Mendelevium', 'Mercury', 'Molybdenum', 'Neodymium', 'Neon', 'Neptunium', 'Nickel', 'Niobium', 'Nitrogen', 'Nobelium', 'Oganesson', 'Osmium', 'Oxygen', 'Palladium', 'Phosphorus', 'Platinum', 'Plutonium', 'Polonium', 'Potassium', 'Praseodymium', 'Promethium', 'Protactinium', 'Radium', 'Radon', 'Rhenium', 'Rhodium', 'Roentgenium', 'Rubidium', 'Ruthenium', 'Rutherfordium', 'Samarium', 'Scandium', 'Seaborgium', 'Selenium', 'Silicon', 'Silver', 'Sodium', 'Strontium', 'Sulfur', 'Tantalum', 'Technetium', 'Tellurium', 'Terbium', 'Thallium', 'Thorium', 'Thulium', 'Tin', 'Titanium', 'Tungsten', 'Ununbium', 'Ununhexium', 'Ununpentium', 'Ununquadium', 'Ununseptium', 'Ununtrium', 'Uranium', 'Vanadium', 'Xenon', 'Ytterbium', 'Yttrium', 'Zinc', 'Zirconium']
        
        if ele in self.elements or ele not in elementsList:
            return None
        else:
            self.elements.append(ele)
            tmpLbl = ttk.Label(win, text=ele)
            tmpLbl.grid(row=i,column=0)
            self.eleLabelList.append(tmpLbl)
            
            tmpBtn = ttk.Button(win, text="Remove", command = lambda x=i:self.remove_element(x))
            tmpBtn.grid(row=i, column=1)
            self.removeBtnList.append(tmpBtn)
            self.comboValue.set('')
            self.elementIndex += 1
    def remove_element(self, i):
        """Remove an element from the ROI select GUI"""
        self.removeBtnList[-1].destroy()
        self.removeBtnList = self.removeBtnList[:-1]
        del self.elements[i-2]
        for j in range(i-2, len(self.elements)):
            self.eleLabelList[j].configure(text=self.eleLabelList[j+1].cget("text"))
        self.eleLabelList[-1].destroy()
        self.eleLabelList = self.eleLabelList[:-1]
    def ROIZoomGUI(self):
        """Setup UI for "Zoom to ROI" Functionality"""
        if len(self.fitIndices) == 0:
            return None
        win = tk.Toplevel()
        win.wm_title("Select ROI to Zoom to")
        val = tk.IntVar()
        val.set(1)
        ttk.Label(win,text="Select ROI to Zoom into").grid(row=0,column=0, columnspan=2)
        i=1
        listToSelect = []
        
        for j in range(0, len(self.fitIndices), 2):
            left = self.fitRanges[j]
            right = self.fitRanges[j+1]
            listToSelect.append([left, right, max(self.graphCPS[self.fitIndices[j]:self.fitIndices[j+1]])])
            ttk.Radiobutton(win, text="ROI #"+str(i)+": "+str(left)+"-"+str(right), variable=val, value=i).grid(row=i,column=0,columnspan=2)
            i += 1
            
        ttk.Button(win, text="Zoom", command=lambda:self.zoom_to_roi(win,*listToSelect[val.get()-1])).grid(row=i,column=0)
        ttk.Button(win, text="Cancel", command=win.destroy).grid(row=i,column=1)
    def zoom_to_roi(self, win, left, right, m):
        """Actually Zoom to the ROI selected"""
        win.destroy()
        self.plotAxes.set_xlim(left, right)
        self.plotAxes.set_ylim(0, m*1.1)
        self.canvas.draw()
    def side_to_side_GUI(self):
        """Side-by-side view GUI"""
        win = tk.Toplevel()
        win.wm_title("Side-By-Side View")
        f = tk.Frame(win)
        regionSelect = tk.StringVar()
        f1Select = tk.StringVar()
        f2Select = tk.StringVar()
        stackGraphs = tk.IntVar()
        compRegionsList = ["Current Bounds", "All Data"] + ["ROI: " + str(self.fitRanges[j]) + "-" + str(self.fitRanges[j+1]) for j in range(0, len(self.fitRanges), 2)]
        ttk.Label(f,text="Select Area to Compare").grid(row=0,column=0)
        ttk.OptionMenu(f,regionSelect, compRegionsList[0], *compRegionsList).grid(row=1,column=0)
        ttk.Label(f,text="Select First File").grid(row=2,column=0)
        ttk.OptionMenu(f, f1Select, self.files[0], *self.files).grid(row=3,column=0)
        ttk.Label(f,text="Select Second File").grid(row=4,column=0)
        ttk.OptionMenu(f, f2Select, self.files[1], *self.files).grid(row=5,column=0)
        ttk.Checkbutton(f, text="Overlay Graphs", variable=stackGraphs).grid(row=6,column=0)
        xlim = self.plotAxes.get_xlim()
        ttk.Button(f, text="Show", command=lambda:self.show_side_to_side(f1Select.get(), f2Select.get(), regionSelect.get(), xlim, stackGraphs.get(), win, f)).grid(row=7, column=0)
        f.grid(row=0,column=0)
    def show_side_to_side(self, fname1, fname2, area, xlim, stacked, win, f):
        """Side-by-side Graph Creator"""
        if fname1 == "" or fname2 == "" or fname1 == fname2:
            return None #TODO add proper error messages
        fig = Figure(figsize=(10,5), dpi=100)
        f1Ind = self.files.index(fname1)
        f1Ener = self.fileInfo[f1Ind][2]
        f1CPS = self.fileInfo[f1Ind][3]
        
        f2Ind = self.files.index(fname2)
        f2Ener = self.fileInfo[f2Ind][2]
        f2CPS = self.fileInfo[f2Ind][3]
        
        if area == "Current Bounds":
            left = xlim[0]
            right = xlim[1]
            f1Left = max(binary_search_find_nearest(f1Ener, left), 5)
            f1Right = min(binary_search_find_nearest(f1Ener, right), len(f1Ener)-5)
            f2Left = max(binary_search_find_nearest(f2Ener, left), 5)
            f2Right = min(binary_search_find_nearest(f2Ener, right), len(f1Ener)-5)
            if stacked:
                a = fig.add_subplot(111)
                a.plot(f1Ener[f1Left-5:f1Right+5],f1CPS[f1Left-5:f1Right+5], label=fname1)
                a.plot(f2Ener[f2Left-5:f2Right+5],f2CPS[f2Left-5:f2Right+5], label=fname2)
                a.set_xlim(*xlim)
            else:
                a = fig.add_subplot(121)
                a.plot(f1Ener[f1Left-5:f1Right+5],f1CPS[f1Left-5:f1Right+5])
                b = fig.add_subplot(122)
                b.plot(f2Ener[f2Left-5:f2Right+5],f2CPS[f2Left-5:f2Right+5])
                a.set_xlim(*xlim)
                b.set_xlim(*xlim)
        elif area == "All Data":
            if stacked:
                a = fig.add_subplot(111)
                a.plot(f1Ener, f1CPS)
                a.plot(f2Ener, f2CPS)
            else:
                a = fig.add_subplot(121)
                a.plot(f1Ener, f1CPS, label=fname1)
                b = fig.add_subplot(122)
                b.plot(f2Ener, f2CPS, label=fname2)
        else:
            bounds = area.split(": ")[1].split("-")
            left = float(bounds[0])
            right = float(bounds[1])
            f1Left = max(binary_search_find_nearest(f1Ener, left), 5)
            f1Right = min(binary_search_find_nearest(f1Ener, right), len(f1Ener)-5)
            f2Left = max(binary_search_find_nearest(f2Ener, left), 5)
            f2Right = min(binary_search_find_nearest(f2Ener, right), len(f1Ener)-5)
            if stacked:
                a = fig.add_subplot(111)
                a.plot(f1Ener[f1Left-5:f1Right+5],f1CPS[f1Left-5:f1Right+5], label=fname1)
                a.plot(f2Ener[f2Left-5:f2Right+5],f2CPS[f2Left-5:f2Right+5], label=fname2)
                a.set_xlim(left, right)
            else:
                a = fig.add_subplot(121)
                a.plot(f1Ener[f1Left-5:f1Right+5],f1CPS[f1Left-5:f1Right+5])
                b = fig.add_subplot(122)
                b.plot(f2Ener[f2Left-5:f2Right+5],f2CPS[f2Left-5:f2Right+5])
                a.set_xlim(left, right)
                b.set_xlim(left, right)
        if stacked:
            fig.set_size_inches(5,5)
            a.set_title("Side-by-Side", size=14)
            a.legend(fontsize=8)
            a.set_xlabel("Energy (kEv)")
            a.set_ylabel("Counts per Second")
        else:
            a.set_title(fname1, fontsize=10)
            a.set_xlabel("Energy (kEv)")
            a.set_ylabel("Counts per Second")
            
            b.set_title(fname2, fontsize = 10)
            b.set_xlabel("Energy (kEv)")
            b.set_ylabel("Counts per Second")
        f.destroy()
        c = FigureCanvasTkAgg(fig, win)
        c.draw()
        c.get_tk_widget().grid(row=0,column=0,columnspan=6, rowspan=6)
    def Elemental_Analysis_GUI(self):
        """Configuration screen for elemental analysis GUI"""
        win = tk.Toplevel()
        configFrame = tk.Frame(win)
        ttk.Label(configFrame, text="Select Files and Confirm ROIs").grid(row=0,column=0,columnspan=2)
        i=1
        self.selectionList = []
        for f in self.files:
            tmp = tk.IntVar()
            tmp.set(0)
            ttk.Checkbutton(configFrame, text=f, variable=tmp, command = self.update_primary_file_select).grid(row=i,column=0,columnspan=2)
            self.selectionList.append(tmp)
            i += 1
        ttk.Label(configFrame, text="Select Primary File: ").grid(row=i,column=0)
        self.primaryFile = tk.StringVar()
        self.primSelMenu = ttk.OptionMenu(configFrame, self.primaryFile, "            ")
        self.primSelMenu.grid(row=i, column=1)
        i += 1
        ttk.Label(configFrame, text="View/Edit ROIs: ").grid(row=i,column=0)
        ttk.Button(configFrame, text="Edit", command=self.edit_ROIs_GUI).grid(row=i,column=1, sticky="w")
        i += 1
        ttk.Button(configFrame, text="Analyze", command=lambda:self.run_analysis(win, configFrame)).grid(row=i, column=0,columnspan=2)
        configFrame.grid(row=0,column=0)
        
    def update_primary_file_select(self):
        """Update which file is listed as primary in the Elemental Analysis Configuration window"""
        tmpLst = []
        for i in range(len(self.files)):
            if self.selectionList[i].get():
                tmpLst.append(self.files[i])
        if self.primaryFile.get() in tmpLst:
            tmpDef = self.primaryFile.get()
        else:
            tmpDef = "            "
        self.primSelMenu.set_menu(tmpDef, *tmpLst)
        
    def run_analysis(self, win, otherFrame):
        """Actually run the elemental analysis"""
        if len(self.elementSymbols) == 0:
            tk.messagebox.showinfo("Please add ROIs", "You have not added any elements of interest. Use the edit button to add some.")
            return None
        fnames = []
        fInfo = []
        for i in range(len(self.files)):
            if self.selectionList[i].get():
                fnames.append(self.files[i])
                fInfo.append(self.fileInfo[i][2:])
        if len(fnames) == 0:
            tk.messagebox.showinfo("Please Add Files", "You have not added any files for analysis. Close the analysis popup and add some through the File -> Add File(s) menu.")
            return None
        if self.primaryFile.get() == "            ":
            tk.messagebox.showinfo("Please Select A Primary File", "You have not selected a primary file. Please do so from the dropdown in this popup.")
            return None
        otherFrame.destroy()
        e = ElementalAnalysisFrame(win)
        e.grid(row=0,column=0)
        tmpRanges = [[self.fitRanges[i],self.fitRanges[i+1]] for i in range(0, len(self.fitRanges),2)]
        e.add_all_data(fnames, fInfo, tmpRanges, self.elementSymbols, self.all_peaks_sens)
        e.run_analysis()
    def decomposition_analysis_GUI(self):
        """Unfinished"""
        win = tk.Toplevel()
        container = tk.Frame(win) #TODO: Replace with DecompositionAnalysisFrame
        container.grid(row=0,column=0)
app = PGAAAnalysisApp()
app.mainloop()