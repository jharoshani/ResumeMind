import sys
import os
# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai_engine import calculate_match

def test_nlp_engine():
    print("==================================================")
    print("Testing ResumeMind UPGRADED Multi-Factor Matching Engine")
    print("==================================================")
    
    # 1. Define a sample Job Description
    job_description = """
    We are looking for a Senior Software Engineer to join our backend team.
    The ideal candidate should have 5+ years of experience with Flask, REST APIs, and MongoDB.
    Key skills: Python, Flask, REST API, MongoDB, AWS, Docker, Kubernetes.
    Experience in leading small teams or project architecture is a plus.
    """
    
    # 2. Define two sample Resumes
    # Resume A: Excellent fit (Senior, 6 years YoE, action verbs, metrics, contact info, standard sections)
    resume_a = """
    Aman Gupta
    Senior Software Developer | Email: aman@example.com | Phone: 123-456-7890
    
    Experience:
    - Spearheaded and designed web applications using Python and Flask framework from 2020 - Present.
    - Led a team of 3 developers to architect and implement robust REST APIs for backend microservices.
    - Optimized MongoDB queries, reducing database load by 35% and improving latency by 120ms.
    - Deployed containerized applications to AWS using Docker and Kubernetes.
    - Worked as a Software Engineer at XYZ Corp from 2018 - 2020.
    
    Education:
    - B.Tech in Computer Science, NIT Jamshedpur (2014 - 2018).
    
    Skills: Python, Flask, REST API, MongoDB, AWS, Docker, Kubernetes, SQL, Git, Leadership.
    """
    
    # Resume B: Poor/average fit (Junior, low tenure, missing section headers, no metrics, missing contact info)
    resume_b = """
    John Doe
    Junior Software Developer
    
    Experience:
    - Helped with building small components in Python.
    - Worked on basic SQL tables and did some minor debugging.
    - Did a 6-month internship in 2024.
    
    Skills: Python, SQL.
    """
    
    print("\n--- Running Multi-Factor Analysis ---")
    
    # Calculate matches
    match_a = calculate_match(job_description, resume_a)
    match_b = calculate_match(job_description, resume_b)
    
    # Output results for Candidate A
    print("\n==================================================")
    print(f"CANDIDATE A (Aman Gupta):")
    print(f"Match Score: {match_a['match_percentage']}%")
    print(f"Sub-Scores Breakdown:")
    print(f"  - Core Match (max 40): {match_a['breakdown']['core']}")
    print(f"  - Experience & Tenure (max 30): {match_a['breakdown']['experience']}")
    print(f"  - Impact Quality (max 20): {match_a['breakdown']['quality']}")
    print(f"  - Formatting (max 10): {match_a['breakdown']['format']}")
    
    print(f"\nMatched Skills ({len(match_a['matched_skills'])}): {', '.join(match_a['matched_skills'])}")
    print(f"Missing Core Skills ({len(match_a['missing_skills'])}): {', '.join(match_a['missing_skills'])}")
    
    print(f"\nCoaching Action Plan:")
    for tip in match_a['coaching_tips']:
        print(f"  [TIP] {tip}")
        
    print(f"\nStructure Warnings:")
    for warn in match_a['warnings']:
        print(f"  [WARN] {warn}")
    if not match_a['warnings']:
        print("  None - formatting is perfect!")
    print("==================================================")

    # Output results for Candidate B
    print("\n==================================================")
    print(f"CANDIDATE B (John Doe):")
    print(f"Match Score: {match_b['match_percentage']}%")
    print(f"Sub-Scores Breakdown:")
    print(f"  - Core Match (max 40): {match_b['breakdown']['core']}")
    print(f"  - Experience & Tenure (max 30): {match_b['breakdown']['experience']}")
    print(f"  - Impact Quality (max 20): {match_b['breakdown']['quality']}")
    print(f"  - Formatting (max 10): {match_b['breakdown']['format']}")
    
    print(f"\nMatched Skills ({len(match_b['matched_skills'])}): {', '.join(match_b['matched_skills'])}")
    print(f"Missing Core Skills ({len(match_b['missing_skills'])}): {', '.join(match_b['missing_skills'])}")
    
    print(f"\nCoaching Action Plan:")
    for tip in match_b['coaching_tips']:
        print(f"  [TIP] {tip}")
        
    print(f"\nStructure Warnings:")
    for warn in match_b['warnings']:
        print(f"  [WARN] {warn}")
    print("==================================================")

if __name__ == "__main__":
    test_nlp_engine()
