const sendBtn = document.getElementById('sendBtn');
const userInput = document.getElementById('userInput');
const chatHistory = document.getElementById('chatHistory');
const newChatBtn = document.getElementById('newChatBtn');
const chatList = document.getElementById('chatList');


function appendMessage(sender, text) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', sender);
  messageDiv.textContent = text;
  chatHistory.appendChild(messageDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}


async function sendMessage() {
  const inputText = userInput.value.trim();
  if (inputText === "") return;
  

  appendMessage("user", inputText);
  userInput.value = "";
  
  try {
    const response = await fetch('http://127.0.0.1:5000/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: inputText })
    });
    const summaries = await response.json();
    let combinedSummary = "";
    summaries.forEach(article => {
      combinedSummary += `Source: ${article.source}\nURL: ${article.final_url}\nSummary: ${article.summary}\n\n`;
    });
    appendMessage("bot", combinedSummary);
  } catch (error) {
    console.error(error);
    appendMessage("bot", `Error fetching summary. ${error}`);
  }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', function(event) {
  if (event.key === "Enter") sendMessage();
});
newChatBtn.addEventListener('click', () => chatHistory.innerHTML = "");
