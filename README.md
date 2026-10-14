# PycharmProjectAT2

# PROJECT SCENARIO

You got your first job as a cybersecurity specialist at Midtown IT. Your boss wants to update the Incident Response Plan. To make a risk assessment matrix, he needs to conduct an assets audit. The first task he assigns to you is to write a Python program that will collect information on all computers used on the Midtown IT network and keep a Microsoft Excell (CSV) file up to date with the following information on all computers:

• Computer Name
• IP-address
• MAC-address
• Processor Model
• Operation System
• System time
• Internet connection speed
• Active ports
The organisation uses computers with Windows and Linux operating systems.

 

# Requirements:

The main purpose of the program is to collect information about all company computers into a single CSV file. Thus, the program must be executed sequentially on all computers, for example, using a USB drive, analyse system information and data that have been already collected, and either update or add data to the .csv file. If, in the process of collecting information, it turns out that information about this computer is already present in the CSV file but differs from the current one, the program should display a warning message.

Possible CSV file format:

Computer Name, IP address, MAC address, Processor Model, Operation System, System time, Internet connection speed, Active ports (delimited with semicolon)

PF1VKNRQ, 192.168.1.2, 54-05-DB-3B-71-31, i7, Windows 10, 6//10/2023 8:00:01, 3Mb/s, 21;25;443;1234

OWH123RZ, 192.168.3.6, 34-7D-F6-9F-6A-18, i5, Windows 10, 7//10/2023 9:00:01, 11Mb/s, 21;25;443;67



# Midtown IT requires that the algorithmic solutions and corresponding script:

• be fully relevant to the purpose (do what is described in the requirements and nothing else)
• secure in terms of network and data security, including data validation and sanitation
• be written in accordance with a defensive style, i.e., be resistant to possible user errors.
• use Python language features, including libraries and packages, effectively, but without additional third-party software tools.
• use a style in accordance with the Midtown IT Python Coding Style Guidelines
• be tested and verified.
 
Scripting language: Python

## Run the Project

```bash
python src/pycharm_project_at2/main.py
```

See [Python Coding Standards](PYTHON_CODING_STANDARDS.md) for the project's naming, layout, commenting, and formatting guidelines.
