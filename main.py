import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import logger

import uuid
import streamlit as st
import tempfile

from functions import load_python_code
from blog_graph import blog_agent_graph
from langgraph.types import Command



from dotenv import load_dotenv

load_dotenv()

completed = "✅"
pending = "⬜"

st.set_page_config(page_title="Code → Blog Assistant", layout="wide")
st.title("🧠 Code to Blog Assistant")

# --- Upload Python Files ---
uploaded_files = st.file_uploader("Upload Python Files", type="py", accept_multiple_files=True)

# --- Initialize Session State ---
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
    st.session_state.thread_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "recursion_limit": 100
        }
    }
    st.session_state.feedback_input = ""
    st.session_state.run_phase = "idle"  # ["idle", "start", "awaiting_feedback", "resume"]
    st.session_state.interrupt_message = ""
    st.session_state.interrupt_value = {}
    st.session_state.last_interrupt_node = ""
    st.session_state.no_of_sections = 0

# --- Load and Process Uploaded Code ---
if uploaded_files and st.session_state.agent_state is None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_paths = []
        for file in uploaded_files:
            path = os.path.join(tmp_dir, file.name)
            with open(path, "wb") as f:
                f.write(file.read())
            file_paths.append(path)

        code = load_python_code(file_paths)
        st.session_state.agent_state = {
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



# --- Start or Resume Agent ---
if st.button("🚀 Run Agent"):
    st.session_state.run_phase = "start"

# --- Agent Execution ---
if st.session_state.run_phase in ["start", "resume"]:
    with st.spinner("Running agent..."):
        input_state = (
            st.session_state.agent_state
            if st.session_state.run_phase == "start"
            else Command(resume=st.session_state.feedback_input)
        )
        logger.info(f"input_state: {input_state}")
        stream = blog_agent_graph.stream(input_state, config=st.session_state.thread_config)

        final_event = None
        for event in stream:
            logger.info(f"event: {event}")
            if isinstance(event, dict) and "__interrupt__" in event:
                interrupt_value = event["__interrupt__"][0].value
                st.session_state.interrupt_value = interrupt_value
                st.session_state.interrupt_message = interrupt_value["message"]
                st.session_state.last_interrupt_node = interrupt_value.get("current_node", "")
                st.session_state.run_phase = "awaiting_feedback"
                break
            else:
                st.session_state.agent_state = event[1] if isinstance(event, tuple) else st.session_state.agent_state
                final_event = event[1] if isinstance(event, tuple) else event

        if st.session_state.run_phase != "awaiting_feedback":
            st.session_state.run_phase = "idle"
        
        # ✅ Display Final Blog After Completion
        if st.session_state.run_phase == "idle" and final_event:
            state = final_event["set_next_section"]
            logger.info("Execution completed")
            logger.info(f"state: {state}")
            logger.info(f"state keys: {state.keys()}")
            if "sections" in state and "section_drafts" in state:
                sections = state["sections"]
                section_drafts = state["section_drafts"]
                logger.info(f"length of sections: {len(sections)}")
                logger.info(f"length of drafts: {len(section_drafts)}")
                logger.info(f"sections: {sections}")
                logger.info(f"section drafts: {section_drafts}")
                st.header(f"Final Draft of the Blog")
                if len(sections) == len(section_drafts):
                    for i, (section, section_draft) in enumerate(zip(sections, section_drafts), start=1):
                        logger.info(f"section: {section}")
                        logger.info(f"section draft: {section_draft}")
                        st.subheader(f"{i}. {section['title']}")
                        st.write(section_drafts[f'section{i}'])
                    
                    # Show "Start Over" option
                    if st.button("🔁 Start Over"):
                        for key in st.session_state.keys():
                            del st.session_state[key]
                        st.rerun()



def show_progress():
    no_of_sections_drafted = int(st.session_state.interrupt_value.get("section_no"))

    bar = "".join([completed for i in range(no_of_sections_drafted-1)] + [pending for j in range(int(st.session_state.no_of_sections) - no_of_sections_drafted + 1)])
    st.write(f"Completed drafting {bar}/{st.session_state.no_of_sections} sections")

# --- Feedback Input ---
if st.session_state.run_phase == "awaiting_feedback":
    logger.info(f"st session state: {st.session_state}")
    # st.session_state.feedback_input = ""
    if st.session_state.interrupt_value.get("current_node") == "human_blog_feedback":
        sections = st.session_state.interrupt_value.get("sections", {})
        st.subheader(f"Version {st.session_state.interrupt_value.get('blog_structuring_version')}: Generated Blog Sections")
        st.json(sections, expanded=True)
        st.session_state.no_of_sections = len(sections)
    elif st.session_state.interrupt_value.get("current_node") == "human_section_feedback":
        section_draft = st.session_state.interrupt_value.get("section_draft", {})
        version = st.session_state.interrupt_value.get('draft_version')
        title = st.session_state.interrupt_value.get('section_title')
        st.subheader(f"Drafted Section Title: {title} (Version {version})")
        st.write(section_draft)
        show_progress()
    st.subheader("✏️ Agent Feedback Required")
    st.info(st.session_state.interrupt_message)
    st.session_state.feedback_input = st.text_area("Enter your feedback (or type 'approved')")

    if st.button("Submit Feedback"):
        st.session_state.run_phase = "resume"
        st.rerun()



