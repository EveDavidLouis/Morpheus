var socket, host

if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
	host = 'ws://'+ window.location.host
} else {
	host = 'wss://pymorpheus.herokuapp.com'
};

function connect() {
	socketISS = new WebSocket(host + '/iss');
	
	socketISS.onmessage = function (msg) {
		var data = JSON.parse(msg.data)
		//console.log(data);
		document.querySelector('#ISS').innerHTML = JSON.stringify(data, null, 2); ;		
	};

}

window.onload = function () {
	connect();
};

window.onbeforeunload = function () {
	socket.close();
};
