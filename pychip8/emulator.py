import sys
import random
import pygame


class Chip8:
    # Chip 8 has 35 opcodes
    # All of which are two bytes long
    _opcode = None

    # 4k memory, 4096 bits
    _memory = list([0 for i in range(4096)])

    # 15 8-bit general purpose registers named V0, V1,
    # up to VE. The 16th is used for 'carry flag'.
    _v = list([0 for i in range(16)])

    # Index register and Program Counter
    _i = None
    _pc = None

    # Graphics has 2048 pixels (64 x 32)
    _gfx = list([0 for i in range(64 * 32)])

    # Interupts and hardware registers
    _delay_timer = 0
    _sound_timer = 0

    # Stack for remembering the current location
    # before a jump is performed
    _stack = list([0 for i in range(16)])
    _sp = 0

    # Keypad
    _key = list([0 for i in range(16)])

    # Fonts to display numbers / characters
    _chip8_fontset = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
        0x20, 0x60, 0x20, 0x20, 0x70,  # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
        0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
        0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
        0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
        0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    ]

    def __init__(self, rom_loc):
        self.rom_loc = rom_loc

        with open(rom_loc, 'rb') as f:
            rom_binary = f.read()
            self.init_chip8(rom_binary)

    def reset(self):
        with open(self.rom_loc, 'rb') as f:
            rom_binary = f.read()
            self.init_chip8(rom_binary)

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    sys.exit()
                
            state = pygame.key.get_pressed()

            # The input keys are mapped to the original keypad layout:
            # 123C
            # 456D
            # 789E
            # A0BF
            self._keys = [
                state[pygame.K_x], state[pygame.K_1], state[pygame.K_2], state[pygame.K_3],
                state[pygame.K_q], state[pygame.K_w], state[pygame.K_e], state[pygame.K_a],
                state[pygame.K_s], state[pygame.K_d], state[pygame.K_z], state[pygame.K_c],
                state[pygame.K_4], state[pygame.K_r], state[pygame.K_f], state[pygame.K_v]
            ]

            # Emulate cycle
            self.emulate_cycle()

            # Display
            scaled_surface = pygame.transform.scale(self._pygame_screen_surface, (512, 256))

            self._pygame_window.blit(scaled_surface, (0, 0))

            pygame.display.flip()

    def init_chip8(self, rom_binary):
        # Init pygame
        pygame.init()

        self._pygame_window = pygame.display.set_mode((512, 256))
        self._pygame_screen_surface = pygame.Surface((64, 32))
        self._pygame_screen = pygame.PixelArray(self._pygame_screen_surface)

        # Program counter starts at 0x200
        self._pc = 0x200

        # Reset current opcode
        self._opcode = 0x0

        # Reset index stack
        self._i = 0x0

        # Reset stack pointer
        self._sp = 0x0

        # Clear display, stack, registers and memory
        for i in range(len(self._chip8_fontset)):
            self._memory[i] = self._chip8_fontset[i]

        # +512 as program counter starts at 0x200
        # 0x200 in hex is 512
        for i in range(len(rom_binary)):
            self._memory[i + 512] = rom_binary[i]

    def emulate_cycle(self):
        self._opcode = self._memory[self._pc] << 8 | self._memory[self._pc + 1]

        # Decode OPCODE
        opcode_buffer = self._opcode & 0xF000

        # Following the OPCODE table
        # https://en.wikipedia.org/wiki/CHIP-8#Opcode_table
        if opcode_buffer == 0x0000:
            if self._opcode == 0x00E0:
                # 00E0: Clear screen
                self._pygame_screen.surface.fill((0, 0, 0))

            elif self._opcode == 0x00EE:
                # 00EE: Returns from a subroutine
                self._sp = self._sp - 1
                self._pc = self._stack[self._sp]

            else:
                pass

        elif opcode_buffer == 0x1000:
            # 1NNN: Jumps to address NNN
            self._pc = self._opcode & 0x0FFF

            # Decrement the pc to undo the automatic increment after each opcode
            self._pc = self._pc - 2

        elif opcode_buffer == 0x2000:
            # 0x2NNN: Calls subroutine at NNN
            self._stack[self._sp] = self._pc
            self._sp = self._sp + 1
            self._pc = self._opcode & 0x0FFF
            self._pc = self._pc - 2

        elif opcode_buffer == 0x3000:
            # 3XNN: Skips the next instruction if VX equals NN
            if self._v[(self._opcode & 0x0F00) >> 8] == self._opcode & 0x00FF:
                self._pc = self._pc + 2

        elif opcode_buffer == 0x4000:
            # 4XNN: Skips the next isntruction if VX doesn't equal NN
            if self._v[(self._opcode & 0x0F00) >> 8] != self._opcode & 0x00FF:
                self._pc = self._pc + 2

        elif opcode_buffer == 0x5000:
            # 5XY0: Skips the next instruction if Vx equals Vy
            if self._v[(self._opcode & 0x0F00) >> 8] == self._v[(self._opcode & 0x00F0) >> 4]:
                self._pc = self._pc + 2

        elif opcode_buffer == 0x6000:
            # 6XNN: Sets Vx to NN
            self._v[(self._opcode & 0x0F00) >> 8] = self._opcode & 0x00FF

        elif opcode_buffer == 0x7000:
            # 7XNN: Adds NN to Vx (Carry flag is not changed)
            self._v[(self._opcode & 0x0F00) >> 8] += self._opcode & 0x00FF

        elif opcode_buffer == 0x8000:
            opcode_inner_buffer = self._opcode & 0x000F

            if opcode_inner_buffer == 0x0000:
                # 8XY0: Sets Vx to the value of Vy
                self._v[(self._opcode & 0x0F00) >>
                        8] = self._v[(self._opcode & 0x00F0) >> 4]

            elif opcode_inner_buffer == 0x0001:
                # 8XY1: Sets VX to VX | VY. (Bitwise OR operation)
                self._v[(self._opcode & 0x0F00) >> 8] = self._v[(
                    self._opcode & 0x0F00) >> 8] | self._v[(self._opcode & 0x00F0) >> 4]

            elif opcode_inner_buffer == 0x0002:
                # 8XY2: Sets VX to VX and VY. (Bitwise AND operation)
                self._v[(self._opcode & 0x0F00) >> 8] = self._v[(
                    self._opcode & 0x0F00) >> 8] & self._v[(self._opcode & 0x00F0) >> 4]

            elif opcode_inner_buffer == 0x0003:
                # 8XY3:	Sets VX to VX xor VY.
                self._v[(self._opcode & 0x0F00) >> 8] = self._v[(
                    self._opcode & 0x0F00) >> 8] ^ self._v[(self._opcode & 0x00F0) >> 4]

            elif opcode_inner_buffer == 0x0004:
                # 8XY4:	Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't.
                r = int(self._v[(self._opcode & 0x0F00) >> 8]) + \
                    int(self._v[(self._opcode & 0x00F0) >> 4])
                self._v[(self._opcode & 0x0F00) >> 8] = r
                if r > 255:
                    self._v[0xF] = 1
                else:
                    self._v[0xF] = 0

            elif opcode_inner_buffer == 0x0005:
                # 8XY5	Vx -= Vy	VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't.
                r = int(self._v[(self._opcode & 0x0F00) >> 8]) - \
                    int(self._v[(self._opcode & 0x00F0) >> 4])
                self._v[(self._opcode & 0x0F00) >> 8] = r

                if r < 0:
                    self._v[0xF] = 1
                else:
                    self._v[0xF] = 0

            elif opcode_inner_buffer == 0x0006:
                # 8XY6:	Vx=Vy=Vy>>1	Shifts VY right by one and copies the result to VX.
                # VF is set to the value of the least significant bit of VY before the shift.
                lsb = self._v[(self._opcode & 0x00F0) >> 4] & 0x1
                r = self._v[(self._opcode & 0x00F0) >> 4] >> 1
                self._v[(self._opcode & 0x00F0) >> 4] = r
                self._v[(self._opcode & 0x0F00) >> 8] = r
                self._v[0xF] = lsb

            elif opcode_inner_buffer == 0x0007:
                # 8XY7: Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't.
                r = int(self._v[(self._opcode & 0x0F00) >> 8]) - \
                    int(self._v[(self._opcode & 0x00F0) >> 4])
                self._v[(self._opcode & 0x0F00) >> 8] = r

                if r < 0:
                    self._v[0xF] = 1
                else:
                    self._v[0xF] = 0

            elif opcode_inner_buffer == 0x000E:
                # 8XYE:	Vx=Vy=Vy<<1	Shifts VY left by one and copies the result to VX. VF is set to the value of the most significant bit of VY before the shift
                msb = self._v[(self._opcode >> 0x00F0) >> 4] >> 7
                r = self._v[(self._opcode >> 0x00F0) >> 4] << 1
                self._v[(self._opcode >> 0x00F0) >> 4] = r
                self._v[(self._opcode >> 0x0F00) >> 8] = r
                self._v[0xF] = msb

        elif opcode_buffer == 0x9000:
            # 9XY0: Skips the next instruction if VX doesn't equal VY. (Usually the next instruction is a jump to skip a code block)
            if self._v[(self._opcode & 0x0F00) >> 8] != self._v[(self._opcode & 0x00F0) >> 4]:
                self._pc = self._pc + 2

        elif opcode_buffer == 0xA000:
            # ANNN: Sets I to the address NNN.
            self._i = self._opcode & 0x0FFF

        elif opcode_buffer == 0xB000:
            # BNNN:	Jumps to the address NNN plus V0.
            self._pc = (self._opcode & 0x0FFF) + self._v[0x0]

        elif opcode_buffer == 0xC000:
            # CXNN: Sets VX to the result of a bitwise and operation on a random number (Typically: 0 to 255) and NN.
            self._v[(self._opcode & 0x0F00) >> 8] = random.randint(
                0, 255) & (self._opcode & 0x00FF)

        elif opcode_buffer == 0xD000:
            # DXYN: Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N pixels.
            # Each row of 8 pixels is read as bit-coded starting from memory location I;
            # I value doesn’t change after the execution of this instruction.
            # As described above, VF is set to 1 if any screen pixels are flipped from set to unset when the sprite is drawn, and to 0 if that doesn’t happen
            n = self._opcode & 0x000F
            x = self._v[(self._opcode & 0x0F00) >> 8]
            y = self._v[(self._opcode & 0x00F0) >> 4]

            self._v[0xF] = 0

            for row in range(n):
                for col in range(8):
                    pixel = self._memory[int(self._i) + row]

                    if pixel & (0x80 >> col) != 0:
                        # By applying a modulo operation positions outiside the screen will be
                        # wrapped to the other side
                        pos_x = (x + col) % 64
                        pos_y = (y + row) % 32

                        if self._pygame_screen[pos_x, pos_y] == 0xFFFFFF:
                            self._pygame_screen[pos_x, pos_y] = 0x0
                            self._v[0xF] = 1

                        else:
                            self._pygame_screen[pos_x, pos_y] = 0xFFFFFF

        elif opcode_buffer == 0xE000:
            if self._opcode & 0x00FF == 0x009E:
                # EX9E	Skips the next instruction if the key stored in VX is pressed. (Usually the next instruction is a jump to skip a code block)
                if self._key[self._v[(self._opcode & 0x0F00) >> 8]] == 1:
                    self._pc = self._pc + 2

            elif self._opcode & 0x00FF == 0x00A1:
                # EXA1: Skip next instruction if key VX is not pressed
                if self._key[self._v[(self._opcode & 0x0F00) >> 8]] == 0:
                    self._pc = self._pc + 2

        elif opcode_buffer == 0xF000:
            opcode_buffer_inner = self._opcode & 0x00FF

            if opcode_buffer_inner == 0x0007:
                # FX07 Sets VX to the value of the delay timer.
                self._v[(self._opcode & 0x0F00) >> 8] = self._delay_timer

            elif opcode_buffer_inner == 0x000A:
                # FX0A	A key press is awaited, and then stored in VX. (Blocking Operation. All instruction halted until next key event)                
                pressed = False

                for i in range(len(self._key)):
                    if self._key[i] == 1:
                        self._v[(self._opcode & 0x0F00) >> 8] = i
                        pressed = True

            elif opcode_buffer_inner == 0x0015:
                # FX15	Timer	delay_timer(Vx)	Sets the delay timer to VX.
                self._delay_timer = self._v[(self._opcode & 0x0F00) >> 8]
            
            elif opcode_buffer_inner == 0x0018:
                # FX18	Sound	sound_timer(Vx)	Sets the sound timer to VX.
                self._sound_timer = self._v[(self._opcode & 0x0F00) >> 8]
            
            elif opcode_buffer_inner == 0x001E:
                # FX1E	MEM	I +=Vx	Adds VX to I
                self._i = self._i + self._v[(self._opcode & 0x0F00) >> 8]

            elif opcode_buffer_inner == 0x0029:
                # FX29	MEM	I=sprite_addr[Vx]	Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.
                self._i = self._v[(self._opcode & 0x0F00) >> 8] * 5
            
            elif opcode_buffer_inner == 0x0033:
                # FX33: Store the binary coded decimal representation of VX in memory
                # starting at location I
                # (In other words, take the decimal representation of VX, place the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.)
                self._memory[self._i] = self._v[(self._opcode & 0x0F00) >> 8] / 100
                self._memory[self._i+1] = (self._v[(self._opcode & 0x0F00) >> 8] / 10) % 10
                self._memory[self._i+2] = (self._v[(self._opcode & 0x0F00) >> 8] % 100) % 10

            elif opcode_buffer_inner == 0x0055:
                # FX55: Store registers V0 to VX in memory starting at I
                for i in range(((self._opcode & 0x0F00) >> 8) + 1):
                    self._memory[self._i + i] = self._v[i]

            elif opcode_buffer_inner == 0x0065:
                # FX65: Fills V0 to VX (including VX) with values from memory starting at address I. I is increased by 1 for each value written.
                for i in range(((self._opcode & 0x0F00) >> 8) + 1):
                    self._v[i] = self._memory[self._i + i]

        else:
            print('Unknown Opcode: 0x{:04X}'.format(opcode_buffer))

        self._pc = self._pc + 2

        if self._delay_timer > 0:
            self._delay_timer = self._delay_timer - 1
        
        if self._sound_timer > 0:
            self._sound_timer = self._sound_timer - 1

        if self._sound_timer == 0:
            # BEEP
            pass
