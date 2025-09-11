#!/bin/bash
# Simple script to start the FastAPI server

cd /home/lucas/Projetos/btc-sideproject-chatai/backend
echo "🚀 Starting BTC Sideproject ChatAI API server..."
echo "Server will be available at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000