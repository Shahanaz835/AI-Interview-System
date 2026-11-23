"""
Resume Parser & NLP Information Extraction Engine
Extracts text, technical skills, projects, education, experience, and certifications from PDF resumes.
"""

import re
from pypdf import PdfReader

# Master taxonomy of technical skills across CSE domains
TECHNICAL_SKILLS_TAXONOMY = {
    'Language': [
        'Python', 'Java', 'C++', 'C', 'C#', 'JavaScript', 'TypeScript', 'PHP',
        'Ruby', 'Go', 'Golang', 'Rust', 'Kotlin', 'Swift', 'Dart', 'R', 'Scala', 'Bash', 'Shell'
    ],
    'Framework': [
        'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Spring', 'React', 'React.js',
        'Node.js', 'Express', 'Angular', 'Vue.js', 'Next.js', 'ASP.NET', 'Bootstrap',
        'Tailwind CSS', 'jQuery', 'Hibernate', 'PyTorch', 'TensorFlow', 'Scikit-learn', 'Pandas', 'NumPy'
    ],
    'Database': [
        'SQL', 'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Oracle',
        'Cassandra', 'Firebase', 'MariaDB', 'MS SQL Server', 'DynamoDB'
    ],
    'Tool': [
        'Git', 'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
        'Linux', 'Jenkins', 'CI/CD', 'Postman', 'VS Code', 'Jira', 'Figma'
    ],
    'Concept': [
        'Data Structures', 'Algorithms', 'DSA', 'OOP', 'Object Oriented Programming',
        'DBMS', 'Database Management', 'Operating Systems', 'Computer Networks',
        'Machine Learning', 'Deep Learning', 'REST API', 'Microservices', 'System Design'
    ]
}


def extract_text_from_pdf(pdf_file_path):
    """Extracts raw text from a PDF file using pypdf."""
    text = ""
    try:
        reader = PdfReader(pdf_file_path)
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_file_path}: {e}")
    return text.strip()


def extract_skills_from_text(text):
    """
    Scans the extracted text against the technical skills taxonomy.
    Returns a dictionary of matched skills organized by category.
    """
    matched_skills = []
    text_lower = f" {text.lower()} "

    for category, skills in TECHNICAL_SKILLS_TAXONOMY.items():
        for skill in skills:
            # Word boundary regex pattern to match exact skill words (e.g., 'C' vs 'C++')
            escaped_skill = re.escape(skill.lower())
            pattern = rf"(?<![\w\+\#]){escaped_skill}(?![\w\+\#])"
            
            if re.search(pattern, text_lower):
                matched_skills.append({
                    'name': skill,
                    'category': category,
                    'proficiency': 'Intermediate'
                })

    # Remove duplicates preserving order
    unique_skills = []
    seen = set()
    for s in matched_skills:
        key = (s['name'].lower(), s['category'])
        if key not in seen:
            seen.add(key)
            unique_skills.append(s)

    return unique_skills


def extract_sections(text):
    """
    Splits resume text into functional sections: Education, Projects, Experience, Certifications.
    """
    sections = {
        'education': [],
        'projects': [],
        'experience': [],
        'certifications': [],
        'missing_sections': []
    }

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_text_lower = text.lower()

    # Detect Education
    edu_keywords = ['b.tech', 'bachelor', 'b.e', 'degree', 'university', 'college', 'cgpa', 'percentage', 'higher secondary', 'diploma']
    edu_matches = []
    for line in lines:
        if any(kw in line.lower() for kw in edu_keywords):
            if len(line) < 120 and line not in edu_matches:
                edu_matches.append(line)
    sections['education'] = edu_matches[:5]

    # Detect Projects
    proj_keywords = ['project', 'system', 'application', 'portal', 'website', 'model', 'detection', 'tracker', 'analyzer']
    proj_matches = []
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in proj_keywords) and ('developed' in line.lower() or 'built' in line.lower() or 'implemented' in line.lower() or len(line) < 80):
            # Capture project title and optional next line description
            proj_desc = line
            if i + 1 < len(lines) and len(lines[i+1]) > 20 and not any(k in lines[i+1].lower() for k in ['education', 'skills', 'experience']):
                proj_desc += ": " + lines[i+1]
            if proj_desc not in proj_matches and len(proj_desc) > 10:
                proj_matches.append(proj_desc)
    sections['projects'] = proj_matches[:4]

    # Detect Experience / Internships
    exp_keywords = ['intern', 'internship', 'experience', 'developer', 'engineer', 'freelance', 'trainee']
    exp_matches = []
    for line in lines:
        if any(kw in line.lower() for kw in exp_keywords) and len(line) < 120:
            if line not in exp_matches:
                exp_matches.append(line)
    sections['experience'] = exp_matches[:4]

    # Detect Certifications
    cert_keywords = ['certified', 'certification', 'course', 'coursera', 'udemy', 'nptel', 'hackerrank', 'badge']
    cert_matches = []
    for line in lines:
        if any(kw in line.lower() for kw in cert_keywords) and len(line) < 120:
            if line not in cert_matches:
                cert_matches.append(line)
    sections['certifications'] = cert_matches[:4]

    # Check for missing sections to provide constructive feedback
    if not sections['projects']:
        sections['missing_sections'].append("Projects (No distinct technical projects detected)")
    if not sections['certifications']:
        sections['missing_sections'].append("Certifications (No verified technical courses or certifications found)")
    if not sections['experience']:
        sections['missing_sections'].append("Experience / Internships (Consider adding open-source contributions or academic internships)")

    return sections


def calculate_resume_score(extracted_skills, sections):
    """Computes a resume completeness score out of 100 with recommendations."""
    score = 40  # Base score for valid document

    # Skills weighting (up to 30 points)
    skill_count = len(extracted_skills)
    if skill_count >= 10:
        score += 30
    elif skill_count >= 5:
        score += 20
    elif skill_count >= 2:
        score += 10

    # Projects weighting (up to 15 points)
    if len(sections.get('projects', [])) >= 2:
        score += 15
    elif len(sections.get('projects', [])) == 1:
        score += 10

    # Education (up to 10 points)
    if sections.get('education'):
        score += 10

    # Certifications / Experience (up to 5 points)
    if sections.get('certifications') or sections.get('experience'):
        score += 5

    score = min(score, 100)

    # Generate summary
    skills_names = [s['name'] for s in extracted_skills[:6]]
    summary = f"Detected {len(extracted_skills)} technical competencies including {', '.join(skills_names) if skills_names else 'core CS basics'}."
    if sections.get('projects'):
        summary += f" Identified {len(sections['projects'])} project highlights ready for interview questioning."
    if sections.get('missing_sections'):
        summary += f" Recommended additions: {', '.join(sections['missing_sections'])}."

    return score, summary


def parse_resume(pdf_path):
    """Master function that extracts text, parses skills, breaks down sections, and calculates score."""
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        return {
            'raw_text': '',
            'skills': [],
            'education': [],
            'projects': [],
            'experience': [],
            'certifications': [],
            'missing_sections': ['Resume unreadable or empty PDF'],
            'score': 20,
            'summary': 'Could not extract readable text from the uploaded PDF. Please upload a non-scanned text PDF.'
        }

    skills = extract_skills_from_text(raw_text)
    sections = extract_sections(raw_text)
    score, summary = calculate_resume_score(skills, sections)

    return {
        'raw_text': raw_text,
        'skills': skills,
        'education': sections['education'],
        'projects': sections['projects'],
        'experience': sections['experience'],
        'certifications': sections['certifications'],
        'missing_sections': sections['missing_sections'],
        'score': score,
        'summary': summary
    }
