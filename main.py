from pychip8.emulator import Chip8

if __name__ == '__main__':
    rom_name = 'pong.rom'

    chip8 = Chip8(rom_name)
    chip8.run()