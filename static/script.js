const form = document.getElementById('chat-form');
const chatLog = document.querySelector('.chat-log');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = document.getElementById('message').value;
    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    });
    const data = await response.json();

    // Display user message
    const userMessage = document.createElement('div');
    userMessage.classList.add('user-message');
    userMessage.innerText = message;
    chatLog.appendChild(userMessage);

    // Display bot response
    const botMessage = document.createElement('div');
    botMessage.classList.add('bot-message');
    botMessage.innerText = data.response;
    chatLog.appendChild(botMessage);

    // Clear input field
    document.getElementById('message').value = '';

    // Scroll to bottom of chat log
    chatLog.scrollTop = chatLog.scrollHeight;
});
