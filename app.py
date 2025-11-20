
##--- START OF FILE app.py ---

import streamlit as st
import json
import asyncio
from google.adk.sessions import InMemorySessionService
from config import setup_config
from agent import researcher_agent, writer_agent, editor_agent, storyboard_agent
import db  # Import our new database module

# --- PAGE SETUP ---
st.set_page_config(page_title="Google ADK Story Studio", page_icon="🎬", layout="wide")

# --- INITIALIZATION ---
if "initialized" not in st.session_state:
    setup_config()
    db.init_db()  # Initialize the DB table
    
    st.session_state["session_service"] = InMemorySessionService()
    
    # Create ADK Session (Sync)
    try:
        session = st.session_state["session_service"].create_session(
            app_name="agentic-story-studio",
            user_id="default_user"
        )
        st.session_state["session_id"] = session.id
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        st.session_state["session_id"] = "error-session"

    # UI State
    st.session_state["current_project_id"] = None
    st.session_state["current_step"] = "1. Research Dept"
    
    # Data Store (mirrors DB)
    st.session_state["user_request"] = ""
    st.session_state["research_context"] = ""
    st.session_state["script_content"] = ""
    st.session_state["editor_feedback"] = "Initial Draft - No feedback yet."
    st.session_state["editor_score"] = 0
    st.session_state["is_approved"] = False
    st.session_state["storyboard_output"] = ""

    st.session_state["initialized"] = True

# --- HELPER FUNCTIONS ---

def run_hooked_agent(agent, input_data):
    return agent.run(
        input_data,
        session_service=st.session_state["session_service"],
        session_id=st.session_state["session_id"]
    )

def navigate_to(step_name):
    st.session_state["current_step"] = step_name
    st.rerun()

def load_project_into_state(project_id):
    """Fetches DB row and hydrates session_state."""
    data = db.load_project(project_id)
    if data:
        st.session_state["current_project_id"] = data["id"]
        st.session_state["user_request"] = data["user_request"] or ""
        st.session_state["research_context"] = data["research_output"] or ""
        st.session_state["script_content"] = data["script_content"] or ""
        st.session_state["editor_feedback"] = data["editor_feedback"] or "Initial Draft - No feedback yet."
        st.session_state["editor_score"] = data["editor_score"] or 0
        st.session_state["is_approved"] = bool(data["is_approved"])
        st.session_state["storyboard_output"] = data["storyboard_output"] or ""
        
        # Determine step based on what data exists
        if data["storyboard_output"]:
            st.session_state["current_step"] = "4. Art Dept"
        elif data["is_approved"]:
            st.session_state["current_step"] = "4. Art Dept"
        elif data["script_content"]:
            st.session_state["current_step"] = "3. Editor's Desk"
        elif data["research_output"]:
            st.session_state["current_step"] = "2. Writer's Room"
        else:
            st.session_state["current_step"] = "1. Research Dept"

def clear_project_state():
    st.session_state["current_project_id"] = None
    st.session_state["user_request"] = ""
    st.session_state["research_context"] = ""
    st.session_state["script_content"] = ""
    st.session_state["editor_feedback"] = "Initial Draft - No feedback yet."
    st.session_state["editor_score"] = 0
    st.session_state["is_approved"] = False
    st.session_state["storyboard_output"] = ""
    st.session_state["current_step"] = "1. Research Dept"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Studio Controls")
    
    # --- PROJECT SELECTION ---
    st.subheader("📂 Projects")
    
    # "New Project" Button
    if st.button("➕ New Project"):
        clear_project_state()
        st.rerun()

    # Existing Projects Dropdown
    projects = db.get_all_projects()
    project_options = {p[0]: f"{p[0]}. {p[1]} ({p[2]})" for p in projects}
    
    selected_project_id = st.selectbox(
        "Load Project:", 
        options=[None] + list(project_options.keys()),
        format_func=lambda x: project_options[x] if x else "Select a project...",
        index=None
    )
    
    if selected_project_id and selected_project_id != st.session_state["current_project_id"]:
        load_project_into_state(selected_project_id)
        st.rerun()

    st.markdown("---")

    # Navigation Menu
    if st.session_state["current_project_id"]:
        st.success(f"Project #{st.session_state['current_project_id']} Active")
        
        steps = ["1. Research Dept", "2. Writer's Room", "3. Editor's Desk", "4. Art Dept"]
        st.session_state["current_step"] = st.radio(
            "Navigation", 
            steps, 
            index=steps.index(st.session_state["current_step"])
        )
    else:
        st.info("Start a new project or load one to begin.")

# --- MAIN LAYOUT ---
st.title("🎬 Agentic Screenwriting Studio")

if not st.session_state["current_project_id"]:
    st.subheader("Start a New Story")
    st.session_state["user_request"] = st.text_area(
        "Enter your Story Idea:",
        value=st.session_state["user_request"],
        placeholder="e.g. A sci-fi thriller about a robot who wants to be a chef on Mars.",
        height=150
    )
    
    if st.button("🚀 Start Project", type="primary"):
        if not st.session_state["user_request"]:
            st.error("Please enter an idea.")
        else:
            # CREATE DB RECORD
            new_id = db.create_project(st.session_state["user_request"])
            load_project_into_state(new_id)
            st.rerun()

else:
    # A PROJECT IS ACTIVE
    st.caption(f"Stage: {st.session_state['current_step']}")
    st.markdown("---")

    # === STAGE 1: RESEARCHER ===
    if st.session_state["current_step"] == "1. Research Dept":
        st.subheader("Story Development")
        st.text_area("Original Idea:", value=st.session_state["user_request"], disabled=True)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Run Researcher", type="primary"):
                with st.spinner("Researcher is analyzing..."):
                    response = run_hooked_agent(
                        researcher_agent,
                        {"user_request": st.session_state["user_request"]}
                    )
                    
                    # UPDATE STATE & DB
                    st.session_state["research_context"] = response
                    db.update_project_field(st.session_state["current_project_id"], "research_output", response)
                    
                    navigate_to("2. Writer's Room")

        if st.session_state["research_context"]:
            st.markdown("### Research Output")
            st.text_area("Brief:", value=st.session_state["research_context"], height=300)

    # === STAGE 2: WRITER ===
    elif st.session_state["current_step"] == "2. Writer's Room":
        st.subheader("Screenwriting Phase")
        
        if not st.session_state["research_context"]:
            st.error("⚠️ No Research found.")
        else:
            col1, col2 = st.columns([3, 1])
            with col2:
                st.info(f"Feedback: {st.session_state['editor_feedback']}")
                manager_notes = st.text_area("Manager Notes:")

                if st.button("✍️ Write Script", type="primary"):
                    with st.spinner("Writer is drafting..."):
                        writer_input = {
                            "research_context": st.session_state["research_context"],
                            "feedback": st.session_state["editor_feedback"] + f"\nManager Notes: {manager_notes}",
                        }
                        response = run_hooked_agent(writer_agent, writer_input)
                        
                        # UPDATE STATE & DB
                        st.session_state["script_content"] = response
                        db.update_project_field(st.session_state["current_project_id"], "script_content", response)
                        
                        navigate_to("3. Editor's Desk")

            with col1:
                if st.session_state["script_content"]:
                    st.text_area("Script Draft:", value=st.session_state["script_content"], height=600)
                else:
                    st.info("Ready to write.")

    # === STAGE 3: EDITOR ===
    elif st.session_state["current_step"] == "3. Editor's Desk":
        st.subheader("Quality Assurance Loop")

        if not st.session_state["script_content"]:
            st.warning("No script to edit.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text_area("Current Script:", value=st.session_state["script_content"], height=400)

            with col2:
                st.metric(label="Quality Score", value=f"{st.session_state['editor_score']}/10")
                
                if st.button("🕵️ Run Review", type="primary"):
                    with st.spinner("Editor is reviewing..."):
                        response = run_hooked_agent(editor_agent, st.session_state["script_content"])
                        try:
                            data = json.loads(response)
                            
                            # UPDATE STATE
                            st.session_state["editor_score"] = data.get("score", 0)
                            st.session_state["editor_feedback"] = data.get("critique", "No feedback")
                            st.session_state["is_approved"] = data.get("approved", False)
                            
                            # UPDATE DB
                            db.update_editor_stats(
                                st.session_state["current_project_id"],
                                st.session_state["editor_feedback"],
                                st.session_state["editor_score"],
                                st.session_state["is_approved"]
                            )

                            if st.session_state["is_approved"]:
                                st.balloons()
                                navigate_to("4. Art Dept")
                            else:
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Parser Error: {e}")
                
                if not st.session_state["is_approved"] and st.session_state["editor_score"] > 0:
                    if st.button("⬅️ Send back to Writer"):
                        navigate_to("2. Writer's Room")

    # === STAGE 4: VISUALS ===
    elif st.session_state["current_step"] == "4. Art Dept":
        st.subheader("Storyboard & Production")

        if not st.session_state["is_approved"]:
            st.warning("⚠️ Script not approved yet.")
        
        if st.button("🎨 Generate Storyboards", type="primary"):
            with st.spinner("Generating visuals..."):
                response = run_hooked_agent(storyboard_agent, st.session_state["script_content"])
                
                # UPDATE STATE & DB
                st.session_state["storyboard_output"] = response
                db.update_project_field(st.session_state["current_project_id"], "storyboard_output", response)
                
                st.rerun()

       
        if st.session_state["storyboard_output"]:
            st.markdown(st.session_state["storyboard_output"])
            st.markdown("---")
            st.download_button(
                label="📥 Download Script",
                data=st.session_state["script_content"],
                file_name="screenplay_final.txt"
            )