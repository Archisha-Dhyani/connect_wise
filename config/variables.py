# config/variables.py

# These are fields from the chatbot JSON that actually influence similarity.
# Each field has a relative importance (weight) between 0.0 and 1.0

VARIABLES = [
    {"key": "role", "desc": "Current role or position", "use_for_embedding": True, "default_weight": 0.9},
    {"key": "domain", "desc": "Primary domain of work/study", "use_for_embedding": True, "default_weight": 0.9},
    {"key": "industry_experience", "desc": "Industries user has worked in", "use_for_embedding": True, "default_weight": 0.8},
    {"key": "skills", "desc": "Professional skills", "use_for_embedding": True, "default_weight": 1.0},
    {"key": "preferred_roles_in_projects", "desc": "Preferred roles in projects", "use_for_embedding": True, "default_weight": 0.9},
    {"key": "preferred_collaboration", "desc": "Collaboration preference", "use_for_embedding": True, "default_weight": 0.6},
    {"key": "availability_timeframe", "desc": "Available time windows", "use_for_embedding": True, "default_weight": 0.5},
    {"key": "experience", "desc": "Years of experience", "use_for_embedding": True, "default_weight": 0.7},
    {"key": "languages_spoken", "desc": "Languages user speaks", "use_for_embedding": True, "default_weight": 0.5},
    {"key": "certifications", "desc": "Professional certifications/degrees", "use_for_embedding": True, "default_weight": 0.6},
    {"key": "offers", "desc": "What user offers to others", "use_for_embedding": True, "default_weight": 0.7},
    {"key": "needs", "desc": "What user is looking for", "use_for_embedding": True, "default_weight": 0.8},
    {"key": "interests_hobbies", "desc": "Personal interests/hobbies", "use_for_embedding": True, "default_weight": 0.6},
    {"key": "one_line_bio", "desc": "Professional tagline", "use_for_embedding": True, "default_weight": 0.7},
    {"key": "location", "desc": "City or region", "use_for_embedding": True, "default_weight": 0.4},
]
