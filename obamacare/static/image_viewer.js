var images = [];

function get_images(rec_id){
	console.log("get images called");
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
        		console.log(httpRequest.responseText);
        		loadImages(createImageUrls(httpRequest.responseText));
        		console.log(httpRequest)
        		return httpRequest.responseText;
      	} 	else {
        		alert('There was a problem with the request.');
      		}
    	}
    };
    httpRequest.open('GET', '/images/' + rec_id);
    httpRequest.send();
}

function createImageUrls(img_ids){
	urls = []
	img_ids = eval('(' + img_ids + ')');
	if (img_ids == null)
		return null;
	console.log("ids: " + img_ids);
	console.log(img_ids.length)
	for (var i =0;i< img_ids.length;i++){
		console.log(i)
		urls.push("/i/" + img_ids[i][0]);
	}
	console.log("urls: " + urls);
	return urls; 
}

function loadImages(urls){
	cont = document.getElementById("imageviewer");
	if (cont == null || urls == null){
		console.log("no images");
		return null;
	}
	for (var i=0;i<urls.length;i++){
		img = document.createElement("img");
		img.src=urls[i];
		cont.appendChild(img);
	}
}