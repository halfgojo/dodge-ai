#!/bin/bash
echo "Starting Backend API..."
cd backend
source venv/bin/activate
uvicorn main:app --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
