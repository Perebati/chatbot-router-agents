from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="llama3.2")

template = """
You are a RouterAgent. 
Your goal is to analyze the user question and classify it into one of two categories:

- "knowledge" - for questions about InfinitePay app, features, help, or support
- "math" - for questions involving mathematical calculations or expressions

User question: {question}

You must respond with exactly one word: either "knowledge" or "math". Nothing else.

Classification:"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break

    result = chain.invoke({"question": question})
    print(f"Classification: {result}")