var socketISS, socketCoPilot
var host

if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
	host = 'ws://'+ window.location.host
} else {
	host = 'wss://pymorpheus.herokuapp.com'
};

function connectISS() {
	socketISS = new WebSocket(host + '/iss');

	socketISS.onmessage = function (msg) {
		
		var data = JSON.parse(msg.data);
		console.log(data);
		document.querySelector('#ISS').innerHTML = JSON.stringify(data, null, 2);	
	};

}

function connectCoPilot() {
	socketCoPilot = new WebSocket(host + '/copilot',{
        headers : {
		'X-Session': create_UUID()	
	}
      	});

	socketCoPilot.onmessage = function (msg) {
		
		var data = JSON.parse(msg.data);
		console.log(data);
		document.querySelector('#CoPilot').innerHTML = JSON.stringify(data, null, 2);	
	};

}

window.onload = function () {
	connectISS();
	connectCoPilot();
};

window.onbeforeunload = function () {
	socketISS.close();
	socketCoPilot.close();
};

function create_UUID(){
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (dt + Math.random()*16)%16 | 0;
        dt = Math.floor(dt/16);
        return (c=='x' ? r :(r&0x3|0x8)).toString(16);
    });
    return uuid;
};
