from researchcrew.models import ResearchPlan, ResearchFinding, ResearchReport

def test_research_plan():
    plan = ResearchPlan(
        topic="Quantum computing",
        sub_questions=["What is qubit?", "How does entanglement work?"],
        scope="Overview of quantum computing fundamentals",
        estimated_depth="moderate",
    )
    assert plan.topic == "Quantum computing"
    assert len(plan.sub_questions) == 2

def test_research_finding():
    f = ResearchFinding(
        sub_question="What is a qubit?",
        key_points=["A qubit is a quantum bit", "It can be 0, 1, or superposition"],
        confidence="high",
    )
    assert f.confidence == "high"
    assert len(f.key_points) == 2

def test_research_report():
    finding = ResearchFinding(
        sub_question="Q?",
        key_points=["Point 1", "Point 2"],
        confidence="medium",
    )
    report = ResearchReport(
        title="Test Report",
        executive_summary="Summary here.",
        findings=[finding],
        conclusions=["Conclusion 1"],
        further_research=["Area 1"],
    )
    assert "training knowledge" in report.sources_note
