from quart import Quart, request, redirect, url_for, render_template, send_file
from quart_auth import AuthManager, AuthUser, login_user, logout_user, current_user, login_required, Unauthorized
from backend import PGAAnalysis
import motor.motor_asyncio
import bcrypt
import asyncio
import os
import uuid
import aiofiles
from werkzeug.utils import secure_filename
from aiotinydb import AIOTinyDB
from tinydb import Query
loop = asyncio.get_event_loop()

#setup db
userDB = await AIOTinyDB("userDB.json")
projectDB = await AIOTinyDB("projectDB.json")

app = Quart(__name__)
app.secret_key = os.environ["secret_key"]
AuthManager(app)

activeProjects = dict()

@app.route("/login", methods=['GET', 'POST'])
async def login():
    if request.method == "POST":
        User = Query()
        user_doc = await userDB.search(User.uname == request.form.get("uname"))
        if user_doc == None:
            return redirect(url_for("login?failed=true"))
        
        if await loop.run_in_executor(None, bcrypt.checkpw, request.form.get("pw").encode("utf-8"), user_doc["hashed_password"]):
            login_user(AuthUser(str(user_doc["id"])))
            return redirect(url_for("profile"))
        else:
            return redirect(url_for("login?failed=true"))
    else:
        if current_user.is_authenticated():
            return redirect(url_for("profile"))
        return await(render_template("login.html"))

@app.route("/signup", methods=['GET', 'POST'])
async def signup():
    if request.method == "POST":
        User = Query()
        user_doc = await userDB.search(User.uname == request.form.get("uname"))
        if user_doc != None:
            return redirect(url_for("signup?exists=true"))
        salt = bcrypt.gensalt(16)
        hashed_pw = await loop.run_in_executor(None, bcrypt.hashpw, request.form.get("pw").encode('utf-8'), salt)
        await userDB.insert({"id":str(uuid.UUID()), "uname":request.form.get("uname"), "hashed_password":hashed_pw})
        return redirect(url_for("login"))
    else:
        if current_user.is_authenticated():
            return redirect(url_for("profile"))
        return await(render_template("signup.html"))

@app.route("/icons/<icon_name>")
async def get_icon(icon_name):
    return await send_file(os.path.join("D:\\CyPat\\OpenAGS\\img\\icons", icon_name))

@app.route("/projects/<projectID>")
async def project(projectID):
    global activeProjects
    uname = await current_user.uname
    if projectID in activeProjects.keys():
        pass
    else:
        Project = Query()
        currentProject = await projectDB.search(Project.id == projectID)
        analysisObject = PGAAnalysis()
        await loop.run_in_executor(None, analysisObject.load_from_dict, currentProject)
        activeProjects[projectID] = {
            "pythonObject" : analysisObject,
            "currentUsers" : [uname]
        }
    return await(render_template("project.html"))
@login_required
@app.route("/create", methods=["GET","POST"])
async def create():
    if request.method == "GET":
        async with aiofiles.open('D:\\CollabDocTest\\create.html', mode='r') as f:
            contents = await f.read()
        return contents
    else:
        upload_path = "D:\\CyPat\\OpenAGS\\uploads"
        proj_id = str(uuid.uuid4())
        await aiofiles.os.mkdir(os.path.join(upload_path,proj_id))
        uploaded_files = await request.files
        files_list = uploaded_files.getlist("file")
        for f in files_list:
            p = os.path.join(upload_path,proj_id,secure_filename(f.filename))
            f.save(p)
        return redirect(url_for("/projects/"+proj_id))

@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Exception):
    return redirect(url_for("login"))
