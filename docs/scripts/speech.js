//host
var host, session

// UI comp
const startBtn = document.createElement("button");
startBtn.innerHTML = "Start listening";
const result = document.createElement("div");
const processing = document.createElement("p");
document.body.append(startBtn);
document.body.append(result);
document.body.append(processing);

// speech to text
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let toggleBtn = null;

if (typeof SpeechRecognition === "undefined") {

  startBtn.remove();
  result.innerHTML = "<b>Browser does not support Speech API. Please download latest chrome.<b>";

} else {

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.onresult = event => {
    const last = event.results.length - 1;
    const res = event.results[last];
    const text = res[0].transcript;

    //last result is final
    if (res.isFinal) {
      processing.innerHTML = "processing ....";

      const response = process(text);
      const p = document.createElement("p");
      p.innerHTML = `You said: ${text} </br>Copilot said: ${response}`;
      processing.innerHTML = "";
      result.appendChild(p);

      // text to speech
      socketCoPilot.send(response);

    //last result is not final
    } else {
      processing.innerHTML = `listening: ${text}`;
    }

  }

  let listening = false;
  toggleBtn = () => {
      recognition.stop();
    if (listening) {
      startBtn.textContent = "Start listening";
    } else {
      recognition.start();
      startBtn.textContent = "Stop listening";
    }
    listening = !listening;
  };
  startBtn.addEventListener("click", toggleBtn);

}

// processor
function process(rawText) {
  let text = rawText.replace(/\s/g, "");
  text = text.toLowerCase();
  let response = null;
  switch(text) {
    case "hello":
      response = "hi, how are you doing?"; break;
    case "what'syourname":
      response = "My name is Copilot.";  break;
    case "howareyou":
      response = "I'm good."; break;
    case "whattimeisit":
      response = new Date().toLocaleTimeString(); break;
    case "you can stop":
      response = "Bye!!";
      toggleBtn();
  }
  if (!response) {
    //window.open(`http://google.com/search?q=${rawText.replace("search", "")}`, "_blank");
    return rawText;
  }
  return response;
}
// speaker
function speak(text) {
  speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}

if (window.location.hostname == '0.0.0.0' || window.location.hostname == 'localhost'){
  host = 'ws://'+ window.location.host
} else {
  host = 'wss://pymorpheus.herokuapp.com'
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

function connectCoPilot() {
  socketCoPilot = new WebSocket(host + '/copilot/' + session);
  socketCoPilot.onmessage = function (msg) {
    
    var data = JSON.parse(msg.data);
    console.log(data);
    document.querySelector('#CoPilot').innerHTML = JSON.stringify(data.response, null, 2);
    speak(data.response)
  };

}

window.onload = function () {
  session = create_UUID();
  connectCoPilot();
};

window.onbeforeunload = function () {
  socketCoPilot.close();
};