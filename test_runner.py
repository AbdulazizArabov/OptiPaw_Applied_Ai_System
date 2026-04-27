import rag_engine

TEST_CASES = [
    {
        "query": "How often should a dog be fed?",
        "expected_keyword": "2-3 times a day",
    },
    {
        "query": "What should a cat have for its litter area?",
        "expected_keyword": "litter",
    },
    {
        "query": "Why are vaccinations important for pets?",
        "expected_keyword": "vaccinations",
    },
    {
        "query": "Which activities help keep a dog active?",
        "expected_keyword": "walks",
    },
    {
        "query": "What is the recommended action when a pet shows emergency symptoms?",
        "expected_keyword": "vet",
    },
]


def normalize_text(text):
    """Standardize characters for more reliable keyword matching."""
    if not text: return ""
    return text.lower().replace('–', '-').replace('—', '-').strip()


def run_tests():
    passed = 0
    total = len(TEST_CASES)

    print("Running RAG engine test harness...")

    for index, case in enumerate(TEST_CASES, start=1):
        query = case["query"]
        expected_keyword = case["expected_keyword"]

        print(f"\nTest {index}/{total}: {query}")
        answer_text, confidence = rag_engine.get_rag_answer(query)
        print(f"Answer: {answer_text} (Confidence: {confidence:.2f})")

        if normalize_text(expected_keyword) in normalize_text(answer_text):
            print("Result: PASS")
            passed += 1
        else:
            print("Result: FAIL")
            print(f"Expected keyword not found: '{expected_keyword}'")

    confidence_score = passed / total * 100
    print("\nTest summary")
    print("------------")
    print(f"Passed: {passed}/{total}")
    print(f"Confidence score: {confidence_score:.0f}%")

    return passed, total


if __name__ == "__main__":
    run_tests()
