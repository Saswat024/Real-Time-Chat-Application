from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #messages { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
        #messageInput { width: 70%; padding: 10px; }
        #sendButton { padding: 10px 20px; }
        .message { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Simple Chat Room</h1>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type your message...">
    <button id="sendButton">Send</button>

    <script>
        const username = prompt("Enter your username: ") || "Anonymous";
        const room = prompt("Enter room name: ") || "General";
        const ws = new WebSocket(`wss://${window.location.host}/ws/${username}/${room}`);
        const messages = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        document.querySelector('h1').textContent = `Chat Room: ${room}`;

        // Receive messages
        ws.onmessage = function(event) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            messageDiv.textContent = event.data;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        };

        // Send message
        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                ws.send(message);
                messageInput.value = '';
            }
        }

        sendButton.onclick = sendMessage;
        messageInput.onkeypress = function(e) {
            if (e.key === 'Enter') sendMessage();
        }
    </script>
</body>
</html>
"""

app = FastAPI()

chat_rooms: dict = {}


@app.get("/")
async def get_chat_page():
    return HTMLResponse(content=html_content)


@app.websocket("/ws/{username}/{room}")
async def websocket_endpoint(websocket: WebSocket, username: str, room: str):
    await websocket.accept()

    if room not in chat_rooms:
        chat_rooms[room] = []

    connection_info = {"websocket": websocket, "username": username, "room": room}
    chat_rooms[room].append(connection_info)

    await broadcast_to_room(f"{username} joined {room}.", room)
    await broadcast_to_room(f"Users in {room}: {get_room_users(room)}.", room)

    try:
        while True:
            data = await websocket.receive_text()
            message = f"[{room}] {username}: {data}"
            await broadcast_to_room(message, room)

    except WebSocketDisconnect:
        chat_rooms[room].remove(connection_info)
        await broadcast_to_room(f"{username} left the {room}.", room)

        if not chat_rooms[room]:
            del chat_rooms[room]


async def broadcast_to_room(message: str, room: str):
    if room in chat_rooms:
        for connection_info in chat_rooms[room][:]:
            try:
                await connection_info["websocket"].send_text(message)
            except:
                chat_rooms[room].remove(connection_info)


def get_room_users(room: str) -> str:
    if room in chat_rooms:
        users = [conn["username"] for conn in chat_rooms[room]]
        return ", ".join(users)

    return "No users."


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8080)
