$(".button").onsubmit(function(){
    var b1=$("this");
    if(b1.val()==""){
    return false;
    b1.css("border-color","red");
}
);
