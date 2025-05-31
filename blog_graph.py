import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import logger


from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END 

from nodes import code_understanding_node, blog_structuring_node, blog_structuring_feedback_node, set_next_section, section_drafting_node, section_drafting_feedback_node

from blog_state import BlogState

from dotenv import load_dotenv

load_dotenv()


# Build the graph
builder = StateGraph(BlogState)
# Register all nodes
builder.add_node("code_understanding", code_understanding_node)
builder.add_node("blog_structuring", blog_structuring_node)
builder.add_node("human_blog_feedback", blog_structuring_feedback_node)
builder.add_node("set_next_section", set_next_section)
builder.add_node("section_drafting", section_drafting_node)
builder.add_node("section_drafting_feedback", section_drafting_feedback_node)

# Set entry point
builder.set_entry_point("code_understanding")

# Linear steps
builder.add_edge("code_understanding", "blog_structuring")
builder.add_edge("blog_structuring", "human_blog_feedback")

# Human feedback on blog structure determines next step via Command
# Command will go to "blog_structuring" (loop) or "set_next_section" (approved)

# Section drafting loop
builder.add_edge("section_drafting", "section_drafting_feedback")
# Feedback node uses Command to go either to section_drafting (for revision) or set_next_section (if approved)

# Conditional routing from set_next_section
def should_continue(state: BlogState):
    return "continue" if state.get("target_section_no") else "end"

builder.add_conditional_edges("set_next_section", should_continue, {
    "continue": "section_drafting",
    "end": END
})


# Compile graph with interrupt/checkpoint support
checkpointer = MemorySaver()
blog_agent_graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    from functions import load_python_code
    import uuid 
    from langgraph.types import Command

    directory = input("Enter directory path to '.py' files: ")
    code = load_python_code(directory)
    initial_state = {
        "code": code,
        "code_summary": "",             
        "section_drafts": {},
        "completed_sections": [],
        "skipped_sections": [],
        "sections": [],
        "current_section": "",
        "feedback": {},
        "target_section_no": ""
    }
    thread_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "recursion_limit": 100
        }
    }

    current_state = initial_state

    while True:
        stream = blog_agent_graph.stream(current_state, config=thread_config)
        
        for event in stream:
            if isinstance(event, dict) and "__interrupt__" in event:
                interrupt_value = event["__interrupt__"][0].value
                print(interrupt_value["message"])
                user_input = input("Your feedback: ")

                current_state = Command(resume=user_input)
                break  # go to outer loop to restart stream
            else:
                # normal node output
                print(event)
                current_state = event[1] if isinstance(event, tuple) else current_state
        else:
            break  # stream finished cleanly

