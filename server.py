from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Chat</title>
    <style>
        :root {
            --primary-color: #4a6fa5;
            --secondary-color: #6c8fc7;
            --background-color: #f5f7fa;
            --message-bg: #ffffff;
            --user-message-bg: #e3f2fd;
            --text-color: #333333;
            --text-light: #666666;
            --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
            min-height: 100vh;
            color: var(--text-color);
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: var(--shadow);
            overflow: hidden;
            height: 90vh;
            display: flex;
            flex-direction: column;
        }

        #messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: var(--background-color);
            scroll-behavior: smooth;
        }

        .message {
            margin-bottom: 16px;
            display: flex;
            flex-direction: column;
            max-width: 80%;
            animation: fadeIn 0.3s ease-out;
        }

        .message.user-message {
            align-self: flex-end;
            align-items: flex-end;
        }

        .message.other-message {
            align-self: flex-start;
            align-items: flex-start;
        }

        .message-content {
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.4;
            font-size: 15px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .user-message .message-content {
            background-color: var(--primary-color);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .other-message .message-content {
            background-color: var(--message-bg);
            color: var(--text-color);
            border-bottom-left-radius: 4px;
        }

        .message-sender {
            font-size: 12px;
            color: var(--text-light);
            margin-bottom: 4px;
            padding: 0 8px;
        }

        .message-time {
            font-size: 11px;
            color: var(--text-light);
            margin-top: 4px;
            padding: 0 8px;
            text-align: right;
        }

        #messageInput {
            width: calc(100% - 100px);
            padding: 14px 20px;
            border: 1px solid #e0e0e0;
            border-radius: 24px;
            margin: 15px;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        #messageInput:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.2);
        }

        #sendButton {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 14px 25px;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 600;
            margin-right: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(74, 111, 165, 0.3);
        }

        #sendButton:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(74, 111, 165, 0.3);
        }

        #sendButton:active {
            transform: translateY(0);
        }

        .input-container {
            display: flex;
            padding: 10px;
            background: white;
            border-top: 1px solid #f0f0f0;
            align-items: center;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 id="room-name">Simple Chat Room</h1>
        <div id="messages"></div>
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message...">
            <button id="sendButton">Send</button>
        </div>
    </div>

    <script>
        const username = prompt("Enter your username: ") || "Anonymous";
        const room = prompt("Enter room name: ") || "General";
        const ws = new WebSocket(`wss://${window.location.host}/ws/${username}/${room}`);
        const messages = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const roomName = document.getElementById('room-name');

        roomName.textContent = `Chat Room: ${room}`;

        // Receive messages
        ws.onmessage = function(event) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            const messageContentDiv = document.createElement('div');
            messageContentDiv.className = 'message-content';
            messageContentDiv.textContent = event.data;
            messageDiv.appendChild(messageContentDiv);
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
