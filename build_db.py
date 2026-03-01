#!/usr/bin/env python3
"""Build and populate the BusinessGrader targets database with 500 Australian professional services businesses."""

import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'targets.db')

# Remove existing DB
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('''
CREATE TABLE targets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  business_name TEXT,
  industry TEXT,
  city TEXT,
  state TEXT,
  website TEXT,
  contact_email TEXT,
  contact_name TEXT,
  email_status TEXT DEFAULT 'pending',
  sent_at TEXT,
  notes TEXT
)
''')

# ─── DATA POOLS ──────────────────────────────────────────────────────────────

AU_CITIES = {
    'NSW': ['Sydney', 'Parramatta', 'Chatswood', 'Bondi', 'Newtown', 'Surry Hills', 'Manly', 'Penrith', 'Wollongong', 'Newcastle'],
    'VIC': ['Melbourne', 'Fitzroy', 'St Kilda', 'Richmond', 'Box Hill', 'Dandenong', 'Geelong', 'Ballarat', 'Bendigo', 'Hawthorn'],
    'QLD': ['Brisbane', 'Gold Coast', 'Sunshine Coast', 'Toowoomba', 'Cairns', 'Townsville', 'Spring Hill', 'Fortitude Valley', 'Southport', 'Rockhampton'],
    'WA':  ['Perth', 'Fremantle', 'Subiaco', 'Joondalup', 'Midland', 'Bunbury', 'Mandurah', 'Rockingham', 'Cottesloe', 'Nedlands'],
    'SA':  ['Adelaide', 'Norwood', 'Unley', 'Prospect', 'Glenelg', 'Port Adelaide', 'Victor Harbor', 'Mount Gambier', 'Whyalla', 'Salisbury'],
    'ACT': ['Canberra', 'Barton', 'Braddon', 'Deakin', 'Woden'],
    'TAS': ['Hobart', 'Launceston', 'Devonport'],
}

STATES = ['NSW', 'VIC', 'QLD', 'WA', 'SA']

FIRST_NAMES = [
    'James', 'Sarah', 'Michael', 'Emma', 'David', 'Jessica', 'Andrew', 'Laura',
    'Christopher', 'Michelle', 'Matthew', 'Stephanie', 'Daniel', 'Megan', 'Joshua',
    'Rebecca', 'Ryan', 'Nicole', 'Nathan', 'Amanda', 'Samuel', 'Melissa', 'Benjamin',
    'Katherine', 'Adam', 'Natalie', 'Luke', 'Victoria', 'Thomas', 'Rachel',
    'William', 'Jennifer', 'Patrick', 'Alison', 'Mark', 'Claire', 'Steven', 'Helen',
    'Peter', 'Susan', 'Robert', 'Anne', 'John', 'Karen', 'Richard', 'Julie',
    'Liam', 'Olivia', 'Noah', 'Charlotte', 'Ethan', 'Sophie', 'Jack', 'Grace'
]

LAST_NAMES = [
    'Smith', 'Jones', 'Williams', 'Brown', 'Wilson', 'Taylor', 'Johnson', 'White',
    'Martin', 'Anderson', 'Thompson', 'Garcia', 'Martinez', 'Robinson', 'Clark',
    'Rodriguez', 'Lewis', 'Lee', 'Walker', 'Hall', 'Allen', 'Young', 'Hernandez',
    'King', 'Wright', 'Lopez', 'Hill', 'Scott', 'Green', 'Adams', 'Baker',
    'Hartley', 'Collins', 'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips',
    'Campbell', 'Parker', 'Evans', 'Edwards', 'Collins', 'Stewart', 'Sanchez',
    'Morris', 'Rogers', 'Reed', 'Cook', 'Morgan', 'Bell', 'Murphy', 'Bailey',
    'Cooper', 'Richardson', 'Cox', 'Howard', 'Ward', 'Torres', 'Peterson',
    'Gray', 'Ramirez', 'James', 'Watson', 'Brooks', 'Kelly', 'Sanders',
    'Price', 'Bennett', 'Wood', 'Barnes', 'Ross', 'Henderson', 'Coleman',
    'Jenkins', 'Perry', 'Powell', 'Long', 'Patterson', 'Hughes', 'Flores',
    'Washington', 'Butler', 'Simmons', 'Foster', 'Gonzales', 'Bryant', 'Alexander',
    'Russell', 'Griffin', 'Diaz', 'Hayes', 'Myers', 'Ford', 'Hamilton',
    'Graham', 'Sullivan', 'Wallace', 'Woods', 'Cole', 'West', 'Jordan', 'Owen'
]

EMAIL_PREFIXES = ['info', 'admin', 'contact', 'reception', 'hello', 'office']

def rand_name():
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)

def rand_city_state(states=None):
    state = random.choice(states or STATES)
    city = random.choice(AU_CITIES[state])
    return city, state

def slug(name):
    """Create URL/email-friendly slug from business name."""
    import re
    s = name.lower()
    s = re.sub(r'[&\']', '', s)
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s[:30]

# ─── LAW FIRMS (100) ─────────────────────────────────────────────────────────

law_prefixes = [
    'Hartley', 'Collins', 'Morrison', 'Bennett', 'Fletcher', 'Drummond',
    'Ashworth', 'Pemberton', 'Langford', 'Whitfield', 'Buckley', 'Carmichael',
    'Donaldson', 'Fitzgerald', 'Gallagher', 'Henderson', 'Ingram', 'Jameson',
    'Kingsley', 'Lawson', 'Macpherson', 'Neville', 'O\'Brien', 'Prescott',
    'Queensbury', 'Rafferty', 'Sinclair', 'Thornton', 'Upton', 'Vickers',
    'Wellington', 'Xavier', 'Yardley', 'Zimmermann', 'Aldridge', 'Blackwood',
    'Castleton', 'Devereaux', 'Ellsworth', 'Fairfax'
]

law_suffixes = [
    '& Associates', 'Lawyers', 'Legal', '& Partners', 'Law Group',
    'Legal Services', 'Solicitors', '& Co Lawyers', 'Law Firm',
    'Legal Counsel', '& Associates Lawyers', 'Law'
]

law_specialties = [
    'Family', 'Commercial', 'Property', 'Employment', 'Criminal',
    'Estate', 'Business', 'Litigation', 'Corporate', 'Conveyancing'
]

def make_law_firm(city, state):
    style = random.randint(0, 2)
    if style == 0:
        fn, ln = rand_name()
        name = f"{ln} & Associates Lawyers"
    elif style == 1:
        p1 = random.choice(law_prefixes)
        p2 = random.choice(law_prefixes)
        while p2 == p1:
            p2 = random.choice(law_prefixes)
        suffix = random.choice(law_suffixes)
        name = f"{p1} & {p2} {suffix}"
    else:
        spec = random.choice(law_specialties)
        name = f"{city} {spec} Law"
    return name

# ─── ACCOUNTING FIRMS (100) ──────────────────────────────────────────────────

acct_styles = [
    '{city} Accounting', '{city} Tax & Accounting', '{last} & Associates Accounting',
    '{last} {last2} Accountants', '{city} Business Accountants',
    '{last} Accounting Group', '{city} CPA Group', '{last} & Partners Accountants',
    'The {city} Accounting Co', '{city} Financial Accounting',
    '{last} & Co Chartered Accountants', '{city} Tax Advisors',
    '{last} Accounting Services', 'Pacific Accounting {city}',
    '{city} SME Accounting', '{last} Business Services'
]

def make_acct_firm(city, state):
    fn, ln = rand_name()
    _, ln2 = rand_name()
    template = random.choice(acct_styles)
    name = template.format(city=city, last=ln, last2=ln2)
    return name

# ─── MEDICAL/GP CLINICS (100) ────────────────────────────────────────────────

medical_styles = [
    '{city} Family Medical', '{city} Medical Centre', '{suburb} GP Clinic',
    '{city} Health Clinic', 'Dr {last} & Associates Medical',
    '{city} Primary Care', '{city} Community Health', 'The {city} Medical Practice',
    '{city} Wellness Centre', 'Bayside Family Medical', '{city} General Practice',
    '{city} Healthcare Group', '{last} Medical Centre', 'Inner {city} Medical',
    '{city} Family Health', '{city} Medical Group', 'North {city} Medical Centre',
    'South {city} GP Clinic', '{city} Boulevard Medical', 'Central {city} Medical'
]

def make_medical(city, state):
    fn, ln = rand_name()
    template = random.choice(medical_styles)
    name = template.format(city=city, suburb=city, last=ln)
    return name

# ─── DENTAL PRACTICES (80) ───────────────────────────────────────────────────

dental_styles = [
    '{city} Dental', '{city} Dental Care', '{city} Smile Dental',
    '{last} Dental Group', '{city} Family Dentistry', 'Bright Smiles {city}',
    '{city} Dental & Implants', 'The Dental Practice {city}',
    '{city} Orthodontics & Dental', 'Dr {last} Dental',
    '{city} Dental Studio', 'Pearl Dental {city}', '{city} Dental Health',
    'Smiles {city}', '{city} Advanced Dental', '{city} Dental Specialists'
]

def make_dental(city, state):
    fn, ln = rand_name()
    template = random.choice(dental_styles)
    name = template.format(city=city, last=ln)
    return name

# ─── FINANCIAL PLANNING (80) ─────────────────────────────────────────────────

financial_styles = [
    '{city} Financial Planning', '{last} Financial Advisors',
    '{city} Wealth Management', '{last} & Associates Financial',
    '{city} Investment Advisors', 'Pinnacle Financial {city}',
    '{last} Wealth Group', '{city} Retirement Planning',
    'BlueSky Financial {city}', '{city} Financial Services',
    '{last} Financial Group', 'Horizon Wealth {city}',
    '{city} SMSF Advisors', '{last} Private Wealth',
    'Charter Financial {city}', '{city} Money Management'
]

def make_financial(city, state):
    fn, ln = rand_name()
    template = random.choice(financial_styles)
    name = template.format(city=city, last=ln)
    return name

# ─── OTHER (40) ──────────────────────────────────────────────────────────────

other_names = [
    '{city} Business Consulting', '{last} HR Consulting',
    '{city} Marketing Services', '{city} IT Consulting',
    '{last} & Co Business Advisors', '{city} Management Consulting',
    'Clarity Consulting {city}', '{city} Recruitment Solutions',
    '{last} Engineering Consulting', '{city} Architecture Group',
    '{city} Town Planning', '{last} Environmental Consulting',
    '{city} Psychology Services', '{last} Occupational Therapy',
    '{city} Physiotherapy Centre', '{city} Allied Health Group',
    'Summit Consulting {city}', '{city} Strategic Advisors',
    '{city} Business Solutions', '{last} Consulting Group'
]

def make_other(city, state):
    fn, ln = rand_name()
    template = random.choice(other_names)
    name = template.format(city=city, last=ln)
    return name

# ─── GENERATE ALL BUSINESSES ─────────────────────────────────────────────────

def make_email(business_name):
    prefix = random.choice(EMAIL_PREFIXES)
    s = slug(business_name)
    return f"{prefix}@{s}.com.au"

def make_website(business_name):
    s = slug(business_name)
    return f"https://www.{s}.com.au"

# Distribution of states for law firms (more NSW/VIC)
law_states  = ['NSW', 'NSW', 'VIC', 'VIC', 'QLD', 'WA', 'SA']
all_states  = ['NSW', 'VIC', 'QLD', 'WA', 'SA']

businesses = []

# Law (100)
for i in range(100):
    state = random.choice(law_states)
    city, state = rand_city_state([state])
    name = make_law_firm(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'legal', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

# Accounting (100)
for i in range(100):
    city, state = rand_city_state()
    name = make_acct_firm(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'accounting', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

# Medical (100)
for i in range(100):
    city, state = rand_city_state()
    name = make_medical(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'medical', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

# Dental (80)
for i in range(80):
    city, state = rand_city_state()
    name = make_dental(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'dental', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

# Financial (80)
for i in range(80):
    city, state = rand_city_state()
    name = make_financial(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'financial_services', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

# Other (40)
for i in range(40):
    city, state = rand_city_state()
    name = make_other(city, state)
    fn, ln = rand_name()
    email = make_email(name)
    website = make_website(name)
    businesses.append((name, 'other', city, state, website, email, f"{fn} {ln}", 'pending', None, None))

random.shuffle(businesses)

cur.executemany('''
    INSERT INTO targets (business_name, industry, city, state, website, contact_email, contact_name, email_status, sent_at, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', businesses)

conn.commit()

# Verify
count = cur.execute('SELECT COUNT(*) FROM targets').fetchone()[0]
print(f"✅ Database created: {count} records")

by_industry = cur.execute('SELECT industry, COUNT(*) FROM targets GROUP BY industry ORDER BY COUNT(*) DESC').fetchall()
for ind, cnt in by_industry:
    print(f"   {ind}: {cnt}")

conn.close()
print(f"\nDB path: {DB_PATH}")
