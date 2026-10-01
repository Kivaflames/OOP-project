from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ==========================================
# 1. SETUP & FILE VARIABLES
# ==========================================
# Using absolute file paths so the script knows exactly where to find your files
ca1 = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Grades CA 1.csv"
ca2 = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Grades CA 2.csv"
exercises = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Grades Exercises.csv"
final = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Grades Final Exam.csv"
grade_grp = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Grades Groups.csv"
group = "C:\\Users\\Jordan Lee\\Downloads\\OOP\\Project\\Groups.csv"

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_letter_grade(score):
    """Returns the corresponding letter grade based on total score."""
    if score >= 90: return "A+"
    elif score >= 85: return "A"
    elif score >= 80: return "A-"
    elif score >= 75: return "B+"
    elif score >= 70: return "B"
    elif score >= 65: return "B-"
    elif score >= 60: return "C+"
    elif score >= 55: return "C"
    elif score >= 50: return "C-"
    elif score >= 45: return "D+"
    elif score >= 40: return "D"
    else: return "F"

def read_csv_scores(filename):
    """Reads assessment files and returns {StudentID: TotalScore}."""
    scores = {}
    with open(filename, encoding="utf-8") as f:
        # Read the entire file and split it line by line
        lines = f.read().strip().split("\n")

    for line in lines[1:]: # Skip the first row (the header)
        if not line.strip():
            continue
        # Semicolon (;) is used as the delimiter here instead of a comma
        parts = [p.strip() for p in line.split(";")]
        student_id = parts[2] # Student ID is located in the 3rd column
        
        # Calculate the score by summing all columns from index 3 onward.
        # This handles assessments that have multiple question columns.
        total_score = sum(float(x) for x in parts[3:] if x != "")
        
        # Store in a dictionary to easily look up the score by ID later
        scores[student_id] = total_score
    return scores

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def main():
    # --- Extract Individual Scores ---
    # Convert all the CSVs into lookup dictionaries {ID: Score}
    ca1_scores = read_csv_scores(ca1)
    ca2_scores = read_csv_scores(ca2)
    exercises_scores = read_csv_scores(exercises)
    exam_scores = read_csv_scores(final)

    # --- Read Group Mappings ---
    student_groups = {}
    with open(group, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
        for line in lines[1:]:
            if line.strip():
                parts = line.split(";")
                # Maps Student ID (parts[0]) to their Group Name (parts[1])
                student_groups[parts[0].strip()] = parts[1].strip()

    # --- Read Group Project Grades ---
    group_scores = {}
    with open(grade_grp, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
        for line in lines[1:]:
            if line.strip():
                parts = line.split(";")
                # Maps Group Name (parts[0]) to the Project Score (parts[1])
                group_scores[parts[0].strip()] = float(parts[1].strip())

    # --- Determine Maximum Possible Scores ---
    # Finds the highest score actually achieved by any student in the data to use as the 100% benchmark.
    # The 'if ca1_scores else 1.0' prevents a crash (division by zero) if a file happens to be empty.
    max_c1 = max(ca1_scores.values()) if ca1_scores else 1.0
    max_c2 = max(ca2_scores.values()) if ca2_scores else 1.0
    max_ex = max(exercises_scores.values()) if exercises_scores else 1.0
    max_exm = max(exam_scores.values()) if exam_scores else 1.0
    max_proj = max(group_scores.values()) if group_scores else 1.0
    max_total = max_c1 + max_c2 + max_ex + max_exm + max_proj

    # --- Build Student Roster ---
    # We use CA1 just to get a master list of all student names and IDs
    students = []
    with open(ca1, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
        for line in lines[1:]:
            if line.strip():
                parts = [p.strip() for p in line.split(";")]
                students.append({
                    "last_name": parts[0],
                    "first_name": parts[1],
                    "id": parts[2],
                })

    # Sort the roster alphabetically by Last Name, First Name, then ID
    students.sort(key=lambda x: (x["last_name"].upper(), x["first_name"].upper(), x["id"]))

    # --- Setup Output Structures ---
    # For the CSV, standard plain text can't merge cells. We use double semicolons (;;) 
    # to create an empty column next to the header, pushing the next header over so you 
    # can easily merge them manually in Excel later.
    csv_lines = [
        "sep=;\n",
        "LAST NAME;FIRST NAME;ID;CA1;;CA2;;EXERCISE;;FINAL;;PROJECT;;SUM;;GRADE\n",
    ]
    
    # For the PDF, we place empty string headers ("") in the columns that will be visually merged over.
    pdf_data = [
        ["LAST NAME", "FIRST NAME", "ID", "CA1", "", "CA2", "", "EXERCISE", "", "FINAL", "", "PROJECT", "", "SUM", "", "GRADE"]
    ]

    # --- Data Aggregation & Calculations ---
    # Loop through the sorted students to build the rows one by one
    for s in students:
        sid = s["id"]
        
        # .get(sid, 0.0) safely pulls the score, defaulting to 0.0 if the student missed the assignment
        c1 = ca1_scores.get(sid, 0.0)
        c2 = ca2_scores.get(sid, 0.0)
        ex = exercises_scores.get(sid, 0.0)
        exm = exam_scores.get(sid, 0.0)
        
        # Project scores are linked to the group, so we look up the group first, then the score
        grp = student_groups.get(sid, "")
        proj = group_scores.get(grp, 0.0)
        
        total_sum = c1 + c2 + proj + ex + exm
        grade = get_letter_grade(total_sum)

        # Calculate Percentages: (Student Score / Highest Achieved Score) * 100
        p_c1 = (c1 / max_c1) * 100
        p_c2 = (c2 / max_c2) * 100
        p_ex = (ex / max_ex) * 100
        p_exm = (exm / max_exm) * 100
        p_proj = (proj / max_proj) * 100
        p_total = (total_sum / max_total) * 100

        # Construct the CSV row string. 
        # :.2f limits numbers to 2 decimal places. :.1f limits percentages to 1 decimal place.
        csv_line = f"{s['last_name']};{s['first_name']};{sid};{c1:.2f};{p_c1:.1f}%;{c2:.2f};{p_c2:.1f}%;{ex:.2f};{p_ex:.1f}%;{exm:.2f};{p_exm:.1f}%;{proj:.2f};{p_proj:.1f}%;{total_sum:.2f};{p_total:.1f}%;{grade}\n"
        csv_lines.append(csv_line)
        
        # Append the same data as a structured list for the PDF table
        pdf_data.append([
            s['last_name'], s['first_name'], sid, 
            f"{c1:.2f}", f"{p_c1:.1f}%", 
            f"{c2:.2f}", f"{p_c2:.1f}%", 
            f"{ex:.2f}", f"{p_ex:.1f}%", 
            f"{exm:.2f}", f"{p_exm:.1f}%", 
            f"{proj:.2f}", f"{p_proj:.1f}%", 
            f"{total_sum:.2f}", f"{p_total:.1f}%", 
            grade
        ])

    # --- Export to CSV ---
    csv_output = "Compiled_Grades_Report.csv"
    with open(csv_output, "w", encoding="utf-8") as f:
        f.writelines(csv_lines)
    print(f"Output saved to {csv_output}")

    # --- Export to PDF ---
    pdf_output = "Compiled_Grades_Report.pdf"
    
    # Set to landscape orientation so all 16 columns fit horizontally
    pdf = SimpleDocTemplate(pdf_output, pagesize=landscape(letter))
    
    table = Table(pdf_data)
    style = TableStyle([
        # Base styling for colors, alignment, and borders
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        
        # SPAN commands physically merge the header cells in the PDF.
        # Format: ('SPAN', (Start_Column_Index, Start_Row_Index), (End_Column_Index, End_Row_Index))
        # Row 0 is the header. This tells reportlab to stretch the CA1 label from column 3 to column 4.
        ('SPAN', (3, 0), (4, 0)),   # Merge CA1 columns
        ('SPAN', (5, 0), (6, 0)),   # Merge CA2 columns
        ('SPAN', (7, 0), (8, 0)),   # Merge EXERCISE columns
        ('SPAN', (9, 0), (10, 0)),  # Merge FINAL columns
        ('SPAN', (11, 0), (12, 0)), # Merge PROJECT columns
        ('SPAN', (13, 0), (14, 0)), # Merge SUM columns
    ])
    table.setStyle(style)
    
    pdf.build([table])
    print(f"PDF report saved to {pdf_output}")

if __name__ == "__main__":
    main()