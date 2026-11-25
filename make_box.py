#!/usr/bin/env python3
"""Generates Box.asm for your K. Usage: python make_box.py K"""
import sys
K = int(sys.argv[1]) if len(sys.argv) > 1 else 85
if not 0 <= K <= 99:
    sys.exit("K must be between 0 and 99")

W = (K % 4) + 1
START = 16384 + 32 * K
SKIP = 32 - W
FONT = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
}


def label_words(k):
    rows = [[] for _ in range(7)]
    for index, character in enumerate("%02d" % k):
        for row in range(7):
            rows[row].extend(int(pixel) for pixel in FONT[character][row])
            if index == 0:
                rows[row].append(0)

    return [
        [
            int("".join(str(pixel) for pixel in row[start:start + 16]).ljust(16, "0"), 2)
            for start in range(0, len(row), 16)
        ]
        for row in rows
    ]


def label_instructions(k, draw):
    instructions = []
    for row_index, words in enumerate(label_words(k)):
        for word_index, mask in enumerate(words):
            value = mask if draw else 0
            address = 16384 + 32 * row_index + word_index
            if value <= 32767:
                instructions.extend((f"@{value}", "D=A"))
            else:
                instructions.extend(("@32767", "D=A", "D=D+1", f"@{value - 32768}", "D=D+A"))
            instructions.extend((f"@{address}", "M=D"))
    return "\n".join(f"    {instruction}" for instruction in instructions)


draw_label = label_instructions(K, True)
clear_label = label_instructions(K, False)

asm = f"""// Box.asm  K={K}: rows {K}..{K+19}, width {16*W}px ({W} words), left edge
// Screen label {K:02d} is drawn while a key is pressed.
// Start address = SCREEN + 32*{K} = {START}
(MAIN)
    @KBD
    D=M
    @PRESSED
    D;JNE
    @COLOR
    M=0            // no key -> white
    @DRAW
    0;JMP
(PRESSED)
    @COLOR
    M=-1           // key -> black
(DRAW)
    @COLOR
    D=M
    @DRAWTEXT
    D;JNE
    @CLEARTEXT
    0;JMP
(DRAWTEXT)
{draw_label}
    @TEXTDONE
    0;JMP
(CLEARTEXT)
{clear_label}
(TEXTDONE)
    @{START}
    D=A
    @ADDR
    M=D
    @ROW
    M=0
(ROWLOOP)
    @ROW
    D=M
    @20
    D=D-A
    @MAIN
    D;JGE          // 20 rows done
    @COL
    M=0
(COLLOOP)
    @COL
    D=M
    @{W}
    D=D-A
    @NEXTROW
    D;JGE          // row finished
    @COLOR
    D=M
    @ADDR
    A=M
    M=D            // write word
    @ADDR
    M=M+1
    @COL
    M=M+1
    @COLLOOP
    0;JMP
(NEXTROW)
    @{SKIP}
    D=A
    @ADDR
    D=D+M
    M=D            // jump to start of next row
    @ROW
    M=M+1
    @ROWLOOP
    0;JMP
"""
with open("Box.asm", "w") as output:
    output.write(asm)
print(f"Box.asm written (K={K}, width={16*W}px, label=K={K})")
