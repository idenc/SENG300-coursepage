function login(username, password){
    var a_username = "admin";
    var a_password = "12345";

    if (username == a_username && password == a_password){
        var session = "12345"
        window.localStorage.setItem("session", session);
        window.location = "../../index.html";
    }
}