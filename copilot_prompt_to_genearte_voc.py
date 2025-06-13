"""
Generate a CSV file with 200 diverse synthetic client feedback comments.

Each comment should be categorized into one of the following buckets:
1. General Digital Positive
2. Functionality
3. Move Money
4. Customer Service
5. Mobile App (NEW)
6. Navigation
7. Other
8. General Digital Negative
9. Login/Password
10. Wells Fargo Brand
11. Administration Functions

The CSV should have the following columns:
- comment_id: integer
- comment_text: synthetic, realistic user feedback
- category_true: one of the predefined categories above
- timestamp: random date within the past year
"""

import csv
import random
from datetime import datetime, timedelta

# Define the output file
output_file = "simulated_voc_feedback.csv"

# Define feedback categories and seed comments for each
categories = {
    "General Digital Positive": [],
    "Functionality": [],
    "Move Money": [],
    "Customer Service": [],
    "Mobile App (NEW)": [],
    "Navigation": [],
    "Other": [],
    "General Digital Negative": [],
    "Login/Password": [],
    "Wells Fargo Brand": [],
    "Administration Functions": []
}

# TODO: Copilot will help generate seed comments inside each category

# Utility: Generate a random timestamp within the last 365 days
def generate_random_date():
    today = datetime.today()
    delta = timedelta(days=random.randint(0, 365))
    return (today - delta).strftime("%Y-%m-%d")

# Generate ~200 rows of feedback
rows = []
comment_id = 0

# Generate 15–20 comments per category
for category in categories:
    for _ in range(18):  # Adjust to hit ~200 total
        # Copilot will help generate varied comment text here
        comment_text = ""  # ← Let Copilot populate from sample variations
        timestamp = generate_random_date()
        rows.append({
            "comment_id": comment_id,
            "comment_text": comment_text,
            "category_true": category,
            "timestamp": timestamp
        })
        comment_id += 1

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    fieldnames = ["comment_id", "comment_text", "category_true", "timestamp"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
