# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 12:47:15 2020

@author: chris
"""
from tkinter import Tk, Frame, DoubleVar, StringVar, IntVar, Checkbutton, Spinbox, messagebox, filedialog
from tkinter.ttk import Button, Entry, Label, OptionMenu
import os, math
from util import var_mul, binary_search_find_nearest, binary_search_buried, get_peak_types
from itertools import chain, groupby
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from scipy.optimize import curve_fit
#Pages
#TODO: variable names camelCase, function names underscore separated
#TODO: possibly resolve star import

class ReviewFitPage(Frame): 
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.controller = parent
        title = Label(self,text="Fit Review",font=("Arial",14,"bold"))
        title.grid(row=0,column=0,columnspan=6)
        self.f = Figure(figsize=(5,5), dpi=100)
        self.a = self.f.add_subplot(111)             
        Label(self, text="Left Bound:").grid(row=1,column=6)
        Label(self, text="Right Bound:").grid(row=1,column=7)
        peakSelectorButton =  Button(self, text="Manually Choose Element", command=self.send_to_mes)
        peakSelectorButton.grid(row=5,column=6)
        ignoreButton = Button(self, text="Ignore this data", command = lambda:self.controller.peakCounter.set(self.controller.peakCounter.get()+1))
        ignoreButton.grid(row=6,column=7)
        self.KnownPeaksFrame = Frame(self)
        Label(self.KnownPeaksFrame, text="Peak Information").grid(row=0, column=0, columnspan=2)
        
        Button(self.KnownPeaksFrame, text="Add", command=self.add_peak).grid(row=1,column=1)
        
        self.KnownPeaksFrame.grid(row=3,column=6, columnspan=2)
        Button(self, text="Reanalyze", command=self.reanalyze).grid(row=4,column=6,columnspan=2)
        self.slope = 0
        self.intercept = 0
        self.ctrs = []
        self.annots = []
        self.fill = None
        self.peakGUIList = []
        self.removeBtns = []
    def populate_values(self, ROI):
        self.ROI = ROI
        self.a.cla()
        peaks = ROI.get_peaks()
        if len(peaks) > 0:
            fitX = np.arange(ROI.range[0]-20, ROI.range[1] + 20, .01)
            self.a.plot(fitX, ROI.get_fitted_curve(fitX), "r-", label = "Fit")
            self.backgroundLine = self.a.plot(fitX,ROI.get_bg().get_ydata(fitX),"k-", label = "Background")
            self.peakPoints = self.a.plot(self.ctrs, fullAmps,"go",label="Found Peaks",picker=6)[0]
            self.peakPoints.set_pickradius(10)
            self.f.canvas.mpl_connect('motion_notify_event', self.on_plot_hover)
        self.a.plot(ROI.get_energies(), ROI.get_cps(),"bo", label="Observed Data")
        self.a.set_xlim(ROI.range[0], ROI.range[1])
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1,column=0,columnspan=6, rowspan=6)
        self.a.legend(loc='upper right', prop={'size': 8})
        toolbarFrame = Frame(self)
        toolbarFrame.grid(row=7,column=0,columnspan=6, sticky="w")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        self.spinboxLeftVal = DoubleVar()
        self.spinboxLeft = Spinbox(self, values=self.energies[:-20], command = self.update_right, textvariable = self.spinboxLeftVal)
        self.spinboxLeft.bind("<Return>",lambda x:self.update_right())
        self.spinboxLeft.bind("<FocusOut>",lambda x:self.update_right())
        self.spinboxLeftVal.set(self.energies[20])
        self.spinboxLeft.grid(row=2,column=6)
        self.spinboxRightVal = DoubleVar()
        self.spinboxRight = Spinbox(self, values = self.energies[21:], command = self.update_left, textvariable = self.spinboxRightVal)
        self.spinboxRight.bind("<Return>",lambda x:self.update_left())
        self.spinboxRight.bind("<FocusOut>",lambda x:self.update_left())
        self.spinboxRightVal.set(self.energies[-20])
        self.spinboxRight.grid(row=2,column=7)
        for i in self.peakGUIList:
            i.destroy()
        for i in self.removeBtns:
            i.destroy()
        self.peakGUIList = []
        self.removeBtns = []
        peaks = self.ROI.get_peaks()
        i=0
        for p in peaks:
            self.peakGUIList.append(Label(self.KnownPeaksFrame, text=("{:5f},"*p.get_num_params()-1+"{:5f}").format(*p.get_params())))
            self.removeBtns.append(Button(self.KnownPeaksFrame, text="Remove", command=lambda temp=i:self.remove_peak(temp)))
            self.peakGUIList[i].grid(row=i+2,column=0)
            self.removeBtns[i].grid(row=i+2,column=1)
            i += 1
    def remove_peak(self, ind):
        #TODO: Slide things up
        self.ROI.remove_peak(self.peakGUIList[ind].cget("text").split(",")[0])
        self.peakGUIList[ind].destroy()
        del self.peakGUIList[ind]
        self.removeBtns[-1].destroy()
        del self.removeBtns[-1]
        self.ROI.fit()
    def add_peak_GUI(self):
        win = Tk.Toplevel()
        peakType = StringVar(self.controller)
        OptionMenu(win, peakType, "Select Peak Type", get_peak_types().keys()).grid(row=0,column=0,columnspan=2)
        peakType.trace("w",lambda:update_add_gui(win, peakType))
    def update_add_gui(self, win, peakType):
        peak = get_peak_types()[peakType.get()]
        entry_fields = peak.get_entry_fields()
        i = 1
        entries = []
        for e in entry_fields:
            Label(win, text=e).grid(row=i,column=0)
            tmp = StringVar(self.controller)
            Entry(win, tmp).grid(row=i,column=1)
            entries.append(tmp)
            i += 1
        Button(text="Submit", command = lambda:add_peak(win, peak, entries))
    def add_peak(self, win, peak, entry_fields):
        peak.handle_entry([float(e.get()) for e in entries])
        self.ROI.add_peak(peak)
        self.peakGUIList.append(Label(self.KnownPeaksFrame, text=("{:5f},"*peak.get_num_params()-1+"{:5f}").format(*peak.get_params())))
        self.removeBtns.append(Button(self.KnownPeaksFrame, text="Remove", command=lambda temp=i:self.remove_peak(temp)))
        self.peakGUIList[-1].grid(row=len(self.peakGUIList)+1,column=0)
        self.removeBtns[-1].grid(row=len(self.removeBtns)+1,column=1)
        self.ROI.fit()
        win.destroy()
        
        
    #TODO: add manual entry flag, and call it with a keybind from the spinboxes
    def update_left(self):
        temp = self.spinboxLeftVal.get()
        try:
            newRange = self.energies[:np.where(self.energies==self.spinboxRightVal.get())[0][0]]
        except IndexError:
            newRange = self.energies[:binary_search_find_nearest(self.energies, self.spinboxRightVal.get())]
        self.spinboxLeft.configure(values=newRange)
        self.spinboxLeftVal.set(temp)
    def update_right(self):
        temp = self.spinboxRightVal.get()
        if self.spinboxLeftVal.get() < self.energies[0]:
            messagebox.showinfo("Out of Bounds","Please enter an X value within the currently plotted points")
            self.spinboxLeftVal.set(self.energies[20])
            return None
        try:
            newRange = self.energies[np.where(self.energies==self.spinboxLeftVal.get())[0][0]+1:]
        except IndexError:
            newRange = self.energies[binary_search_find_nearest(self.energies, self.spinboxLeftVal.get()):]
        self.spinboxRight.configure(values=newRange)
        self.spinboxRightVal.set(temp)
        
    def clear_new_entry(self, _):
        self.newPeakEntry.delete(0,"end")
    def reset_new_entry(self):
        self.newPeakEntry.delete(0,"end")
        self.newPeakEntry.insert(0,"Enter Peak Energy")
    def submit(self):
        self.controller.show_frame(ManualElementSelect)
        self.controller.frames[ManualElementSelect].populate_values(self.ROI, self.poss)

class ManualElementSelect(Frame): 
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.controller = parent
        title = Label(self,text="Manual Peak Matching",font=("Arial",14,"bold"))
        title.grid(row=0,column=0,columnspan=6)
        self.f = Figure(figsize=(5,5), dpi=100)
        self.a = self.f.add_subplot(111)        
        Label(self, text="Peak Location: ").grid(row=1,column=4)
        Label(self, text="Match: ").grid(row=1,column=5)
        Button(self, text="Submit", command=self.submit).grid(row=20, column=5)
        self.newObjects = []
        Button(self, text="Back",command=self.back).grid(row=25,column=0)
    def populate_values(self, ROI, poss):
        self.ROI = ROI
        self.poss = poss
        self.a.cla()
        self.a.plot(ROI.get_energies(), ROI.get_fitted_curve(),"b-")
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1,column=0, columnspan=4, rowspan=20)
        for o in self.newObjects:
            o.destroy()
        self.newObjects = []
        self.selected = []
        self.peaks = ROI.get_peaks()
        centers = [p.get_ctr() for p in self.peaks]
        for i in range(len(centers)):
            self.selected.append(StringVar(self.controller))
        for i in range(len(centers)):
            self.selected[i].set("Ignore")
            opts = ["","Ignore"] + [j.get_ele()+": "+str(j.get_ctr()) for j in poss[i]] #Stupid tkinter workaround
            #TODO: Dicts of these?
            copy = i
            temp = Label(self,text=str(centers[i]))
            temp.grid(row=i+2, column = 4)
            self.newObjects.append(temp)
            temp=OptionMenu(self,self.selected[copy],*opts)
            temp.grid(row=i+2, column = 5)
            self.newObjects.append(temp)
    def back(self):
        self.controller.show_frame(ReviewFitPage)
    def submit(self): #TODO: Remove all peak locations and option menus
        sel = False
        inp = []
        usedPoss = []
        usedPeaks = []
        usedVars = []
        for i in range(len(self.selected)):
            if self.selected[i].get() != "Ignore":
                inp.append(self.selected[i].get())
                usedPeaks += self.peaks[i]
                sel = True
        if not sel:
            messagebox.showinfo("Error","Please match at least one peak!")
            return None
        for p in inp:
            temp = p.split(": ")
            for q in self.poss:
                if q.get_ele() == temp[0] and str(q.get_ctr()) == temp[1]:
                    usedPoss.append(q)
        peakPairs = []
        outputs = []
        for i in range(len(usedPoss)):
            outputs.append([usedPoss[i],usedPeaks[i]])
            peakPairs += (usedPeaks[i].get_ctr(), usedPoss[i])
        self.ROI.add_peak_pairs(peakPairs)
        self.controller.increment_peak_counter()
        
class ResultsViewer(Frame):
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent=parent
        self.header = Label(self, text="Results by File", font=("Arial",14,"bold"))
        self.header.grid(row=0,column=0,columnspan=3)
        self.currentRow = 1
    def display_file_results(self,fname,results):
        self.parent.show_frame(SingleFileViewer)
        self.parent.frames[SingleFileViewer].display_file_results(fname, results)
    def export_all_data(self,filesDict):
        fname = filedialog.asksaveasfilename(initialdir = ".",title = "Select export file",filetypes = [("CSV files","*.csv")])
        if fname[-4:] != ".csv":
            fname += ".csv"
        exportFile = open(fname,'w')
        for f in filesDict.keys():
            exportFile.write(f+"\n")
            exportFile.write("Peaks Used for Mass Calculations:\n")
            exportFile.write("Element, Theorhetical Peak Energy, Observed Peak Energy, Peak Height, Peak Width, Peak Area, Peak Sensitivity, Predicted Mass (mg), Std. Dev. (mg)\n")
            for element in filesDict[f][0].keys():
                exportFile.write(element+",")
                for peak in filesDict[f][0][element]:
                    outList = [peak[1]] + list(peak[0][:4]) + list(peak[2:])
                    exportFile.write(','.join([str(i) for i in outList])+"\n,")
                exportFile.seek(exportFile.tell() - 1, os.SEEK_SET)  #Don't indent the next element
            exportFile.write("Disregarded Peaks:\n")
            exportFile.write("Observed Peak Energy, Peak Height, Peak Width, Peak Area, Closest Element, Element's Peak Center, Element Sensitivity, Predicted Mass (mg), Std. Dev. (mg)\n")
            for element in filesDict[f][2].keys():
                for peak in filesDict[f][2][element]:
                    outList = list(peak[0][:4]) + [element] + list(peak[1:])
                    exportFile.write(','.join([str(i) for i in outList])+"\n")
                exportFile.seek(exportFile.tell() - 1, os.SEEK_SET)  #Don't indent the next element
            exportFile.write("Masses Calculated:"+"\n")
            exportFile.write("Element, Predicted Mass (mg), Std. Dev. (mg), Number of Atoms (mol), Std. Dev. (mol)\n")
            for element in filesDict[f][1].keys():
                exportFile.write(element + ',' + ','.join([str(i) for i in filesDict[f][1][element]])+"\n")
            exportFile.write("\n\n")
        exportFile.close()
    def show_files(self,filesDict):
        for f in filesDict.keys():
            fileLabel = Label(self, text=f)
            fileLabel.grid(row=self.currentRow,column=0)
            showButton = Button(self, text = "Show", command=lambda tmp=f:self.display_file_results(tmp,filesDict[tmp]))
            showButton.grid(row=self.currentRow,column=1)
            self.currentRow += 1
        exportAllButton = Button(self, text="Export All Data", command=lambda:self.export_all_data(filesDict))
        exportAllButton.grid(row=self.currentRow, column=0,columnspan=2)
class SingleFileViewer(Frame):
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent=parent
        self.currentRow = 0
    
    def write_row(self, itemsList):
        for i in range(len(itemsList)):
            Label(self, text=str(itemsList[i]), borderwidth=4, relief="solid").grid(row=self.currentRow, column=i, sticky="nsew")
        self.currentRow += 1
        
    def display_file_results(self,fname, results):
        self.currentRow = 0
        Button(self, text="Back",command=self.go_back).grid(row=1000,column=0)
        Label(self, text=fname,font=("Arial",14)).grid(row=0,column=0,columnspan=8)
        Label(self, text="Peaks Used for Mass Calculations:").grid(row=1,column=0, columnspan=2, pady=(20,0), sticky="w")
        self.currentRow = 2
        self.write_row(['Element', 'Theorhetical Peak Energy', 'Observed Peak Energy', 'Peak Height', 'Peak Width', 'Peak Area','Peak Sensitivity', 'Predicted Mass (mg)', 'Std. Dev. (mg)'])
        for element in results[0].keys():
            for peak in results[0][element]:
                outList = [element, peak[1]] + list(peak[0][:4]) + list(peak[2:])
                self.write_row(outList)
        Label(self, text="Disregarded Peaks:").grid(row=self.currentRow,column=0, columnspan=2, pady=(20,0), sticky="w") 
        self.currentRow += 1
        self.write_row(['Observed Peak Energy', 'Peak Height', 'Peak Width', 'Peak Area','Closest Element', "Element's Peak Center", 'Element Sensitivity', 'Predicted Mass (mg)', 'Std. Dev. (mg)'])
        for element in results[2].keys():
            for peak in results[2][element]:
                outList = list(peak[0][:4]) + [element] + list(peak[1:])
                self.write_row(outList)
        Label(self, text="Masses Calculated:").grid(row=self.currentRow,column=0, columnspan=2, pady=(20,0), sticky="w") 
        self.currentRow += 1
        self.write_row(['Element', 'Predicted Mass (mg)', 'Std. Dev. (mg)', 'Number of Atoms (mol)', 'Std. Dev. (mol)'])
        for element in results[1].keys():
            self.write_row([element]+results[1][element])
            
    def go_back(self):
        for c in self.winfo_children():
            c.destroy()
        self.parent.show_frame(ResultsViewer)
class BaseFileSelectorFrame(Frame):
    def __init__(self, parent, files):
        Frame.__init__(self, parent)
        self.files = files
        self.controller = parent
        Label(self, text="Select Base Files").grid(row=0,column=0)
        i=1
        self.checkBoxList = []
        for f in files:
            tmpVar = IntVar()
            Checkbutton(text=f,variable=tmpVar).grid(row=i,column=0)
            self.checkBoxList.append(tmpVar)
        Button(text="Next", command=self.send_to_sample_select)
    def send_to_sample_select(self):
        outFiles = []
        for i in range(len(self.files)):
            if self.checkBoxList[i].get():
                outFiles.append(self.files[i])
        self.controller.show_frame(SampleSelectFrame)
        self.controller.frames[SampleSelectFrame].populate_list(outFiles)
class SampleSelectFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.filesList = []
        self.checkBoxList = []
        Label(self, text="Select Sample Files").grid(row=0,column=0)
        Button(self, text="Analyze",command=self.do_analysis).grid(row=1000,column=0)
        
    def populate_list(self, files):
        for currentCheckbox in self.filesList:
            currentCheckbox.grid_forget()
        self.filesList = []
        self.checkBoxList = []
        for newFile in files:
            tmpVar = IntVar()
            tmpBtn = Checkbutton(text=newFile, variable=tmpVar)
            self.fileslist.append(tmpBtn)
            self.checkBoxList.append(tmpVar)
    def do_analysis(self):
        outFiles = []
        for i in range(len(self.filesList)):
            if self.checkBoxList[i].get():
                outFiles.append(self.filesList[i].cget("text"))
        