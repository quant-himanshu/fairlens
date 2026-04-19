#!/bin/bash
set -e
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1
cd backend
if [ ! -d "venv" ]; then python3 -m venv venv; fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
cd ..
sleep 5
cd frontend
if [ ! -d "node_modules" ]; then npm install; fi
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev &
cd ..
sleep 3
echo "✅ App: http://localhost:3000"
echo "✅ API: http://localhost:8000/docs"
open http://localhost:3000
wait
