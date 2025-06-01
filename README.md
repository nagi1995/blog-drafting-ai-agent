# 🤖 Code to Blog AI Agent

A **[Streamlit](https://streamlit.io/)-based AI Agent built using [LangGraph](https://www.langchain.com/langgraph)** that transforms Python scripts into structured, human-readable blog posts. The agent uses LLMs to understand code, structure content, and iteratively draft each section, all with human-in-the-loop feedback.

---

# [Link](https://binginagesh.medium.com/from-python-scripts-to-blog-posts-a-langgraph-powered-ai-agent-fa4a26e7a835) to medium blog

---

## 🧠 What It Does

- 🔍 Understands uploaded Python code files
- 🧾 Generates a blog outline structure
- ✍️ Drafts each section individually using LLMs
- 🔁 Accepts human feedback on blog structure and drafts
- 📄 Outputs a final blog once all sections are approved

---

## 🔧 How It Works

This project uses **LangGraph** to model a multistep agent with interruptible nodes and memory:

Python Code → Code Summary → Blog Structure → Feedback Loop → Draft Sections → Feedback Loop → Final Blog


### LangGraph Nodes:
- `code_understanding`: Summarizes uploaded Python code
- `blog_structuring`: Proposes an outline
- `human_blog_feedback`: Requests approval or revision of outline
- `section_drafting`: Generates individual section drafts
- `section_drafting_feedback`: Requests feedback on each section
- `set_next_section`: Tracks and selects the next section to draft

---

## 📁 File Structure
 - `main.py`: Streamlit app interface
 - `blog_graph.py`: LangGraph pipeline setup
 - `nodes.py`: Core logic for summarization, structuring, drafting, and feedback handling
 - `blog_state.py`: Typed state for LangGraph
 - `functions.py`: Utilities (e.g., for loading code)
 - `requirements.txt`: All required Python packages

---

## 📦 Installation

1. **Clone the Repository**

```bash
git clone https://github.com/nagi1995/blog-drafting-ai-agent.git
cd blog-drafting-ai-agent
```

2. **Download and Install Miniconda**

    Install Miniconda from the [link](https://www.anaconda.com/docs/getting-started/miniconda/install).

3. **Create a Conda Environment**

```bash
conda create --name blog_drafting_ai_agent python=3.12.9 -y
conda activate blog_drafting_ai_agent  
```

4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

5. **Create a .env file with necessary credentials**

```bash
GROQ_API_KEY=your_groq_api_key
```

---

## 🖥️ Interface Options

### 1. **Streamlit UI**

Launch the web interface with:

```bash
streamlit run main.py
```

Features:
- Upload .py files directly
- Review blog structure and draft sections
- Provide feedback via text input
- Automatically compiles final blog draft

### 2. **CLI Agent**

Run the agent in a terminal:

```bash
python blog_graph.py
```

---

## ▶️ Demo Video

https://github.com/user-attachments/assets/493ecc71-eaf4-4f1d-9573-c5f649a2194c

---

## 🧑‍💻 Author

**Nagesh**  
[GitHub](https://github.com/nagi1995) | [LinkedIn](https://www.linkedin.com/in/bnagesh1/)

