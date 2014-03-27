
var element;


function close_peoplePicker(value){
	console.log(element);
	document.getElementById(element).value=value;
	$(".overlay").hide();	
}


function open_peoplepicker(elmid, role){
	element = elmid;
	$(".overlay").show();
	get_people(role);
}



function populate(data){
	console.log(data);
	people_data = eval("("+data+")").data;
	
	body = document.getElementById("table1").getElementsByTagName('tbody')[0]
	body.innerHTML="";
	for (i=0;i<people_data.length;i++){
		var row = document.createElement("tr");
		row.className = (i%2==0) ? "even_zebra" : "odd_zebra";
		row.pid = people_data[i][0];
		row.onclick = function (){
			close_peoplePicker(this.pid);
			$(".overlay").hide();	
		};
		for (j=0;j<people_data[0].length;j++){
			cell = document.createElement("td");
			cell.className="picker";
			cell.innerHTML = people_data[i][j];
			row.appendChild(cell);
		}
		body.appendChild(row);
		

	}
}

$(document).click(function(event) { 
	console.log(event.target);
    if($(event.target).get(0).tagName != "INPUT" && $(event.target).parents().index($('#overlay')) == -1) {
        if($('#overlay').is(":visible")) {
            $('#overlay').hide()
        }
    }        
})

function get_people(role){
	console.log("get people called");
	if (window.XMLHttpRequest) { // Mozilla, Safari, ...
		httpRequest = new XMLHttpRequest();
	} else if (window.ActiveXObject) { // IE
		try {
			httpRequest = new ActiveXObject("Msxml2.XMLHTTP");
		} 
		catch (e) {
			alert("Image view: unsupported browser");
			try {
	  			httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
			} 
			catch (e) {}
		}
	}
    if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
    }
    console.log("ajax object created");
    httpRequest.onreadystatechange = function (){
    	if (httpRequest.readyState === 4) {
    		
      		if (httpRequest.status === 200) {
        		populate(httpRequest.responseText);
        		return httpRequest.responseText;
      	} 	else {
        		alert('There was a problem with the request.');
      		}
    	}
    };
    httpRequest.open('GET', '/p?r=' + role);
    httpRequest.send();
    return httpRequest;
}
