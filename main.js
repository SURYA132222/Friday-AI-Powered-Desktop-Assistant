const chatForm = document.getElementById('chat-form');
const chatLog = document.getElementById('chat-log');
const userInput = document.getElementById('user-input');
const micButton = document.getElementById('mic-button');

// Speech recognition setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = false;

// Speak text
function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  speechSynthesis.speak(utterance);
}

// Handle mic click
micButton.addEventListener('click', () => {
  recognition.start();
});

recognition.onresult = (event) => {
  const speechToText = event.results[0][0].transcript;
  userInput.value = speechToText;
  sendMessage(speechToText);
};

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (message !== '') {
    sendMessage(message);
  }
});

// ── load greeting once page is ready ──
fetch("/greet")
  .then(r => r.json())
  .then(d => { addMsg(d.response, "bot"); speak(d.response); });


micBtn.addEventListener('click', () => {
  if (!recognition) { alert('Speech recognition not supported'); return; }
  micBtn.classList.add('active');          // already there
  recognition.start();
});
recognition.onend = () => micBtn.classList.remove('active');


function sendMessage(message) {
  appendMessage('You', message);
  userInput.value = '';

  fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(data => {
      appendMessage('Friday', data.response);
      speak(data.response);
    });
}

function appendMessage(sender, text) {
  const li = document.createElement('li');
  li.textContent = `${sender}: ${text}`;
  chatLog.appendChild(li);
  chatLog.scrollTop = chatLog.scrollHeight;
}
