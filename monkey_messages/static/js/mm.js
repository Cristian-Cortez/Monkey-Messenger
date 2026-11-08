// check local storage if api key was saved
document.addEventListener("DOMContentLoaded", () => {
    const savedKey = localStorage.getItem("monkey_api_key");
    if (savedKey) {
        document.getElementById("apiKey").value = savedKey;
        loadHistory();
    }
});

// saves api key to local storage
function saveApiKey() {
    const key = document.getElementById("apiKey").value.trim();
    localStorage.setItem("monkey_api_key", key);
    loadHistory();
}

// updates text count as the message is typed
function updateCounter() {
    const text = document.getElementById("messageText").value;
    document.getElementById("charCounter").innerText = `${text.length} / 1000`;
}

// helper that opens full-screen view for the clicked image
function openModal(imageSrc) {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImage");
    
    modalImg.src = imageSrc;
    modal.style.display = "flex";
}

// helper that closes modal when clicking background overlay or 'X' button
function closeModal(event) {
    // Only close if clicking outside the image container or on the close icon
    if (event.target.id === "imageModal" || event.target.classList.contains("modal-close")) {
        const modal = document.getElementById("imageModal");
        modal.style.display = "none";
    }
}

// sends POST request to api containing the message in the text box
async function sendMessage(e) {
    
    if (e) e.preventDefault();
    const apiKey = document.getElementById("apiKey").value.trim();
    const text = document.getElementById("messageText").value.trim();
    const imageInput = document.getElementById("imageInput");
    const imageFile = imageInput ? imageInput.files[0] : null;
    const statusEl = document.getElementById("status");
    const sendBtn = document.getElementById("sendBtn");

    // error checking
    if (!apiKey) {
        statusEl.innerText = "Error: API key required.";
        statusEl.style.color = "#e96963";
        return;
    }
    if (!text) {
        statusEl.innerText = "Error: Message cannot be empty.";
        statusEl.style.color = "#e96963";
        return;
    }

    const formData = new FormData();
    formData.append("text", text);
    if (imageFile) {
        formData.append("image", imageFile);
    }

    // loading message and disable send btn
    statusEl.innerText = "sending message...";
    statusEl.style.color = "#c49852";
    if (sendBtn) {
        sendBtn.disabled = true;
    }

    // trying to force loading message to show, i dont think this works
    await new Promise(resolve => requestAnimationFrame(() => setTimeout(resolve, 0)));

    try {
        // sends JSON with only api key in header and text in the body
        const response = await fetch("/api/monkey_messages/", {
            method: "POST",
            headers: {
                // "Content-Type": "application/json",
                "X-API-Key": apiKey
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            statusEl.innerText = "Message sent successfully!";
            statusEl.style.color = "#c668c4";
            document.getElementById("messageText").value = "";
            if (imageInput) imageInput.value = "";
            updateCounter();
            loadHistory();
        } else {
            statusEl.innerText = `Error: ${data.error || 'Failed to send'}`;
            statusEl.style.color = "#e96963";
        }
    } catch (err) {
        statusEl.innerText = "Network error occurred.";
        statusEl.style.color = "#e96963";
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}

// function to fetch history from api
async function loadHistory() {
    const apiKey = document.getElementById("apiKey").value.trim();
    const historyList = document.getElementById("historyList");

    if (!apiKey) {
        historyList.innerHTML = '<li class="history-item">Enter API Key to load history.</li>';
        return;
    }

    try {
        const response = await fetch("/api/monkey_messages/history/", {
            headers: { "X-API-Key": apiKey }
        });

        if (!response.ok) {
            historyList.innerHTML = '<li class="history-item">Failed to load history. Check API Key.</li>';
            return;
        }

        const data = await response.json();
        historyList.innerHTML = "";

        if (!data.messages || data.messages.length === 0) {
            historyList.innerHTML = '<li class="history-item">No messages sent yet.</li>';
            return;
        }

        // build messages stack
        data.messages.forEach(msg => {
            const li = document.createElement("li");
            li.className = "history-item";
            const date = new Date(msg.created_at).toLocaleString();

            // render image on the left (if present) and open modal if image present
            const imgHTML = msg.image_url 
                ? `<img src="${msg.image_url}" class="history-image" onclick="openModal('${msg.image_url}')" alt="Attached image">` 
                : '';

            // render text and timestamp inside a content container on the right
            li.innerHTML = `
                ${imgHTML}
                <div class="history-content">
                    <div class="history-text">${msg.text || ''}</div>
                    <div class="history-date">${date}</div>
                </div>
            `;

            historyList.appendChild(li);
        });
    } catch (err) {
        historyList.innerHTML = '<li class="history-item">Error fetching history.</li>';
    }
}