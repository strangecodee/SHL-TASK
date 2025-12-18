#!/usr/bin/env python
"""
Single-command execution script for SHL Assessment Recommendation System
Runs complete pipeline: setup → evaluation → CSV generation → API server
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Execute command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Error in: {description}")
        sys.exit(1)
    
    print(f"\n✓ Completed: {description}")

def main():
    """Main execution flow"""
    print("\n" + "="*60)
    print("SHL ASSESSMENT RECOMMENDATION SYSTEM")
    print("Production Pipeline Execution")
    print("="*60)
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Step 1: Build FAISS index
    run_command(
        "python vector_store.py",
        "Step 1/4: Building FAISS vector index"
    )
    
    # Step 2: Evaluate on train set
    run_command(
        "python production_evaluator.py",
        "Step 2/4: Evaluating on train set (Recall@10)"
    )
    
    # Step 3: Generate test predictions
    run_command(
        "python production_csv_generator.py",
        "Step 3/4: Generating test set predictions"
    )
    
    # Step 4: Start API server
    print(f"\n{'='*60}")
    print("Step 4/4: Starting FastAPI server")
    print(f"{'='*60}\n")
    print("API will be available at: http://localhost:8000")
    print("Endpoints:")
    print("  - GET  /health")
    print("  - POST /recommend")
    print("\nPress CTRL+C to stop the server\n")
    
    subprocess.run("python api_server.py", shell=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        sys.exit(0)
