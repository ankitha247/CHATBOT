const API_URL = "http://127.0.0.1:8000/chat";

const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// 👇 New: store session id from backend
let sessionId = null;

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.classList.add("message", sender); // "user" or "bot"
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Show user message
    addMessage(message, "user");
    userInput.value = "";
    userInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = "Thinking...";

    try {
        // 👇 Build request body
        let body = { message: message };
        if (sessionId) {
            body.session_id = sessionId;
        }

        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const data = await response.json();

        // 👇 Save session_id returned from backend
        if (data.session_id) {
            sessionId = data.session_id;
        }

        addMessage(data.reply, "bot");
    } catch (err) {
        console.error(err);
        addMessage("Oops, something went wrong. Please try again.", "bot");
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        sendBtn.textContent = "Send";
        userInput.focus();
    }
}

// Button click
sendBtn.addEventListener("click", sendMessage);

// Enter key (Shift+Enter for new line)
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
