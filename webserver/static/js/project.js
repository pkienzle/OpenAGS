
var wsUrl = window.location.href.toString().replace("http","ws").replace("edit","ws");
var ws = new WebSocket(wsUrl);
ws.onmessage = function (event) {
    var data = JSON.parse(event.data);
    switch(data.type){
        case "titleUpdate":
            document.getElementById("cdTitle").value = data.newTitle;
            break;
        case "entryReprResponse":
            if(data.class == "peaks"){
                var peaksList = document.getElementById("fittedPeaksList-"+data.index.toString());
                var output = data.output;
                var peakData = [data.name].concat(data.params);
                window.newPeaks[data.index][output] = peakData;
                peaksList.innerHTML = peaksList.innerHTML + "<li class='list-group-item compact' id=\""+output+"\"><p class = 'peak-label'>"+output+"</p><img class='rmv-btn' src='/icons/file-x.svg' onclick='remove_peak_from_list(\""+ output +"\")'/></li>";
            }
            else if(data.class == "backgrounds"){
                var bgList = document.getElementById("fittedBgList-"+data.index.toString());
                var output = data.output;
                var bgData = [data.name].concat(data.params);
                window.newBackgrounds[data.index] = bgData;
                bgList.innerHTML = "<li class='list-group-item compact' id=\""+output+"\"><p class = 'bg-label'>"+output+"</p>";
            }
            break;
        case "ROIUpdate":
            var i = data.index;

            window.newPeaks[i] = {};
            window.newBackgrounds[i] = null;
            window.originalEnergyBounds[i] = data.ROIRange;
            resetEnergyBounds(i);

            dataTrace = {
                x : data.xdata,
                y : data.ydata,
                mode : "markers",
                name : "Data"
            }
            if(data.fitted && window.unfittedRegions.indexOf(data.index) !== -1){
                window.unfittedRegions.splice(window.unfittedRegions.indexOf(data.index), 1);
            }

            var bgList = document.getElementById("fittedBgList-"+data.index.toString());
            bgList.innerHTML = "<li class='list-group-item compact' id=\""+ data.bgString +"\"><p class = 'bg-label'>"+ data.bgString +"</p>";
            
            var peaksList = document.getElementById("fittedPeaksList-"+data.index.toString());
            peaksList.innerHTML = "";
            for(j=0;j<data.peakStrings.length;j++){
                var output = data.peakStrings[j];
                peaksList.innerHTML = peaksList.innerHTML + "<li class='list-group-item compact' id=\""+output+"\"><p class = 'peak-label'>"+output+"</p><img class='rmv-btn' src='/icons/file-x.svg' onclick='remove_peak_from_list(\""+ output +"\")'/></li>";
            }
            var knownPeaks = document.getElementById("userPeakMatches-"+i.toString()).getElementsByTagName("p");
            var matchSelects = document.getElementById("userPeakMatches-"+i.toString()).getElementsByClassName("peak-match-select");
            for(j=0;j<matchSelects.length;j++){
                var selectHTML = '';
                var knownCtr = parseFloat(knownPeaks[j].id);
                var minSep = 99;
                for(k=0;k<data.peakX.length;k++){
                    if(Math.abs(data.peakX[k] - knownCtr) < minSep){
                        minSep = Math.abs(data.peakX[k] - knownCtr);
                    }
                }
                for(k=0;k<data.peakStrings.length;k++){
                    if(Math.abs(data.peakX[k] - knownCtr) === minSep){
                        selectHTML += "<option selected value='"+data.peakX[k].toString()+"'>"+data.peakStrings[k]+"</option>"
                    }
                    else{
                        selectHTML += "<option value='"+data.peakX[k].toString()+"'>"+data.peakStrings[k]+"</option>"
                    }
                }
                matchSelects[j].innerHTML = selectHTML;
            }

            var plot = document.getElementById("ROI-"+i.toString());

            if(data.fitted){
                var fitTrace = {
                    x : data.curveX,
                    y : data.curveY,
                    mode : "lines",
                    name : "Fit"
                }
                var peakY = data.peakX.map(x => data.curveY[Math.floor((x - data.curveX[0])*100)]);
                var peakTrace = {
                    x : data.peakX,
                    y : peakY,
                    mode : "markers",
                    name : "Peaks" 
                }
                var bgTrace = {
                    x : data.ROIRange,
                    y : data.backgroundY,
                    mode : "lines",
                    name : "Background"
                }
                var allTraces = [bgTrace, fitTrace, peakTrace, dataTrace];
                while(plot.data.length > 0){
                    Plotly.deleteTraces(plot, 0);
                }
                Plotly.addTraces(plot, allTraces);
            }
            else{
                var allTraces = [dataTrace];
                while(plot.data.length > 0){
                    Plotly.deleteTraces(plot, 0);
                }
                Plotly.addTraces(plot, allTraces);
            }
            break;
        case "matchUpdate":
            document.getElementById("userPeakMatches-"+data.ROIIndex.toString()).getElementsByTagName('select')[data.matchIndex.toString()].value = data.newValue.toString();
            break;
        case "isotopeUpdateResponse":
            ws.close();       
            showRefreshModal();
            break;
        case "user":
            if(data.action == "joined"){
                document.getElementById("usersDiv").innerHTML += "<img class='userImage' id='"+data.username+"' src='https://www.gravatar.com/avatar/"+data.userHash+"' title='"+data.username+"'/>"
            }
        case "resultsGenerated":
            ws.close();
            showRedirectModal();
    }

};
function updatePeakEntry(i){
    var peakType = document.getElementById("peakSelect-"+i.toString()).value;
    var peaksList = document.getElementById("userPeakEntry-"+i.toString());
    var newInnerHTML = "";
    if(peakType !== "Select Peak Type"){
        window.entryFields["peaks"][peakType].forEach((field) => {newInnerHTML = newInnerHTML + "<li class='list-group-item'><p style='float:left;'>"+field+"</p><input class='form-control w-50 peak-entry' style='float:right;'/></li>"});
    }
    peaksList.innerHTML = newInnerHTML;
};

function add_peak_to_list(i){
    var peakType = document.getElementById("peakSelect-"+i.toString()).value;
    var peaksList = document.getElementById("userPeakEntry-"+i.toString());
    var peakProps = peaksList.getElementsByClassName("peak-entry");
    var propValues = [];
    for(j=0;j<peakProps.length;j++){
        propValues[j] = peakProps[j].value;
        peakProps[j].value = "";
    }
    var wsSendObj = {
        "type" : "entryReprRequest",
        "ROIIndex" : i,
        "class" : "peaks",
        "name" : peakType,
        "entryParams" : propValues
    }
    ws.send(JSON.stringify(wsSendObj));
};
function remove_peak_from_list(peakID){
    document.getElementById(peakID).remove();
}

function editBackground(i){
    var bgType = document.getElementById("backgroundSelect-"+i.toString()).value;
    var wsSendObj = {
        "type" : "entryReprRequest",
        "ROIIndex" : i,
        "class" : "backgrounds",
        "name" : bgType,
        "entryParams" : []
    }
    ws.send(JSON.stringify(wsSendObj));
}

function resetEnergyBounds(i){
    var entryList = document.getElementById("editRangeList-"+i.toString()).getElementsByTagName("input");
    entryList[0].value = window.originalEnergyBounds[i][0].toString();
    entryList[1].value = window.originalEnergyBounds[i][1].toString();
}

function reanalyze(i){
    var peaksList = document.getElementById("fittedPeaksList-"+i.toString());
    var peaks = peaksList.getElementsByClassName("peak-label");
    
    var existingPeaksToKeep = [];
    var newPeaksToAdd = [];
    for(j=0;j<peaks.length;j++){
        peak = peaks[j].innerText;
        if(window.newPeaks[i].hasOwnProperty(peak)){
            newPeaksToAdd.push(window.newPeaks[i][peak]);
        }
        else{
            existingPeaksToKeep.push(peak);
        }
    }
    var bgToAdd = window.newBackgrounds[i];
    
    outputObject = {"type" : "ROIUpdate","index":i};
    var entryList = document.getElementById("editRangeList-"+i.toString()).getElementsByTagName("input");
    if(entryList[0].value != window.originalEnergyBounds[i][0] || entryList[1].value != window.originalEnergyBounds[i][1]){
        try {
            outputObject["newRange"] = [parseFloat(entryList[0].value), parseFloat(entryList[1].value)];
        } catch (error) {
            return showErrorMessage("Please enter decimal numbers for the range.")
        }
    }
    if(existingPeaksToKeep !== []){
        outputObject["existingPeaks"] = existingPeaksToKeep;
    }
    if(newPeaksToAdd !== []){
        outputObject["newPeaks"] = newPeaksToAdd;
    }
    if(bgToAdd !== null){
        outputObject["background"] = bgToAdd;
    }
    console.log(JSON.stringify(outputObject));
    ws.send(JSON.stringify(outputObject));
}
//websocket stuff
function updateTitle(){
    var newTitle = document.getElementById("cdTitle").value;
    ws.send('{"type":"titleUpdate","newTitle":"'+newTitle+'"}');
}
function submitMatches(){
    var peakPairs = [];
    for(var i=0;i<numberPages;i++){
        var numKnownPeaks = document.getElementById("userPeakMatches-"+i.toString()).childElementCount;
        var knownPeakLabels = document.getElementById("userPeakMatches-"+i.toString()).getElementsByTagName("p");
        var peakMatches = document.getElementById("userPeakMatches-"+i.toString()).getElementsByTagName("select");
        var pairsInRegion = []
        for(var j=0;j<numKnownPeaks;j++){
            var pair = [parseFloat(peakMatches[j].value), parseFloat(knownPeakLabels[j].id)];
            pairsInRegion.push(pair);
        }
        peakPairs.push(pairsInRegion);
    }
    var outputObj = {
        "type" : "peakMatchSubmission",
        "pairs" : peakPairs
    }
    ws.send(JSON.stringify(outputObj));
}
function sendMatchUpdate(i,j){
    var newValue = document.getElementById("userPeakMatches-"+i.toString()).getElementsByTagName('select')[j.toString()].value;
    var outputObj = {
        "ROIIndex" : i,
        "matchIndex" : j,
        "newValue" : newValue
    };
    ws.send(JSON.stringify(outputObj));
}