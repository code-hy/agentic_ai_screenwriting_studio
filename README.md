Here is a comprehensive `README.md` file for your project. It documents the architecture, the agent personas, the workflow, and specifically how the Google Agent Development Kit is utilized.

***

# 🎬 Agentic Screenwriting Studio

**A multi-agent AI system powered by the Google Agent Development Kit (ADK) and Gemini models.**

This application simulates a Hollywood creative studio where a team of specialized AI agents collaborate to turn a raw story idea into a greenlit screenplay and visual storyboard. It features a Streamlit UI, SQLite state management, and a "Human-in-the-loop" feedback system.

---

## 🌟 Key Features

*   **Multi-Agent Workflow:** Four distinct agents (Researcher, Writer, Editor, Artist) pass context and deliverables between each other.
*   **Google ADK Integration:** Uses `LlmAgent`, `Runner`, and `SessionService` to manage complex conversational state and tool execution.
*   **Persistent Projects:** SQLite database stores every draft, critique, and storyboard, allowing users to switch between projects seamlessly.
*   **Quality Assurance Loop:** The "Editor" agent acts as a gatekeeper, rejecting scripts that don't meet quality standards and providing feedback for revisions.
*   **Visual Storyboarding:** The "Art Dept" agent uses function calling to generate mock visualizations of key scenes.

---

## 🤖 The Agents

The studio is staffed by four specialized `LlmAgents`:

### 1. 🧐 The Researcher
*   **Role:** Story Development & World Building.
*   **Input:** User's raw logline or vague idea.
*   **Task:** Refines the logline, creates character bios (Protagonist/Antagonist), and defines the setting and tone.
*   **Output:** A structured Research Brief.

### 2. ✍️ The Screenwriter
*   **Role:** Drafting.
*   **Input:** Research Brief + Editor Feedback + Manager (User) Notes.
*   **Task:** Writes scenes in standard Fountain/Screenplay format.
*   **Tools:** `save_script_to_file` (Simulates saving the draft).
*   **Output:** A full script draft.

### 3. 🕵️ The Editor
*   **Role:** Quality Assurance & Gatekeeping.
*   **Input:** The Script Draft.
*   **Task:** strict review of the script.
*   **Output:** A structured JSON object containing:
    *   `score`: (0-10)
    *   `critique`: Specific feedback on pacing, dialogue, etc.
    *   `approved`: Boolean flag (Greenlight/Reject).

### 4. 🎨 The Storyboard Artist
*   **Role:** Visualization.
*   **Input:** The "Greenlit" Script.
*   **Task:** Identifies key visual moments and generates images.
*   **Tools:** `generate_storyboard_image_mock` (Generates visual panels).
*   **Output:** A visual report embedded with image panels.

---

## ⚙️ How Google ADK is Used

This project relies heavily on the **Google Agent Development Kit** to orchestrate the AI logic.

### 1. Agent Definition (`LlmAgent`)
Each persona is defined using the `LlmAgent` class. We configure the specific `model` (Gemini 1.5 Flash) and provide strict system `instructions` to enforce the persona.

```python
writer_base = LlmAgent(
    name="screenwriter",
    model="gemini-1.5-flash",
    instruction="You are a professional Screenwriter...",
    tools=[save_script_to_file] # ADK handles tool binding automatically
)
```

### 2. The Runner Pattern
We do not call the LLM directly. Instead, we use the ADK `Runner`. The Runner handles:
*   Session context management (memory).
*   Automatic Function Calling (AFC) loops.
*   Event streaming (Text generation events vs. Tool use events).

### 3. Custom Hook Wrapper (`HookedAgent`)
To integrate ADK's asynchronous, event-driven architecture with Streamlit's synchronous UI, we built a `HookedAgent` wrapper.
*   **Event Parsing:** It iterates through the `runner.run()` event stream.
*   **Output Aggregation:** It intelligently combines standard text responses with "Function Response" events (images/tool outputs) into a single readable transcript for the UI.
*   **Context Injection:** It passes the `session_id` and `session_service` ensuring that the agents "remember" previous interactions within the session.

### 4. Tooling & Function Calling
We define Python functions (e.g., `save_script_to_file`) and pass them to the ADK agents. The ADK automatically parses the LLM's intent, executes the Python code, and feeds the result back to the LLM context.

---

## 🔄 Workflow Description

1.  **Project Creation:** The user starts a new project in the DB.
2.  **Research Phase:** User inputs an idea. The **Researcher** generates a brief. The result is saved to SQLite.
3.  **Writing Phase:** The brief is passed to the **Writer**. The Writer drafts a script.
4.  **Review Loop:**
    *   The **Editor** reviews the script.
    *   If `score < 7` or `approved == False`, the flow is sent *back* to the Writer with specific feedback.
    *   The User can add "Manager Notes" to override or guide the revision.
5.  **Approval:** Once the Editor returns `approved: true`, the "Greenlight" status is saved.
6.  **Production:** The **Storyboard Artist** reads the approved script and calls image generation tools to visualize the movie.

---

## 📂 Project Structure

```text
.
├── app.py           # Main Streamlit application (UI & Logic)
├── agent.py         # ADK Agent definitions & Runner wrapper
├── db.py            # SQLite database management
├── config.py        # Configuration & API Key setup
├── tools.py         # Python functions exposed to Agents
└── requirements.txt # Python dependencies
```

---

## 🚀 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/agentic-story-studio.git
    cd agentic-story-studio
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set your Google API Key:**
    *   Get a key from [Google AI Studio](https://aistudio.google.com/).
    *   Set it in your environment:
        *   **Mac/Linux:** `export GOOGLE_API_KEY="your_key_here"`
        *   **Windows (PowerShell):** `$env:GOOGLE_API_KEY="your_key_here"`

4.  **Run the Studio:**
    ```bash
    streamlit run app.py
    ```

---

## 🛠️ Requirements

*   Python 3.10+
*   `streamlit`
*   `google-adk`
*   `google-genai`

---

**Disclaimer:** This project uses generative AI. Output quality depends on the specific Gemini model version used and the complexity of the prompts. The "Image Generation" tool currently uses a placeholder service for demonstration purposes.