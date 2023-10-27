"""
text_utils.py

This module contains utility functions to process and analyze text.

Functions:
- extract_ascii_art(message: str) -> str:
    Extracts ASCII art from a given textual message, primarily designed to capture welcome messages from servers.

Author: dbd
Date: [Creation Date, October 27, 2023]
"""

#-------Tries to extracts the ASCII Welcome message on VPS Login------#

def extract_ascii_art(message):
    # Split the message into lines
    lines = message.split("\n")

    # Words and phrases indicating the line is textual and not part of ASCII art
    textual_words = ["Welcome", "Documentation", "Management", "Support", "Last login", "Run", "*"]

    # Function to check if a line is primarily composed of non-alphabetic characters
    def is_non_alphabetic(line):
        non_alpha_count = sum(1 for char in line if not char.isalpha())
        return non_alpha_count > len(line) * 0.7

    # Identify potential ASCII art lines
    potential_art_lines = [line for line in lines if is_non_alphabetic(line) and not any(word in line for word in textual_words)]

    # Find the largest block of consecutive potential art lines
    art_lines = []
    temp_lines = []
    for line in lines:
        if line in potential_art_lines:
            temp_lines.append(line)
        else:
            if len(temp_lines) > len(art_lines):  # If the new sequence is longer, replace the old one
                art_lines = temp_lines.copy()
            temp_lines = []  # Reset for the next sequence

    # Handle the scenario where the last sequence in the message is the longest
    if len(temp_lines) > len(art_lines):
        art_lines = temp_lines

    return "\n".join(art_lines) if art_lines else None