function setCookie(cname, cvalue, exdays) {
	const d = new Date();
	d.setTime(d.getTime() + (exdays*24*60*60*1000));
	let expires = "expires="+ d.toUTCString();
	document.cookie = cname + "=" + cvalue + ";" + expires + ";SameSite=Strict;path=/";
}

function getCookie(cname) {
	let name = cname + "=";
	let decodedCookie = decodeURIComponent(document.cookie);
	let ca = decodedCookie.split(';');
	for(let i = 0; i <ca.length; i++) {
		let c = ca[i];
		while (c.charAt(0) == ' ') {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return "";
}

function deleteCookie(cname) {
	document.cookie = cname + "=; SameSite=Strict; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

function RegisterAccount() {
    let login = document.getElementById("login").value;
    let password = document.getElementById("password").value;
	let status = document.getElementById("status");

	status.innerHTML = "Registering...";

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
		if (this.readyState != 4) return;

		status.innerHTML = xhr.responseText;

        if( this.status == 200 ) {
			setCookie("l", login, 180);
			setCookie("p", password, 180);
			window.location.href = window.location.href.split('/').slice(0, -1).join('/'); // Go back one
        }
    }

    xhr.open("POST", window.location.href);
    xhr.send(JSON.stringify( { login: login, password: password, skin1: dm_skin, skin2: tdm_skin } ))
}

function LoginAccount() {
    let login = document.getElementById("login").value;
    let password = document.getElementById("password").value;
	let status = document.getElementById("status");

	status.innerHTML = "Logging in...";

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
		if (this.readyState != 4) return;
		status.innerHTML = xhr.responseText;
	
        if( this.readyState == 4 && this.status == 200 ) {
			if( this.status == 200 ) {
				setCookie("l", login, 180);
				setCookie("p", password, 180);
				window.location.href = window.location.href.split('/').slice(0, -1).join('/'); // Go back one
			}
        }
    }

    xhr.open("POST", window.location.href);
    xhr.send(JSON.stringify( { login: login, password: password } ))
}

function SaveAccount() {
	let login = getCookie("l");
	let password = getCookie("p");
	let nickname = document.getElementById("nickname").value;
	let status = document.getElementById("status");

	status.innerHTML = "Saving...";

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
		if (this.readyState != 4) return;

		status.innerHTML = xhr.responseText;
    }

    xhr.open("POST", window.location.href);
    xhr.send(JSON.stringify( { login: login, password: password, display: nickname, skin1: dm_skin, skin2: tdm_skin } ))
}

function LogOutAccount() {
	deleteCookie("l");
	deleteCookie("p");
	window.location.href = window.location.href.split('/').slice(0, -1).join('/'); // Go back one
}