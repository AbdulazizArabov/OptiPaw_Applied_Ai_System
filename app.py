import streamlit as st
import base64
from datetime import datetime
from pathlib import Path
from pawpal_system import Owner, Pet, Task, Scheduler
import rag_engine

# Page configuration
st.set_page_config(
    page_title="OptiPaw - AI Pet Care Companion",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = Path(__file__).parent / "data.json"
ASSETS_DIR = Path(__file__).parent / "assets"

# -------------------------------------------------------------------
# WARM & MODERN CSS THEME
# -------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    /* Root variables for consistent theming */
    :root {
        --primary-color: #E67E22;
        --secondary-color: #F39C12;
        --accent-color: #E74C3C;
        --warm-bg: #FDF8F3;
        --card-bg: #FFFFFF;
        --text-primary: #2C3E50;
        --text-secondary: #7F8C8D;
        --border-color: #ECF0F1;
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        --border-radius: 12px;
    }

    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, var(--warm-bg) 0%, #FAF6F0 100%);
        font-family: 'Nunito', sans-serif;
    }

    /* Main content area */
    .main {
        background-color: transparent;
        padding: 2rem;
    }

    /* Headers with warm styling */
    h1, h2, h3, h4 {
        font-family: 'Nunito', sans-serif;
        color: var(--text-primary);
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
    }

    h1 {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    /* Card-based sections */
    .card {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        color: white !important;
        border-radius: var(--border-radius) !important;
       
    }

    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8F3ED 0%, #F0EBE3 100%);
        border-right: 3px solid var(--primary-color);
        padding: 2rem 1rem;
    }

    /* Buttons with warm gradient */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #E67E22 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Primary button variant */
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-color) 0%, #C0392B 100%) !important;
    }

    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #C0392B 0%, var(--accent-color) 100%) !important;
    }

    /* Secondary button variant */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #95A5A6 0%, #7F8C8D 100%) !important;
        color: white !important;
    }

    /* Input fields with warm styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: var(--card-bg) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        padding: 0.75rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(230, 126, 34, 0.1) !important;
        outline: none !important;
    }

    /* Dropdown styling */
    .stSelectbox > div > div > select {
        background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23E67E22' stroke-width='2'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e") !important;
        background-repeat: no-repeat !important;
        background-position: right 12px center !important;
        background-size: 1.2em !important;
        padding-right: 40px !important;
        cursor: pointer !important;
    }

    /* Labels */
    label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }

    /* Success/Warning/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #D4EDDA 0%, #C3E6CB 100%) !important;
        border-left: 4px solid #28A745 !important;
        color: #155724 !important;
        border-radius: var(--border-radius) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }

    .stWarning {
        background: linear-gradient(135deg, #FFF3CD 0%, #FFEAA7 100%) !important;
        border-left: 4px solid #FFC107 !important;
        color: #856404 !important;
        border-radius: var(--border-radius) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }

    .stError {
        background: linear-gradient(135deg, #F8D7DA 0%, #F5C6CB 100%) !important;
        border-left: 4px solid #DC3545 !important;
        color: #721C24 !important;
        border-radius: var(--border-radius) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }

    .stInfo {
        background: linear-gradient(135deg, #D1ECF1 0%, #BEE5EB 100%) !important;
        border-left: 4px solid #17A2B8 !important;
        color: #0C5460 !important;
        border-radius: var(--border-radius) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }

    /* Tables */
    .stTable {
        background: var(--card-bg) !important;
        border-radius: var(--border-radius) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow) !important;
    }

    .stTable table {
        width: 100% !important;
        border-collapse: collapse !important;
    }

    .stTable th {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        text-align: left !important;
    }

    .stTable td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    .stTable tr:nth-child(even) {
        background-color: #FAF9F8 !important;
    }

    .stTable tr:hover {
        background-color: #F0EBE3 !important;
    }

    /* Metrics cards */
    .stMetric {
        background: var(--card-bg) !important;
        border-radius: var(--border-radius) !important;
        padding: 1.5rem !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border-color) !important;
        text-align: center !important;
    }

    .stMetric label {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    .stMetric .metric-value {
        color: var(--primary-color) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0.5rem 0 !important;
    }

    /* Chat messages */
    .chat-user {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        color: white !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 1rem 1.5rem !important;
        margin: 0.5rem 0 !important;
        max-width: 80% !important;
        margin-left: auto !important;
        box-shadow: var(--shadow) !important;
    }

    .chat-assistant {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 1rem 1.5rem !important;
        margin: 0.5rem 0 !important;
        max-width: 80% !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow) !important;
    }

    /* Expandable sections */
    .streamlit-expanderHeader {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius) !important;
        padding: 1rem 1.5rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow) !important;
    }

    .streamlit-expanderContent {
        background: var(--warm-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 var(--border-radius) var(--border-radius) !important;
        padding: 1.5rem !important;
    }

    /* Form styling */
    .stForm {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius) !important;
        padding: 2rem !important;
        box-shadow: var(--shadow) !important;
    }

    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
    }

    /* Dividers */
    hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%) !important;
        margin: 2rem 0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--warm-bg);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SIDEBAR - Clean and informative
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: var(--primary-color); margin-bottom: 0.5rem;">🐾 OptiPaw</h2>
        <p style="color: var(--text-secondary); font-size: 0.9rem;">AI Pet Care Companion</p>
    </div>
    """, unsafe_allow_html=True)

    # System status
    st.markdown("### System Status")
    ai_status = "🟢 Online" if rag_engine.is_api_configured() else "🔴 Offline"
    st.write(f"AI Assistant: **{ai_status}**")
    if not rag_engine.is_api_configured():
        st.warning("⚠️ AI features are disabled. Check your `.env` or `gem.env` file.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tasks", len([t for p in st.session_state.get('owner', Owner("Default", "", 90)).get_pets() for t in p.get_tasks()]))
    with col2:
        st.metric("Pets", len(st.session_state.get('owner', Owner("Default", "", 90)).get_pets()))

    st.divider()

    # Quick actions
    st.markdown("### Quick Actions")
    if st.button("Generate Schedule", use_container_width=True):
        st.info("💡 Scroll down to the Schedule Generation section to create your pet care schedule!")

    if st.button("Ask AI Assistant", use_container_width=True):
        st.info("💡 Scroll down to the AI Pet Care Assistant section to ask questions!")

    st.divider()

    # Tips
    st.markdown("### 💡 Pro Tips")
    st.info("Set your daily time budget first for better scheduling.")
    st.info("Use the AI assistant for pet care questions anytime.")

# -------------------------------------------------------------------
# HERO SECTION
# -------------------------------------------------------------------
hero_image_path = ASSETS_DIR / "main_update.jpg"
if hero_image_path.exists():
    with open(hero_image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <div style='
        background: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.25)), 
                    url("data:image/jpg;base64,{img_b64}");
        background-size: cover;
        background-position: center;
        min-height: 450px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        padding: 3rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    '>
        <h1 style="
            font-color: white !important;
            font-size: 3.2rem; 
            margin-bottom: 1rem; 
            color: white !important; 
            -webkit-text-fill-color: white !important;
            # text-shadow: 2px 2px 10px rgba(0,0,0,0.7);
        ">OptiPaw Applied AI System</h1>
        <p style="font-size: 1.4rem; color: white; max-width: 800px; margin: 0 auto; font-weight: 500; text-shadow: 1px 1px 5px rgba(0,0,0,0.7);">
            Your intelligent companion for pet care scheduling and advice.
            Plan tasks, track routines, and get instant AI-powered guidance.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align: center; margin-bottom: 2rem; padding: 2rem; background: var(--card-bg); border-radius: var(--border-radius);'><h1>OptiPaw Applied AI System</h1><p>🐾 <i>Your pets deserve the best care</i></p></div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------------
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except FileNotFoundError:
        st.session_state.owner = Owner("Pet Parent", "", 90)

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------------------------------------------------------
# OWNER PROFILE CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 👤 Owner Profile")

col1, col2 = st.columns([2, 1])
with col1:
    owner_name = st.text_input("Your Name", value=st.session_state.owner.name, key="owner_name")
with col2:
    available_minutes = st.number_input(
        "Daily Time Budget (minutes)",
        min_value=30,
        max_value=480,
        value=st.session_state.owner.available_minutes_per_day,
        key="time_budget"
    )

if st.button("Save Profile", type="primary"):
    st.session_state.owner = Owner(owner_name, "", int(available_minutes))
    st.session_state.owner.save_to_json(DATA_FILE)
    st.session_state.last_plan = None
    st.success(f"✅ Profile saved: {owner_name} with {available_minutes} min/day budget")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# PETS MANAGEMENT CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 🐕 Pets")

# Add new pet form
st.markdown("### Add New Pet")
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
with col1:
    pet_name = st.text_input("Pet Name", placeholder="e.g., Max", key="pet_name")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"], key="pet_species")
with col3:
    age = st.number_input("Age", min_value=0, max_value=30, value=1, key="pet_age")
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Add Pet", type="primary", use_container_width=True):
        existing_names = [p.name for p in st.session_state.owner.get_pets()]
        if pet_name.strip() in existing_names:
            st.error(f"❌ A pet named '{pet_name}' already exists.")
        elif not pet_name.strip():
            st.error("❌ Please enter a pet name.")
        else:
            st.session_state.owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
            st.session_state.owner.save_to_json(DATA_FILE)
            st.success(f"✅ {pet_name} has been added to your pets!")
            st.rerun()

# Display current pets
pets = st.session_state.owner.get_pets()
if pets:
    st.markdown("### Your Pets")
    pet_data = []
    for p in pets:
        pet_data.append({
            "Name": p.name,
            "Species": p.species.title(),
            "Age": f"{p.age} years",
            "Tasks": len(p.get_tasks()),
            "Total Time": f"{p.total_duration()} min"
        })

    if pet_data:
        st.table(pet_data)
else:
    st.info("🐾 No pets added yet. Add your first pet above!")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# TASKS MANAGEMENT CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 📋 Tasks")

pet_names = [p.name for p in st.session_state.owner.get_pets()]

if not pet_names:
    st.warning("⚠️ Please add at least one pet before creating tasks.")
else:
    # Add new task form
    with st.form("add_task_form", clear_on_submit=True):
        st.markdown("### Create New Task")

        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task Title", placeholder="e.g., Morning walk")
            category = st.selectbox("Category", ["walk", "feeding", "meds", "play", "grooming", "training"])
            selected_pet_name = st.selectbox("Assign to Pet", pet_names)

        with col2:
            duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=30)
            priority = st.selectbox("Priority (1-5)", [1, 2, 3, 4, 5], index=3,
                                  help="1=Low, 5=High priority")

        col3, col4 = st.columns(2)
        with col3:
            due_time = st.text_input("Due Time (optional)", placeholder="HH:MM, e.g., 08:00")
            recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])

        with col4:
            recur_day = st.selectbox("Day (weekly only)",
                                   ["—", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

        submitted = st.form_submit_button("Create Task", type="primary")

    if submitted:
        # Validate inputs
        errors = []
        if not task_title.strip():
            errors.append("Task title is required")
        if duration < 5:
            errors.append("Duration must be at least 5 minutes")

        # Validate due time format
        due_time_clean = due_time.strip()
        if due_time_clean:
            try:
                datetime.strptime(due_time_clean, "%H:%M")
            except ValueError:
                errors.append("Due time must be in HH:MM format (e.g., 08:00)")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Create task
            day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

            task = Task(
                name=task_title.strip(),
                category=category,
                duration_minutes=int(duration),
                priority=int(priority),
                due_time=due_time_clean if due_time_clean else None,
                recurrence=recurrence if recurrence != "none" else None,
                recur_day=day_map.get(recur_day) if recur_day != "—" else None,
            )

            target_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)
            target_pet.add_task(task)
            st.session_state.owner.save_to_json(DATA_FILE)
            st.session_state.last_plan = None
            st.success(f"✅ '{task_title}' added to {selected_pet_name}'s schedule!")

    # Display current tasks
    any_tasks = any(p.get_tasks() for p in st.session_state.owner.get_pets())
    if any_tasks:
        st.markdown("### Current Tasks")
        for p in st.session_state.owner.get_pets():
            if not p.get_tasks():
                continue

            with st.expander(f"📋 {p.name} — {len(p.get_tasks())} tasks, {p.total_duration()} min total"):
                task_rows = []
                for t in p.get_tasks():
                    task_rows.append({
                        "Task": t.name,
                        "Category": t.category.title(),
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": t.priority_label,
                        "Due Time": t.due_time or "—",
                        "Recurrence": t.recurrence or "One-time",
                        "Status": "✅ Complete" if t.is_complete else "⏳ Pending"
                    })
                st.table(task_rows)
    else:
        st.info("📝 No tasks created yet. Add your first task above!")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# AI ASSISTANT CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 🤖 AI Pet Care Assistant")

st.markdown("Get instant, AI-powered answers to your pet care questions!")

# Chat history display
if st.session_state.chat_history:
    st.markdown("### Conversation History")
    chat_container = st.container(height=300)
    with chat_container:
        for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
            if message["role"] == "user":
                st.markdown(f'<div class="chat-user"><strong>You:</strong> {message["content"]}</div>',
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant"><strong>🐾 Assistant:</strong> {message["content"]}</div>',
                          unsafe_allow_html=True)

# Chat input
col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input(
        "Ask about pet care...",
        placeholder="e.g., 'How often should I feed my dog?' or 'What are signs of illness?'",
        key="chat_input",
        label_visibility="collapsed"
    )
with col2:
    send_disabled = not user_question.strip()
    send_chat = st.button("Send", type="primary", disabled=send_disabled, use_container_width=True)

if send_chat and user_question.strip():
    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question.strip()
    })

    # Get AI response
    with st.spinner("🐾 Thinking..."):
        try:
            answer, confidence = rag_engine.get_rag_answer(user_question.strip())
            display_answer = f"{answer}\n\n*Confidence Score: {confidence:.2f}*"
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": display_answer
            })
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error getting AI response: {str(e)}")

# Sample questions - simplified as quick suggestions
with st.expander("💡 Quick Question Starters"):
    st.markdown("Click any question below to ask the AI:")
    sample_questions = [
        "How often should I feed my dog?",
        "What vaccinations do cats need?",
        "How much exercise does a puppy need?",
        "What are signs of pet illness?",
        "How do I prevent pet obesity?",
        "What should I do if my cat won't eat?"
    ]

    # Display as simple clickable text
    for question in sample_questions:
        if st.button(question, key=f"sample_{question[:20]}", help="Click to ask this question", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.spinner("🐾 Getting answer..."):
                answer, confidence = rag_engine.get_rag_answer(question)
                display_answer = f"{answer}\n\n*Confidence Score: {confidence:.2f}*"
                st.session_state.chat_history.append({"role": "assistant", "content": display_answer})
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# SCHEDULE GENERATION CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 📅 Schedule Generation")

# Check if we have tasks to schedule
has_tasks = any(p.get_tasks() for p in st.session_state.owner.get_pets())

if not has_tasks:
    st.warning("⚠️ No tasks to schedule. Please add some tasks first.")
else:
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        strategy = st.selectbox(
            "Scheduling Strategy",
            ["priority-first", "time-first", "priority-time"],
            help="priority-first: High priority tasks first | time-first: Earliest deadlines first | priority-time: Priority then earliest deadline"
        )

    with col2:
        filter_options = ["All Pets"] + [p.name for p in st.session_state.owner.get_pets()]
        pet_filter = st.selectbox("Filter by Pet", filter_options)

    with col3:
        generate = st.button("Generate Schedule", type="primary", use_container_width=True)

    if generate:
        scheduler = Scheduler(owner=st.session_state.owner, strategy=strategy)
        plan = scheduler.generate_plan(
            pet_name_filter=None if pet_filter == "All Pets" else pet_filter,
            include_complete=False,
        )
        st.session_state.last_plan = plan

# Display generated schedule
plan = st.session_state.last_plan
if plan is not None:
    # Schedule metrics
    st.markdown("### 📊 Schedule Overview")
    budget = st.session_state.owner.get_available_time()
    used = plan.total_time_used
    remaining = budget - used

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tasks Scheduled", len(plan.scheduled_entries))
    with col2:
        st.metric("Time Used", f"{used} min")
    with col3:
        st.metric("Time Budget", f"{budget} min")
    with col4:
        remaining_color = "normal" if remaining >= 0 else "inverse"
        st.metric("Remaining Time", f"{remaining} min", delta=f"{abs(remaining)} min" if remaining < 0 else None, delta_color=remaining_color)

    # Conflicts warning
    if plan.conflicts:
        st.error("⚠️ Scheduling Conflicts Detected:")
        for conflict in plan.conflicts:
            st.error(f"• {conflict}")

    # Scheduled tasks table
    if plan.scheduled_entries:
        st.markdown("### 📋 Your Schedule")
        schedule_data = []
        for entry in plan.scheduled_entries:
            t = entry.task
            schedule_data.append({
                "Pet": entry.pet_name,
                "Task": t.name,
                "Category": t.category.title(),
                "Priority": t.priority_label,
                "Due Time": t.due_time or "—",
                "Duration": f"{t.duration_minutes} min",
                "Recurrence": t.recurrence or "One-time"
            })

        st.table(schedule_data)

        # Task completion
        st.markdown("### ✅ Mark Tasks Complete")
        if plan.scheduled_entries:
            col1, col2 = st.columns([3, 1])
            with col1:
                task_options = [f"{e.pet_name} → {e.task.name}" for e in plan.scheduled_entries]
                selected_task = st.selectbox("Select completed task", task_options)
            with col2:
                if st.button("Mark Done", type="secondary", use_container_width=True):
                    selected_entry = plan.scheduled_entries[task_options.index(selected_task)]
                    try:
                        pet_obj = next(p for p in st.session_state.owner.get_pets() if p.name == selected_entry.pet_name)
                        scheduler = Scheduler(owner=st.session_state.owner, strategy=strategy)
                        next_task = scheduler.mark_task_complete(selected_entry.task.name, pet_obj)
                        st.session_state.owner.save_to_json(DATA_FILE)
                        st.session_state.last_plan = None

                        if next_task is not None:
                            st.success(f"✅ Task completed! Next occurrence scheduled.")
                        else:
                            st.success(f"✅ '{selected_entry.task.name}' marked complete.")
                    except ValueError as e:
                        st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ No tasks could be scheduled within your time budget.")

    # Scheduling reasoning
    with st.expander("🔍 Scheduling Details"):
        st.info(plan.reasoning)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# SLOT FINDER CARD
# -------------------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 🔍 Find Available Time Slot")

st.markdown("Find the next available time slot that fits a new task without conflicting with your schedule.")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    slot_duration = st.number_input("Task Duration (minutes)", min_value=5, max_value=480, value=30, key="slot_duration")
with col2:
    slot_search_from = st.text_input("Search From Time (optional)", placeholder="HH:MM, e.g., 09:00", key="slot_search_from")
with col3:
    find_slot = st.button("Find Slot", type="secondary", use_container_width=True)

if find_slot:
    search_from_min = None
    valid = True

    if slot_search_from.strip():
        try:
            parsed = datetime.strptime(slot_search_from.strip(), "%H:%M")
            search_from_min = parsed.hour * 60 + parsed.minute
        except ValueError:
            st.error("❌ Invalid time format. Use HH:MM (e.g., 09:00)")
            valid = False

    if valid:
        current_entries = (
            st.session_state.last_plan.scheduled_entries
            if st.session_state.last_plan is not None
            else []
        )
        scheduler = Scheduler(owner=st.session_state.owner)
        result = scheduler.suggest_slot(
            duration_minutes=int(slot_duration),
            entries=current_entries,
            search_from=search_from_min,
        )

        if result:
            st.success(f"✅ Next available slot: **{result}** (fits {slot_duration} minutes)")
        else:
            st.warning(f"⚠️ No available slot found for a {slot_duration}-minute task today.")

        if st.session_state.last_plan is None:
            st.info("💡 Tip: Generate a schedule first for more accurate slot suggestions.")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------------
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; background: var(--card-bg); border-radius: var(--border-radius); box-shadow: var(--shadow);">
    <h3 style="color: var(--primary-color); margin-bottom: 1rem;">🐾 Happy Pet Parenting!</h3>
    <p style="color: var(--text-secondary); margin-bottom: 0;">
        OptiPaw helps you provide the best care for your furry friends.
        Remember: A well-planned schedule means happier, healthier pets!
    </p>
</div>
""", unsafe_allow_html=True)
