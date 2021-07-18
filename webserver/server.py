from quart import Quart, request, redirect, url_for, render_template, send_file, websocket, make_response
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from werkzeug.utils import secure_filename
import aiofiles
import aiofiles.os

import os
import uuid
import json
import time
import sys
import functools
from copy import deepcopy

sys.path.append(os.path.join("..","backend"))

from backend import ActivationAnalysis
from parsers import CSVWriter, ExcelWriter
from constants import som
from evaluators import MassSensEval

loop = None

app = Quart(__name__)

activeProjects = dict()

@app.before_serving
async def startup():
    global loop
    loop = asyncio.get_event_loop()

@app.route("/icons/<icon_name>")
async def get_icon(icon_name):
    return await send_file(os.path.join(os.getcwd(), "icons", icon_name))

@app.route("/")
async def homepage():
    async with aiofiles.open(os.path.join(os.getcwd(),'homepage.html'), mode='r') as f:
        contents = await f.read()
    return contents

@app.route("/error")
async def errorpage():
    async with aiofiles.open(os.path.join(os.getcwd(),'error.html'), mode='r') as f:
        contents = await f.read()
    return contents

@app.route("/projects/<projectID>/<action>")
async def project(projectID, action):
    global activeProjects
    analysisObject = None
    if projectID in activeProjects.keys():
        analysisObject = activeProjects[projectID]["analysisObject"]
    else:
        async with aiofiles.open(os.path.join(os.getcwd(),"uploads",projectID,"state.json"), mode="r") as f:
            contents = await f.read()
            currentProject = json.loads(contents)
            analysisObject = ActivationAnalysis()
            try:
                await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
            except:
                return redirect("/error")
            activeProjects[projectID] = {
                "analysisObject" : analysisObject,
                "webSockets" : [],
                "numUsers" : 0,
                "saveAction" : None
            }
    if action == "edit":
        if not analysisObject.ROIsFitted:
            analysisObject.get_fitted_ROIs()
        return await(render_template("project.html", analysisObject=analysisObject, projectID=projectID, pathSplit=os.path.split))
    elif action == "view":
        return await(render_template("view.html", analysisObject=analysisObject, projectID=projectID, som=som, pathSplit=os.path.split))
    elif action == "results":
        return await(render_template("results.html", analysisObject=analysisObject, projectID=projectID, pathSplit=os.path.split))
    else: 
        return ""

@app.route("/create", methods=["GET","POST"])
async def create():
    if request.method == "GET":
        async with aiofiles.open(os.path.join(os.getcwd(),'create.html'), mode='r') as f:
            contents = await f.read()
        return contents
    else:
        upload_path = os.path.join(os.getcwd(), "uploads")
        projectID = str(uuid.uuid4())
        #TODO: aiofiles.os.mkdir not working for some reason. Debug this
        
        os.mkdir(os.path.join(upload_path,projectID))
        os.mkdir(os.path.join(os.getcwd(), "results", projectID))

        uploaded_files = await request.files  
        form = await request.form      
        files_list = uploaded_files.getlist("file")
        try:
            standardsFile = uploaded_files.get("standardsFile")
            standardsFilename = os.path.join(upload_path,projectID,secure_filename(standardsFile.filename))
            await standardsFile.save(standardsFilename)
        except:
            standardsFilename = os.path.join(os.getcwd(),"AllSensitivity.csv")
    
        filenamesList = []
        for f in files_list:
            filenamesList.append(os.path.join(upload_path,projectID,secure_filename(f.filename)))
            p = os.path.join(upload_path,projectID,secure_filename(f.filename))
            await f.save(p)
        
        delayed = form.get("analysisType") == "delayed"

        async with aiofiles.open(os.path.join(os.getcwd(), "uploads", projectID, "state.json"), mode="w") as f:
            await f.seek(0)
            await f.write(json.dumps({
                "title" : form["title"],
                "files" : filenamesList,
                "standardsFilename" : standardsFilename,
                "ROIsFitted" : False,
                "ROIs" : [],
                "resultsGenerated" : False,
                "delayed" : delayed,
                "NAATimes" : [[] for i in range(len(filenamesList))]
            }))
        return json.dumps({"id" : projectID})

@app.route("/results/<projectID>/<filename>")
async def serve_result(projectID, filename):
    try:
        async with aiofiles.open(os.path.join(os.getcwd(),"results",projectID,filename), mode="rb") as f:
            c = await f.read()
            return c, 200, {'Content-Disposition' : 'attachment; filename="'+filename+'"'}
    except:
        global activeProjects
        if projectID in activeProjects.keys():
            analysisObject = activeProjects[projectID]["analysisObject"]
        else:
            async with aiofiles.open(os.path.join(os.getcwd(),"uploads", projectID, "state.json"), mode="r") as f:
                contents = await f.read()
                currentProject = json.loads(contents)
                analysisObject = ActivationAnalysis()
                await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
        if filename.split(".")[-1] == "xlsx":
            headings = [fd["resultHeadings"] for fd in analysisObject.fileData]
            data = [fd["results"] for fd in analysisObject.fileData]
            ew = ExcelWriter(projectID, analysisObject.get_title(), analysisObject.fileList, headings, data)
            ew.write()
        elif filename[-21:] == "_Analysis_Results.csv":
            origFilename = filename.replace("_Analysis_Results.csv","")
            for i in range(len(analysisObject.fileList)):
                if os.path.split(analysisObject.fileList[i])[1].split('.')[0] == origFilename:
                    cw = CSVWriter(projectID, filename, analysisObject.fileData[i]["resultHeadings"][0], analysisObject.fileData[i]["results"])
                    cw.write()
                    break
        else:
            origFilename = filename.replace("_xy.csv","")
            for i in range(len(analysisObject.fileList)):
                if os.path.split(analysisObject.fileList[i])[1].split('.')[0] == origFilename:
                    cw = CSVWriter(projectID, filename, ["Energy (keV)", "Counts Per Second"], zip(analysisObject.fileData[i]["energies"], analysisObject.fileData[i]["cps"]))
                    cw.write()
                    break
        async with aiofiles.open(os.path.join(os.getcwd(),"results",projectID, filename), mode="rb") as f:
            c = await f.read()
            return c, 200, {'Content-Disposition' : 'attachment; filename="'+filename+'"'}

async def saveProject(projectID):
    await asyncio.sleep(60)
    print("saving "+projectID)
    global activeProjects
    async with aiofiles.open(os.path.join(os.getcwd(),"uploads",projectID,"state.json"), mode="w") as f:
        await f.seek(0)
        await f.write(json.dumps(activeProjects[projectID]["analysisObject"].export_to_dict()))
    
    del activeProjects[projectID]

async def saveProjectNow(projectID):
    print("saving "+projectID)
    global activeProjects
    async with aiofiles.open(os.path.join(os.getcwd(),"uploads",projectID,"state.json"), mode="w") as f:
        await f.seek(0)
        await f.write(json.dumps(activeProjects[projectID]["analysisObject"].export_to_dict()))
    
    del activeProjects[projectID]


@app.websocket("/projects/<projectID>/ws")
async def ws(projectID):
    async def producer(projectID):
        global activeProjects
        queue = asyncio.Queue()
        if projectID not in activeProjects.keys():
            async with aiofiles.open(os.path.join(os.getcwd(),"uploads",projectID,"state.json"), mode="r") as f:
                contents = await f.read()
                currentProject = json.loads(contents)
                analysisObject = ActivationAnalysis()
                await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
                activeProjects[projectID] = {
                    "analysisObject" : analysisObject,
                    "webSockets" : [],
                    "numUsers" : 0,
                    "saveAction" : None
                }
        activeProjects[projectID]["webSockets"].append(queue)
        activeProjects[projectID]["numUsers"] += 1
        if activeProjects[projectID]["saveAction"] != None:
            activeProjects[projectID]["saveAction"].cancel()
        activeProjects[projectID]["saveAction"] = None
        print("save action cancelled")
        while True:
            try:
                data = await queue.get()
                await websocket.send(data)
            except asyncio.CancelledError:
                activeProjects[projectID]["webSockets"].remove(queue)

    async def consumer(projectID):
        global activeProjects
        while True:
            data = await websocket.receive()
            dataDict = json.loads(data)
            if dataDict["type"] == "ROIUpdate":
                analysisObject = activeProjects[projectID]["analysisObject"]
                ROI = analysisObject.ROIs[dataDict["index"]]
                ROI.fitted = False
                if "newRange" in dataDict.keys():
                    analysisObject.set_ROI_range(dataDict["index"],dataDict["newRange"])
                #remove the peaks that were removed by the user
                if "existingPeaks" in dataDict.keys():
                    peaks = ROI.get_peaks()
                    newPeaks = []
                    for peak in peaks:
                        if peak.to_string() in dataDict["existingPeaks"]:
                            newPeaks.append(peak)
                    ROI.set_peaks(newPeaks)
                if "newPeaks" in dataDict.keys():
                    for peak in dataDict["newPeaks"]:
                        peakType = peak[0]
                        peakParams = peak[1:]
                        ROI.peaks.append(som["peaks"][peakType](*peakParams))
                if "background" in dataDict.keys():
                    bg = dataDict["background"]
                    bgType = bg[0]
                    bgParams = bg[1:]
                    ROI.set_background(som["backgrounds"][bgType](*bgParams))
                ROI.fit()
                outputObj = {
                    "type" : "ROIUpdate",
                    "index" : dataDict["index"],
                    "fitted" : ROI.fitted,
                    "xdata" : ROI.get_energies(),
                    "ydata" : ROI.get_cps(),
                    "peakStrings" : [p.to_string() for p in ROI.get_peaks()],
                    "bgString" : ROI.get_background().to_string(),
                    "ROIRange" : ROI.get_range()
                    }
                if ROI.fitted:
                    curve = ROI.get_fitted_curve()
                    outputObj["curveX"] = curve[0]
                    outputObj["curveY"] = curve[1]
                    outputObj["peakX"] = ROI.get_peak_ctrs()
                    outputObj["backgroundY"] = list(ROI.get_background().get_ydata(ROI.get_range()))

                data = json.dumps(outputObj)   

                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(data)
            
            elif dataDict["type"] == "entryReprRequest":
                analysisObject = activeProjects[projectID]["analysisObject"]
                entryParams = []
                try:
                    entryParams = [float(x) for x in dataDict["entryParams"]]
                except:
                    await websocket.send(json.dumps({"type" : "error", "text":"Please enter only numbers for peak paramaters."}))
                    continue
                try:
                    stringRepr, params = analysisObject.get_entry_repr(dataDict["class"],dataDict["name"],dataDict["ROIIndex"],entryParams)
                except:
                    await websocket.send(json.dumps({"type" : "error", "text":"Your peak is outside the ROI bounds."}))
                    continue
                outputObj = {
                    "type" : "entryReprResponse",
                    "class" : dataDict["class"],
                    "index" : dataDict["ROIIndex"],
                    "name" : dataDict["name"],
                    "params" : params,
                    "output" : stringRepr
                }
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(json.dumps(outputObj))
            elif dataDict["type"] == "matchUpdate":
                #just echo back to all
                for queue in activeProjects[projectID]["webSockets"]:
                        await queue.put(data)

            elif dataDict["type"] == "titleUpdate":
                analysisObject = activeProjects[projectID]["analysisObject"]
                if dataDict["newTitle"] != analysisObject.get_title():
                    analysisObject.set_title(dataDict["newTitle"])
                    for queue in activeProjects[projectID]["webSockets"]:
                        await queue.put(data)
            elif dataDict["type"] == "NAATimeUpdate":
                analysisObject = activeProjects[projectID]["analysisObject"]
                analysisObject.fileData[dataDict["fileIndex"]]["NAATimes"] = dataDict["times"]
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(data)
            elif dataDict["type"] == "isotopeUpdate":
                analysisObject = activeProjects[projectID]["analysisObject"]
                analysisObject.update_ROIs(dataDict["addedIsotopes"], dataDict["removedIsotopes"])
                outputObj = {
                    "type" : "isotopeUpdateResponse",
                    "currentIsotopes" : analysisObject.get_isotopes(),
                    "ROIRanges" : [r.get_formatted_range() for r in analysisObject.ROIs],
                    "ROIIndicies" : [r.get_indicies() for r in analysisObject.ROIs],
                    "ROIIsotopes" : [', '.join(r.get_isotopes()) for r in analysisObject.ROIs]
                }
                outputData = json.dumps(outputObj)
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(outputData)
            elif dataDict["type"] == "peakMatchSubmission":
                analysisObject = activeProjects[projectID]["analysisObject"]
                for i in range(len(dataDict["pairs"])):
                    analysisObject.ROIs[i].set_original_peak_pairs(dataDict["pairs"][i])
                #TODO: Maybe allow users to customize this, as that is kinda the point of evaluators. 
                analysisObject.run_evaluators([MassSensEval], [[]])
                
                async with aiofiles.open(os.path.join(os.getcwd(),"uploads",projectID,"state.json"), mode="w") as f:
                    await f.seek(0)
                    await f.write(json.dumps(analysisObject.export_to_dict()))
                
                
                for f in os.listdir(os.path.join(os.getcwd(), "results", projectID)):
                    await aiofiles.os.remove(f)

                outputData = json.dumps({"type" : "resultsGenerated"})
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(outputData)
            elif dataDict["type"] == "userPrefsUpdate":
                analysisObject = activeProjects[projectID]["analysisObject"]
                analysisObject.set_user_prefs(dataDict["newPrefs"])
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(data)
    consumer_task = asyncio.ensure_future(consumer(projectID))
    producer_task = asyncio.ensure_future(producer(projectID))
    try:
        await asyncio.gather(consumer_task, producer_task)
    finally:
        activeProjects[projectID]["numUsers"] -= 1
        if activeProjects[projectID]["numUsers"] <= 0:
            print("started save action")
            activeProjects[projectID]["saveAction"] = asyncio.create_task(saveProject(projectID))
        consumer_task.cancel()
        producer_task.cancel()
@app.after_serving
async def export_to_db():
    global activeProjects
    for projectID in activeProjects.keys():
        a = activeProjects[projectID]["saveAction"]
        if a != None:
            a.cancel()
        await saveProjectNow(projectID)
serverConfig = Config()
serverConfig.bind=["0.0.0.0:80"]
asyncio.run(serve(app, serverConfig))