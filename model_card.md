# Model Card

## System Limitations and Biases

- I designed the scheduler for simple pet care task planning; it may not generalize to large, complex task sets.
- I built the AI answer flow in `rag_engine.py` to rely on a local static context file (`study_notes.txt`); it may return incorrect responses if the query is outside those notes.
- My task priority logic assumes tasks are independent; I implemented conflict detection, but the system does not automatically resolve scheduling trade-offs beyond providing warnings.

## Potential Misuse and Preventative Measures

- I identified a potential misuse: users treating the app as a substitute for professional veterinary advice. 
- My preventative measure: I added clear disclaimers in the UI that the app is for planning and educational purposes only.
- I am aware of the risk of users relying on the RAG engine for medical instructions. 
- My preventative measure: I designed the UI to explicitly show confidence scores and mention that answers are based on local notes.

## Challenges and Surprises during Testing

- I encountered significant hurdles setting up the **Gemini API and RAG pipeline**. Initially, authentication was failing and the vectorizer was not correctly parsing `study_notes.txt`. I fixed these by implementing a custom environment loader and a knowledge base caching system.
- My test harness exposed cases where the scheduler’s earliest-gap logic differed from my expectations, which forced me to refine the algorithm.
- I found that recurrence handling required careful separation of completed tasks and newly generated recurring copies to avoid duplicate scheduling.

## My AI Collaboration Reflection

- **Helpful:** AI assisted me in structuring the scheduling backend and suggesting modular test cases for the scheduler.
- **Helpful:** AI made it easier for me to draft documentation and identify the key architectural components.
- **Flawed:** I noticed that AI-generated suggestions sometimes assumed a single-file solution rather than the actual multi-module architecture I was building.
- **Flawed:** I had to adjust several proposed test scenarios because they didn't align with how I ultimately implemented the scheduling logic.
