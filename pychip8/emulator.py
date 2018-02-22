# Chip 8 has 35 opcodes
# All of which are two bytes long
OPCODE = None

# 4k memory, 4096 bits
MEMORY = list([0 for i in range(4096)])

# 15 8-bit general purpose registers named V0, V1,
# up to VE. The 16th is used for 'carry flag'.
V = list([0 for i in range(16)])

# Index register and Program Counter
I = None
PC = None

# Graphics has 2048 pixels (64 x 32)
GFX = list([0 for i in range(64 * 32)])

# Interupts and hardware registers
DELAY_TIMER = 0
SOUND_TIMER = 0

# Stack for remembering the current location
# before a jumpis performed
STACK = list([0 for i in range(16)])
SP = 0

# Keypad
KEY = list([0 for i in range(16)])