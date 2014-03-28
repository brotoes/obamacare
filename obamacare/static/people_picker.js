
var element;


function close_peoplePicker(value){
	console.log(element);
	document.getElementById(element).value=value;
	$(".overlay").hide();	
}


function open_peoplepicker(elmid){
	element = elmid;
	$(".overlay").show();
	get_people('d');
}
function populate(data){
	people_data = eval("("+data+")").data;
	console.log(people_data);
	body = document.getElementById("table1").getElementsByTagName('tbody')[0]
	body.innerHTML="";
	for (i=0;i<people_data.length;i++){
		console.log(people_data[i]);
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
