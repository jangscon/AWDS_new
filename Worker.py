from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import argparse

app = FastAPI()

# Task model, now with repetitions as an integer
class Task(BaseModel):
    task_id: int
    repetitions: int  # Number of times the task should be executed

@app.post("/execute_task")
async def execute_task(tasks: list[Task]):
    results = []
    for task in tasks:
        # Simulate processing task based on repetitions
        result = f"Processed task {task.task_id} {task.repetitions} times"
        
        # Convert the Task object to a dictionary before sending
        task_dict = {"task_id": task.task_id, "data": result}
        
        # Send result back to server
        response = requests.post("http://<SERVER_IP>:8000/task_result", json=task_dict)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send task result.")
        
        results.append(result)
    
    return {"message": "Tasks executed and results sent."}

if __name__ == "__main__":
    import uvicorn
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--port", type=int, default=8000, help="Port number to run the server on.")
    args = parser.parse_args()

    # Run the app with the specified port
    uvicorn.run(app, host="0.0.0.0", port=args.port)
