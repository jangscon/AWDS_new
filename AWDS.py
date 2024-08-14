from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from uuid import uuid4

app = FastAPI()

# Updated Device model to include port
class Device(BaseModel):
    name: str
    ip: str
    port: int  # New port field

# Task model, now represents the number of repetitions
class Task(BaseModel):
    task_id: int
    repetitions: int  # Updated to represent how many times the task should be performed

# Session model
class Session:
    def __init__(self, device_1: Device):
        self.id = str(uuid4())
        self.device_1 = device_1
        self.device_2 = None
        self.tasks = []
        self.results = {}

    def is_complete(self):
        return len(self.results) == len(self.tasks)

# Storage for sessions
sessions = {}

@app.post("/register_device")
async def register_device(device: Device):
    print("register device")
    # Find an incomplete session or create a new one
    incomplete_session = next((s for s in sessions.values() if not s.device_2), None)
    
    if incomplete_session:
        incomplete_session.device_2 = device
        return {"message": f"Device {device.name} registered to session {incomplete_session.id}."}
    else:
        new_session = Session(device)
        sessions[new_session.id] = new_session
        return {"message": f"Device {device.name} registered and created session {new_session.id}."}

@app.post("/trigger_tasks/{session_id}")
async def trigger_tasks(session_id: str, tasks: list[Task]):
    session = sessions.get(session_id)
    if not session or not session.device_2:
        raise HTTPException(status_code=400, detail="Invalid session or session not ready.")

    session.tasks.extend(tasks)

    # Split tasks between two devices
    half = len(tasks) // 2
    tasks_for_device_1 = tasks[:half]
    tasks_for_device_2 = tasks[half:]

    # Send tasks to devices with custom port
    device_1 = session.device_1
    device_2 = session.device_2
    
    response_1 = requests.post(f"http://{device_1.ip}:{device_1.port}/execute_task", json=tasks_for_device_1)
    response_2 = requests.post(f"http://{device_2.ip}:{device_2.port}/execute_task", json=tasks_for_device_2)

    if response_1.status_code != 200 or response_2.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send tasks to devices.")
    print("trigger tasks")
    return {"message": f"Tasks are being executed by the devices in session {session_id}."}

@app.post("/task_result/{session_id}")
async def task_result(session_id: str, task: Task):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session ID.")

    # Store task result
    session.results[task.task_id] = task.repetitions
    print("task result")
    if session.is_complete():
        return {"message": f"All tasks completed in session {session_id}.", "results": session.results}
    
    return {"message": f"Task {task.task_id} result received in session {session_id}."}

# New endpoint to check the status of all registered devices
@app.get("/device_status")
async def device_status():
    status = []
    for session_id, session in sessions.items():
        session_info = {
            "session_id": session_id,
            "device_1": {"name": session.device_1.name, "ip": session.device_1.ip, "port": session.device_1.port},
            "device_2": {"name": session.device_2.name if session.device_2 else "Waiting for device 2",
                         "ip": session.device_2.ip if session.device_2 else None,
                         "port": session.device_2.port if session.device_2 else None}
        }
        status.append(session_info)
    print("device status")
    return {"devices": status}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
