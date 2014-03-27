
var element;


function close_peoplePicker(value){
	console.log(element);
	document.getElementById(element).value=value;
	$(".overlay").hide();	
}


function open_peoplepicker(elmid){
	element = elmid;
	$(".overlay").show();

}
$(document).click(function(event) { 
	console.log(event.target);
    if($(event.target).get(0).tagName != "INPUT" && $(event.target).parents().index($('#overlay')) == -1) {
        if($('#overlay').is(":visible")) {
            $('#overlay').hide()
        }
    }        
})