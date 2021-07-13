var linearScaleIcon = {
    'name' : "linear-scale",
    'svg' : '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="isolation:isolate" viewBox="0 0 100 100" width="100pt" height="100pt"><defs><clipPath id="_clipPath_PryGnnTZIQ4lIJ2Dby2iX67e7hrcObL8"><rect width="100" height="100"/></clipPath></defs><g clip-path="url(#_clipPath_PryGnnTZIQ4lIJ2Dby2iX67e7hrcObL8)"><line x1="9" y1="8" x2="8" y2="92" vector-effect="non-scaling-stroke" stroke-width="3" stroke="rgb(0,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/><line x1="8" y1="92" x2="92" y2="92" vector-effect="non-scaling-stroke" stroke-width="3" stroke="rgb(0,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/><line x1="11" y1="89" x2="92" y2="7" vector-effect="non-scaling-stroke" stroke-width="2" stroke="rgb(255,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/></g></svg>'
};
var logScaleIcon = {
    'name' : 'log-scale',
    'svg' : '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="isolation:isolate" viewBox="0 0 100 100" width="100pt" height="100pt"><defs><clipPath id="_clipPath_yr8WnDDLyZc7YlyCSm2ThMbIIFAQCXIn"><rect width="100" height="100"/></clipPath></defs><g clip-path="url(#_clipPath_yr8WnDDLyZc7YlyCSm2ThMbIIFAQCXIn)"><line x1="9" y1="8" x2="8" y2="92" vector-effect="non-scaling-stroke" stroke-width="3" stroke="rgb(0,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/><line x1="8" y1="92" x2="92" y2="92" vector-effect="non-scaling-stroke" stroke-width="3" stroke="rgb(0,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/><path d=" M 10 90 L 13.644 80.862 L 20.933 67.662 L 32.778 53.446 L 48.267 39.231 L 64.667 30.092 L 80.156 25.015 L 92 24" fill="none" vector-effect="non-scaling-stroke" stroke-width="2" stroke="rgb(255,0,0)" stroke-linejoin="miter" stroke-linecap="square" stroke-miterlimit="3"/></g></svg>'
};
var universalPlotConfig = {
    responsive : true,
    modeBarButtonsToAdd : [
        {
            "name" : "Linear Scale",
            "icon" : linearScaleIcon,
            click : function(gd){
                if(gd.data.length === 1){
                    var newLayout = {
                        yaxis: {
                            type: 'linear',
                            title: "Counts Per Second",
                            autorange: true
                        }
                    }
                }
                else if(gd.data.length === 2){
                    var newLayout = {
                        yaxis: {
                            type: 'linear',
                            title: "Counts Per Second",
                            autorange: true
                        },
                        yaxis2: {
                            type: 'linear',
                            autorange: true,
                            domain: [0, 1],
                            anchor: "x2"
                        }
                    }
                }
                Plotly.relayout(gd,newLayout)
            }
        },
        {
            "name" : "Log Scale",
            "icon" : logScaleIcon,
            click : function(gd){
                if(gd.data.length === 1){
                    var newLayout = {
                        yaxis: {
                            type: 'log',
                            title: "Counts Per Second",
                            autorange: true
                        }
                    }
                }
                else if(gd.data.length === 2){
                    var newLayout = {
                        yaxis: {
                            type: 'log',
                            title: "Counts Per Second",
                            autorange: true
                        },
                        yaxis2: {
                            type: 'log',
                            autorange: true,
                            domain: [0, 1],
                            anchor: "x2"
                        }
                    }
                }
                Plotly.relayout(gd,newLayout)
            }
        }
    ],
    modeBarButtonsToRemove : ['select2d','lasso2d']
};
function findClosest(arr, target)
{
    let n = arr.length;
 
    // Corner cases
    if (target <= arr[0])
        return arr[0];
    if (target >= arr[n - 1])
        return arr[n - 1];
    let l = 0;
    let u = n;
    let i = Math.floor((l+u)/2);
    while(target < arr[i-1] || target > arr[i+1]){
        if(target > arr[i]){
            l = i + 1;
        }
        else if(target < arr[i]){
            u = i - 1;
        }
        else{
            return i;
        }
        i = Math.floor((l+u)/2);
        if(i <= 2 || i >= n - 2){
            break;
        }
    }
    return i;
}
function updateCompareModal(){
    var file1 = document.getElementById("file1Select").value;
    var file2 = document.getElementById("file2Select").value;
    var filename1 = file1.split("\\")[file1.split("\\").length - 1]
    var filename2 = file2.split("\\")[file2.split("\\").length - 1]
    var file1Index = filesList.indexOf(file1);
    var file2Index = filesList.indexOf(file2);
    var rangeSelectValue = document.getElementById("compRangeSelect").value;
    if(rangeSelectValue == "custom"){
        var minEnergy = parseFloat(document.getElementById("lowerBoundInput").value);
        var maxEnergy = parseFloat(document.getElementById("upperBoundInput").value);
    }
    else{
        var range = rangeSelectValue.split(",")
        var minEnergy = parseFloat(range[0]);
        var maxEnergy = parseFloat(range[1]);
    }
    var plot1 = document.getElementById("file-"+file1Index);
    var plot2 = document.getElementById("file-"+file2Index);
    var xData1 = plot1.data[0].x.slice(findClosest(plot1.data[0].x,minEnergy), findClosest(plot1.data[0].x,maxEnergy));
    var xData2 = plot2.data[0].x.slice(findClosest(plot2.data[0].x,minEnergy), findClosest(plot2.data[0].x,maxEnergy));
    var yData1 = plot1.data[0].y.slice(findClosest(plot1.data[0].x,minEnergy), findClosest(plot1.data[0].x,maxEnergy));
    var yData2 = plot2.data[0].y.slice(findClosest(plot2.data[0].x,minEnergy), findClosest(plot2.data[0].x,maxEnergy));
    var overlayGraphs = document.getElementById("overlayCheckbox").checked;
    if(overlayGraphs){
        var data = [
            {
                x : xData1,
                y : yData1,
                mode : 'lines',
                name: filename1
            },
            {
                x: xData2,
                y: yData2,
                mode: 'lines',
                name: filename2
            }
        ];
        var layout = {
            title: "Comparison ("+minEnergy+"-"+maxEnergy+" keV)",
            showlegend: false,
            xaxis: {
                "title" : "Energy (keV)"
            },
            yaxis: {
                "title" : "Counts Per Second"
            }
        };
        Plotly.react(document.getElementById("compareSpectraPlot"),data,layout,universalPlotConfig);
    }
    else{
        var data = [
            {
                x : xData1,
                y : yData1,
                mode : 'lines',
                name: filename1,
                xaxis : "x",
                yaxis : "y"
            },
            {
                x: xData2,
                y: yData2,
                mode: 'lines',
                name: filename2,
                xaxis : "x2",
                yaxis : "y2"
            }
        ];
        var layout = {
            title: "Comparison ("+minEnergy+"-"+maxEnergy+" keV)",
            showlegend: false,
            xaxis: { 
              domain: [0,0.48] ,
              title: "Energy (keV)"
            },
            yaxis: { 
              domain: [0,1],
              title: "Counts Per Second"
            },
            xaxis2: {
              domain: [0.52, 1],
              anchor: "y2",
              title: "Energy (keV)"
            },
            yaxis2: {
              domain: [0, 1],
              anchor: "x2"
            },
            annotations: [
              {
                text: "File 1",
                showarrow: false,
                x: 0,
                xref: "x domain",
                y: 1.1,
                yref: "y domain"
              },
              {
                text: "File 2",
                showarrow: false,
                x: 0,
                xref: "x2 domain",
                y: 1.1,
                yref: "y2 domain"
              }
            ]
          };
          Plotly.react(document.getElementById("compareSpectraPlot"),data,layout,universalPlotConfig);
    }
}


function zoomToRegion(i){
    var selectObject = document.getElementById("zoomToRegion-"+i.toString());
    if(selectObject.value === ""){
        var plot = document.getElementById("file-"+i.toString());
        var xdata = plot.data[0].x
        var newLayout = {
            xaxis : {
                title: plot.layout.xaxis.title,
                range: [xdata[0], xdata[xdata.length - 1]]
            },
            yaxis : {
                title: plot.layout.yaxis.title,
                type : plot.layout.yaxis.type,
                range : [0, Math.max(...plot.data[0].y)*1.1]
            }
        };
    }
    var values = selectObject.value.split(",");
    var plot = document.getElementById("file-"+i.toString());
    var dataRange = plot.data[0].y.slice(parseInt(values[2]), parseInt(values[3]));
    document.getElementById("minEnergyInput-"+i.toString()).value = values[0];
    document.getElementById("maxEnergyInput-"+i.toString()).value = values[1];
    var newLayout = {
        xaxis : {
            title: plot.layout.xaxis.title,
            range: [parseFloat(values[0]), parseFloat(values[1])]
        },
        yaxis : {
            title: plot.layout.yaxis.title,
            type : plot.layout.yaxis.type,
            range : [0, Math.max(...dataRange)*1.1]
        }
    };
    Plotly.relayout(plot, newLayout);
}

function updateRange(i){
    try {
        var minEnergy = parseFloat(document.getElementById("minEnergyInput-"+i.toString()).value);
        var maxEnergy = parseFloat(document.getElementById("maxEnergyInput-"+i.toString()).value);
    } catch (error) {
        showErrorMessage("Please enter decimal numbers for the data range.");
    }
    
    var plot = document.getElementById("file-"+i.toString());
    var lowerIndex = findClosest(plot.data[0].x, minEnergy);
    var upperIndex = findClosest(plot.data[0].x, maxEnergy);
    var dataRange = plot.data[0].y.slice(lowerIndex, upperIndex);
    var myLayout = {
        xaxis : {
            title: plot.layout.xaxis.title,
            range: [minEnergy, maxEnergy]
        },
        yaxis : {
            title: plot.layout.yaxis.title,
            type : plot.layout.yaxis.type,
            range : [0, Math.max(...dataRange)*1.5]
        }
    };
    Plotly.relayout(plot, myLayout);
}

addedIsotopes = [];
removedIsotopes = [];

function addIsotope(isotope){
    if(addedIsotopes.includes(isotope)){
        return null
    }
    else if(removedIsotopes.includes(isotope)){
        for(var i=0;i<removedIsotopes.length;i++){
            if(removedIsotopes[i] === isotope){
                removedIsotopes.splice(i,1);
                break;
            }
        }
    }
    else{
        addedIsotopes.push(isotope);
    }
    newElement = "<p class='iso-label'>" + isotope  + "</p>"
    removeButton = '<img class="rmv-btn" src="/icons/file-x.svg" onclick="removeIsotope('+"'"+isotope+"'"+')">'
    var ufl = document.getElementById("selectedIsotopes");
    ufl.innerHTML += "<li class='list-group-item w-50' id='"+isotope+"'>" + newElement + removeButton +"</li>";
    document.getElementById("search-input").value = "";
    applyFilter();
}
function removeIsotope(name){
    document.getElementById(name).remove();
    if(removedIsotopes.includes(name)){
        return null;
    }
    else if(addedIsotopes.includes(name)){
        for(var i=0;i<addedIsotopes.length;i++){
            if(addedIsotopes[i] === name){
                addedIsotopes.splice(i,1);
                break;
            }
        }
    }
    else{
        removedIsotopes.push(name);
    }
}
function applyFilter(){
    var input = document.getElementById("search-input");
    var filter = input.value.toUpperCase();
    ul = document.getElementById("allIsotopes");
    li = ul.getElementsByTagName('li');
    for (i = 0; i < li.length; i++) {
        a = li[i].getElementsByClassName("iso-label")[0];
        txtValue = a.textContent || a.innerText;
        if (filter.length == 0 || !(txtValue.toUpperCase().indexOf(filter) > -1)) {
        li[i].style.display = "none";
        } else {
        li[i].style.display = "";
        }
    }
}

function updateShownTimes(){
    var times = NAATimes[filesList.indexOf(document.getElementById("timeFileSelect").value)];
    document.getElementById("irrTimeInput").value = times[0].toString();
    document.getElementById("waitTimeInput").value = times[1].toString();
    document.getElementById("countTimeInput").value = times[2].toString();
}

var wsUrl = window.location.href.toString().replace("http","ws").replace("view","ws");
var ws = new WebSocket(wsUrl);
ws.onmessage = function (event) {
    var data = JSON.parse(event.data);
    switch(data.type){
        case "titleUpdate":
            document.getElementById("cdTitle").value = data.newTitle;
            break;
        case "isotopeUpdateResponse":
            var currentIsotopes = data.currentIsotopes;
            var newInnerHTML = "";
            for(var i=0;i<currentIsotopes.length;i++){
                var isotope = currentIsotopes[i];
                var newElement = "<p class='iso-label'>" + isotope  + "</p>";
                var removeButton = '<img class="rmv-btn" src="/icons/file-x.svg" onclick="removeIsotope('+"'"+isotope+"'"+')">';
                newInnerHTML += "<li class='list-group-item w-50' id='"+isotope+"'>" + newElement + removeButton +"</li>";
            }
            document.getElementById("selectedIsotopes").innerHTML = newInnerHTML;
            var newSelectHTML = "";
            for(var i=0;i<data.ROIRanges.length;i++){
                newSelectHTML += "<option value='"+data.ROIRanges[i][0]+","+data.ROIRanges[i][1]+","+data.ROIIndicies[i][0].toString()+","+data.ROIIndicies[i][1].toString()+"'>"+data.ROIRanges[i][0]+"-"+data.ROIRanges[i][1]+" keV ("+data.ROIIsotopes[i]+")</option>"
            }
            
            document.getElementById("compRangeSelect").innerHTML = "<option selected value='custom'>Custom Range</option>" + newSelectHTML;
            for(var i=0;i<filesList.length;i++){
                document.getElementById("zoomToRegion-"+i.toString()).innerHTML = "<option selected value=''>Whole Spectrum</option>" + newSelectHTML;
            }

            break;
        case "NAATimeUpdate":
            NAATimes[data.fileIndex] = data.times;
            break;
    }
};

function startAnalysis(){
    if(document.getElementById("selectedIsotopes").childElementCount > 0){
        window.location.replace(window.location.href.replace("/view","/edit"))
    }
    else{
        showROIModal();
    }
}

function submitROIs(){
    var wsObj = {
        "type" : "isotopeUpdate",
        "addedIsotopes" : addedIsotopes,
        "removedIsotopes" : removedIsotopes
    }
    ws.send(JSON.stringify(wsObj));
}

function sendNAATimes(){
    try {
        var irrTime = parseFloat(document.getElementById("irrTimeInput").value);
        var waitTime = parseFloat(document.getElementById("waitTimeInput").value);
        var countTime = parseFloat(document.getElementById("countTimeInput").value);
    } catch (error) {
        showErrorMessage("Please enter times as floats.");
    }
    var allTimes = [irrTime, waitTime, countTime];
    var wsObj = {
        "type" : "NAATimeUpdate",
        "fileIndex" : filesList.indexOf(document.getElementById("timeFileSelect").value),
        "times" : allTimes
    };
    ws.send(JSON.stringify(wsObj));
}

function updateTitle(){
    var newTitle = document.getElementById("cdTitle").value;
    ws.send('{"type":"titleUpdate","newTitle":"'+newTitle+'"}');
}