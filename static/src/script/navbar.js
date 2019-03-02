/**
 * Get the navigation bar
 */

const name = "UCalgary";
const loginButton = '<button class="btn btn-primary" onclick="goToLogin()" type="submit">Login</button>';
const popUp =
    '<div class="modal fade" id="logoutAlert" tabindex="-1" data-backdrop="false" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">' +
    '  <div class="modal-dialog" role="document">' +
    '    <div class="modal-content" style="color:#212529">' +
    '      <div class="modal-header">' +
    '        <h5 class="modal-title" id="exampleModalLabel">Log out</h5>' +
    '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
    '          <span aria-hidden="true">×</span>' +
    '        </button>' +
    '      </div>' +
    '      <div class="modal-body">' +
    '        Are you sure you want to sign out ?' +
    '      </div>' +
    '      <div class="modal-footer">' +
    '        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>' +
    '        <button type="button" class="btn btn-primary" onclick="logOut()">Sign out</button>' +
    '      </div>' +
    '    </div>' +
    '  </div>' +
    '</div>';


$(function () {
    $("#navbar").html(getNavbar());
});


function goToLogin() {
    window.location = "/login";
}

function logOut() {
    localStorage.removeItem("session");
    window.location = "/";
}

function getNavbar() {

    var rightComponent = null;

    if (isAuthenticated()) {

        rightComponent =
            '    <ul class="collapse navbar-nav">' +
            '      <li class="nav-item dropdown">' +
            '        <a class="nav-link dropdown-toggle" style="font-size:16px" href="#" id="navbarDropdownMenuLink" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
            getUsername() +
            '        </a>' +
            '        <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarDropdownMenuLink">' +
            '          <a class="dropdown-item" href="/">Dashboard</a>' +
            '          <a class="dropdown-item" href="/logout" data-toggle="modal" data-target="#logoutAlert">Log out</a>' +
            '        </div>' +
            '      </li>' +
            '    </ul>' + popUp;

    } else {

        rightComponent = loginButton;

    }

    return '       <nav class="navbar navbar-expand-lg navbar-dark justify-content-between" style="color: white; background-color: #474747;">' +
        '           <a class="navbar-brand">' + name + '</a>' + rightComponent +
        '       </nav>';
}

function isAuthenticated() {
    return !!localStorage.getItem("session");
}

function getUsername() {
    data = $.parseJSON(localStorage.getItem("session"));
    return data.username;
}