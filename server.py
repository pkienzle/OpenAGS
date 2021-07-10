from quart import Quart, request, redirect, url_for, render_template, send_file, websocket, make_response
from quart_auth import AuthManager, AuthUser, login_user, logout_user, current_user, login_required, Unauthorized
from backend import PGAAnalysis
from parsers import CSVWriter, ExcelWriter
import bcrypt
import asyncio
import os
import uuid
import aiofiles
import aiofiles.os
from hashlib import md5
import json
from werkzeug.utils import secure_filename
from aiotinydb import AIOTinyDB
from tinydb import Query
from util import som
from copy import deepcopy
from evaluators import MassSensEval
import time

loop = None

app = Quart(__name__)
app.secret_key = "sFmsFAWjJEX96jJUXkGSQA"
AuthManager(app)

activeProjects = dict()
tmpRmvLst = []

@app.before_serving
async def startup():
    global loop
    loop = asyncio.get_event_loop()

@app.route("/login", methods=['GET', 'POST'])
async def login():
    if request.method == "POST":
        User = Query()
        form = await request.form
        async with AIOTinyDB("userDB.json") as userDB:
            user_doc = userDB.search(User.uname == form["uname"])
            if user_doc == []:
                return redirect(url_for("login")+"?failed=true")
            user_doc = user_doc[0]
            if await loop.run_in_executor(None, bcrypt.checkpw, form["pw"].encode("utf-8"), user_doc["hashed_password"].encode('utf-8')):
                login_user(AuthUser(str(user_doc["uname"])))
                return redirect(url_for("view_profile"))
            else:
                return redirect(url_for("login")+"?failed=true")
    else:
        if await current_user.is_authenticated:
            return redirect(url_for("view_profile"))
        return await(render_template("login.html"))

@app.route("/signup", methods=['GET', 'POST'])
async def signup():
    if request.method == "POST":
        User = Query()
        async with AIOTinyDB("userDB.json") as userDB:
            form = await request.form
            user_doc = userDB.search(User.uname == form["uname"])
            if user_doc != []:
                return redirect(url_for("signup")+"?exists=true")
            salt = bcrypt.gensalt(16)
            hashed_pw = await loop.run_in_executor(None, bcrypt.hashpw, form["pw"].encode('utf-8'), salt)
            email = form["email"]
            emailHash = md5(email.lower().encode('utf-8')).hexdigest()
            userDB.insert({"uname": form["uname"], "hashed_password" : hashed_pw.decode('utf-8'), "email" : email, "emailHash" : emailHash})
        return redirect(url_for("login"))
    else:
        if await current_user.is_authenticated:
            return redirect(url_for("view_profile"))
        return await(render_template("signup.html"))

@login_required
@app.route("/profile")
async def view_profile():
    User = Query()
    async with AIOTinyDB("userDB.json") as userDB:
        userEntry = userDB.search(User.uname == current_user.auth_id)
    return await(render_template("profile.html", userEntry=userEntry))

@app.route("/icons/<icon_name>")
async def get_icon(icon_name):
    return await send_file(os.path.join("D:\\CyPat\\OpenAGS\\img\\icons", icon_name))

"""
@login_required
@app.route("/projects/<projectID>/setup", methods=["GET","POST"])
async def editAnalysisOptions(projectID):
    global activeProjects
    if request.method == "GET":
        uname = current_user.auth_id
        User = Query()
        async with AIOTinyDB("userDB.json") as userDB:
            userEntry = userDB.search(User.uname == uname)[0]
        currentUser = {"uname" : uname, "hash" : userEntry["emailHash"]}
        if projectID in activeProjects.keys():
            analysisObject = activeProjects[projectID]["analysisObject"]
            activeProjects[projectID]["activeUsers"].append(currentUser)
        else:
            Project = Query()
            async with AIOTinyDB("projectDB.json") as projectDB:
                currentProject = projectDB.search(Project.id == projectID)[0]
                analysisObject = PGAAnalysis()
                await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
                activeProjects[projectID] = {
                    "analysisObject" : analysisObject,
                    "activeUsers" : [currentUser],
                    "webSockets" : []
                }
        return await(render_template("setup.html", analysisObject=analysisObject, currentUser=currentUser))
    else:
        form = await request.form
        isotopes = form.getlist("isotopes")
        activeProjects[projectID]["analysisObject"].create_ROIs(isotopes)
        await loop.run_in_executor(None, activeProjects[projectID]["analysisObject"].get_fitted_ROIs)
        #TODO: make this periodic or something
        async with AIOTinyDB("projectDB.json") as projectDB:
            Project = Query()
            exportDict = activeProjects[projectID]["analysisObject"].export_to_dict()
            exportDict["id"] = projectID
            projectDB.update(exportDict, Project.id == projectID)
        return json.dumps({"id" : projectID})"""

@login_required
@app.route("/projects/<projectID>/<action>")
async def project(projectID, action):
    global activeProjects
    uname = current_user.auth_id
    User = Query()
    async with AIOTinyDB("userDB.json") as userDB:
        userEntry = userDB.search(User.uname == uname)[0]
    analysisObject = None
    activeUsers = None
    currentUser = {"uname" : uname, "hash" : userEntry["emailHash"]}
    if projectID in activeProjects.keys():
        analysisObject = activeProjects[projectID]["analysisObject"]
        activeProjects[projectID]["activeUsers"].append(currentUser)
        wsData = {"type" : "user", "action": "joined", "username": currentUser["uname"], "userHash" : currentUser["hash"]}
        for queue in activeProjects[projectID]["webSockets"]:
            await queue.put(json.dumps(wsData)) 
        activeUsers = activeProjects[projectID]["activeUsers"]
    else:
        Project = Query()
        async with AIOTinyDB("projectDB.json") as projectDB:
            currentProject = projectDB.search(Project.id == projectID)[0]
            analysisObject = PGAAnalysis()
            await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
            activeUsers = [currentUser]
            activeProjects[projectID] = {
                "analysisObject" : analysisObject,
                "activeUsers" : activeUsers,
                "webSockets" : []
            }
    if currentUser["uname"] in tmpRmvLst:
        tmpRmvLst.remove(currentUser["uname"])
    if action == "edit":
        if not analysisObject.ROIsFitted:
            analysisObject.get_fitted_ROIs()
        return await(render_template("project.html", analysisObject=analysisObject, activeUsers=activeUsers, currentUser=currentUser))
    elif action == "view":
        return await(render_template("view.html", analysisObject=analysisObject, activeUsers=activeUsers, currentUser=currentUser))
    elif action == "results":
        return await(render_template("results.html", analysisObject=analysisObject, activeUsers=activeUsers, currentUser=currentUser))
    else: 
        return ""

@login_required
@app.route("/create", methods=["GET","POST"])
async def create():
    if request.method == "GET":
        async with aiofiles.open('D:\\Cypat\\OpenAGS\\create.html', mode='r') as f:
            contents = await f.read()
        return contents
    else:
        upload_path = "D:\\CyPat\\OpenAGS\\uploads"
        projectID = str(uuid.uuid4())
        #TODO: aiofiles.os.mkdir not working for some reason. Debug this
        os.mkdir(os.path.join(upload_path,projectID))
        uploaded_files = await request.files  
        form = await request.form      
        files_list = uploaded_files.getlist("file")
        standardsFilename = "D:\\CyPat\\OpenAGS\\AllSensitivity.csv"
        filenamesList = []
        for f in files_list:
            if f.filename[-4:] == ".csv":
                standardsFilename = os.path.join(upload_path,projectID,secure_filename(f.filename))
            else:
                filenamesList.append(os.path.join(upload_path,projectID,secure_filename(f.filename)))
            p = os.path.join(upload_path,projectID,secure_filename(f.filename))
            await f.save(p)
        async with AIOTinyDB("projectDB.json") as projectDB:
            projectDB.insert({
                "id" : projectID,
                "title" : form["title"],
                "files" : filenamesList,
                "standardsFilename" : standardsFilename,
                "ROIsFitted" : False,
                "ROIs" : [],
                "resultsGenerated" : False
            })
        return json.dumps({"id" : projectID})

@app.route("/results/<projectID>/<filename>")
async def serve_result(projectID, filename):
    try:
        res = make_response(send_file("./results/"+projectID+"/"+filename))
        res.headers['Content-Disposition'] = 'attachment; filename="'+filename+'"'
        return res
    except:
        global activeProjects
        if projectID in activeProjects.keys():
            analysisObject = activeProjects[projectID]["analysisObject"]
        else:
            Project = Query()
            async with AIOTinyDB("projectDB.json") as projectDB:
                currentProject = projectDB.search(Project.id == projectID)[0]
                analysisObject = PGAAnalysis()
                await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
        if filename.split(".")[-1] == "xlsx":
            headings = [fd["headings"] for fd in analysisObject.fileData]
            data = [fd["results"] for fd in analysisObject.fileData]
            ew = ExcelWriter(projectID, analysisObject.get_title(), analysisObject.fileList, headings, data)
            ew.write()
        else:
            origFilename = filename.replace("_Analysis_Results.csv","")
            for i in range(len(analysisObject.fileList)):
                if analysisObject.fileList[i].split('.')[0] == origFilename:
                    cw = CSVWriter(projectID, analysisObject.fileList[i], analysisObject.fileData[i]["headings"], analysisObject.fileData[i]["results"])
                    cw.write()
                    break
        res = make_response(send_file("./results/"+projectID+"/"+filename))
        res.headers['Content-Disposition'] = 'attachment; filename="'+filename+'"'
        return res

async def user_left(uname, projectID):
    global tmpRmvLst
    global activeProjects
    tmpRmvLst.append(uname)
    await asyncio.sleep(10)
    if uname in tmpRmvLst:
        for u in activeProjects[projectID]["activeUsers"]:
            if u["uname"] == uname:
                activeProjects[projectID]["activeUsers"].remove(u)
                break
        wsData = {"type" : "user", "action" : "left", "username" : uname}
        for queue in activeProjects[projectID]["websockets"]:
            queue.send(json.dumps(wsData))

@app.websocket("/projects/<projectID>/ws")
async def ws(projectID):
    async def producer(projectID):
        global activeProjects
        queue = asyncio.Queue()
        activeProjects[projectID]["webSockets"].append(queue)
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
            if dataDict["type"] == "user":
                pass
            elif dataDict["type"] == "ROIUpdate":
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
                stringRepr, params = analysisObject.get_entry_repr(dataDict["class"],dataDict["name"],dataDict["ROIIndex"],dataDict["entryParams"])
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
                
                Project = Query()
                async with AIOTinyDB("projectDB.json") as projectDB:
                    projectDB.update(analysisObject.export_to_dict(), Project.id == projectID)

                outputData = json.dumps({"type" : "resultsGenerated"})
                for queue in activeProjects[projectID]["webSockets"]:
                    await queue.put(outputData)
    consumer_task = asyncio.ensure_future(consumer(projectID))
    producer_task = asyncio.ensure_future(producer(projectID))
    try:
        await asyncio.gather(consumer_task, producer_task)
    finally:
        consumer_task.cancel()
        producer_task.cancel()
@app.after_serving
async def export_to_db():
    global activeProjects
    async with AIOTinyDB("projectDB.json") as projectDB:
        Project = Query()
        for projectID in activeProjects.keys():
            exportDict = activeProjects[projectID]["analysisObject"].export_to_dict()
            exportDict["id"] = projectID
            projectDB.update(exportDict, Project.id == projectID)

@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Exception):
    return redirect(url_for("login"))

app.run()