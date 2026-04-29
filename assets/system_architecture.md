# PawPal+ System Architecture

> Export this diagram as a PNG using [Mermaid Live Editor](https://mermaid.live) and save as `architecture.png` in this folder.

```mermaid
graph TD
    User["👤 User"]
    UI["🌐 Streamlit UI\napp.py"]
    Logic["🧠 Logic Layer\npawpal_system.py"]
    Scheduler["📅 Scheduler\n(sort · filter · plan · conflicts)"]
    Owner["👤 Owner"]
    Pet["🐾 Pet"]
    Task["✅ Task"]
    AI["🤖 AI Advisor\nai_advisor.py"]
    Claude["☁️ Claude API\nclaude-haiku-4-5"]
    Harness["🧪 Test Harness\ntest_harness.py"]
    Report["📊 Pass/Fail Report\n+ Confidence Scores"]
    Session["💾 Session State\n(in-memory)"]
    Log["📋 Logger\npawpal_system logs"]

    User -->|"enters data"| UI
    UI -->|"creates objects"| Logic
    Logic --> Owner
    Logic --> Pet
    Logic --> Task
    Logic --> Scheduler
    Scheduler -->|"analyze_schedule()"| AI
    AI -->|"prompt + context"| Claude
    Claude -->|"explanation + confidence"| AI
    AI -->|"result dict"| UI
    Scheduler -->|"run scenarios"| Harness
    Harness --> Report
    UI -->|"persists state"| Session
    Logic -->|"logs events"| Log
```

## Data Flow Summary

1. **User** enters owner/pet/task info in the Streamlit UI
2. **UI** creates `Owner`, `Pet`, `Task` objects and stores them in session state
3. **Scheduler** sorts, filters, and plans tasks using priority + time logic
4. When user clicks **Get AI Analysis**, `ai_advisor.py` sends the plan + pet health context to Claude
5. **Claude** (haiku model) returns an explanation, health flags, and confidence score
6. **Test Harness** can be run independently to evaluate scheduler reliability across 6 scenarios

## Components

| Component | File | Role |
|---|---|---|
| Streamlit UI | `app.py` | User-facing interface, session state management, guardrails |
| Logic Layer | `pawpal_system.py` | Task/Pet/Owner/Scheduler classes with logging |
| AI Advisor | `ai_advisor.py` | Agentic reasoning — sends schedule to Claude, parses response |
| Test Harness | `test_harness.py` | Automated evaluation: 6 scenarios, pass/fail + confidence |
| Unit Tests | `tests/test_pawpal.py` | 25 pytest tests covering all scheduler behaviors |
