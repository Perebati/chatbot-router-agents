#!/usr/bin/env python3
"""
Simple API test script to verify the FastAPI backend is working.
"""
import requests
import json


def test_api():
    """Test the chat API with various messages."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing BTC Sideproject ChatAI API")
    print("=" * 50)
    
    # Test health endpoint first
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        print("Make sure the server is running on http://localhost:8000")
        return
    
    print("\n" + "=" * 50)
    
    # Test chat endpoint with different messages
    test_cases = [
        {
            "name": "Knowledge Query - Portuguese",
            "message": "Qual é a taxa da maquininha?",
            "expected_agent": "KnowledgeAgent"
        },
        {
            "name": "Math Query - English",
            "message": "How much is 10 x 5?",
            "expected_agent": "MathAgent"
        },
        {
            "name": "PIX Knowledge Query",
            "message": "O que é PIX?",
            "expected_agent": "KnowledgeAgent"
        },
        {
            "name": "Simple Math",
            "message": "25 + 15",
            "expected_agent": "MathAgent"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Message: '{test_case['message']}'")
        
        payload = {
            "message": test_case["message"],
            "user_id": "test_user",
            "conversation_id": f"test_conv_{i}"
        }
        
        try:
            response = requests.post(f"{base_url}/chat", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"Response: {result['response']}")
                print(f"Agent Workflow: {result['agent_workflow']}")
                
                # Check if correct agent was chosen
                if len(result['agent_workflow']) >= 2:
                    chosen_agent = result['agent_workflow'][0]['decision']
                    if chosen_agent == test_case['expected_agent']:
                        print(f"✅ Correct agent chosen: {chosen_agent}")
                    else:
                        print(f"⚠️  Expected {test_case['expected_agent']}, got {chosen_agent}")
                
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 30)
    
    print("\n✅ API testing completed!")


if __name__ == "__main__":
    test_api()