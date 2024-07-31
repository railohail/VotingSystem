from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# File to store poll data
POLL_FILE = "poll_data.json"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def load_poll_data():
    logger.info(f"Loading poll data from {POLL_FILE}")
    if not os.path.exists(POLL_FILE):
        logger.info(f"{POLL_FILE} does not exist, creating new file")
        empty_data = {"subjects": {}}
        save_poll_data(empty_data)
        return empty_data
    
    try:
        with open(POLL_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded data: {data}")
            if not data or "subjects" not in data:
                logger.info("Invalid data structure, initializing with empty data")
                data = {"subjects": {}}
                save_poll_data(data)
            return data
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {POLL_FILE}, initializing with empty data")
        empty_data = {"subjects": {}}
        save_poll_data(empty_data)
        return empty_data

def save_poll_data(data):
    logger.info(f"Saving poll data to {POLL_FILE}")
    with open(POLL_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Data saved: {data}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            poll_data = load_poll_data()  # Always load fresh data
            action = json.loads(data)
            
            if action["type"] == "vote":
                subject = action["subject"]
                option = action["option"]
                username = action["username"]
                
                if subject in poll_data["subjects"]:
                    subject_data = poll_data["subjects"][subject]
                    if option in subject_data["options"]:
                        user_votes = subject_data["votes"].get(username, [])
                        
                        if option in user_votes:
                            # Remove vote
                            user_votes.remove(option)
                            subject_data["options"][option] -= 1
                        elif len(user_votes) < 2:
                            # Add vote
                            user_votes.append(option)
                            subject_data["options"][option] += 1
                        else:
                            # Replace oldest vote
                            old_vote = user_votes.pop(0)
                            subject_data["options"][old_vote] -= 1
                            user_votes.append(option)
                            subject_data["options"][option] += 1
                        
                        subject_data["votes"][username] = user_votes
                        save_poll_data(poll_data)
                        await manager.broadcast(json.dumps(poll_data, ensure_ascii=False))
            
            elif action["type"] == "new_option":
                subject = action["subject"]
                new_option = action["option"]
                
                if subject in poll_data["subjects"]:
                    if new_option not in poll_data["subjects"][subject]["options"]:
                        poll_data["subjects"][subject]["options"][new_option] = 0
                        save_poll_data(poll_data)
                        await manager.broadcast(json.dumps(poll_data, ensure_ascii=False))
            
            elif action["type"] == "new_subject":
                subject = action["subject"]
                
                if subject not in poll_data["subjects"]:
                    poll_data["subjects"][subject] = {
                        "options": {},
                        "votes": {}
                    }
                    save_poll_data(poll_data)
                    await manager.broadcast(json.dumps(poll_data, ensure_ascii=False))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/poll_data")
async def get_poll_data():
    return load_poll_data()  # Always load fresh data

@app.post("/new_subject")
async def add_new_subject(subject: str):
    poll_data = load_poll_data()  # Always load fresh data
    if subject not in poll_data["subjects"]:
        poll_data["subjects"][subject] = {
            "options": {},
            "votes": {}
        }
        save_poll_data(poll_data)
        await manager.broadcast(json.dumps(poll_data, ensure_ascii=False))
        return {"message": f"New subject '{subject}' added successfully"}
    else:
        return {"message": f"Subject '{subject}' already exists"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)