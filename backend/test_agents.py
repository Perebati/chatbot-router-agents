"""
Simple test script to verify the agent system works.
Run this to test the agents before starting the web server.
"""
from agents import RouterAgent, KnowledgeAgent, MathAgent


def test_agents():
    """Test all agents with sample messages."""
    print("🧪 Testing BTC Sideproject ChatAI Agents")
    print("=" * 50)
    
    # Initialize agents
    router = RouterAgent()
    knowledge = KnowledgeAgent()
    math = MathAgent()
    
    # Sample context
    context = {
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    
    # Test messages
    test_messages = [
        "Qual é a taxa da maquininha?",  # Should route to Knowledge
        "How much is 10 x 5?",           # Should route to Math
        "O que é PIX?",                  # Should route to Knowledge
        "Calculate 100 / 4",             # Should route to Math
    ]
    
    print("\n🔀 Testing RouterAgent:")
    for message in test_messages:
        print(f"\nMessage: '{message}'")
        result = router.execute(message, context)
        print(f"Decision: {result['agent']} (Reason: {result['reasoning']})")
    
    print("\n\n📚 Testing KnowledgeAgent:")
    knowledge_queries = ["Qual é a taxa da maquininha?", "O que é PIX?"]
    for query in knowledge_queries:
        print(f"\nQuery: '{query}'")
        result = knowledge.execute(query, context)
        print(f"Response: {result['response'][:100]}...")
    
    print("\n\n🧮 Testing MathAgent:")
    math_queries = ["10 x 5", "100 / 4", "25 + 15"]
    for query in math_queries:
        print(f"\nQuery: '{query}'")
        result = math.execute(query, context)
        print(f"Response: {result['response']}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_agents()