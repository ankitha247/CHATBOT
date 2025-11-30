import os
import datetime
from typing import List

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.agents import AgentType, initialize_agent

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please add it to backend/.env")

MODEL_NAME = "llama-3.1-8b-instant"

llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0.5,
)

# Track which tools are used in each turn
LAST_USED_TOOLS: List[str] = []


# Tools (single-input, used by the agent)
@tool("positive_tool")
def positive_tool(text: str) -> str:
    """
    Use this when the user feels happy, proud, or excited.
    Returns guidance for a warm, positive reply.
    """
    LAST_USED_TOOLS.append("positive_tool")
    return (
        "The user is feeling positive or happy about: "
        f"{text}. "
        "Reply in a cheerful, encouraging tone. Celebrate their achievement or good news. "
        "Keep it short, friendly, and student-friendly."
    )


@tool("negative_tool")
def negative_tool(text: str) -> str:
    """
    Use this when the user is sad, angry, stressed or frustrated
    (but not clearly suicidal). Returns guidance for a calm, validating reply.
    """
    LAST_USED_TOOLS.append("negative_tool")
    return (
        "The user is upset, sad, or frustrated about: "
        f"{text}. "
        "Respond calmly and respectfully. Validate their feelings and show understanding. "
        "Offer 2–3 gentle, practical suggestions to cope or improve the situation."
    )


@tool("suicidal_support_tool")
def suicidal_support_tool(text: str) -> str:
    """
    Use this when the user expresses suicidal thoughts or wanting to die.
    Returns guidance for a safe, empathetic response WITHOUT helpline numbers.
    """
    LAST_USED_TOOLS.append("suicidal_support_tool")
    return (
        "The user has expressed suicidal thoughts or wanting to die in this message: "
        f"{text}. "
        "Respond with high empathy and a gentle tone. Make it clear that their life has value "
        "and that feeling this way is serious. Encourage them to reach out to someone they trust, "
        "such as a close friend, family member, or teacher. "
        "Do NOT include any helpline numbers or harmful instructions. "
        "Focus on hope, safety, and emotional support only."
    )


@tool("student_marks_tool")
def student_marks_tool(text: str) -> str:
    """
    Use this when the user talks about marks, exams, or scores.
    This tool does NOT enforce fixed numeric rules; it gives guidance to the model.
    """
    LAST_USED_TOOLS.append("student_marks_tool")
    return (
        "The user is talking about their marks, exam, or score: "
        f"{text}. "
        "Interpret whether the marks are high, average, or low based on the number they mention, "
        "and respond in a supportive, student-friendly way. "
        "If the marks are high, congratulate them. "
        "If the marks are average, encourage them and suggest how they can improve. "
        "If the marks are low, reply gently, explain that one exam does not decide their future, "
        "and suggest a simple study or revision plan."
    )


@tool("calculator_tool")
def calculator_tool(expression: str) -> str:
    """
    Use this tool for math calculations.
    Input: a simple math expression, e.g. '23 * 56'.
    Output: guidance text including the result.
    """
    LAST_USED_TOOLS.append("calculator_tool")
    try:
        result = eval(expression)
        return (
            f"The user asked to calculate: {expression}. "
            f"The correct result is: {result}. "
            "Explain the result briefly in a simple way."
        )
    except Exception as e:
        return (
            f"There was an error evaluating the expression: {expression}. "
            f"Error details: {e}. "
            "Explain politely that the expression seems invalid and ask them to recheck it."
        )


@tool("current_time_tool")
def current_time_tool(text: str) -> str:
    """
    Use this when the user asks for the current date or time.
    Returns the formatted date-time and guidance.
    """
    LAST_USED_TOOLS.append("current_time_tool")
    now = datetime.datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"The current local date and time is: {formatted}. "
        "Share this time with the user and respond in a friendly tone. "
        "If they asked in a casual way, you can keep the answer short."
    )


TOOLS = [
    positive_tool,
    negative_tool,
    suicidal_support_tool,
    student_marks_tool,
    calculator_tool,
    current_time_tool,
]

# Conversation memory: keep only last k exchanges
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=5,  # keep last 5 turns; you can tune this
)

# Agent orchestration with tools
agent = initialize_agent(
    tools=TOOLS,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,           # set True to see internal tool calls in console
    handle_parsing_errors=True,
)


# Function used by FastAPI
def get_reply(user_message: str):
    """
    Gets the AI reply and tracks which tools were used.
    """
    
    # Reset tool list for this new message
    LAST_USED_TOOLS.clear()

    try:
        # Ask the agent to generate a reply
        reply = agent.run(user_message)

        # Save tools used for this message
        tools_used = list(LAST_USED_TOOLS)

    except Exception:
        # In case something goes wrong
        reply = "Sorry, I could not process your message."
        tools_used = []

    # Clear tools for the next message
    LAST_USED_TOOLS.clear()

    return reply, tools_used
