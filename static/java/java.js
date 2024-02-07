<script type="text/javascript">
  var socketio = io();

  const messages = document.getElementById("messages");

  const createMessage = (name, msg) => {
    const content = `
    <div class="text">
        <span>
            <strong>${name}</strong>: ${msg}
        </span>
        <span class="muted">
            ${new Date().toLocaleString()}
        </span>
    </div>
    `;
    messages.innerHTML += content;
  };

  socketio.on("message", (data) => {
    createMessage(data.name, data.message);
  });

  socketio.on("file_uploaded", (data) => {
    const msg = `<a href="/uploads/${data.filename}" target="_blank">File uploaded: ${data.filename}</a>`;
    createMessage("System", msg);
  });

  // Listening for clear_messages event from the server
  socketio.on("clear_messages", () => {
    messages.innerHTML = ''; // Clear the messages div
  });

  const sendMessage = () => {
    const message = document.getElementById("message");
    if (message.value === "") return;
    socketio.emit("message", { data: message.value });
    message.value = "";
  };

  const uploadFile = () => {
    const formData = new FormData();
    const fileInput = document.getElementById("file-input");
    if(fileInput.files.length === 0) return; // No file chosen
    formData.append('file', fileInput.files[0]);

    fetch('/upload', {
      method: 'POST',
      body: formData,
    }).then(response => {
      if(response.ok) {
        console.log("File uploaded successfully.");
        fileInput.value = ''; // Reset file input
        // Optionally, emit an event or refresh messages to show the uploaded file immediately
      }
    }).catch(error => {
      console.error("Error uploading file:", error);
    });
  };

  // Handle clear messages button click
  document.getElementById("clear-btn").addEventListener("click", function() {
    fetch('/clear-messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // If using CSRF tokens, you need to include the CSRF token in the request headers
      },
      // No need to send room info, as it's stored in session on the server
    }).then(response => {
      if(response.ok) {
        console.log("Messages cleared.");
        // The server will emit a clear_messages event, which is handled above
      }
    }).catch(error => {
      console.error("Error clearing messages:", error);
    });
  });
</script>
