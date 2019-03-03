/**
 * Validate username && password
 * Retrieve token from backend and store to local storage
 */


const loginURL = "/login";
const home = "/";
const decline = "The username or the password is incorrect";
const inputUsername = "#inputUsername";
const inputPassword = "#inputPassword";
const reject = "#declineSession";

$(function () {
    $("button[type='submit']").click(function (ev) {
        ev.preventDefault();
        var username = $(inputUsername).val();
        var password = $(inputPassword).val();
        if (username.length > 0 && password.length > 0) {
            loginSubmit(username, password);
        }
    });
});

function loginSubmit(i_username, i_password) {
    $.post(loginURL, {
        username: i_username,
        password: i_password,
    }, function (data) {
        result = $.parseJSON(data);
        if (result.token) {
            createSession(data);
        } else {
            declineSession();
        }
    });
}

function declineSession() {
    $(reject).text(decline);
}

function createSession(data) {
    localStorage.setItem("session", data);
    window.location = home;
}
