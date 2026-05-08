import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama


def build_agent(
    tools: list,
    return_intermediate_steps: bool = False,
) -> AgentExecutor:
    model = os.getenv("OLLAMA_MODEL", "ministral-3:8b")
    llm = ChatOllama(model=model, temperature=0.3)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=8,
        return_intermediate_steps=return_intermediate_steps,
    )
