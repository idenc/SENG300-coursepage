
function goToLogin(){
    window.location = "././Layouts/Login/Login.html";
}

function getNavbar(name){

  var html = '<script src="/Login.js"/><nav class="navbar navbar-dark justify-content-between" style="color: white; background-color: #474747;">'+
  '<a class="navbar-brand">'
            +name+
            '</a><button class="btn btn-primary" onclick="goToLogin()" type="submit">Login</button></nav>';

  return html;
}
