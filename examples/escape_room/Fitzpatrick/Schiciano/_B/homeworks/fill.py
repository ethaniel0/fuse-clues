import random
import os

# Pool of possible answers for each question
ANSWER_BANK = {
    1: ["16", "32", "64", "8", "128"],
    2: ["Harvard", "Von Neumann", "Modified Harvard"],
    3: ["ALU", "FPU", "control unit", "decoder"],
    4: ["0", "1"],
    5: ["0", "1"],
    6: ["pipelining", "superscalar", "out-of-order", "branch prediction"],
    7: ["2", "4", "8", "16"],
    8: ["cache", "register", "RAM", "TLB"],
    9: ["1", "2", "3", "4"],
    10: ["42", "255", "13", "99", "7"],  # normal answers (will override for special files)
    11: ["register", "stack", "heap", "cache line"],
    12: ["32", "64", "128"],
    13: ["little-endian", "big-endian"],
    14: ["4", "8", "16"],
    15: ["control unit", "ALU", "memory controller"]
}

OUTPUT_DIR = "homeworks"
NUM_RANDOM_FILES = 20


def generate_answers():
    """Generate one random homework answer set."""
    answers = {}
    for q, choices in ANSWER_BANK.items():
        answers[q] = random.choice(choices)
    return answers


def write_homework(filename, answers):
    """Write answers to a file."""
    with open(filename, "w") as f:
        for i in range(1, len(answers) + 1):
            f.write(f"{i}. {answers[i]}\n")


names = 'Tyrone,Destinee,Sheridan,Kami,Betty,Yaritza,Livia,Davin,Cara,Bryana,Notnamed,Javier,Dontae,Christianna,Madysen,Alden,Darby,Miguelangel,Priscilla,Maria,Cedric,Kyla,Jorden,Bradford,Abigayle,Adrien,Federico,Xiomara,Trever,Jessie,Zane,Cherish,Grecia,Leann,Guy,Calli,Jamarcus,Shelton,Tamara,Macayla,Karly,Ananda,Douglas,Sage,Roberto,Makaela,Micheal,Colleen,Fernando,Martin,Jaquelyn,Aron,Julio,Cruz,Aidan,Jeffery,Philip,Derick,Beau,Jala,Estefany,Ericka,Jameson,Ernest,Kellie,Cory,Davonte,Kale,Cailin,Damaris,Savannah,Maddie,Shelly,Alejandra,Kaylen,Estrella,Shayla,Winston,Keyonna,Asya,Ross,Shreya,Ali,Alexus,Darius,Jayson,Sheldon,Anais,Jensen,Karson,Milena,Katelynn,Alayna,Stella,Ashton,Enoch,Zachery,Karime,Bradly,Steven'
names = names.split(',')

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate random "noise" files
    for i in range(len(names)):
        answers = generate_answers()
        filename = f'{names[i]}.txt'
        write_homework(filename, answers)

    # Generate the two special files
    base_answers = generate_answers()

    student_a = base_answers.copy()
    student_b = base_answers.copy()

    student_a[10] = "11110011"  # 243
    student_b[10] = "1000101"   # 69

    write_homework(os.path.join(OUTPUT_DIR, "hw_special_A.txt"), student_a)
    write_homework(os.path.join(OUTPUT_DIR, "hw_special_B.txt"), student_b)


if __name__ == "__main__":
    main()