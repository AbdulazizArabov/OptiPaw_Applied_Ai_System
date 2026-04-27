# Model Card

## System Limitations and Biases

- The scheduler is designed for simple pet care task planning and may not generalize to large, complex task sets.
- The AI answer flow in `rag_engine.py` relies on a local static context file (`study_notes.txt`) and may return incorrect or incomplete responses if the query is outside the notes.
- Task priority and time scheduling assume tasks are independent; overlapping tasks are detected but the system does not automatically resolve scheduling trade-offs beyond warnings.

- **Data Bias:** The RAG system only knows what is in `study_notes.txt`. If a user asks about a specific exotic pet (like a hedgehog), the system will return a low confidence score because the data is biased toward cats and dogs.

- **Scope Bias:** The RAG system is limited to the `study_notes.txt`. It cannot provide medical advice for exotic animals not covered in the text, such as reptiles or amphibians.

## Potential Misuse and Preventative Measures
- **Medical Dependency:** Users might treat the AI as a veterinarian.
- **Prevention:** I added a "Guardrail" that triggers a polite refusal with low confidence scores for out-of-scope questions, and added a specific "Contact vet" recommendation in the knowledge base.
- **Emergency Misuse:** A user might try to use the chat for a pet emergency.
- **Prevention:** I implemented a "Confidence Score" and hardcoded a disclaimer: "Contact vet immediately for emergencies" within the knowledge base to ensure the model prioritizes professional help for high-risk keywords.

- Misuse: treating the app as a substitute for professional veterinary advice.
- Preventative measure: add clear disclaimers in the UI and documentation that the app is for planning and educational purposes only.
- Misuse: relying on the RAG engine for medical or emergency instructions.
- Preventative measure: require explicit confirmation that the answer is based on local notes and not a certified source.

## Surprises during Testing

- The test harness exposed cases where the scheduler’s earliest-gap logic differed from expected behavior, highlighting the importance of clear test expectations.
- Recurrence handling required careful separation of completed tasks and newly generated recurring copies to avoid duplicate scheduling.
- The human-facing test runner helped find keyword-based response failures in the retrieval pathway more quickly than manual checks.

## AI Collaboration Reflection

- Helpful: AI assisted in structuring the scheduling backend and suggesting modular test cases for the scheduler.
- Helpful: AI made it easier to draft documentation and identify the key architectural components for the README.
- Flawed: AI-generated suggestions sometimes assumed a single-file solution rather than the actual multi-module Streamlit + scheduler + evaluation architecture.
- Flawed: Some proposed test scenarios needed adjustment after the actual scheduling logic was reviewed and validated against the code.
