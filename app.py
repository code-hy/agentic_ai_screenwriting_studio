import streamlit as st
import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import setup_config
from agent import researcher_agent, writer_agent, editor_agent, storyboard_agent

# --- PAGE SETUP ---
st.set_page_config(page_title="Google ADK Story Studio", page_icon="🎬", layout="wide")

# --- INITIALIZATION & STATE ---
if "runner" not in st.session_state:
    # Initialize the ADK System
    config = setup_config()
    session_service = InMemorySessionService()
    session_id = session_service.create_session()
    
    st.session_state["runner"] = Runner(
        session_service=session_service,
        retry_policy=config.RETRY_POLICY
    )
    st.session_state["session_id"] = session_id
    
    # Initialize Data Store
    st.session_state["user_request"] = ""
    st.session_state["research_context"] = ""
    st.session_state["script_content"] = ""
    st.session_state["editor_feedback"] = "Initial Draft - No feedback yet."
    st.session_state["editor_score"] = 0
    st.session_state["is_approved"] = False
    st.session_state["storyboard_output"] = ""

# --- HELPER FUNCTIONS ---
async def run_adk_agent(agent, input_data):
    """Async wrapper to run ADK agents inside Streamlit."""
    runner = st.session_state["runner"]
    session_id = st.session_state["session_id"]
    return await runner.run_async(agent=agent, session_id=session_id, input=input_data)

def run_sync(agent, input_data):
    """Bridge between Streamlit sync UI and Async ADK."""
    return asyncio.run(run_adk_agent(agent, input_data))

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Studio Controls")
    st.info(f"Session ID: {st.session_state['session_id']}")
    
    st.markdown("### Workflow Status")
    if st.session_state["research_context"]:
        st.success("1. Research: Done")
    else:
        st.warning("1. Research: Pending")
        
    if st.session_state["script_content"]:
        st.success("2. Drafting: In Progress")
    else:
        st.warning("2. Drafting: Pending")
        
    if st.session_state["is_approved"]:
        st.success("3. Approval: GREENLIT ✅")
    else:
        st.error("3. Approval: Pending ❌")

    if st.button("🔄 Reset Studio"):
        st.session_state.clear()
        st.rerun()

# --- MAIN LAYOUT ---
st.title("🎬 Agentic Screenwriting Studio")
st.markdown("Powered by **Google Agent Development Kit**")

# Create Tabs for the different personas
tab_research, tab_writer, tab_editor, tab_visuals = st.tabs([
    "1. Research Dept", "2. Writer's Room", "3. Editor's Desk", "4. Art Dept"
])

# === TAB 1: RESEARCHER ===
with tab_research:
    st.subheader("Story Development")
    st.session_state["user_request"] = st.text_area(
        "Enter your Story Idea:", 
        value=st.session_state["user_request"],
        placeholder="e.g. A sci-fi thriller about a robot who wants to be a chef on Mars.",
        height=100
    )
    
    if st.button("Run Researcher Agent"):
        if not st.session_state["user_request"]:
            st.error("Please enter a story idea first.")
        else:
            with st.spinner("Researcher is analyzing market trends and character archetypes..."):
                # Run Agent
                response = run_sync(researcher_agent, {"user_request": st.session_state["user_request"]})
                st.session_state["research_context"] = response.text
                st.rerun()

    if st.session_state["research_context"]:
        st.markdown("---")
        st.subheader("Research Brief")
        # Allow Human-in-the-loop editing of research before passing to writer
        st.session_state["research_context"] = st.text_area(
            "Edit Research Brief (if needed):", 
            value=st.session_state["research_context"], 
            height=300
        )

# === TAB 2: WRITER ===
with tab_writer:
    st.subheader("Screenwriting Phase")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### Directives")
        st.caption("Current Feedback:")
        st.info(st.session_state["editor_feedback"])
        
        # Human Override
        manager_notes = st.text_area("Add Manager Notes:", placeholder="Override feedback here...")
        
        if st.button("✍️ Write / Revise Script"):
            if not st.session_state["research_context"]:
                st.error("Research is missing! Go to Tab 1.")
            else:
                with st.spinner("Writer is working..."):
                    # Construct detailed input for the writer
                    writer_input = {
                        "research_context": st.session_state["research_context"],
                        "feedback": st.session_state["editor_feedback"] + f"\nManager Notes: {manager_notes}"
                    }
                    response = run_sync(writer_agent, writer_input)
                    st.session_state["script_content"] = response.text
                    st.rerun()

    with col1:
        st.markdown("### Script Draft")
        if st.session_state["script_content"]:
            st.text_area("Output:", value=st.session_state["script_content"], height=600)
        else:
            st.info("No script generated yet. Click 'Write' in the sidebar.")

# === TAB 3: EDITOR ===
with tab_editor:
    st.subheader("Quality Assurance Loop")
    
    if not st.session_state["script_content"]:
        st.warning("No script to edit.")
    else:
        if st.button("Run Editor Review"):
            with st.spinner("Editor is reviewing pacing and dialogue..."):
                response = run_sync(editor_agent, st.session_state["script_content"])
                
                try:
                    # Parse JSON output
                    data = response.json()
                    st.session_state["editor_score"] = data.get("score", 0)
                    st.session_state["editor_feedback"] = data.get("critique", "No feedback")
                    st.session_state["is_approved"] = data.get("approved", False)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse Editor response: {e}")
                    st.code(response.text)

        # Dashboard
        score = st.session_state["editor_score"]
        st.metric(label="Quality Score", value=f"{score}/10")
        
        if st.session_state["is_approved"]:
            st.success("✅ STATUS: APPROVED")
            st.balloons()
        else:
            st.error("❌ STATUS: REVISION REQUESTED")
            
        st.markdown(f"**Critique:** {st.session_state['editor_feedback']}")

# === TAB 4: VISUALS ===
with tab_visuals:
    st.subheader("Storyboard & Production")
    
    if not st.session_state["is_approved"]:
        st.warning("⚠️ Script not yet approved by Editor. Proceed with caution.")
    
    if st.button("Generate Storyboards"):
        if not st.session_state["script_content"]:
            st.error("No script available.")
        else:
            with st.spinner("Art Department is generating assets..."):
                response = run_sync(storyboard_agent, st.session_state["script_content"])
                st.session_state["storyboard_output"] = response.text
    
    if st.session_state["storyboard_output"]:
        st.markdown("### Visual Plan")
        st.markdown(st.session_state["storyboard_output"])
        
        st.markdown("---")
        st.download_button(
            label="📥 Download Complete Package (Script)",
            data=st.session_state["script_content"],
            file_name="screenplay_final.txt",
            mime="text/plain"
        )