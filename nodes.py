import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import logger

import time

from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq
from langgraph.types import Command, interrupt
from langchain.schema import SystemMessage, HumanMessage


from blog_state import BlogState

from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant")


# Code Understanding Module
def code_understanding_node(state: BlogState):
    logger.info(f"state: {state}")
    # Get code from state
    code = state["code"]

    messages = [
        SystemMessage(content="You are an expert Python code reviewer."),
        HumanMessage(content=f"""
        I have the following Python codebase:

        ```python
        {code}
        ```
        Summarize what this code is doing. Cover the overall purpose, key components, and any interesting structure or design patterns.
        """)
    ]

    response = llm.invoke(messages)
    logger.info(f"code understanding node response: {response}")

    blog_state = {
        **state,
        "code_summary": response.content.strip()
    }
    return blog_state

def invoke_with_retries(llm, messages, output_class, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            response = llm.with_structured_output(output_class).invoke(messages)
            return response
        except Exception as e:
            logger.info(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt == max_retries - 1:
                raise  # re-raise if last attempt
            sleep_time = base_delay * (2 ** attempt)  # exponential backoff
            logger.info(f"Retrying after {sleep_time} seconds...")
            time.sleep(sleep_time)

# Blog Structuring Module
class Section(BaseModel):
    title: str = Field(..., description="The title of the blog section")
    description: str = Field(..., description="A brief one-line description of what the section covers")

class SectionsOutput(BaseModel):
    sections: List[Section] = Field(..., description="List of blog sections with titles and descriptions")

def blog_structuring_node(state: BlogState):
    logger.info(f"state: {state}")
    code_summary = state.get("code_summary", "")
    feedback = state.get("feedback", {}).get("blog_structuring", "")
    previous_sections = state.get("sections", [])

    # Compose base prompt
    prompt = f"""
    Based on the following code summary, generate a high-level blog post outline with 5-7 sections.

    Code Summary:
    {code_summary}

    Each section should include:
    - A clear title
    - A 1-2 sentence description explaining what the section will cover
    """

    # Include previous outline if feedback is present
    if feedback and previous_sections:
        logger.info(f"previous drafts and feedback is present. So, adding them to prompt")
        logger.info(f"feedback from user: {feedback}")
        formatted_previous = "\n".join([
            f"{s['no']}. {s['title']}: {s['description']}"
            for s in previous_sections
        ])
        prompt += f"""

        Previous Outline:
        {formatted_previous}

        Human Feedback on Previous Outline:
        {feedback}

        Please generate a revised outline considering the feedback above.
        """

    prompt += """
    Return only a valid JSON object in the format:
    ```json
    {
    "sections": [
        {
        "title": "Your section title here",
        "description": "Short description here."
        },
        ...
    ]
    }
    ```
    """
    messages = [
        SystemMessage(
            content="You are an expert technical writer helping to create a blog post outline. "
                    "You must return a JSON object with a single key 'sections', whose value is a list of sections. "
                    "Each section must be an object with the keys: 'title' (str), 'description' (str). Do not add any commentary or explanation."
        ),
        HumanMessage(content=prompt)
    ]
    logger.info(f"prompt: {prompt}")

    response = invoke_with_retries(llm=llm, messages=messages, output_class=SectionsOutput)
    logger.info(f"blog structuring node output: {response}")

    numbered_sections = [
        {"no": str(i + 1), **section.model_dump()}
        for i, section in enumerate(response.sections)
    ]
    return {
        **state,
        "sections": numbered_sections
    }


# Section Drafting Node
def section_drafting_node(state: BlogState):
    logger.info(f"state: {state}")

    target_no = state.get("target_section_no")
    if target_no is None:
        raise ValueError("Missing 'target_section_no' in state")

    section_drafts = state.get("section_drafts", {})
    sections = state.get("sections", [])
    code_summary = state.get("code_summary", "")
    feedback_dict = state.get("feedback", {})

    # Find the target section by number
    target_section = next((s for s in sections if s.get("no") == target_no), None)
    if not target_section:
        raise ValueError(f"No section found with number {target_no}")

    section_key = f"section{str(target_no)}"
    feedback_key = f"section_drafting_{target_no}"
    previous_draft = section_drafts.get(section_key, None)
    section_feedback = feedback_dict.get(feedback_key, None)

    prompt_parts = [
        f"You are writing the blog section titled **{target_section['title']}**.",
        f"\nSection Description: {target_section['description']}",
        f"\nCode Summary for context:\n{code_summary}"
    ]

    if previous_draft:
        prompt_parts.append(f"\nPrevious Draft:\n{previous_draft}")

    if section_feedback:
        logger.info(f"feedback from user: {section_feedback}")
        prompt_parts.append(f"\nHuman Feedback:\n{section_feedback}")

    prompt_parts.append("\nWrite a detailed, revised plain-text draft for this section. Avoid using any markdown formatting. Just write natural, readable sentences and paragraphs.")

    messages = [
        SystemMessage(content="You are a technical writer drafting one section of a blog post based on a code summary."),
        HumanMessage(content="\n".join(prompt_parts))
    ]

    response = llm.invoke(messages)
    updated_draft = response.content.strip()
    logger.info(f"Updated draft for section {target_no}:\n{updated_draft}")

    section_drafts[section_key] = updated_draft

    return {
        **state,
        "section_drafts": section_drafts
    }

# Blog Structure Feedback Node
def blog_structuring_feedback_node(state: BlogState):
    logger.info(f"state: {state}")
    logger.info("[blog_structuring_feedback_node] Awaiting human feedback for blog structure...")
    version = state.get("feedback", {}).get("blog_structuring_version", 0)
    # Interrupt to display sections and capture human feedback
    user_feedback = interrupt({
        "sections": state.get("sections", []),
        "blog_structuring_version": version+1,
        "message": "Provide feedback on the blog structure (or type 'approved')",
        "current_node": "human_blog_feedback"
    })
    

    logger.info(f"[blog_structuring_feedback_node] Received feedback: {user_feedback}")

    feedback_update = {"blog_structuring": user_feedback, "blog_structuring_version": version+1}

    if user_feedback.lower() == "approved":
        return Command(update={"feedback": feedback_update}, goto="set_next_section")
    else:
        return Command(update={"feedback": feedback_update}, goto="blog_structuring")


# Section Drafting Feedback Node
def section_drafting_feedback_node(state: BlogState):
    logger.info(f"state: {state}")
    logger.info("[section_drafting_feedback_node] Awaiting human feedback for blog structure...")
    target_no = state.get("target_section_no")
    if not target_no:
        raise ValueError("No target section number found in state")

    section_key = f"section{target_no}"
    section_draft = state.get("section_drafts", {}).get(section_key, "")

    # Extract the section object (title + description)
    section_obj = next((s for s in state.get("sections", []) if s.get("no") == target_no), {})
    section_title = section_obj.get("title", "")
    section_description = section_obj.get("description", "")
    version = state.get("feedback", {}).get(f"section_drafting_{target_no}_version", 0)
    logger.info(f"section no: {target_no}")
    logger.info(f"section_title: {section_title}")
    logger.info(f"section_draft: {section_draft}")

    # Interrupt to get feedback from human
    feedback = interrupt({
        "message": "Please review the drafted section and provide feedback, or type 'approved' to proceed.",
        "section_no": target_no,
        "section_title": section_title,
        "section_description": section_description,
        "section_draft": section_draft,
        "draft_version": version+1,
        "current_node": "human_section_feedback"
    })

    logger.info(f"[section_drafting_feedback_node] Received feedback: {feedback}")

    update = {
            "feedback": {
                **state.get("feedback", {}),
                f"section_drafting_{target_no}": feedback,
                f"section_drafting_{target_no}_version": version+1
            }
        }
    logger.info(f"update: {update}")

    # Save feedback keyed to the section number
    return Command(
        update=update,
        goto="section_drafting" if feedback.lower().strip() != "approved" else "set_next_section"
    )

# Node wrappers
def blog_structuring_approved(state: BlogState) -> str:
    logger.info("in blog_structuring_approved function")
    feedback = state.get("feedback", {})
    return "approved" if feedback.get("blog_structuring", "").lower().strip() == "approved" else "not approved"

def section_drafting_approved(state: BlogState) -> str:
    logger.info("in section_drafting_approved function")
    target_no = state.get("target_section_no")
    if target_no is None:
        return "not approved"
    section_key = f"section_drafting_{target_no}"
    feedback = state.get("feedback", {})
    return "approved" if feedback.get(section_key, "").lower().strip() == "approved" else "not approved"

def set_next_section(state: BlogState):
    logger.info("in set_next_section function")
    sections = state.get("sections", [])
    drafted = state.get("section_drafts", {}).keys()
    next_section = next((s for s in sections if f"section{s['no']}" not in drafted), None)
    if next_section:
        logger.info(f"will draft section no: {next_section["no"]}")
        state["target_section_no"] = next_section["no"]
        return state
    return {**state, "target_section_no": None}

def has_more_sections(state: BlogState) -> str:
    logger.info("in has_more_sections function")
    return "more sections" if state.get("target_section_no") else "done"

def all_sections_drafted(state: BlogState) -> str:
    logger.info("in all_sections_drafted function")
    sections = state.get("sections", [])
    drafted_keys = state.get("section_drafts", {}).keys()
    
    all_drafted = all(f"section{section['no']}" in drafted_keys for section in sections)
    logger.info(f"all sections drafted: {all_drafted}")
    return "yes" if all_drafted else "no"

def check_if_all_sections_drafted(state: BlogState):
    logger.info("in check_if_all_sections_drafted node")
    return state


