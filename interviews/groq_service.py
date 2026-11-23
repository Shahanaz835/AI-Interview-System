"""
Groq API Integration & Agentic Prompt Engineering Service
Connects Django to Groq Cloud for LLM inference (LLaMA-3.3 / LLaMA-3.1)
Handles question generation, answer evaluation, follow-up Q&A, and learning roadmaps.
"""

import os
import json
import re
from django.conf import settings

def get_groq_client():
    """Returns an authenticated Groq client or None if key is absent."""
    api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
    if not api_key or api_key.strip() in ['your_groq_api_key_here', '']:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key.strip())
    except Exception as e:
        print(f"Failed to initialize Groq client: {e}")
        return None


def clean_json_response(raw_content):
    """Safely extracts and parses JSON even if wrapped in markdown code blocks."""
    if not raw_content:
        return None
    
    content = raw_content.strip()
    # Remove markdown code fences ```json ... ```
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content, flags=re.IGNORECASE).strip()
        content = re.sub(r"```$", "", content).strip()
    
    # Try finding outer JSON object or array
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass
    return None


def generate_interview_questions(category, subject, difficulty, num_questions=5, resume_data=None):
    """
    Generates tailored interview questions.
    If resume data is provided, explicitly grounds questions in the candidate's projects and skills!
    """
    client = get_groq_client()

    resume_context = ""
    if resume_data:
        skills = resume_data.get('skills', [])
        skills_str = ", ".join([s['name'] if isinstance(s, dict) else s for s in skills])
        projects_str = " | ".join(resume_data.get('projects', []))
        resume_context = f"""
Candidate Resume Context:
- Extracted Skills: {skills_str or 'General Computer Science'}
- Projects: {projects_str or 'Academic coursework and applications'}
"""

    system_prompt = f"""You are an elite Senior Technical Interviewer and Engineering Manager at a top tech company.
You are conducting a professional mock interview.
Category: {category.upper()}
Subject/Domain: {subject}
Difficulty: {difficulty.upper()}
Number of questions required: {num_questions}

Instructions:
1. If resume context is present, make at least 50% of the questions direct inquiries into the candidate's actual projects, architectural decisions, and specific technologies listed on their resume.
2. For HR category, focus on behavioral STAR scenarios (Situation, Task, Action, Result), leadership, conflict resolution, and career ambitions.
3. For Aptitude category, provide realistic quantitative or logical reasoning scenarios.
4. Output strictly a JSON array of objects with the following schema:
[
  {{
    "question_number": 1,
    "question_text": "Question string here",
    "category": "{category}",
    "difficulty": "{difficulty}",
    "ideal_answer_summary": "Key points expected in a strong answer"
  }}
]
Do NOT include any markdown preamble or postscript, return raw valid JSON only."""

    user_prompt = f"Generate {num_questions} interview questions for {subject} at {difficulty} level.{resume_context}"

    if client:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1500,
            )
            parsed = clean_json_response(chat_completion.choices[0].message.content)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            print(f"Groq API error during question generation: {e}")

    # Fallback questions if Groq key is absent or network fails
    return get_fallback_questions(category, subject, difficulty, num_questions, resume_data)


def evaluate_candidate_answer(question_text, candidate_answer, interview_context, resume_context=None, difficulty="intermediate"):
    """
    Evaluates candidate's voice/text answer using Groq LLM.
    Evaluates technical correctness, completeness, relevance, and clarity.
    Returns structured JSON with conversational AI response and adaptive next question.
    """
    client = get_groq_client()

    system_prompt = """You are an empathetic yet rigorous Senior Technical Interviewer evaluating a candidate's spoken answer.
Evaluate the answer holistically across:
1. Technical Correctness (Are the definitions, code logic, or facts accurate?)
2. Relevance (Did they answer what was asked without rambling?)
3. Completeness (Did they cover essential edge cases, trade-offs, or examples?)
4. Clarity & Organization (Is the explanation articulate and structured?)

Respond strictly with a JSON object in this format:
{
  "score": 7.5,
  "technical_correctness": "High | Moderate | Low",
  "relevance": "High | Moderate | Low",
  "completeness": "High | Moderate | Low",
  "clarity": "High | Moderate | Low",
  "positive_points": ["Strong understanding of concept X", "Good practical example"],
  "missing_concepts": ["Did not mention time complexity", "Missed edge case Y"],
  "mistakes": ["Confused terminology A with B"],
  "correct_explanation": "A concise expert-level summary of the correct solution.",
  "improved_answer": "How a top 1% candidate would formulate this answer in 3-4 sentences.",
  "spoken_feedback": "Short natural sentence spoken out loud to the candidate, e.g. 'Good explanation of the basic concept! Can you tell me how it behaves under high concurrency?'",
  "follow_up_question": "Next natural question adapting to how well they answered",
  "next_difficulty": "beginner | intermediate | advanced"
}

Important Behavioral Guidelines:
- If score >= 7.5: Praise briefly and ask a deeper or more advanced follow-up question.
- If score 4.0 - 7.0: Acknowledge what they got right, and ask a clarifying question or request a simple example.
- If score < 4.0 or answer is empty: Be supportive, give a hint, or offer an easier related question.
Return strictly the JSON object."""

    user_prompt = f"""
Question Asked:
"{question_text}"

Candidate Answer:
"{candidate_answer}"

Interview History & Context:
{json.dumps(interview_context or [])}
"""

    if client:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.5,
                max_tokens=1200,
            )
            parsed = clean_json_response(chat_completion.choices[0].message.content)
            if isinstance(parsed, dict) and "score" in parsed:
                return parsed
        except Exception as e:
            print(f"Groq API error during answer evaluation: {e}")

    # Fallback Evaluation Engine if API is temporarily unavailable
    return get_fallback_evaluation(question_text, candidate_answer, difficulty)


def generate_learning_roadmap_ai(user_profile, session, evaluations):
    """Generates a structured learning roadmap based on detected mistakes and weak areas."""
    client = get_groq_client()

    eval_data = []
    for ev in evaluations:
        eval_data.append({
            'score': ev.score,
            'mistakes': ev.mistakes,
            'missing_concepts': ev.missing_concepts
        })

    system_prompt = """You are an AI Career Mentor for CSE students.
Analyze the candidate's interview session performance and produce a personalized study roadmap.
Return strictly a JSON object:
{
  "weak_areas": ["List of weak topics identified"],
  "recommended_topics": [
    {"topic": "Topic Name", "reason": "Why practice is needed", "priority": "High | Medium"}
  ],
  "practice_questions": [
    "Practice Question 1", "Practice Question 2", "Practice Question 3"
  ],
  "action_plan": "A step-by-step 7-day study plan explaining what to practice daily."
}"""

    user_prompt = f"Candidate Profile: {user_profile.target_role} ({user_profile.experience_level}). Interview Subject: {session.subject}. Category: {session.category}. Final Score: {session.final_score}/10. Performance Details: {json.dumps(eval_data)}"

    if client:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.6,
                max_tokens=1500,
            )
            parsed = clean_json_response(chat_completion.choices[0].message.content)
            if isinstance(parsed, dict) and "recommended_topics" in parsed:
                return parsed
        except Exception as e:
            print(f"Groq API error during roadmap generation: {e}")

    return {
        "weak_areas": [f"Deep dive into {session.subject} core principles", "Handling architectural trade-offs"],
        "recommended_topics": [
            {"topic": f"Advanced {session.subject} Concepts", "reason": "Demonstrate deep domain mastery in technical interviews", "priority": "High"},
            {"topic": "System Design & Scalability", "reason": "Crucial for software engineering interviews", "priority": "Medium"}
        ],
        "practice_questions": [
            f"Explain how internal memory management works in {session.subject}.",
            f"What design patterns are most effective when architecting a {session.subject} application?",
            "How would you troubleshoot performance bottlenecks in production?"
        ],
        "action_plan": "Day 1-2: Review core fundamentals and memory model. Day 3-4: Build hands-on mini projects reinforcing concurrency and database indexing. Day 5-7: Practice verbal explanations using the STAR technique."
    }


def get_fallback_questions(category, subject, difficulty, num_questions=5, resume_data=None):
    """Provides high-quality realistic fallback questions when Groq API key is not connected."""
    projects = resume_data.get('projects', []) if resume_data else []
    proj_name = projects[0] if projects else "your recent project"

    if category == 'hr':
        pool = [
            ("Tell me about yourself and your journey into Computer Science.", "Clear, structured elevator pitch covering education, key projects, and career passion."),
            ("Describe a challenging technical obstacle you faced in a project and how you solved it.", "STAR method: context, roadblock, creative solution, and final impact."),
            ("How do you handle disagreement with a teammate regarding technical architecture?", "Demonstrates empathy, active listening, data-driven decisions, and collaboration."),
            ("Where do you see yourself in the next 3 to 5 years as a software developer?", "Focus on continuous technical learning, mentorship, and ownership."),
            ("Why should our company hire you over other CSE candidates?", "Unique blend of technical grit, fast learning curve, and proactive problem solving.")
        ]
    elif category == 'aptitude':
        pool = [
            ("A train 240 m long passes a pole in 24 seconds. How long will it take to pass a platform 650 m long?", "Speed = 240/24 = 10 m/s. Total distance = 240 + 650 = 890 m. Time = 890/10 = 89 seconds."),
            ("Pointing to a photograph, a person says: 'He is the son of the only son of my grandfather.' How is the person in the photograph related?", "Grandfather's only son is father. Father's son is brother or self."),
            ("If 6 workers can complete a coding module in 12 days, how many days will 9 workers take working at the same pace?", "Work = 6 * 12 = 72 man-days. Days = 72 / 9 = 8 days."),
            ("Find the next number in the series: 3, 7, 15, 31, 63, ?", "Pattern is x * 2 + 1. Next number = 63 * 2 + 1 = 127."),
            ("Explain the difference between inductive and deductive reasoning with a simple example.", "Deductive moves from general rule to specific case; inductive moves from specific observations to a generalized theory.")
        ]
    else:
        # Technical interview questions
        if "python" in subject.lower():
            pool = [
                ("Can you explain how Python manages memory, specifically referencing GIL and garbage collection?", "Explains reference counting, cyclic garbage collection, and Global Interpreter Lock."),
                (f"In your project '{proj_name}', how did you structure your codebase and handle dependencies?", "Details modular architecture, virtual environments, and clean separation of concerns."),
                ("What is the difference between shallow copy and deep copy in Python?", "Shallow copy copies reference pointers of nested objects; deep copy recursively copies distinct objects."),
                ("How do Python decorators work under the hood?", "Explains higher-order functions, closures, and returning wrapped function objects."),
                ("Explain the difference between lists and tuples in terms of mutability and memory overhead.", "Lists are mutable and over-allocated for growth; tuples are immutable, fixed size, and memory optimized.")
            ]
        elif "java" in subject.lower():
            pool = [
                ("Explain the difference between Method Overloading and Method Overriding in Java.", "Overloading is compile-time polymorphism within same class; overriding is runtime polymorphism in subclass with @Override."),
                (f"How did you leverage Object-Oriented Principles in '{proj_name}'?", "Encapsulation, Inheritance, Polymorphism, and Abstraction in practical project context."),
                ("What is the difference between JVM, JRE, and JDK?", "JDK is development kit with compiler; JRE is runtime environment; JVM is virtual machine executing bytecode."),
                ("Explain Java's memory structure: Heap vs Stack memory.", "Stack stores local primitives and method call frames; Heap stores dynamic objects and instance variables."),
                ("How does the Java Garbage Collector decide when an object is eligible for garbage collection?", "Unreachable objects with no active reference path from root objects (GC Roots).")
            ]
        else:
            pool = [
                ("What is the difference between an Array and a Linked List in terms of memory layout and search complexity?", "Arrays have contiguous memory with O(1) random access; Linked Lists have pointer overhead with O(N) access."),
                (f"Walk me through the architecture and database schema you designed for '{proj_name}'.", "Clear schema design, normalization, foreign keys, and API interaction."),
                ("Explain ACID properties in Database Management Systems.", "Atomicity, Consistency, Isolation, Durability."),
                ("What is the difference between TCP and UDP protocols?", "TCP is connection-oriented, reliable with 3-way handshake; UDP is connectionless, fast, used for streaming."),
                ("What is the time and space complexity of QuickSort, and what is its worst-case scenario?", "Average O(N log N), worst O(N^2) with already sorted pivot; space O(log N).")
            ]

    questions = []
    for i, (q_text, ideal) in enumerate(pool[:num_questions]):
        questions.append({
            "question_number": i + 1,
            "question_text": q_text,
            "category": category,
            "difficulty": difficulty,
            "ideal_answer_summary": ideal
        })
    return questions


def get_fallback_evaluation(question_text, candidate_answer, difficulty="intermediate"):
    """Intelligent rule-based evaluator when Groq LLM API is unavailable."""
    answer_clean = candidate_answer.strip()
    words = answer_clean.split()
    word_count = len(words)

    if word_count < 5:
        return {
            "score": 3.0,
            "technical_correctness": "Low",
            "relevance": "Low",
            "completeness": "Low",
            "clarity": "Low",
            "positive_points": ["Attempted to answer"],
            "missing_concepts": ["Answer was too brief to demonstrate conceptual understanding"],
            "mistakes": ["Lacks technical details and examples"],
            "correct_explanation": "A complete answer requires defining the core concept, giving a working scenario, and mentioning trade-offs.",
            "improved_answer": "Provide a structured answer: define the term, explain the underlying mechanism, and give a concrete CSE example.",
            "spoken_feedback": "That was a bit brief. Let's explore this further. Can you try explaining with a simple example?",
            "follow_up_question": "Can you elaborate on that and explain how this behaves in a real-world scenario?",
            "next_difficulty": "beginner"
        }
    elif word_count < 25:
        return {
            "score": 6.5,
            "technical_correctness": "Moderate",
            "relevance": "High",
            "completeness": "Moderate",
            "clarity": "Moderate",
            "positive_points": ["Addressed the question directly", "Identified primary keywords"],
            "missing_concepts": ["Could include more depth regarding performance and edge cases"],
            "mistakes": ["Did not fully contrast with alternatives"],
            "correct_explanation": "Good foundational grasp. Bolster your answer by linking to real applications and complexity analysis.",
            "improved_answer": "State the definition, state the key advantages, and mention when not to use this approach.",
            "spoken_feedback": "You've explained the basic concept correctly. Can you also explain its primary advantages and trade-offs?",
            "follow_up_question": "What are the primary performance advantages and trade-offs of this approach?",
            "next_difficulty": "intermediate"
        }
    else:
        return {
            "score": 8.5,
            "technical_correctness": "High",
            "relevance": "High",
            "completeness": "High",
            "clarity": "High",
            "positive_points": ["Thorough explanation", "Clear technical vocabulary", "Logical organization"],
            "missing_concepts": ["Minor details on advanced optimization"],
            "mistakes": [],
            "correct_explanation": "Excellent comprehensive answer covering theoretical mechanism and practical implementation.",
            "improved_answer": "Your answer is already strong. You can top it off by mentioning real-world industry benchmarks.",
            "spoken_feedback": "Good explanation! That was very clear. Let me challenge you with a related follow-up.",
            "follow_up_question": "How would you optimize this implementation if dealing with millions of concurrent requests?",
            "next_difficulty": "advanced"
        }
